from datetime import timedelta

from store import load_logs, read_state, write_state        # import store TRƯỚC, vì store thêm thư mục src vào sys.path
from config import NOW, classify_ip
from schemas import (Account, BlocklistResult, BlockResult, CountFailedResult, CreateIncidentResult,
                     IncidentListResult, LockResult, QueryLogsResult, SearchResult, UnblockResult)
import logging
log = logging.getLogger("soc-tools")

SEVERITIES = ("Medium", "High", "Critical")
AGENT_STATUSES = ("open", "escalated")

# Nạp RAG ngay khi server khởi động (trước khi MCP bắt đầu đọc stdin).
# Lỗi RAG không được làm chết server: các tool khác vẫn chạy.
try:
    from search import search as _rag_search
    log.info("RAG đã nạp xong")
except Exception as e:
    _rag_search = None
    _rag_error = repr(e)
    log.error("Không nạp được RAG: %r", e)

def _filter(logs, ip=None, username=None, lookback_minutes=1440):
    since = NOW - timedelta(minutes=lookback_minutes)
    return [r for r in logs
            if r["ts"] >= since
            and (ip is None or r["src_ip"] == ip)
            and (username is None or r["username"] == username)]

# Tool đọc
def query_auth_logs(ip: str = None, username: str = None, only_failed: bool = False,
                    lookback_minutes: int = 1440, limit: int = 20) -> QueryLogsResult:
    """Liệt kê các bản ghi đăng nhập (mới nhất trước), lọc theo IP và/hoặc username."""
    rows = _filter(load_logs(), ip, username, lookback_minutes)
    if only_failed:
        rows = [r for r in rows if not r["success"]]
    rows.sort(key=lambda r: r["ts"], reverse=True)
    return {
        "total": len(rows),
        "rows": [{**r, "ts": r["ts"].isoformat()} for r in rows[:limit]],
    }

def count_failed_logins(ip: str, window_minutes: int = 5, lookback_minutes: int = 1440) -> CountFailedResult:
    """Đếm lần đăng nhập thất bại của 1 IP. Trả về loại IP, số lần sai nhiều nhất, số username
    khác nhau nhiều nhất trong một cửa sổ window_minutes phút liên tục bất kỳ, và các lần đăng nhập
    thành công ngay sau chuỗi sai."""
    if window_minutes <= 0:
        raise ValueError("window_minutes phải > 0")
    ip_type = classify_ip(ip)                          # internal / partner / external (theo SEC-03)
    rows = sorted(_filter(load_logs(), ip, None, lookback_minutes), key=lambda r: r["ts"])
    streak, success_after_fail = {}, []                # đếm số lần sai liên tiếp của từng username
    for r in rows:
        if not r["success"]:
            streak[r["username"]] = streak.get(r["username"], 0) + 1
        else:
            if streak.get(r["username"]):
                success_after_fail.append({"username": r["username"], "fails_before": streak[r["username"]],
                                           "success_at": r["ts"].isoformat()})
            streak[r["username"]] = 0
    fails = sorted((r for r in _filter(load_logs(), ip, None, lookback_minutes) if not r["success"]),
                   key=lambda r: r["ts"])
    window = timedelta(minutes=window_minutes)
    max_fails, max_users = 0, 0
    for i, start in enumerate(fails):                  # mỗi cửa sổ bắt đầu tại 1 lần sai
        inside = [r for r in fails[i:] if r["ts"] - start["ts"] < window]
        max_fails = max(max_fails, len(inside))
        max_users = max(max_users, len({r["username"] for r in inside}))
    users_30 = 0                                       # số username khác nhau trong cửa sổ 30 phút (cho password spraying)
    for i, start in enumerate(fails):
        inside = {r["username"] for r in fails[i:] if r["ts"] - start["ts"] < timedelta(minutes=30)}
        users_30 = max(users_30, len(inside))
    return {
        "ip": ip,
        "ip_type": ip_type,
        "window_minutes": window_minutes,
        "total_failed": len(fails),
        "max_failed_in_window": max_fails,
        "max_distinct_users_in_window": max_users,
        "max_distinct_users_in_30min": users_30,
        "usernames": sorted({r["username"] for r in fails}),
        "first_failed": fails[0]["ts"].isoformat() if fails else None,
        "last_failed": fails[-1]["ts"].isoformat() if fails else None,
        "success_after_fail": success_after_fail,
    }
    
# Tool đọc: trạng thái
def get_blocklist(ip: str = None) -> BlocklistResult:
    """Xem danh sách IP đang bị chặn. Truyền ip để chỉ xem bản ghi của IP đó."""
    entries = read_state("blocklist")
    if ip:
        entries = [e for e in entries if e["ip"] == ip.strip()]
    return {"count": len(entries), "entries": entries}

def get_incident(incident_id: str = None, ip: str = None) -> IncidentListResult:
    """Xem sự cố theo mã (vd 'INC-0001') hoặc theo IP. Không truyền gì thì trả về tất cả."""
    incidents = read_state("incidents")
    if incident_id:
        incidents = [i for i in incidents if i["incident_id"] == incident_id.strip()]
        if not incidents:
            raise ValueError(f"không có sự cố '{incident_id}'")
    if ip:
        incidents = [i for i in incidents if i["ip"] == ip.strip()]
    return {"count": len(incidents), "incidents": incidents}

def get_account_status(username: str) -> Account:
    """Xem tài khoản: có phải admin không, có đang bị khoá không."""
    for acc in read_state("accounts"):
        if acc["username"] == username.strip():
            return acc
    raise ValueError(f"không có tài khoản '{username}'")

# Tool đọc: playbook
def search_docs(query: str, mode: str = "hybrid", top_k: int = 3, only_active: bool = True) -> SearchResult:
    """Tìm đoạn playbook SEC liên quan tới câu hỏi. results rỗng = tài liệu không có thông tin."""
    if not query.strip():
        raise ValueError("query không được rỗng")
    if _rag_search is None:
        raise ValueError(f"RAG chưa sẵn sàng: {_rag_error}")
    log.info("search_docs: bắt đầu tìm %r", query)
    results = _rag_search(query, mode=mode, top_k=top_k, only_active=only_active)
    log.info("search_docs: xong, %d kết quả", len(results))
    return {"query": query, "mode": mode, "results": results}

# Tools ghi
def _check_severity(severity):
    if severity not in SEVERITIES:
        raise ValueError(f"severity phải là một trong {SEVERITIES}, nhận được {severity!r}")

def block_ip(ip: str, severity: str, duration_minutes: int, reason: str, doc_id: str,
             incident_id: str = None) -> BlockResult:
    """Chặn 1 IP bên ngoài. KHÔNG chặn được IP nội bộ/đối tác (SEC-03): phải tạo incident escalated."""
    ip = ip.strip()
    kind = classify_ip(ip)                       # IP sai định dạng -> ValueError luôn
    if kind != "external":
        raise ValueError(f"không được chặn IP {kind} {ip} (SEC-03): hãy tạo incident escalated")
    _check_severity(severity)
    if not 0 < duration_minutes <= 10080:
        raise ValueError("duration_minutes phải trong khoảng 1..10080")
    blocklist = read_state("blocklist")
    for e in blocklist:
        if e["ip"] == ip:
            return {"status": "already_blocked", "entry": e}
    entry = {"ip": ip, "severity": severity, "duration_minutes": duration_minutes,
             "blocked_at": NOW.isoformat(),
             "expires_at": (NOW + timedelta(minutes=duration_minutes)).isoformat(),
             "reason": reason, "doc_id": doc_id, "incident_id": incident_id}
    blocklist.append(entry)
    write_state("blocklist", blocklist)
    log.info("block_ip: đã chặn %s", ip)
    return {"status": "blocked", "entry": entry}

def unblock_ip(ip: str, reason: str) -> UnblockResult:
    """Bỏ chặn 1 IP (khi chặn nhầm)."""
    ip = ip.strip()
    blocklist = read_state("blocklist")
    remaining = [e for e in blocklist if e["ip"] != ip]
    if len(remaining) == len(blocklist):
        raise ValueError(f"IP {ip} không có trong danh sách chặn")
    write_state("blocklist", remaining)
    return {"status": "unblocked", "ip": ip, "reason": reason}

def create_incident(ip: str, severity: str, status: str, summary: str, evidence: str,
                    doc_ids: list[str]) -> CreateIncidentResult:
    """Tạo sự cố mới, mã tự tăng INC-0001, INC-0002... status chỉ được 'open' hoặc 'escalated'."""
    _check_severity(severity)
    if status not in AGENT_STATUSES:
        raise ValueError(f"status phải là 'open' hoặc 'escalated' ('resolved' chỉ con người đặt)")
    if not doc_ids:
        raise ValueError("doc_ids không được rỗng: phải ghi playbook làm căn cứ")
    incidents = read_state("incidents")
    incident = {"incident_id": f"INC-{len(incidents) + 1:04d}", "created_at": NOW.isoformat(),
                "ip": ip.strip(), "severity": severity, "status": status,
                "summary": summary, "evidence": evidence, "doc_ids": doc_ids}
    incidents.append(incident)
    write_state("incidents", incidents)
    return {"status": "created", "incident_id": incident["incident_id"], "incident": incident}

def lock_account(username: str, reason: str, duration_minutes: int = None) -> LockResult:
    """Khoá 1 tài khoản. duration_minutes=None: khoá đến khi trưởng ca mở (SEC-10)."""
    if duration_minutes is not None and duration_minutes <= 0:
        raise ValueError("duration_minutes phải > 0")
    accounts = read_state("accounts")
    for acc in accounts:
        if acc["username"] == username.strip():
            if acc["locked"]:
                return {"status": "already_locked", "account": acc}
            acc["locked"] = True
            acc["locked_until"] = (None if duration_minutes is None
                                   else (NOW + timedelta(minutes=duration_minutes)).isoformat())
            acc["reason"] = reason
            write_state("accounts", accounts)
            return {"status": "locked", "account": acc}
    raise ValueError(f"không có tài khoản '{username}'")




if __name__ == "__main__":
    for ip, w in [("203.0.113.7", 5), ("192.0.2.44", 5), ("203.0.113.99", 5),
                  ("203.0.113.120", 5), ("203.0.113.120", 30), ("203.0.113.200", 15)]:
        r = count_failed_logins(ip, w)
        print(f"{ip:15} cửa sổ {w:2} phút: tổng {r['total_failed']:2}, "
              f"max {r['max_failed_in_window']:2} lần, {r['max_distinct_users_in_window']:2} username")
    print(query_auth_logs(ip="203.0.113.200", limit=2))