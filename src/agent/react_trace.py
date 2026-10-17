# Đọc 1 file log .jsonl và in lại theo vòng ReAct: Thought -> Action -> Observation -> ... -> Final Answer
import json
import textwrap

WIDTH = 100                                  # độ rộng 1 dòng khi in ra terminal
LINE = "-" * WIDTH

def _pretty(text):
    # Observation thường là JSON viết liền 1 dòng -> in thụt lề cho dễ đọc.
    # Dòng "Verify (tool): {...}" do loop.py nối thêm cũng được tách ra và in đẹp.
    out = []
    for part in str(text).split("\n"):
        head, sep, body = part.partition(": ") if part.startswith("Verify") else ("", "", part)
        try:
            obj = json.loads(body)
            body = json.dumps(obj, ensure_ascii=False, indent=2)
        except ValueError:
            pass
        out.append(f"{head}{sep}{body}")
    return "\n".join(out)

def _wrap(label, text):
    # "Thought     : chữ dài..." -> xuống dòng, các dòng sau thụt vào thẳng hàng sau dấu ":"
    pad = " " * (len(label) + 2)
    lines = []
    for para in str(text).splitlines() or [""]:
        lines += textwrap.wrap(para, WIDTH - len(pad)) or [""]
    return f"{label}: " + ("\n" + pad).join(lines)

def _indent(label, text):
    pad = " " * (len(label) + 2)
    return f"{label}: " + text.replace("\n", "\n" + pad)

def format_trace(records):
    # records = list các dòng log (dict). Trả về 1 chuỗi nhiều dòng.
    out = []
    for r in records:
        ev = r.get("event")
        if ev == "question":
            out += ["", "=" * WIDTH, _wrap("Câu hỏi", r["question"]), "=" * WIDTH]
        elif ev == "llm":
            try:
                obj = json.loads(r.get("output") or "")
            except ValueError:
                obj = {}
            thought = (obj.get("thought") if isinstance(obj, dict) else "") or r.get("reasoning") or "(model không ghi suy nghĩ)"
            out += ["", f"[Bước {r['step']}]", _wrap("Thought     ", thought)]
        elif ev == "observation":
            out.append(f"Action      : {r['action'] or '(không đọc được lệnh)'}")
            if r.get("args"):
                out.append(_indent("Action Input", json.dumps(r["args"], ensure_ascii=False, indent=2)))
            out.append(_indent("Observation ", _pretty(r["observation"])))
        elif ev == "final":
            out += ["", LINE, _wrap("Final Answer", r["answer"]),
                    f"({r['steps']} bước, {r['tokens']} token)"]
        elif ev == "usage":
            out.append(f"USAGE: {r['calls']} lần gọi LLM, prompt {r['prompt_tokens']} + "
                       f"completion {r['completion_tokens']} token, prompt lớn nhất {r['max_prompt']}")
    return "\n".join(out)

def read_log(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
