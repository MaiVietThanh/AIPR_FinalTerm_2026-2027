# Test thủ công các tool ĐỌC qua MCP server thật (không cần LLM):  python tests\test_read_tools.py
# Có cả trường hợp lỗi (tài khoản / sự cố không tồn tại) để xem server trả isError mà không bị dừng.
import os
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / "src" / "mcp_server" / "server.py"

CALLS = [
    ("get_blocklist", {}),
    ("get_account_status", {"username": "tuananh"}),
    ("get_account_status", {"username": "khongco"}),
    ("get_incident", {"incident_id": "INC-9999"}),
    ("search_docs", {"query": "ngưỡng brute-force hiện hành"}),
]

async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = [t.name for t in (await session.list_tools()).tools]
            print(len(names), "tool:", names)
            for name, args in CALLS:
                res = await session.call_tool(name, args)
                print(f"\n>>> {name}({args})  isError={res.isError}")
                print(res.content[0].text[:300] if res.content else "(rỗng)")

asyncio.run(main())