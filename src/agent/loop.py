# phần hết hợp parser với call_llm để tạo thành loop

import json
from pathlib import Path
from parser import parse_action
from llm import call_llm
from logger import RunLogger

MAX_STEPS = 10
MAX_OBS = 2000
_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = (_ROOT / "prompts" / "system.txt").read_text(encoding="utf-8")

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

def _count_objects(text):
    # Đếm số object JSON nằm liền nhau trong 1 câu trả lời (model đôi khi viết 2 lệnh gọi tool 1 lúc)
    dec, i, n = json.JSONDecoder(), 0, 0
    while True:
        i = text.find("{", i)
        if i < 0:
            return n
        try:
            _, i = dec.raw_decode(text, i)
            n += 1
        except ValueError:
            i += 1

def run_agent(question, call_tool, tools_text, tool_names, logger= None):
    log = logger.log if logger else (lambda *a, **k: None)   # không truyền logger thì bỏ qua
    log("question", question=question)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("{tools}", tools_text)},
        {"role": "user", "content": question},
    ]
    tokens = 0
    usage_sum = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "max_prompt": 0}   # USAGE cả câu hỏi
    for step in range(1, MAX_STEPS + 1):
        text, usage = call_llm(messages)                       # hỏi
        log("llm",step=step, output=text, usage=usage)
        tokens += usage.get("total_tokens", 0)
        usage_sum["calls"] += 1
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            usage_sum[k] += usage.get(k, 0)
        usage_sum["max_prompt"] = max(usage_sum["max_prompt"], usage.get("prompt_tokens", 0))   # request lớn nhất
        messages.append({"role": "assistant", "content": text})
        action = parse_action(text)                            # đọc

        if action.kind == "final":
            log("final", answer=action.text, steps=step, tokens=tokens)
            log("usage", **usage_sum)
            return {"answer": action.text, "steps": step, "tokens": tokens, "usage": usage_sum, "messages": messages}
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
            if not isinstance(observation, str):            # phòng khi call_tool trả về dict
                observation = json.dumps(observation, ensure_ascii=False)
            if action.name in VERIFY_TOOL and not observation.startswith("Error"):
                vname = VERIFY_TOOL[action.name]
                try:
                    vresult = call_tool(vname, _verify_args(action.name, action.args, observation))
                except Exception as e:
                    vresult = f"Error: {e}"
                observation += f"\nVerify ({vname}): {vresult}"
        if len(observation) > MAX_OBS:                   # chống tràn context / vượt giới hạn token
            observation = observation[:MAX_OBS] + " ...(đã cắt bớt)"
        if action.kind != "error" and _count_objects(text) > 1:   # chỉ chạy lệnh đầu tiên -> báo cho model biết
            observation += (f"\nLưu ý: lượt này bạn viết nhiều lệnh, chỉ lệnh đầu tiên ({action.name}) được chạy. "
                            "Các lệnh sau CHƯA chạy, hãy gọi lại từng lệnh ở lượt tiếp theo.")
        log("observation", step=step, action=action.name, args=action.args, observation=observation)
        messages.append({"role": "user", "content": "Observation: " + observation})   # báo

    log("final", answer=f"Dừng vì vượt quá {MAX_STEPS} bước.", steps=MAX_STEPS, tokens=tokens)
    log("usage", **usage_sum)
    return {"answer": f"Dừng vì vượt quá {MAX_STEPS} bước.", "steps": MAX_STEPS,
            "tokens": tokens, "usage": usage_sum, "messages": messages}


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
    result = run_agent("IP 203.0.113.7 sai 23 lần, hãy chặn 1440 phút.", fake_call_tool, tools, names, RunLogger())
    for m in result["messages"][1:]:
        print(m["role"], ":", m["content"][:200])
    print("=>", result["answer"], "| steps:", result["steps"], "| tokens:", result["tokens"])