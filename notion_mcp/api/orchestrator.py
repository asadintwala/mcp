"""Gemini + MCP Orchestrator.

This module is the *brain* of the system.  It:
1. Receives a user message and session history.
2. Sends it to Gemini Flash along with MCP tool declarations.
3. When Gemini returns function_call parts, routes them through the MCP
   Bridge (which calls the MCP server).
4. Feeds MCP responses back to Gemini until it produces a text answer.

The orchestrator never imports tool Python functions directly — it only
knows tool *schemas* obtained from MCP at startup.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from google import genai
from google.genai import types

from notion_mcp.api.mcp_bridge import get_bridge
from notion_mcp.api.session_store import Session

logger = logging.getLogger(__name__)

# System prompt that guides Gemini's behaviour
SYSTEM_INSTRUCTION = (
    "You are an advanced Notion Assistant powered by Gemini and the Notion MCP server.\n"
    "You have access to tools that interact with the user's Notion workspace.\n\n"
    "GUIDELINES:\n"
    "1. Never guess or hallucinate. Always call tools to fetch real data.\n"
    "2. When asked about counts of databases/pages, call `search` with appropriate filter_value.\n"
    "3. Remember IDs from previous messages — never ask the user for an ID you already know.\n"
    "4. Always display IDs alongside names so the user can reference them later.\n"
    "5. Present results in a clean, readable format.\n"
)

# Keys that appear in JSON Schema but are not accepted by Gemini
_STRIP_KEYS = {"additionalProperties", "additional_properties", "$schema", "default"}


def _clean_schema(obj: Any) -> Any:
    """Recursively remove keys that Gemini's function calling API rejects."""
    if isinstance(obj, dict):
        cleaned: dict[str, Any] = {}
        for k, v in obj.items():
            if k in _STRIP_KEYS:
                continue
            # Gemini does not support "anyOf" — flatten to the first variant
            if k == "anyOf" and isinstance(v, list):
                # Pick the first non-null type if possible
                for variant in v:
                    if isinstance(variant, dict) and variant.get("type") != "null":
                        return _clean_schema(variant)
                # All variants are null; just return string type
                return {"type": "string"}
            cleaned[k] = _clean_schema(v)
        return cleaned
    elif isinstance(obj, list):
        return [_clean_schema(item) for item in obj]
    return obj


def _mcp_schemas_to_function_declarations(
    mcp_tools: list[dict[str, Any]],
) -> list[types.FunctionDeclaration]:
    """Convert MCP tool schemas into Gemini FunctionDeclaration objects."""
    declarations = []
    for tool in mcp_tools:
        params_schema = copy.deepcopy(tool.get("parameters", {}))
        # Clean the schema of unsupported keys
        params_schema = _clean_schema(params_schema)

        decl = types.FunctionDeclaration(
            name=tool["name"],
            description=tool.get("description", ""),
            parameters_json_schema=params_schema if params_schema else None,
        )
        declarations.append(decl)
    return declarations


class Orchestrator:
    """Stateless orchestrator — each call gets session history explicitly."""

    def __init__(self, gemini_api_key: str) -> None:
        self._client = genai.Client(api_key=gemini_api_key)

    async def chat(
        self,
        user_message: str,
        session: Session,
        *,
        model: str = "gemini-2.5-flash",
        max_tool_rounds: int = 10,
    ) -> str:
        """Process a single user message, potentially calling MCP tools.

        Returns the final assistant text response.
        """
        bridge = await get_bridge()

        # Build Gemini tool declarations from MCP schemas
        func_decls = _mcp_schemas_to_function_declarations(bridge.tools)
        gemini_tools = [types.Tool(function_declarations=func_decls)]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=gemini_tools,
            temperature=0.2,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        )

        # Build conversation contents from session history + new user msg
        contents = list(session.history)  # shallow copy
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        tool_call_log: list[dict[str, Any]] = []

        for _round in range(max_tool_rounds):
            response = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            # Check if the response contains function calls
            function_calls = []
            text_parts = []
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                    elif part.text:
                        text_parts.append(part.text)

            if not function_calls:
                # No more tool calls — Gemini produced a final answer
                final_text = "\n".join(text_parts) if text_parts else "(no response)"

                # Persist history
                session.history.append(
                    {"role": "user", "parts": [{"text": user_message}]}
                )
                session.history.append(
                    {"role": "model", "parts": [{"text": final_text}]}
                )

                return final_text

            # Gemini wants to call tools — append its request to contents
            fc_parts = []
            for fc in function_calls:
                fc_parts.append(types.Part(function_call=fc))
            contents.append({"role": "model", "parts": fc_parts})

            # Execute each tool call through MCP
            fr_parts = []
            for fc in function_calls:
                name = fc.name
                args = dict(fc.args) if fc.args else {}

                logger.info("[Orchestrator] Tool call: %s(%s)", name, args)
                tool_call_log.append({"tool": name, "args": args})

                result = await bridge.call_tool(name, args)

                fr_parts.append(
                    types.Part.from_function_response(
                        name=name,
                        response={"result": result},
                    )
                )

            contents.append({"role": "user", "parts": fr_parts})

        # Exhausted tool rounds
        return "(Reached maximum tool call rounds without a final answer)"
