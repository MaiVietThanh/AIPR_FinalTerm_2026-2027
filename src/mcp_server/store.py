# file gọi tool

import copy, csv, json, sys
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))            # để import được src/config.py
sys.path.insert(0, str(SRC / "rag"))    # để import được search.py của Tuyết
from config import LOG_FILE, STATE_DIR

def _acc(username, is_admin=False):
    return {"username": username, "is_admin": is_admin, "locked": False,
            "locked_until": None, "reason": None}

# Trạng thái ban đầu, phải giống hệt 3 file trong data/state/
INITIAL_STATE = {
    "blocklist": [],
    "incidents": [],
    "accounts": [_acc(u) for u in ["thanh", "tuyet", "trung", "phat", "tabi", "tuananh", "kiet", "hai"]]
                + [_acc("admin", True), _acc("root", True)],
}

# Log (read only)
def load_logs():
    """Đọc auth_logs.csv, đổi ts thành datetime và success thành bool."""
    with open(LOG_FILE, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["ts"] = datetime.fromisoformat(r["ts"])
        r["success"] = r["success"] == "1"
    return rows

#   Funtion xử lí trong MCP Server
def _path(name):
    if name not in INITIAL_STATE:
        raise ValueError(f"không có file trạng thái '{name}'")
    return STATE_DIR / f"{name}.json"

def read_state(name):
    with open(_path(name), encoding="utf-8") as f:
        return json.load(f)

def write_state(name, data):
    path = _path(name)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)          # ghi xong hết mới thay file cũ

def reset_state():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in INITIAL_STATE.items():
        write_state(name, copy.deepcopy(data))

if __name__ == "__main__":
    logs = load_logs()
    print("Số dòng log:", len(logs))
    print("Dòng đầu:", logs[0])
    reset_state()
    bl = read_state("blocklist")
    bl.append({"ip": "1.2.3.4"})
    write_state("blocklist", bl)
    print("Sau khi thêm:", read_state("blocklist"))
    reset_state()
    print("Sau reset:", read_state("blocklist"), "| số tài khoản:", len(read_state("accounts")))