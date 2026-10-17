# Nối agent (code đồng bộ) với MCP server (code async) qua stdio.
# MCP SDK chỉ có hàm async, còn run_agent() gọi call_tool() kiểu bình thường,
# nên ta chạy 1 event loop riêng trong 1 thread nền và gửi việc sang đó.
import asyncio
import os
import sys
import threading
from pathlib import Path
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / "mcp_server" / "server.py"


class MCPClient:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()
        self._ready = threading.Event()
        self._main = asyncio.run_coroutine_threadsafe(self._serve(), self._loop)
        if not self._ready.wait(timeout=120):            # chờ server khởi động (nạp RAG hơi lâu)
            raise RuntimeError("MCP server không khởi động được")
        if self._main.done():                            # server chết ngay lúc khởi động
            self._main.result()

    async def _serve(self):
        # Mở kết nối và GIỮ nó trong 1 coroutine duy nhất đến khi close().
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)],
                                       env=dict(os.environ))
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
                    self.tools = (await session.list_tools()).tools
                    self._stop = asyncio.Event()
                    self._ready.set()
                    await self._stop.wait()
        finally:
            self._ready.set()                            # lỗi thì cũng nhả __init__ ra

    def _run(self, coro, timeout=120):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    @property
    def tool_names(self):
        return {t.name for t in self.tools}

    def tools_text(self):
        # Danh sách tool để chèn vào {tools} trong prompts/system.txt
        lines = []
        for t in self.tools:
            props = t.inputSchema.get("properties", {})
            params = ", ".join(f"{p}: {s.get('type', 'any')}" for p, s in props.items())
            desc = (t.description or "").strip().splitlines()[0] if t.description else ""
            lines.append(f"- {t.name}({params}): {desc}")
        return "\n".join(lines)

    def openai_tools(self):
        # Danh sách tool theo định dạng "function calling" của OpenAI/Groq (cho gpt-oss)
        return [{"type": "function",
                 "function": {"name": t.name,
                              "description": (t.description or "").strip().splitlines()[0] if t.description else "",
                              "parameters": t.inputSchema}}
                for t in self.tools]

    def call_tool(self, name, args) -> str:
        res = self._run(self.session.call_tool(name, args))
        text = "\n".join(c.text for c in res.content if hasattr(c, "text"))
        try:
            text = json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
        except ValueError:
            pass                                         # không phải JSON (vd lỗi) thì giữ nguyên
        if res.isError and not text.startswith("Error"):
            text = "Error: " + text                      # loop.py nhận lỗi qua chữ "Error"
        return text

    def close(self):
        self._loop.call_soon_threadsafe(self._stop.set)
        self._main.result(timeout=30)
        self._loop.call_soon_threadsafe(self._loop.stop)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()