# Notion MCP Orchestrator

A full-stack application that integrates **Gemini** with the **Notion API** using the **Model Context Protocol (MCP)**. It consists of a FastAPI backend coordinator/MCP bridge and a Next.js chat interface.

---

## Workspace Structure

- **`mcp/`** - Python backend (FastMCP server & FastAPI gateway orchestrator)
- **`frontend/`** - Next.js React frontend (Modern chat UI)

---

## Setup

### 1. Environment Variables
Create a `.env` file in the root directory (or in the `mcp/` folder) with the following variables:
```env
NOTION_TOKEN=your_notion_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Run the Backend
The backend requires Python 3.11+ and `uv`.
```bash
cd mcp
uv run notion-api
```
- **API Docs**: View the interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs)
- **CLI Mode**: Run `uv run notion-chat` to talk to the model directly in your terminal.

### 3. Run the Frontend
The frontend requires Node.js.
```bash
cd frontend
npm install
npm run dev
```
- **Web App**: Open [http://localhost:3000](http://localhost:3000) to chat with your Notion workspace.
