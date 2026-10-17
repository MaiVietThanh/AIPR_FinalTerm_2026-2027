import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src" / "mcp_server" / "server.py"
sys.path.insert(0, str(ROOT / "src" / "mcp_server"))
from store import reset_state

CALLS = [
    ("block_ip", {"ip": "10.0.5.12", "severity": "High", "duration_minutes": 1440,
                  "reason": "15 lần sai", "doc_id": "SEC-02"}),                 # nội bộ -> phải lỗi
    ("create_incident", {"ip": "203.0.113.7", "severity": "High", "status": "resolved",
                         "summary": "x", "evidence": "x", "doc_ids": ["SEC-02"]}),  # resolved -> phải lỗi
    ("create_incident", {"ip": "203.0.113.7", "severity": "High", "status": "open",
                         "summary": "Brute-force 23 lần/4 phút", "evidence": "max_failed_in_window=23",
                         "doc_ids": ["SEC-02", "SEC-04"]}),
    ("block_ip", {"ip": "203.0.113.7", "severity": "High", "duration_minutes": 1440,
                  "reason": "23 lần sai trong 5 phút", "doc_id": "SEC-02", "incident_id": "INC-0001"}),
    ("block_ip", {"ip": "203.0.113.7", "severity": "High", "duration_minutes": 1440,
                  "reason": "lặp lại", "doc_id": "SEC-02"}),                    # -> already_blocked
    ("get_blocklist", {}),
    ("lock_account", {"username": "tuananh", "reason": "SEC-10: sai 6 lần rồi đăng nhập được"}),
    ("get_account_status", {"username": "tuananh"}),
    ("unblock_ip", {"ip": "203.0.113.7", "reason": "test"}),
    ("get_blocklist", {}),
]

async def main():
    reset_state()
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = [t.name for t in (await session.list_tools()).tools]
            print(len(names), "tool:", names)
            for name, args in CALLS:
                res = await session.call_tool(name, args)
                print(f"\n>>> {name}  isError={res.isError}")
                print(res.content[0].text[:250] if res.content else "(rỗng)")
    reset_state()
    print("\nĐã reset_state() về ban đầu.")

asyncio.run(main())