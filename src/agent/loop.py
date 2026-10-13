# phần hết hợp parser với call_llm để tạo thành loop

import json
from pathlib import Path
from llm import call_llm
from parser import parse_action

MAX_STEPS = 8
_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = (_ROOT / "prompts" / "system.txt").read_text(encoding="utf-8") # promt đang trống nên bỏ qua

def run_agent(question, call_tool, tools_text):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("{tools}", tools_text)},
        {"role": "user", "content": question},
    ]
    tokens = 0
    for step in range(1, MAX_STEPS + 1):
        text, usage = call_llm(messages)                       # hỏi
        tokens += usage.get("total_tokens", 0)
        messages.append({"role": "assistant", "content": text})
        action = parse_action(text)                            # đọc

        if action.kind == "final":
            return {"answer": action.text, "steps": step, "tokens": tokens, "messages": messages}
        if action.kind == "error":
            observation = "Error: " + action.text
        else:                                                  # làm
            try:
                observation = call_tool(action.name, action.args)
            except Exception as e:
                observation = f"Error: {e}"                    # tool lỗi -> chuỗi, không raise
        messages.append({"role": "user", "content": "Observation: " + observation})   # báo

    return {"answer": f"Dừng vì vượt quá {MAX_STEPS} bước.", "steps": MAX_STEPS,
            "tokens": tokens, "messages": messages}


# Test thửu xem loop chạy đc chưa
if __name__ == "__main__":
    def fake_call_tool(name, args):
        if name == "count_failed_logins":
            return json.dumps({"ip": args.get("ip"), "failed": 23, "window_minutes": 4})
        raise ValueError(f"Không có tool tên {name}")

    tools = "- count_failed_logins(ip: str): đếm số lần đăng nhập sai của IP trong 5 phút gần nhất"
    result = run_agent("IP 203.0.113.7 đăng nhập sai bao nhiêu lần?", fake_call_tool, tools)
    for m in result["messages"][1:]:
        print(m["role"], ":", m["content"][:200])
    print("=>", result["answer"], "| steps:", result["steps"], "| tokens:", result["tokens"])