# Test nhanh MCP server: liệt kê tool + tham số, gọi count_failed_logins 1 lần đúng và 1 lần sai tham số.
#   python tests\test_server.py
import os
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / "src" / "mcp_server" / "server.py"

async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            for t in listed.tools:
                print("TOOL:", t.name, "| tham số:", list(t.inputSchema["properties"]))
            res = await session.call_tool("count_failed_logins", {"ip": "203.0.113.7"})
            print("isError:", res.isError)
            print(res.content[0].text)
            res = await session.call_tool("count_failed_logins", {"ip": "203.0.113.7", "window_minutes": 0})
            print("isError:", res.isError, "|", res.content[0].text)

asyncio.run(main())