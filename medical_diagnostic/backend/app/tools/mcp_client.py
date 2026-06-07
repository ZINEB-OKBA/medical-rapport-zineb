"""
Client MCP — Permet aux agents LangGraph d'appeler les outils via le serveur MCP.
"""
import asyncio
import json
from typing import Any

from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Client MCP async pour appeler les outils du serveur médical."""

    def __init__(self, server_script: str = "../mcp_server/server.py"):
        self.server_script = server_script
        self._session: ClientSession | None = None

    async def __aenter__(self):
        self._server_params = StdioServerParameters(
            command="python",
            args=[self.server_script],
        )
        self._client_ctx = stdio_client(self._server_params)
        read, write = await self._client_ctx.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.__aexit__(*args)
        await self._client_ctx.__aexit__(*args)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Appelle un outil MCP et retourne le résultat textuel."""
        if not self._session:
            raise RuntimeError("MCPClient non initialisé")
        result = await self._session.call_tool(name, arguments)
        if result.content:
            return result.content[0].text
        return ""

    async def list_tools(self) -> list:
        """Liste les outils disponibles sur le serveur MCP."""
        if not self._session:
            raise RuntimeError("MCPClient non initialisé")
        result = await self._session.list_tools()
        return result.tools


# ── Wrappers LangChain (compatibles avec bind_tools) ─────────────────────────

async def mcp_ask_patient(question_index: int) -> str:
    """Appelle ask_patient via MCP."""
    async with MCPClient() as client:
        return await client.call_tool("ask_patient", {"question_index": question_index})


async def mcp_recommend_interim_care(symptoms_text: str) -> str:
    """Appelle recommend_interim_care via MCP."""
    async with MCPClient() as client:
        return await client.call_tool("recommend_interim_care", {"symptoms_text": symptoms_text})
