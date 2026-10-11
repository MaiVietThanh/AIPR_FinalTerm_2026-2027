import time, sys, os, json, urllib.request
from pathlib import Path
from dotenv import load_dotenv

_HERE = Path(__file__).resolve().parent
load_dotenv(_HERE.parents[1] / ".env")      # 1. nạp .env TRƯỚC

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.getenv("GROQ_API_KEY")          # 2. rồi mới đọc biến
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
RETRY_CODES ={429, 500, 502, 503, 504}

if not API_KEY:
    raise RuntimeError("Thiếu GROQ_API_KEY trong .env")

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
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage",{})
    return text, usage
    
    

def call_llm(messages, retries=3):
    body = {"model": MODEL, "messages": messages, "temperature": 0, "max_tokens": 512}
    for i in range(retries):
        try:
            return _post(body)  # thành công thì xuất ra terminal luôn
        except urllib.error.HTTPError as e:
            print(f"[llm] HTTP {e.code}: {e.read()[:200]}", file=sys.stderr)
            if e.code != 429 and e.code < 500:
                raise                               # lỗi do mình (400/401/403): dừng ngay
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"[llm] lỗi mạng: {e}", file=sys.stderr)
        time.sleep(2 ** i)                          # chờ 1s, 2s, 4s rồi thử lại
    raise RuntimeError(f"Gọi LLM thất bại sau {retries} lần")


# Test thử call lmm có chạy k
if __name__ == "__main__" :
    print(call_llm([{"role":"user", "content":"Hãy giới thiệt sơ qua về bạn đi? Trả lời ngắn gọn"}]))