# Hợp đồng tool (Tool Contract) của MCP server `soc-server`

Tài liệu này chốt **10 tool** mà MCP server (phần của Phát) cung cấp cho agent (phần của Thành). Mỗi tool ghi rõ: dùng để làm gì, nhận tham số gì, trả về gì, khi nào báo lỗi, và có làm thay đổi trạng thái hay không.

Ai sửa tên tool, tên tham số hoặc dạng kết quả thì **phải sửa file này trước và báo cả nhóm**, vì `loop.py` (`VERIFY_TOOL`), `prompts/system.txt` và `tests/testset.jsonl` đều dựa vào đây.

## 1. Quy ước chung

- **Thời gian:** mọi tool coi `NOW = 2026-10-01T10:00:00` (trong `src/config.py`) là "bây giờ". Thời gian trả về dạng chuỗi ISO, ví dụ `"2026-10-01T09:55:12"`.
- **Kết quả:** mỗi tool trả về một `dict` (MCP gửi đi dưới dạng JSON).
- **Lỗi:** tham số sai hoặc hành động bị cấm thì tool `raise ValueError("...")`. MCP gửi về `isError: true`, và agent nhận được chuỗi bắt đầu bằng `Error`. Server không bị dừng.
- **Tool chỉ trả số liệu, không kết luận.** Việc so với ngưỡng và chọn mức độ là của agent, dựa trên playbook tra bằng `search_docs`.
- **Phân loại IP** theo SEC-03 v1.3, bằng hàm `config.classify_ip()`: `internal`, `partner` hoặc `external`.
- **Dữ liệu:** log đọc từ `data/auth_logs/auth_logs.csv` (chỉ đọc). Trạng thái nằm trong 3 file `data/state/blocklist.json`, `incidents.json`, `accounts.json`. `reset_state()` đưa 3 file này về ban đầu.
- **Mức độ (severity):** `Medium`, `High`, `Critical`. **Trạng thái sự cố (status):** agent chỉ được đặt `open` hoặc `escalated`. `resolved` chỉ con người đặt.

## 2. Bảng tóm tắt

| # | Tool | Loại | Đọc/ghi | Tool verify |
|---|---|---|---|---|
| 1 | `search_docs` | Tra playbook (RAG) | Đọc | |
| 2 | `query_auth_logs` | Xem log | Đọc | |
| 3 | `count_failed_logins` | Đếm lần sai | Đọc | |
| 4 | `get_blocklist` | Xem danh sách chặn | Đọc | |
| 5 | `get_incident` | Xem sự cố | Đọc | |
| 6 | `get_account_status` | Xem tài khoản | Đọc | |
| 7 | `block_ip` | Chặn IP | **Ghi** `blocklist.json` | `get_blocklist` |
| 8 | `unblock_ip` | Bỏ chặn IP | **Ghi** `blocklist.json` | `get_blocklist` |
| 9 | `create_incident` | Tạo sự cố | **Ghi** `incidents.json` | `get_incident` |
| 10 | `lock_account` | Khoá tài khoản | **Ghi** `accounts.json` | `get_account_status` |

Cột "Tool verify" khớp với `VERIFY_TOOL` trong `src/agent/loop.py`: ngay sau mỗi tool ghi, agent gọi tool đọc tương ứng để chứng minh trạng thái đã đổi.

## 3. Tool đọc

### 3.1 `search_docs`
Tìm đoạn playbook liên quan đến câu hỏi. Gọi hàm `search()` trong `src/rag/search.py` (phần của Tuyết).

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `query` | str | (bắt buộc) | Câu hỏi hoặc từ khoá |
| `mode` | str | `"hybrid"` | `"dense"` hoặc `"hybrid"` |
| `top_k` | int | `3` | Số đoạn trả về, từ 1 đến 8 |
| `only_active` | bool | `true` | Chỉ lấy tài liệu `status: active` |

Trả về: `{"query", "mode", "results": [{"chunk_id", "doc_id", "version", "status", "title", "section", "text", "score"}]}`. `results` rỗng nghĩa là tài liệu không có thông tin, agent phải trả lời "Không tìm thấy trong tài liệu".
Lỗi: `mode` không hợp lệ, `query` rỗng.

### 3.2 `query_auth_logs`
Liệt kê các lượt đăng nhập, mới nhất trước.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `ip` | str | `null` | Lọc theo IP nguồn |
| `username` | str | `null` | Lọc theo tài khoản |
| `only_failed` | bool | `false` | Chỉ lấy lượt sai |
| `lookback_minutes` | int | `1440` | Chỉ xét log trong N phút trước `NOW` |
| `limit` | int | `20` | Số dòng tối đa trả về |

Trả về: `{"total", "rows": [{"ts", "src_ip", "username", "service", "success"}]}`. `total` là tổng số dòng khớp, còn `rows` bị cắt theo `limit`.

### 3.3 `count_failed_logins`
Đếm lượt đăng nhập sai của một IP bằng **cửa sổ trượt**: tìm cửa sổ `window_minutes` phút liên tục **bất kỳ** có nhiều lượt sai nhất (SEC-02 mục 3). Dùng chung cho SEC-02 (5 phút), SEC-10 (15 phút) và SEC-09 (30 phút, xem số username khác nhau).

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `ip` | str | (bắt buộc) | IP cần đếm |
| `window_minutes` | int | `5` | Độ dài cửa sổ |
| `lookback_minutes` | int | `1440` | Chỉ xét log trong N phút trước `NOW` |

Trả về: `{"ip", "window_minutes", "total_failed", "max_failed_in_window", "max_distinct_users_in_window", "usernames", "first_failed", "last_failed"}`.
Lỗi: `window_minutes <= 0`.

### 3.4 `get_blocklist`
Xem danh sách IP đang bị chặn.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `ip` | str | `null` | Có thì chỉ trả về bản ghi của IP này |

Trả về: `{"count", "entries": [{"ip", "severity", "duration_minutes", "blocked_at", "expires_at", "reason", "doc_id", "incident_id"}]}`.

### 3.5 `get_incident`
Xem sự cố theo mã, hoặc mọi sự cố của một IP.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `incident_id` | str | `null` | Ví dụ `"INC-0001"` |
| `ip` | str | `null` | Lọc theo IP |

Trả về: `{"count", "incidents": [{"incident_id", "created_at", "ip", "severity", "status", "summary", "evidence", "doc_ids"}]}`. Không truyền gì thì trả về tất cả.
Lỗi: `incident_id` không tồn tại.

### 3.6 `get_account_status`
Xem trạng thái một tài khoản.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `username` | str | (bắt buộc) | Tên tài khoản |

Trả về: `{"username", "is_admin", "locked", "locked_until", "reason"}`.
Lỗi: tài khoản không tồn tại.

## 4. Tool ghi

### 4.1 `block_ip`
Thêm một IP vào `blocklist.json`.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `ip` | str | (bắt buộc) | IP cần chặn |
| `severity` | str | (bắt buộc) | `Medium`, `High` hoặc `Critical` |
| `duration_minutes` | int | (bắt buộc) | Thời gian chặn theo SEC-04 (60, 1440 hoặc 10080) |
| `reason` | str | (bắt buộc) | Lý do ngắn, kèm số liệu |
| `doc_id` | str | (bắt buộc) | Playbook làm căn cứ, ví dụ `"SEC-02"` |
| `incident_id` | str | `null` | Sự cố liên quan, nếu đã tạo |

Trả về: `{"status": "blocked", "entry": {...}}`. Nếu IP đã có trong danh sách thì trả về `{"status": "already_blocked", "entry": {...}}` và không thêm bản ghi trùng.
**Guard (bắt buộc):** IP sai định dạng, hoặc IP `internal`/`partner` theo SEC-03, thì báo lỗi và **không ghi gì**. Agent phải leo thang (tạo incident `escalated`) thay vì chặn.
Lỗi khác: `severity` không hợp lệ, `duration_minutes <= 0` hoặc lớn hơn 10080.

### 4.2 `unblock_ip`
Xoá một IP khỏi `blocklist.json`, dùng khi chặn nhầm.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `ip` | str | (bắt buộc) | IP cần bỏ chặn |
| `reason` | str | (bắt buộc) | Lý do bỏ chặn |

Trả về: `{"status": "unblocked", "ip", "reason"}`.
Lỗi: IP không có trong danh sách chặn.

### 4.3 `create_incident`
Tạo một sự cố mới trong `incidents.json`. Mã sự cố tự sinh tăng dần: `INC-0001`, `INC-0002`...

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `ip` | str | (bắt buộc) | IP liên quan |
| `severity` | str | (bắt buộc) | `Medium`, `High` hoặc `Critical` |
| `status` | str | (bắt buộc) | `open` hoặc `escalated` |
| `summary` | str | (bắt buộc) | Mô tả ngắn sự việc |
| `evidence` | str | (bắt buộc) | Số liệu từ tool đọc log |
| `doc_ids` | list[str] | (bắt buộc) | Các playbook làm căn cứ |

Trả về: `{"status": "created", "incident_id", "incident": {...}}`. `loop.py` lấy `incident_id` từ đây để gọi `get_incident` verify.
Lỗi: `status = "resolved"` hoặc giá trị lạ, `severity` không hợp lệ, `doc_ids` rỗng.

### 4.4 `lock_account`
Khoá một tài khoản trong `accounts.json` (SEC-07, SEC-10). Khác với chặn IP: khoá tài khoản thì không ai đăng nhập được vào tài khoản đó, từ bất kỳ IP nào.

| Tham số | Kiểu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `username` | str | (bắt buộc) | Tài khoản cần khoá |
| `reason` | str | (bắt buộc) | Lý do khoá |
| `duration_minutes` | int | `null` | Số phút khoá. `null` = khoá cho đến khi trưởng ca mở |

Trả về: `{"status": "locked", "account": {...}}`. Nếu tài khoản đã bị khoá thì trả về `{"status": "already_locked", "account": {...}}`.
Lỗi: tài khoản không tồn tại, `duration_minutes <= 0`.

## 5. Ví dụ một lượt chặn IP (theo SEC-02 v2.0)

1. `search_docs({"query": "ngưỡng brute-force"})` → SEC-02: 5 lần sai trong 5 phút.
2. `count_failed_logins({"ip": "203.0.113.7"})` → `max_failed_in_window: 23`.
3. Agent kết luận: 23 lần, nằm trong khoảng 20–49 của SEC-04 → `High`, chặn 1440 phút. IP là `external` → được chặn.
4. `create_incident({... "status": "open"})` → `INC-0001`, verify bằng `get_incident`.
5. `block_ip({"ip": "203.0.113.7", "severity": "High", "duration_minutes": 1440, ...})`, verify bằng `get_blocklist`.
