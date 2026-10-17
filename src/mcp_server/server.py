import logging
import sys
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Code RAG của Tuyết dùng đường dẫn tương đối "data/index", nên chuyển về thư mục gốc dự án
os.chdir(Path(__file__).resolve().parents[2])

# stdout là đường truyền tin nhắn MCP, nên log phải ra stderr
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

import tools    # import SAU khi đã chdir và cấu hình log, vì tools nạp RAG ngay lúc import

mcp = FastMCP("soc-server")

READ_TOOLS = [tools.search_docs, tools.query_auth_logs, tools.count_failed_logins,
              tools.get_blocklist, tools.get_incident, tools.get_account_status]
WRITE_TOOLS = [tools.block_ip, tools.unblock_ip, tools.create_incident, tools.lock_account]

for fn in READ_TOOLS + WRITE_TOOLS:
    mcp.tool()(fn)

if __name__ == "__main__":
    mcp.run()          # mặc định chạy qua stdio