# Schema kết quả trả về của 10 tool MCP (TypedDict có type hint, không dùng dict thô).
# FastMCP đọc các kiểu này để sinh outputSchema và kiểm tra kết quả trước khi gửi cho client.
# Tham số đầu vào của tool lấy từ type hint của hàm trong tools.py (inputSchema).
from typing import Optional, TypedDict


# ---------- Bản ghi dùng chung ----------
class LogRow(TypedDict):
    ts: str
    src_ip: str
    username: str
    service: str
    success: bool


class SuccessAfterFail(TypedDict):
    username: str
    fails_before: int          # số lần sai liên tiếp ngay trước lần thành công
    success_at: str


class BlockEntry(TypedDict):
    ip: str
    severity: str
    duration_minutes: int
    blocked_at: str
    expires_at: str
    reason: str
    doc_id: str
    incident_id: Optional[str]


class Incident(TypedDict):
    incident_id: str
    created_at: str
    ip: str
    severity: str              # Medium | High | Critical
    status: str                # open | escalated (resolved chỉ con người đặt)
    summary: str
    evidence: str
    doc_ids: list[str]


class Account(TypedDict):
    username: str
    is_admin: bool
    locked: bool
    locked_until: Optional[str]
    reason: Optional[str]


class DocChunk(TypedDict):
    chunk_id: str
    doc_id: str
    version: str
    status: str
    title: str
    section: str
    text: str
    score: float


# ---------- Kết quả của từng tool ----------
class QueryLogsResult(TypedDict):
    total: int
    rows: list[LogRow]


class CountFailedResult(TypedDict):
    ip: str
    ip_type: str               # internal | partner | external (SEC-03)
    window_minutes: int
    total_failed: int
    max_failed_in_window: int
    max_distinct_users_in_window: int
    max_distinct_users_in_30min: int
    usernames: list[str]
    first_failed: Optional[str]
    last_failed: Optional[str]
    success_after_fail: list[SuccessAfterFail]


class BlocklistResult(TypedDict):
    count: int
    entries: list[BlockEntry]


class IncidentListResult(TypedDict):
    count: int
    incidents: list[Incident]


class SearchResult(TypedDict):
    query: str
    mode: str
    results: list[DocChunk]


class BlockResult(TypedDict):
    status: str                # blocked | already_blocked
    entry: BlockEntry


class UnblockResult(TypedDict):
    status: str                # unblocked
    ip: str
    reason: str


class CreateIncidentResult(TypedDict):
    status: str                # created | already_exists (IP đã có sự cố đang mở)
    incident_id: str
    incident: Incident


class LockResult(TypedDict):
    status: str                # locked | already_locked
    account: Account
