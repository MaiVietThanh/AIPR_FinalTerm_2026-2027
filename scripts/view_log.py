# Xem 1 file log theo dạng Thought / Action / Observation:
#   python scripts\view_log.py                  (file log mới nhất trong logs\)
#   python scripts\view_log.py logs\run_xxx.jsonl
#   python scripts\view_log.py --save           (ghi thêm logs\run_xxx.txt cạnh file .jsonl)
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "agent"))

from react_trace import format_trace, read_log

args = [a for a in sys.argv[1:] if a != "--save"]
if args:
    path = Path(args[0])
else:
    logs = sorted((ROOT / "logs").glob("run_*.jsonl"))
    if not logs:
        sys.exit("Chưa có log nào trong logs\\, hãy chạy make demo trước")
    path = logs[-1]

text = format_trace(read_log(path))
print(f"Log: {path}")
print(text)
if "--save" in sys.argv:
    out = path.with_suffix(".txt")
    out.write_text(text, encoding="utf-8")
    print(f"\nĐã ghi {out}")
