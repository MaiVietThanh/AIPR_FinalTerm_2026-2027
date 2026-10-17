# MCP server "soc-server": đăng ký 10 hàm trong tools.py thành tool MCP và chạy qua stdio.
# Agent (mcp_client.py) và các script test khởi động file này làm tiến trình con.
import logging
import sys
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Chuyển về thư mục gốc dự án để đường dẫn tương đối (nếu có) luôn tính từ gốc.
# Trước đây RAG dùng "data/index" tương đối; nay đã đổi sang đường dẫn tuyệt đối nhưng vẫn giữ cho chắc
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