# phần hết hợp parser với call_llm để tạo thành loop

import json
from pathlib import Path
from parser import parse_action
import logger
from llm import call_llm
from logger import RunLogger

MAX_STEPS = 8
_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = (_ROOT / "prompts" / "system.txt").read_text(encoding="utf-8") # promt đang trống nên bỏ qua

VERIFY_TOOL = {                     # tool ghi -> tool đọc để kiểm chứng
    "block_ip": "get_blocklist",
    "unblock_ip": "get_blocklist",
    "lock_account": "get_account_status",
    "create_incident": "get_incident",
}

def _verify_args(name, args, result):
    if name == "lock_account":
        return {"username": args.get("username")}
    if name == "create_incident":
        try:
            return {"incident_id": json.loads(result).get("incident_id")}
        except (ValueError, AttributeError):
            return {}
    return {}                       # get_blocklist không cần tham số

def run_agent(question, call_tool, tools_text, tool_names, logger= None):
    log = logger.log if logger else (lambda *a, **k: None)   # không truyền logger thì bỏ qua
    log("question", question=question)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("{tools}", tools_text)},
        {"role": "user", "content": question},
    ]
    tokens = 0
    for step in range(1, MAX_STEPS + 1):
        text, usage = call_llm(messages)                       # hỏi
        log("llm",step=step, output=text, usage=usage)
        tokens += usage.get("total_tokens", 0)
        messages.append({"role": "assistant", "content": text})
        action = parse_action(text)                            # đọc

        if action.kind == "final":
            log("final", answer=action.text, steps=step, tokens=tokens)
            return {"answer": action.text, "steps": step, "tokens": tokens, "messages": messages}
        if action.kind == "error":
            observation = "Error: " + action.text
        elif action.name not in tool_names:
            observation = (f"Error: unknown tool '{action.name}'. "
                           f"Chỉ được dùng: {', '.join(sorted(tool_names))}")
        else:                                                  # làm
            try:
                observation = call_tool(action.name, action.args)
            except Exception as e:
                observation = f"Error: {e}"                   # tool lỗi -> chuỗi, không raise
            if action.name in VERIFY_TOOL and not observation.startswith("Error"):
                vname = VERIFY_TOOL[action.name]
                try:
                    vresult = call_tool(vname, _verify_args(action.name, action.args, observation))
                except Exception as e:
                    vresult = f"Error: {e}"
                observation += f"\nVerify ({vname}): {vresult}"
        log("observation", step=step, action=action.name, args=action.args, observation=observation)
        messages.append({"role": "user", "content": "Observation: " + observation})   # báo

    return {"answer": f"Dừng vì vượt quá {MAX_STEPS} bước.", "steps": MAX_STEPS,
            "tokens": tokens, "messages": messages}


# Test thửu xem loop chạy đc chưa
if __name__ == "__main__":
    blocklist = set()
    def fake_call_tool(name, args):
        if name == "count_failed_logins":
            return json.dumps({"ip": args.get("ip"), "failed": 23, "window_minutes": 4})
        if name == "block_ip":
            blocklist.add(args["ip"])
            return json.dumps({"ok": True, "ip": args["ip"], "duration_minutes": args.get("duration_minutes")})
        if name == "get_blocklist":
            return json.dumps({"blocked": sorted(blocklist)})
        raise ValueError(f"Không có tool tên {name}")
    names = {"count_failed_logins", "get_blocklist"}
    tools = ("- count_failed_logins(ip: str): đếm số lần đăng nhập sai trong 5 phút\n"
             "- block_ip(ip: str, duration_minutes: int, reason: str): chặn IP\n"
             "- get_blocklist(): xem danh sách IP đang bị chặn")
    result = run_agent("IP 203.0.113.7 sai 23 lần, hãy chặn 1440 phút.", fake_call_tool, tools, names, logger.RunLogger())
    for m in result["messages"][1:]:
        print(m["role"], ":", m["content"][:200])
    print("=>", result["answer"], "| steps:", result["steps"], "| tokens:", result["tokens"])