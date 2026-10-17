import time, sys, os, json, urllib.request
from pathlib import Path
from dotenv import load_dotenv
import truststore

truststore.inject_into_ssl()
_HERE = Path(__file__).resolve().parent
load_dotenv(_HERE.parents[1] / ".env")      # 1. nạp .env TRƯỚC

API_URL = os.getenv("LLM_URL", "https://api.groq.com/openai/v1/chat/completions")   # đổi nhà cung cấp qua .env
API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")          # 2. rồi mới đọc biến
MODEL = os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
JSON_MODE = os.getenv("LLM_JSON_MODE", "1") == "1"          # gpt-oss: đặt 0 (model này lỗi khi bật JSON mode)
REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT")         # gpt-oss: low | Qwen: none | bên khác: để trống
NATIVE_TOOLS = os.getenv("LLM_NATIVE_TOOLS", "0") == "1"  # gpt-oss: đặt 1 (gọi tool theo kiểu gốc của model)
TOOLS = None                                                 # set_tools() điền vào khi NATIVE_TOOLS=1
RETRY_CODES ={429, 500, 502, 503, 504}

if not API_KEY:
    raise RuntimeError("Thiếu GROQ_API_KEY trong .env")

def set_tools(tools):
    # ask.py / run_eval.py gọi hàm này với client.openai_tools(); chỉ có tác dụng khi LLM_NATIVE_TOOLS=1
    global TOOLS
    if NATIVE_TOOLS:
        TOOLS = tools

def _post(body): # Lấy text và usage sd trong call llm
    req=urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization":"Bearer " + API_KEY,
                "Content-Type":"application/json",
                "User-Agent": "soc-agent/0.1"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data=json.loads(resp.read())
    msg = data["choices"][0]["message"]
    text = msg.get("content") or ""
    usage = data.get("usage",{})
    if msg.get("tool_calls"):                # model gọi tool kiểu gốc -> đổi sang JSON {"action","args"} của mình
        fn = msg["tool_calls"][0]["function"]   # chỉ lấy lệnh gọi đầu tiên, mỗi bước 1 tool
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except ValueError:
            args = {}
        return json.dumps({"thought": text.strip(), "action": fn["name"], "args": args},
                          ensure_ascii=False), usage
    return _normalize(text), usage

def _normalize(text):
    # gpt-oss hay trả câu trả lời cuối dạng chữ thường, không bọc JSON -> coi là final_answer
    if text.strip() and "{" not in text:
        return json.dumps({"thought": "", "final_answer": text.strip()}, ensure_ascii=False)
    return text

def _from_tool_call(err):
    # gpt-oss hay tự "gọi tool" theo kiểu gốc của nó -> Groq báo lỗi tool_use_failed kèm failed_generation.
    # Lấy lại lệnh gọi đó và đổi sang định dạng JSON của mình.
    try:
        call = json.loads(json.loads(err)["error"]["failed_generation"])
        return json.dumps({"thought": "", "action": call["name"],
                           "args": call.get("arguments") or {}}, ensure_ascii=False)
    except (ValueError, KeyError, TypeError):
        return None

def call_llm(messages, retries=5, use_tools=True):  # judge gọi với use_tools=False
    body = {"model": MODEL, "messages": messages, "temperature": 0, "max_tokens": 2048}
    if TOOLS and use_tools:
        body["tools"] = TOOLS
        body["tool_choice"] = "auto"
    elif JSON_MODE:
        body["response_format"] = {"type": "json_object"}     # ép trả JSON
    if REASONING_EFFORT:
        body["reasoning_effort"] = REASONING_EFFORT
    for i in range(retries):
        wait=2**i
        try:
            return _post(body)  # thành công thì xuất ra terminal luôn
        except urllib.error.HTTPError as e:
            err = e.read()
            print(f"[llm] HTTP {e.code}: {err[:200]}", file=sys.stderr)
            if b"per day" in err:                   # hết giới hạn theo NGÀY: chờ cũng vô ích, dừng luôn
                raise RuntimeError("Hết giới hạn token/request theo ngày của LLM: chờ sang ngày mới hoặc đổi model/nhà cung cấp")
            if e.code == 400 and b"tool_use_failed" in err:
                text = _from_tool_call(err)
                if text:
                    return text, {}
            if e.code == 400 and b"json_validate_failed" in err and "response_format" in body:
                print("[llm] model không hợp JSON mode, thử lại không ép JSON", file=sys.stderr)
                body.pop("response_format")
                continue                            # thử lại ngay, không cần chờ
            if e.headers.get("retry-after"):
                wait = float(e.headers["retry-after"]) + 1   # Groq bảo chờ bao lâu thì chờ bấy lâu
                if wait > 120:
                    raise RuntimeError(f"LLM bắt chờ {wait:.0f} giây, quá lâu nên dừng")
            if e.code != 429 and e.code < 500:
                raise                               # lỗi do mình (400/401/403): dừng ngay
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"[llm] lỗi mạng: {e}", file=sys.stderr)
        time.sleep(wait)                          # đợi đến khi chạy đc thì thôi
    raise RuntimeError(f"Gọi LLM thất bại sau {retries} lần")


# Test thử call lmm có chạy k
if __name__ == "__main__" :
    print(call_llm([{"role":"user", "content":"Hãy giới thiệt sơ qua về bạn đi? Trả lời ngắn gọn"}]))
