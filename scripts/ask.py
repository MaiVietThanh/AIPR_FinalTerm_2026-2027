# Hỏi agent 1 câu, chạy với MCP server thật:  python scripts\ask.py "câu hỏi"
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "agent"))

from llm import set_tools
from loop import run_agent
from logger import RunLogger
from mcp_client import MCPClient

question = " ".join(sys.argv[1:]) or "Kiểm tra IP 203.0.113.7 và xử lý theo playbook."

with MCPClient() as client:
    print(len(client.tool_names), "tool:", sorted(client.tool_names))
    set_tools(client.openai_tools())
    result = run_agent(question, client.call_tool, client.tools_text(),
                       client.tool_names, RunLogger())

for m in result["messages"][2:]:
    print(f"\n[{m['role']}] {m['content'][:300]}")
print("\n=> TRẢ LỜI:", result["answer"])
print(f"   ({result['steps']} bước, {result['tokens']} token)")