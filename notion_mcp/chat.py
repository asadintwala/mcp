"""Interactive natural language chat client for Notion MCP using Gemini 2.5 Flash."""

from __future__ import annotations

import asyncio
import os
import sys
from dotenv import load_dotenv

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding crashes on Windows
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Import standard tools from the project
from notion_mcp.tools.search import search
from notion_mcp.tools.pages import (
    retrieve_page,
    create_page,
    update_page_properties,
    archive_page,
    move_page,
)
from notion_mcp.tools.blocks import retrieve_block_children, append_block_children
from notion_mcp.tools.databases import (
    retrieve_database,
    retrieve_data_source,
    query_data_source,
    create_data_source,
)
from notion_mcp.tools.comments import list_comments, create_comment
from notion_mcp.tools.users import list_users, retrieve_user

# List of tools to register with Gemini
notion_tools = [
    search,
    retrieve_page,
    create_page,
    update_page_properties,
    archive_page,
    move_page,
    retrieve_block_children,
    append_block_children,
    retrieve_database,
    retrieve_data_source,
    query_data_source,
    create_data_source,
    list_comments,
    create_comment,
    list_users,
    retrieve_user,
]


async def _run() -> None:
    # Load environment variables from .env file
    load_dotenv()

    notion_token = os.environ.get("NOTION_TOKEN")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if not notion_token:
        print("ERROR: NOTION_TOKEN is not set in your .env file.", file=sys.stderr)
        sys.exit(1)

    if not gemini_api_key:
        print("ERROR: GEMINI_API_KEY is not set in your .env file.", file=sys.stderr)
        sys.exit(1)

    print("Initializing Gemini Client & importing tools...")
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: google-genai package is not installed. Run 'uv sync' or 'pip install google-genai'.", file=sys.stderr)
        sys.exit(1)

    # Initialize Google GenAI client
    client = genai.Client(api_key=gemini_api_key)

    # System instruction guiding the model to use tools to fetch real data
    system_instruction = (
        "You are an advanced Notion Assistant powered by Gemini 2.5 Flash and the Notion MCP server.\n"
        "You have access to a set of Python functions (tools) that can interact directly with the user's Notion workspace. "
        "Use these tools whenever the user asks for real-time information or actions in Notion.\n\n"
        "GUIDELINES:\n"
        "1. Never guess or hallucinate pages, databases, or users. Always query Notion first.\n"
        "2. When asked 'How many databases and pages are there?', use the `search` tool. Call it once with filter_value='page' to count the pages, "
        "and call it once with filter_value='data_source' to count the databases. Present a clean summary of both counts and list the names and IDs.\n"
        "3. Keep track of page/database IDs mentioned in the conversation. When the user asks subsequent questions about "
        "one of them (e.g., 'What are the comments on it?' or 'Show me the contents of the database'), use the saved/referenced "
        "ID from the chat history automatically without asking the user to provide the ID again.\n"
        "4. Display IDs of pages/databases you find so that the user is aware of them."
    )

    print("Starting chat session with Gemini 2.5 Flash...")
    # We will use manual tool execution so we can print exactly what tools Gemini is calling.
    chat = client.chats.create(
        model="gemini-flash-latest",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=notion_tools,
            temperature=0.2,
            automatic_function_calling={"disable": True},
        ),
    )

    print("\n=================================================================")
    print("Welcome to the Notion Natural Language Assistant!")
    print("You can chat naturally. Type 'exit' or 'quit' to end the session.")
    print("=================================================================\n")

    # Map function names to their python references
    tool_map = {func.__name__: func for func in notion_tools}

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            print("\nGemini is thinking...")
            
            # Send the initial user message
            response = chat.send_message(user_input)

            # Process function calls in a loop (the model may request multiple tool calls sequentially)
            while response.function_calls:
                # We collect the function responses to send them all back
                tool_responses = []
                for call in response.function_calls:
                    name = call.name
                    args = dict(call.args) if call.args else {}
                    
                    print(f"-> [TOOL REQUEST] Calling {name} with arguments: {args}")
                    
                    func = tool_map.get(name)
                    if func:
                        try:
                            # Invoke tool function (now async)
                            result = await func(**args)
                            
                            # Print summary of the result to keep terminal output clean
                            if isinstance(result, dict) and "results" in result:
                                items_count = len(result["results"])
                                print(f"<- [TOOL OUTPUT] {name} returned {items_count} items.")
                            elif isinstance(result, dict) and "error" in result:
                                print(f"<- [TOOL ERROR] {name} failed: {result['error']}")
                            else:
                                print(f"<- [TOOL OUTPUT] {name} executed successfully.")
                        except Exception as e:
                            result = {"error": str(e)}
                            print(f"<- [TOOL ERROR] {name} raised exception: {e}")
                    else:
                        result = {"error": f"Tool '{name}' not found."}
                        print(f"<- [TOOL ERROR] Tool '{name}' not found.")
                    
                    # Create the function response part
                    part = types.Part.from_function_response(
                        name=name,
                        response={"result": result}
                    )
                    tool_responses.append(part)

                # Send the function responses back to Gemini
                print("\nSending tool results back to Gemini...")
                response = chat.send_message(tool_responses)

            print(f"\nAssistant: {response.text}\n")
            print("-" * 65)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n", file=sys.stderr)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
