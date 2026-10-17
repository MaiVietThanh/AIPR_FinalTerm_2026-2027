# Chạy toàn bộ tests/testset.jsonl và chấm điểm agent.
#   python scripts\run_eval.py                 chạy hết
#   python scripts\run_eval.py --only T01,T03  chạy vài câu
#   python scripts\run_eval.py --no-judge      bỏ LLM judge (đỡ tốn token)
#   python scripts\run_eval.py --resume        chạy tiếp các câu chưa có trong results/eval.csv
import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "agent"))
sys.path.insert(0, str(ROOT / "src" / "mcp_server"))

from llm import call_llm, set_tools
from logger import RunLogger
from loop import run_agent
from mcp_client import MCPClient
from parser import _extract_json
from store import read_state, reset_state

TESTSET = ROOT / "tests" / "testset.jsonl"
USAGE_KEYS = ("calls", "prompt_tokens", "completion_tokens", "max_prompt")
REFUSAL_TYPES = {"no_answer", "no_evidence"}   # câu agent phải từ chối: không có trong tài liệu / không đủ bằng chứng
RESULTS = ROOT / "results"
JUDGE_PROMPT = (ROOT / "prompts" / "judge.txt").read_text(encoding="utf-8")
MAX_CONTEXT = 12000         # ký tự bằng chứng gửi cho judge, tránh vượt giới hạn token của Groq


# ---------- 1. Chấm state: so 3 file JSON với expected_state ----------
def actual_state():
    blocked = {e["ip"]: e["duration_minutes"] for e in read_state("blocklist")}
    incidents = [{"ip": i["ip"], "severity": i["severity"], "status": i["status"]}
                 for i in read_state("incidents")]
    locked = sorted(a["username"] for a in read_state("accounts") if a["locked"])
    return {"blocked": blocked, "incidents": incidents, "locked": locked}


def _as_set(incidents):
    return Counter((i["ip"], i["severity"], i["status"]) for i in incidents)


def check_state(expected, actual):
    """Trả về danh sách chỗ sai; rỗng = đúng hoàn toàn."""
    errors = []
    if expected["blocked"] != actual["blocked"]:
        errors.append(f"blocked: cần {expected['blocked']}, có {actual['blocked']}")
    if _as_set(expected["incidents"]) != _as_set(actual["incidents"]):
        errors.append(f"incidents: cần {expected['incidents']}, có {actual['incidents']}")
    if sorted(expected["locked"]) != actual["locked"]:
        errors.append(f"locked: cần {expected['locked']}, có {actual['locked']}")
    return errors


# ---------- 2. Chấm câu trả lời: có trích đúng tài liệu, có chữ cần có ----------
def check_answer(case, answer):
    answer = answer.replace("\u2011", "-").replace("\u2010", "-").replace("\u2013", "-")  # model hay viết SEC‑03 bằng gạch nối đặc biệt
    missing_cite = [d for d in case.get("must_cite", []) if d not in answer]
    missing_text = [t for t in case.get("answer_contains", []) if t.lower() not in answer.lower()]
    return missing_cite, missing_text


# ---------- 3. LLM judge: câu trả lời có bám bằng chứng không ----------
def evidence(messages):
    # Bằng chứng = mọi Observation agent đã nhận (kết quả search_docs + tool đọc log)
    obs = [m["content"] for m in messages if m["role"] == "user" and m["content"].startswith("Observation:")]
    # Kết quả tool log/ghi state ngắn mà quan trọng -> đặt TRƯỚC, kết quả search_docs dài đặt sau,
    # để khi cắt bớt cho vừa MAX_CONTEXT thì không mất số liệu log
    obs.sort(key=lambda o: '"results":' in o)
    return "\n".join(obs)[:MAX_CONTEXT]


def judge(answer, context):
    prompt = JUDGE_PROMPT.replace("{context}", context or "(không có)").replace("{answer}", answer)
    text, _ = call_llm([{"role": "user", "content": prompt}], use_tools=False)
    obj = _extract_json(text)
    claims = obj.get("claims", []) if isinstance(obj, dict) else []
    if not claims:
        return None, 0                      # không có khẳng định nào (vd câu từ chối) -> không tính
    yes = sum(1 for c in claims if str(c.get("supported", "")).lower() == "yes")
    return yes / len(claims), len(claims)


# ---------- Chạy từng câu ----------
def run_case(case, client, use_judge):
    reset_state()                           # mỗi câu bắt đầu từ state sạch
    t0 = time.time()
    result = run_agent(case["question"], client.call_tool, client.tools_text(),
                       client.tool_names, RunLogger())
    seconds = round(time.time() - t0, 1)
    answer = result["answer"]

    state_errors = check_state(case["expected_state"], actual_state())
    missing_cite, missing_text = check_answer(case, answer)
    faith, n_claims = judge(answer, evidence(result["messages"])) if use_judge else (None, 0)

    return {
        "id": case["id"], "type": case["type"],
        "state_ok": not state_errors, "cite_ok": not missing_cite, "answer_ok": not missing_text,
        "pass": not state_errors and not missing_cite and not missing_text,
        "faithfulness": "" if faith is None else round(faith, 2), "claims": n_claims,
        "steps": result["steps"], "tokens": result["tokens"], "seconds": seconds,
        **{k: result.get("usage", {}).get(k, 0) for k in USAGE_KEYS},
        "errors": "; ".join(state_errors + [f"thiếu nguồn {missing_cite}"] * bool(missing_cite)
                            + [f"thiếu chữ {missing_text}"] * bool(missing_text)),
        "answer": answer.replace("\n", " ")[:300],
    }


def summary(rows):
    print("\n========== KẾT QUẢ ==========")
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r["pass"])
    for t, v in by_type.items():
        print(f"{t:22s} {sum(v)}/{len(v)}")
    n = len(rows)
    faiths = [r["faithfulness"] for r in rows if r["faithfulness"] != ""]
    print(f"\nĐạt toàn bộ : {sum(r['pass'] for r in rows)}/{n}")
    print(f"State đúng  : {sum(r['state_ok'] for r in rows)}/{n}")
    print(f"Trích nguồn : {sum(r['cite_ok'] for r in rows)}/{n}")
    if faiths:
        print(f"Faithfulness: {sum(faiths) / len(faiths):.2f} (trung bình {len(faiths)} câu)")
    refuse = [r for r in rows if r["type"] in REFUSAL_TYPES]
    if refuse:
        print(f"Từ chối đúng: {sum(r['pass'] for r in refuse)}/{len(refuse)} (câu {', '.join(sorted(REFUSAL_TYPES))})")
    used = [r for r in rows if r.get("calls")]     # dòng cũ chưa có USAGE thì bỏ qua
    if used:
        m = len(used)
        print(f"USAGE TB    : {sum(r['calls'] for r in used) / m:.1f} calls, "
              f"{sum(r['prompt_tokens'] for r in used) / m:.0f} prompt, "
              f"{sum(r['completion_tokens'] for r in used) / m:.0f} completion, "
              f"max_prompt lớn nhất {max(r['max_prompt'] for r in used)} ({m} câu)")
    print(f"Trung bình  : {sum(r['steps'] for r in rows) / n:.1f} bước, "
          f"{sum(r['tokens'] for r in rows) / n:.0f} token, {sum(r['seconds'] for r in rows) / n:.0f} giây/câu")
    return by_type


def plot(by_type, path):
    import matplotlib
    matplotlib.use("Agg")                   # vẽ ra file, không mở cửa sổ
    import matplotlib.pyplot as plt
    types = list(by_type)
    rates = [sum(v) / len(v) * 100 for v in by_type.values()]
    plt.figure(figsize=(9, 4))
    plt.bar(types, rates, color="#3b82f6")
    plt.ylim(0, 100)
    plt.ylabel("% câu đạt")
    plt.title("SOC Agent: tỉ lệ đạt theo loại tình huống")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=120)


def save(rows):
    # Ghi lại sau MỖI câu: dừng giữa chừng (Ctrl+C, hết token) vẫn giữ được kết quả đã chạy
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / "eval.csv", "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig để Excel đọc đúng tiếng Việt
        fields = list(dict.fromkeys(k for r in rows for k in r))   # đủ cột cả khi dòng cũ thiếu cột mới
        w = csv.DictWriter(f, fieldnames=fields, restval="")
        w.writeheader()
        w.writerows(rows)


def load_done():
    path = RESULTS / "eval.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:                          # csv lưu mọi thứ thành chuỗi -> đổi lại kiểu
        for k in ("state_ok", "cite_ok", "answer_ok", "pass"):
            r[k] = r[k] == "True"
        for k in ("steps", "tokens", "claims", *USAGE_KEYS):
            r[k] = int(r[k]) if r.get(k) else 0
        r["seconds"] = float(r["seconds"])
        r["faithfulness"] = "" if r["faithfulness"] == "" else float(r["faithfulness"])
    return [r for r in rows if not r["errors"].startswith("LỖI")]   # câu bị lỗi thì chạy lại


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="vd T01,T03")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    cases = [json.loads(l) for l in TESTSET.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.only:
        keep = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in keep]

    rows = load_done() if args.resume else []
    done = {r["id"] for r in rows}
    cases = [c for c in cases if c["id"] not in done]
    with MCPClient() as client:
        set_tools(client.openai_tools())
        for case in cases:
            print(f"\n--- {case['id']} ({case['type']}): {case['question']}")
            try:
                row = run_case(case, client, not args.no_judge)
            except Exception as e:          # 1 câu lỗi (vd hết lượt gọi LLM) không làm dừng cả bộ
                row = {"id": case["id"], "type": case["type"], "state_ok": False, "cite_ok": False,
                       "answer_ok": False, "pass": False, "faithfulness": "", "claims": 0,
                       "steps": 0, "tokens": 0, "seconds": 0, "errors": f"LỖI: {e!r}", "answer": ""}
            print("    ĐẠT" if row["pass"] else f"    TRƯỢT: {row['errors']}")
            rows.append(row)
            save(rows)
    reset_state()                           # trả state về ban đầu sau khi chấm

    by_type = summary(rows)
    plot(by_type, RESULTS / "eval.png")
    print(f"\nĐã ghi {RESULTS / 'eval.csv'} và {RESULTS / 'eval.png'}")


if __name__ == "__main__":
    main()
