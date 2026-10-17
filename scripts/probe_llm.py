# Thử 1 model Groq với nhiều cấu hình, xem cấu hình nào chạy. Dùng xong có thể xoá.
# python scripts\probe_llm.py qwen/qwen3.8-27b
from pathlib import Path
import truststore; truststore.inject_into_ssl()
ROOT = Path(__file__).resolve().parents[1]
import json, urllib.request, urllib.error, os, sys
from dotenv import dotenv_values
env = dotenv_values(ROOT/".env")
key = env.get("LLM_API_KEY") or env["GROQ_API_KEY"]
URL = env.get("LLM_URL") or "https://api.groq.com/openai/v1/chat/completions"
sysmsg = open(ROOT/"prompts"/"system.txt", encoding="utf-8").read().replace("{tools}", "- search_docs(query: string): tìm playbook\n- count_failed_logins(ip: string): đếm lần sai")
msgs=[{"role":"system","content":sysmsg},{"role":"user","content":"Kiểm tra IP 203.0.113.7 và xử lý theo playbook."}]
def call(model, extra):
    body={"model":model,"messages":msgs,"temperature":0,"max_tokens":2048, **extra}
    req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","User-Agent":"soc-agent/0.1"})
    try:
        d=json.loads(urllib.request.urlopen(req,timeout=60).read())
        print("OK", repr(d["choices"][0]["message"]["content"][:200]), d.get("usage",{}).get("total_tokens"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read()[:300])
    except Exception as e:
        print("EXC", repr(e)[:200])
M=sys.argv[1] if len(sys.argv)>1 else 'qwen/qwen3.8-27b'
for extra in [ {"response_format":{"type":"json_object"},"reasoning_effort":"none"},
               {"response_format":{"type":"json_object"}},
               {"reasoning_effort":"none"},
               {"reasoning_format":"hidden"},
               {} ]:
    print(M, list(extra.items())); call(M, extra)
