# Hỏi agent 1 câu, chạy với MCP server thật:  python scripts\ask.py "câu hỏi"
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "agent"))

from llm import set_tools
from loop import run_agent
from logger import RunLogger
from mcp_client import MCPClient
from react_trace import format_trace, read_log

question = " ".join(sys.argv[1:]) or "Kiểm tra IP 203.0.113.7 và xử lý theo playbook."

with MCPClient() as client:
    print(len(client.tool_names), "tool:", sorted(client.tool_names))
    set_tools(client.openai_tools())
    logger = RunLogger()
    result = run_agent(question, client.call_tool, client.tools_text(),
                       client.tool_names, logger)

print(format_trace(read_log(logger.path)))     # in lại theo Thought / Action / Observation
print(f"\nLog: {logger.path}")