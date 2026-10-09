# AIPR FINAL PROJECT 2026-2027

**Đề tài:** SOC Agent — Trợ lý phát hiện và chặn tấn công đăng nhập

**Thành viên:**

| Thành viên              | Vai trò                        | Branch  |
| ----------------------- | ------------------------------ | ------- |
| Mai Viết Thành          | SV1 — RAG & chất lượng trả lời | `thanh` |
| Lê Huy Phát             | SV2 — Agent loop               | `phat`  |
| Nguyễn Huỳnh Minh Tuyết | SV3 — Dữ liệu log & MCP server | `tuyet` |

**Thời gian:** Thứ 7 10/10/2026 → Thứ 2 19/10/2026 (10 ngày)

------

## 1. Tổng quan

Đây là đồ án cuối kỳ môn AIPR (W1–W7). Đề yêu cầu xây một **agent có RAG, có đo lường**, gồm 3 phần trọng tâm:

- **RAG** (W3–W4): tra cứu tài liệu, có ≥2 chế độ truy vấn (dense + hybrid BM25).
- **Agent loop & tool** (W6): vòng lặp agent tự viết tay, có tool ghi (thay đổi trạng thái thật) và bước verify ngay sau đó.
- **MCP** (W7): MCP server tự viết, chạy qua stdio, client tự lấy danh sách tool.
- Kèm **đánh giá** (W5): testset ≥12 câu (≥4 câu no_answer), đo faithfulness, tỉ lệ từ chối đúng, chi phí token từng câu.

Một đề tài đạt yêu cầu phải có đủ **3 tầng**:

| Tầng          | Ý nghĩa                               | Trong project này                                            |
| ------------- | ------------------------------------- | ------------------------------------------------------------ |
| (a) Tra cứu   | Câu trả lời nằm ở đâu trong tài liệu? | Trả lời về playbook bảo mật, trích đúng `doc_id` và phiên bản; từ chối khi tài liệu không có |
| (b) Biến đổi  | Từ tài liệu, suy ra được gì?          | Đếm số lần đăng nhập sai từ log, đối chiếu ngưỡng và mức độ nghiêm trọng, chọn đúng phiên bản quy định |
| (c) Hành động | Làm gì, và làm sao biết đã làm?       | Chặn IP / khoá tài khoản / tạo sự cố, rồi đọc lại để chứng minh trạng thái đã đổi |

**Sản phẩm nộp:** `report.docx` (8–9 trang), repo code kèm `.git`, `logs/` (≥3 lần chạy thật), `tests/testset.jsonl`, `ai-usage.md`, `README.md`.

**Chạy trên máy GV bằng đúng 1 lệnh:** `make setup && make demo`. Mọi số liệu trong report phải tái lập được bằng `make eval`.

------

## 2. Mô tả bài toán

### Bối cảnh

Công ty kinh tế nào đó tên llaf **UTE** có đội an ninh mạng (SOC). Hệ thống ghi lại hàng nghìn lượt đăng nhập mỗi ngày, và chuyên viên SOC phải trả lời những câu như *"IP này có đang dò mật khẩu không?"* hay *"Theo quy định thì xử lý thế nào?"*.

**SOC Agent** là trợ lý giúp chuyên viên đó:

- 📖 **Đọc quy định bảo mật** (playbook) và trả lời có trích dẫn nguồn.
- 🔍 **Xem log đăng nhập**, đếm số lần sai, đối chiếu với quy định để kết luận.
- 🛡️ **Ra tay xử lý**: chặn IP, khoá tài khoản bị chiếm, hoặc **leo thang** (chuyển cho trưởng ca quyết định) khi không được tự chặn.
- ✅ **Tự kiểm chứng**: sau mỗi hành động, đọc lại hệ thống để chứng minh việc đã thực sự xảy ra.

### Các loại tấn công xử lý

1. **Brute-force:** một IP đăng nhập sai nhiều lần trong thời gian ngắn.
2. **Password spraying:** một IP thử ít lần nhưng trên rất nhiều tài khoản khác nhau.
3. **Tài khoản bị chiếm:** đăng nhập sai liên tục rồi thành công.

### Hệ thống KHÔNG làm

- Không đụng vào firewall hay hệ thống thật. Mọi thứ chạy trên dữ liệu giả lập (SQLite).
- Không xử lý ransomware, DDoS, phishing… (hỏi thì trả lời "không có trong playbook").
- Không tự chặn IP nội bộ hoặc IP đối tác, mà luôn leo thang cho con người.

### Luồng xử lý một câu hỏi

Ví dụ: *"IP 203.0.113.7 có đang tấn công không? Xử lý theo playbook."*

1. Người dùng gõ câu hỏi.
2. Agent gọi `search_docs` (RAG) → ngưỡng brute-force là 5 lần / 5 phút (SEC-02).
3. Agent gọi `count_failed_logins` → IP sai 23 lần trong 4 phút.
4. Agent suy luận: 23 ≥ 5, không phải IP nội bộ → mức High → chặn 24 giờ.
5. Agent gọi `block_ip` → rồi gọi `get_blocklist` để xác nhận đã chặn.
6. Trả lời kèm `doc_id` căn cứ; toàn bộ các bước được ghi vào `logs/`.

**Vai trò từng phần:**

- **RAG** trả lời *"quy định nói gì"*.
- **Tool đọc log** trả lời *"thực tế đã xảy ra gì"*.
- **Agent** ghép hai thứ lại để suy ra kết luận và quyết định hành động.
- **MCP server** cung cấp tất cả các tool đó cho agent.

### Dữ liệu

- **`data/docs/`**: 10 playbook bảo mật (SEC-01 → SEC-10), mỗi file có metadata `doc_id`, `title`, `version`, `date`, `owner`, `status`. Có quy định nhiều phiên bản (SEC-01 v1 cũ, SEC-02 v2 hiện hành). **Chỉ thư mục này đi vào RAG.**
- **`data/auth_logs/`**: log đăng nhập giả lập dạng CSV, mỗi dòng gồm `timestamp, ip, username, service, result`. **Không đưa vào RAG**: log được nạp vào SQLite và agent đọc qua tool. Không lưu mật khẩu hay hash mật khẩu.

------

## 3. Cấu trúc thư mục (đây là cấu trúc thử nghiệm, có thể tùy chỉnh nếu xuất hiện trường hợp ngoài ý muốn)

```
SOC_Agent/
├── Makefile                  # make setup, make demo, make eval
├── README.md                 # lệnh chạy duy nhất
├── requirements.txt          # thư viện
├── .env.example              # mẫu biến môi trường (KHÔNG chứa key thật)
├── .gitignore
├── ai-usage.md               # khai báo dùng AI (mỗi người tự khai phần mình)
│
├── data/
│   ├── docs/                 # playbook SEC-01 → SEC-10, đầu vào của RAG
│   ├── auth_logs/
│   │   └── auth_logs.csv     # log đăng nhập giả lập (KHÔNG vào RAG)
│   ├── index/                # index RAG đã build (không commit)
│   └── soc.db                # SQLite: log, blocklist, incidents, accounts (không commit)
│
├── prompts/                  # prompt tách khỏi code
│   ├── system.txt
│   └── judge.txt             # prompt chấm faithfulness
│
├── src/
│   ├── config.py             # NOW cố định, đường dẫn, dải IP nội bộ/đối tác
│   ├── db.py                 # tạo bảng, nạp CSV vào SQLite, reset
│   ├── rag/
│   │   ├── chunking.py       # đọc metadata, cắt theo mục
│   │   ├── embed.py          # embedding (NVIDIA API, có cache)
│   │   ├── hybrid_search.py  # tái dùng w4/ex2_1_hybrid_search.py
│   │   └── search.py         # search(query, mode, top_k, only_active)
│   ├── mcp_server/
│   │   ├── schemas.py        # @dataclass cho input/output của tool
│   │   ├── tools.py          # logic từng tool
│   │   └── server.py         # MCP server chạy stdio
│   └── agent/
│       ├── llm.py            # call_llm(): retry, timeout, log lỗi HTTP
│       ├── parser.py         # parse action JSON an toàn
│       ├── mcp_client.py     # kết nối server, list_tools() động
│       ├── loop.py           # agent loop, MAX_STEPS, verify-after-write
│       └── logger.py         # ghi trace jsonl + USAGE
│
├── scripts/
│   ├── gen_logs.py           # sinh auth_logs.csv có chủ đích
│   ├── build_index.py        # build index RAG
│   ├── ask.py                # hỏi 1 câu từ terminal
│   ├── run_eval.py           # chạy testset, xuất kết quả
│   └── client2.py            # client MCP thứ hai (điểm cộng)
│
├── tests/
│   └── testset.jsonl         # ≥12 câu, ≥4 câu no_answer
├── logs/                     # trace các lần chạy thật (FILE NỘP BÀI)
└── results/                  # eval.csv, đồ thị
```

**Lưu ý:**

- `data/auth_logs/` là **dữ liệu đầu vào**; `logs/` là **trace của agent** để nộp bài. Hai thư mục khác nhau.
- `.env`, `.venv/`, `data/*.db`, `data/index/` **không được commit** (đã có trong `.gitignore`).

------

## 4. Hướng dẫn commit bài của mình lên GitHub

### 4.1. Ý tưởng chung ( này gthich cho dễ hiểu để xài chung nè)

- Có 2 nơi chứa code: **máy của mình** (local) và **GitHub** (nơi cả nhóm dùng chung).
- `main` là **bàn chung** của nhóm. Mỗi người làm ở **bàn riêng** là branch mang tên mình (`thanh`, `phat`, `tuyet`).
- Làm xong một phần thì đặt lên bàn chung (merge vào `main`). Muốn lấy code của bạn thì kéo từ bàn chung về bàn mình.

| Lệnh             | Tác dụng                                           |
| ---------------- | -------------------------------------------------- |
| `git commit`     | Lưu một "bản chụp" thay đổi, **chỉ trên máy mình** |
| `git push`       | Đẩy các commit **lên GitHub** để cả nhóm thấy      |
| `git pull`       | Kéo các commit mới **từ GitHub về máy mình**       |
| `git merge main` | Đưa code mới trên `main` vào branch của mình       |

### 4.2. Setup (làm 1 lần)

**1. Cấu hình tên và email** (để GV nhìn commit biết ai làm; email nên trùng email tài khoản GitHub):

bash

```bash
git config --global user.name "Ten Cua Ban"
git config --global user.email "email-tai-khoan-github@..."
```

**2. Clone repo và tạo branch của mình:**

bash

```bash
git clone https://github.com/MaiVietThanh/AIPR_FinalTerm_2026-2027.git
cd soc-agent
git checkout -b thanh        # Phát dùng: phat, Tuyết dùng: tuyet
git push -u origin thanh
```

**3. Tạo môi trường ảo và cài thư viện:**

bash

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # rồi điền API key vào .env
```

### 4.3. Vòng làm việc mỗi ngày

bash

```bash
# Đầu buổi: lấy code mới nhất của cả nhóm
git checkout main
git pull
git checkout thanh
git merge main

# ... code ...

# Cuối buổi: lưu và đẩy lên GitHub
git add src/<phần của mình làm>/
git commit -m "feat(rag): add hybrid search with BM25"
git push
```

### 4.4. Đưa code của mình vào `main`

1. Lên GitHub, mở **Pull Request** từ branch của mình (ví dụ `thanh`) vào `main`.
2. Nhờ 1 bạn khác đọc qua code.
3. Bấm **Merge**.
4. Báo nhóm để 2 bạn còn lại `git pull` main và `git merge main` vào branch của họ.

### 4.5. Khi gặp lỗi

- **`push` báo \*"rejected… fetch first"\*:** trên GitHub có commit mới mà máy mình chưa có → `git pull` trước rồi `push` lại.
- **Conflict:** xảy ra khi 2 người sửa **cùng một dòng trong cùng một file**. Git đánh dấu như sau:

```
  <<<<<<< HEAD
  MAX_STEPS = 8          # bản của mình
  =======
  MAX_STEPS = 10         # bản của người kia
  >>>>>>> main
```

Giữ lại phiên bản đúng, xoá các dòng `<<<<<<<`, `=======`, `>>>>>>>`, rồi chạy `git add` và `git commit`. VS Code có sẵn nút *Accept Current / Accept Incoming*.

### 4.6. Cách ghi commit để đẩy code lên repo
## 1. Các loại Commit phổ biến

| Prefix     | Ý nghĩa                | Khi nào sử dụng                                         | Ví dụ                               |
| ---------- | ---------------------- | ------------------------------------------------------- | ----------------------------------- |
| `feat`     | Feature                | Thêm tính năng mới                                      | `feat: add user login`              |
| `fix`      | Fix bug                | Sửa lỗi trong chương trình                              | `fix: resolve login error`          |
| `docs`     | Documentation          | Thêm hoặc sửa tài liệu                                  | `docs: update README`               |
| `style`    | Code Style             | Chỉnh format, khoảng trắng, dấu câu; không đổi logic    | `style: format Python code`         |
| `refactor` | Refactoring            | Tái cấu trúc code mà không chủ đích đổi hành vi         | `refactor: simplify auth logic`     |
| `perf`     | Performance            | Tối ưu hiệu năng                                        | `perf: optimize image processing`   |
| `test`     | Testing                | Thêm hoặc sửa test                                      | `test: add login unit tests`        |
| `build`    | Build System           | Thay đổi hệ thống build hoặc dependencies phục vụ build | `build: update build configuration` |
| `ci`       | Continuous Integration | Thay đổi cấu hình CI/CD                                 | `ci: add GitHub Actions workflow`   |
| `chore`    | Maintenance            | Công việc bảo trì, cấu hình hoặc tác vụ phụ trợ         | `chore: update dependencies`        |
| `revert`   | Revert                 | Hoàn tác một commit trước đó                            | `revert: remove login feature`      |

## 2. Cấu trúc Commit Message

Cú pháp:

```text
<type>(<scope>): <description>
```

| Thành phần    | Ý nghĩa                                          | Ví dụ                     |
| ------------- | ------------------------------------------------ | ------------------------- |
| `type`        | Loại thay đổi                                    | `feat`, `fix`, `docs`     |
| `scope`       | Module hoặc phạm vi bị ảnh hưởng; không bắt buộc | `auth`, `api`, `database` |
| `description` | Mô tả ngắn gọn thay đổi                          | `add user login`          |

Ví dụ:

```text
feat(auth): add Google login
fix(api): handle null response
docs(readme): add installation guide
refactor(database): simplify query logic
test(auth): cover invalid password
perf(image): optimize image processing
```

## 3. Quy tắc viết Commit Message

| Quy tắc                        | Nên làm                                | Nên tránh                          |
| ------------------------------ | -------------------------------------- | ---------------------------------- |
| Mô tả rõ ràng                  | `feat: add product search`             | `update code`                      |
| Ngắn gọn, đúng trọng tâm       | `fix: prevent null pointer error`      | `fix some bugs and update stuff`   |
| Dùng động từ mô tả hành động   | `docs: add setup instructions`         | `docs: instructions added`         |
| Tập trung vào một mục đích     | Một commit cho một thay đổi logic      | Gom nhiều thay đổi không liên quan |
| Thống nhất ngôn ngữ            | Dùng tiếng Anh nhất quán trong project | Trộn nhiều ngôn ngữ tùy tiện       |
| Không dùng thông điệp vô nghĩa | `refactor: simplify user service`      | `final`, `update`, `test123`       |

## 4. Các lệnh Git cơ bản

| Lệnh                        | Chức năng                                                    |
| --------------------------- | ------------------------------------------------------------ |
| `git status`                | Kiểm tra trạng thái file                                     |
| `git diff`                  | Xem nội dung thay đổi chưa được stage                        |
| `git add <file>`            | Đưa file cụ thể vào staging area                             |
| `git add .`                 | Stage các thay đổi trong thư mục hiện tại                    |
| `git diff --staged`         | Xem các thay đổi đã stage                                    |
| `git commit -m "feat: ..."` | Tạo commit với thông điệp mô tả                              |
| `git log --oneline`         | Xem lịch sử commit dạng ngắn                                 |
| `git push`                  | Đẩy commit lên remote                                        |
| `git pull`                  | Lấy và tích hợp thay đổi từ remote                           |
| `git fetch`                 | Lấy dữ liệu remote mà chưa tích hợp vào nhánh hiện tại       |
| `git switch -c <branch>`    | Tạo và chuyển sang nhánh mới                                 |
| `git branch`                | Liệt kê các nhánh local                                      |
| `git restore <file>`        | Khôi phục file về trạng thái trong working tree theo index; có thể làm mất thay đổi chưa commit |
| `git stash`                 | Tạm cất các thay đổi chưa commit                             |

### 4.7. Quy ước của nhóm

- ✅ Commit **nhỏ, thường xuyên**, mỗi commit một việc. Không dồn 1 commit lớn cuối kỳ.
- ✅ Message có tiền tố phần việc: `rag: ...`, `agent: ...`, `mcp: ...`, `docs: ...`, `report: ...`.
- ✅ Mỗi người chủ yếu sửa thư mục của mình. Muốn sửa file dùng chung (`requirements.txt`, `Makefile`, `config.py`, `schemas.py`) thì **báo nhóm trước**.
- ✅ Merge `main` vào branch mình **mỗi ngày**.
- ❌ Không commit `.env`, `.venv/`, `data/*.db`.
- ❌ Không commit code của người khác dưới tên mình: GV đối chiếu commit hash với bảng phân công khi vấn đáp.

------

## 5. Phân công nhiệm vụ

> **Hai việc phải chốt chung ngay ngày 1** để 3 người code song song được:
>
> 1. **Hợp đồng tool**: tên, tham số, kiểu trả về `ToolResult` của các tool (Tuyết soạn, Phát duyệt).
> 2. **Hàm `search(query, mode, top_k, only_active)`** (Thành viết, Tuyết gói thành tool `search_docs`).
>
> **Mốc ghép thử ngày 5 (14/10):** chạy được trọn 1 câu tra cứu và 1 câu chặn IP có verify.

### 👤 TUYẾT — SV1: RAG & chất lượng trả lời

**Playbook (`data/docs/`)**

- [ ] SEC-01, SEC-02: playbook brute-force v1 (cũ) và v2 (hiện hành)
- [ ] SEC-03: dải IP nội bộ và IP đối tác
- [ ] SEC-04: ma trận mức độ nghiêm trọng và thời gian chặn
- [ ] SEC-05, SEC-06: quy trình leo thang, quy định ghi nhận sự cố
- [ ] SEC-07, SEC-08: chính sách khoá tài khoản, thuật ngữ SOC
- [ ] SEC-09, SEC-10: password spraying, tài khoản bị chiếm
- [ ] Metadata đầy đủ cho cả 10 file

**RAG (`src/rag/`)**

- [ ] `chunking.py`: đọc metadata, cắt theo mục `##`, viết 3–5 dòng lý do chunking
- [ ] `embed.py`: gọi NVIDIA embedding (`input_type` query/passage), cache ra `.npy`
- [ ] `hybrid_search.py`: tái dùng file `w4/ex2_1_hybrid_search.py` của lớp
- [ ] `search.py`: dense + hybrid + filter `status=active`
- [ ] `scripts/build_index.py`

**Đánh giá chất lượng**

- [ ] `tests/testset.jsonl`: ≥16 câu (≥4 no_answer), có `expected_doc_ids`, `expected_state`
- [ ] `prompts/judge.txt` + chấm faithfulness, tỉ lệ từ chối đúng
- [ ] So sánh dense vs hybrid trên testset (điểm cộng)
- [ ] Phân tích ≥1 ca thất bại

**Report**

- [ ] Mục 1: Vấn đề, phạm vi, giả định
- [ ] Mục 3: Thiết kế RAG
- [ ] Nửa mục 6: chất lượng RAG và ca thất bại

### 👤 THÀNH — SV2: Agent loop

**Setup repo**

- [ ] Tạo repo GitHub private, mời 2 bạn vào
- [ ] Khung thư mục, `requirements.txt`, `.gitignore`, `.env.example`

**Agent (`src/soc/agent/`)**

- [ ] `llm.py`: `call_llm()` có retry, timeout, log lỗi HTTP, trả về số token
- [ ] `parser.py`: parse action JSON an toàn (thiếu ngoặc không làm sập chương trình)
- [ ] `mcp_client.py`: kết nối server stdio, `list_tools()` động, đưa schema vào prompt
- [ ] `loop.py`: vòng lặp agent, `MAX_STEPS`, tool lỗi trả `"Error: ..."`
- [ ] Ép bước verify sau mỗi tool ghi bằng code
- [ ] `logger.py`: ghi `logs/run_<timestamp>.jsonl` + USAGE từng câu
- [ ] Chế độ `--confirm` (hỏi y/n trước khi ghi)
- [ ] `prompts/system.txt`, `scripts/ask.py`
- [ ] Tinh chỉnh prompt cho ca leo thang và prompt injection

**Chạy và đóng gói**

- [ ] `Makefile` (`setup`, `demo`, `eval`)
- [ ] `README.md`
- [ ] Chạy ≥3 lần thật, lưu vào `logs/`

**Report**

- [ ] Mục 2: Kiến trúc tổng thể (sơ đồ + luồng 1 câu hỏi)
- [ ] Mục 4: Thiết kế Agent & tool (kèm trace thật)
- [ ] Mục 7: Hạn chế & hướng phát triển

### 👤 PHÁT — SV3: Dữ liệu log & MCP server

**Hợp đồng và cấu hình**

- [ ] `docs/tool_contract.md`: hợp đồng 10 tool (chốt ngày 1)
- [ ] `src/soc/config.py`: `NOW` cố định, dải IP nội bộ/đối tác

**Dữ liệu log**

- [ ] `scripts/gen_logs.py`: log nền bình thường
- [ ] Kịch bản: brute-force High, Critical (nhắm admin), Medium (bẫy phiên bản), sai rải rác
- [ ] Kịch bản: IP nội bộ, IP đối tác, prompt injection
- [ ] Kịch bản: password spraying, tài khoản bị chiếm
- [ ] `src/soc/db.py`: bảng `auth_logs`, `blocklist`, `incidents`, `accounts`; nạp CSV; `reset_db()`

**MCP server (`src/soc/mcp_server/`)**

- [ ] `schemas.py`: các `@dataclass` input/output
- [ ] Tool đọc: `search_docs`, `query_auth_logs`, `count_failed_logins`, `get_blocklist`, `get_incident`, `get_account_status`
- [ ] Tool ghi: `block_ip` (có guard IP nội bộ/đối tác), `unblock_ip`, `create_incident`, `lock_account`
- [ ] `server.py`: chạy stdio, stdout sạch (không `print`)
- [ ] `scripts/client2.py`: client thứ hai (điểm cộng)

**Đánh giá**

- [ ] `scripts/run_eval.py`: reset DB trước mỗi câu, so trạng thái DB với `expected_state`
- [ ] Tổng hợp token, xuất `results/eval.csv` + đồ thị (điểm cộng)

**Report**

- [ ] Mục 5: MCP server
- [ ] Nửa mục 6: kết quả eval, chi phí token
- [ ] Mục 8: Phân công & đóng góp (kèm commit hash)
- [ ] Mục 9: Phụ lục

### 👥 Cả nhóm

- [ ] Ngày 1: chốt hợp đồng tool và hàm `search()`

- [ ] Ngày 5 (14/10): ghép thử, chạy được 1 câu tra cứu + 1 câu chặn IP

- [ ] Ngày 8 (17/10): clone repo vào thư mục trống, chạy `make setup && make demo` như máy GV
- [ ] `ai-usage.md`: mỗi người tự khai phần mình
- [ ] Đọc chéo report, kiểm tra số liệu khớp với `make eval`
- [ ] Tập demo: mỗi người 3 phút về phần mình
- [ ] Tập sửa code tại chỗ: mỗi người nhận 1 yêu cầu sửa nhỏ từ bạn khác
- [ ] In sơ đồ kiến trúc, ôn khái niệm W1–W7, nhớ số liệu eval của mình
- [ ] Nộp: `report.docx`, repo (kèm `.git`), `logs/`, `tests/testset.jsonl`, `ai-usage.md`, `README.md`
