# Ghi trace mỗi lần chạy agent ra logs/run_<thời gian>[_<mã câu>].jsonl, mỗi dòng là 1 sự kiện JSON
# (question, llm, observation, final, usage). react_trace.py đọc lại file này để in theo dạng ReAct.
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"

class RunLogger:
    def __init__(self, name=""):
        LOG_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{name}" if name else ""           # vd run_20261017_170512_T01.jsonl
        self.path = LOG_DIR / f"run_{stamp}{suffix}.jsonl"

    def log(self, event, **data):
        # Ghi thêm 1 dòng: thời điểm + tên sự kiện + dữ liệu đi kèm
        record = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, **data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")