# AIPR FINAL PROJECT 2026-2027 — SOC Agent

Trợ lý SOC của công ty **UTE**: đọc playbook bảo mật (RAG), đọc log đăng nhập qua MCP server, phát hiện brute-force / password spraying / tài khoản bị chiếm, rồi chặn IP, khoá tài khoản, tạo sự cố và tự đọc lại để kiểm chứng.

| Thành viên              | Vai trò                                  | Branch  |
| ----------------------- | ---------------------------------------- | ------- |
| Nguyễn Huỳnh Minh Tuyết | SV1: RAG, playbook, chất lượng trả lời   | `tuyet` |
| Mai Viết Thành          | SV2: Agent loop, Makefile, README        | `thanh` |
| Lê Huy Phát             | SV3: Log, state JSON, MCP server, eval   | `phat`  |

## Chạy nhanh

Cần Python 3.11+ và API key Groq, Jina.

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
make setup                      # cài thư viện, tạo .env, sinh log, build index, reset state
# điền GROQ_API_KEY và JINA_API_KEY vào .env
make demo                       # agent kiểm tra IP 203.0.113.7 và xử lý theo playbook
make eval                       # chạy 20 câu trong tests/testset.jsonl
```

Hỏi câu khác: `make demo Q="Ngưỡng phát hiện brute-force hiện tại là bao nhiêu?"`

Máy không có `make` (Windows) thì chạy trực tiếp:

| Lệnh make          | Lệnh Python tương đương                                        |
| ------------------ | -------------------------------------------------------------- |
| `make setup`       | `pip install -r requirements.txt`, copy `.env.example` thành `.env`, rồi `python scripts/seed_logs.py`, `python scripts/build_index.py`, `python scripts/reset_state.py` |
| `make demo`        | `python scripts/reset_state.py` rồi `python scripts/ask.py`    |
| `make eval`        | `python scripts/run_eval.py`                                   |
| `make eval-resume` | `python scripts/run_eval.py --resume` (chạy tiếp khi bị dừng do hết token) |

Kết quả eval: `results/eval.csv` và `results/eval.png`. Trace từng lần chạy: `logs/run_<timestamp>.jsonl`.

## Cấu hình `.env`

Xem `.env.example`. Mặc định dùng `openai/gpt-oss-120b` trên Groq với function calling gốc (`LLM_NATIVE_TOOLS=1`). Muốn dùng `qwen/qwen3.8-27b` thì đặt `LLM_JSON_MODE=1`, `LLM_REASONING_EFFORT=none`, `LLM_NATIVE_TOOLS=0`. Gói free của Groq giới hạn token theo phút và theo ngày: code tự chờ khi gặp 429, còn hết hạn mức ngày thì dừng và chạy tiếp bằng `make eval-resume`.

## Kiến trúc

```
câu hỏi ─► agent loop (src/agent/loop.py) ──► LLM (Groq)
                │  ▲
     tool call  │  │ Observation
                ▼  │
          MCP client (stdio) ──► MCP server (src/mcp_server/server.py)
                                   ├─ search_docs        → RAG (src/rag, data/index)
                                   ├─ query_auth_logs, count_failed_logins → data/auth_logs/auth_logs.csv
                                   ├─ get_blocklist, get_incident, get_account_status
                                   └─ block_ip, unblock_ip, create_incident, lock_account → data/state/*.json
```

- **RAG:** 10 playbook trong `data/docs/` (SEC-01 v1.0 đã thay thế, SEC-02 v2.0 hiện hành…), cắt theo mục `##`, embedding Jina, tìm kiếm dense hoặc hybrid (BM25 + dense), lọc `status: active`.
- **Agent loop:** tự viết, `MAX_STEPS = 10`, tool lỗi trả về `"Error: ..."` thay vì làm sập chương trình, tên tool lạ bị từ chối.
- **Verify-after-write:** sau mỗi tool ghi, code tự gọi tool đọc tương ứng (`block_ip` → `get_blocklist`, `create_incident` → `get_incident`, `lock_account` → `get_account_status`).
- **State:** không dùng database; blocklist, incidents, accounts lưu trong 3 file JSON, `reset_state()` đưa về ban đầu trước mỗi câu eval.
- Hợp đồng 10 tool: `docs/tool_contract.md`.

## Đánh giá

`scripts/run_eval.py` chạy từng câu trong `tests/testset.jsonl` (20 câu, 4 câu `no_answer`) trên state sạch và chấm:

- **State đúng:** blocklist, incidents (IP, severity, status), tài khoản bị khoá khớp với `expected_state`.
- **Trích nguồn:** câu trả lời có đủ `doc_id` trong `must_cite`.
- **Faithfulness:** LLM judge (`prompts/judge.txt`) tách câu trả lời thành các khẳng định và so với bằng chứng agent đã nhận.
- **Từ chối đúng:** tỉ lệ câu `no_answer` và `no_evidence` mà agent từ chối đúng (không bịa, không gọi tool ghi).
- **Chi phí:** số bước, thời gian và USAGE mỗi câu (calls, prompt_tokens, completion_tokens, max_prompt) trong `eval.csv`.

## Log

Mỗi câu hỏi tạo 1 file `logs/run_<timestamp>.jsonl`, mỗi dòng 1 sự kiện: `question`, `llm` (output và usage từng lần gọi), `observation` (tool, args, kết quả, verify), `final`, `usage` (calls, prompt_tokens, completion_tokens, total_tokens, max_prompt của cả câu; max_prompt là prompt lớn nhất trong 1 lần gọi).

## Cấu trúc thư mục

```
data/docs/          playbook SEC-01..SEC-10 (đầu vào RAG)
data/auth_logs/     auth_logs.csv giả lập (sinh bằng scripts/seed_logs.py)
data/index/         embeddings.npy + meta.json
data/state/         blocklist.json, incidents.json, accounts.json
prompts/            system.txt (agent), judge.txt (chấm faithfulness)
src/config.py       NOW cố định, dải IP nội bộ/đối tác
src/rag/            chunking, embedding, hybrid_search, search
src/mcp_server/     store.py (đọc log, state), schemas.py (TypedDict kết quả tool), tools.py (10 tool), server.py (FastMCP stdio)
src/agent/          llm.py, parser.py, mcp_client.py, loop.py, logger.py, react_trace.py
scripts/            ask.py, run_eval.py, build_index.py, seed_logs.py, reset_state.py, view_log.py
tests/             testset.jsonl (20 câu eval), test_*.py (test MCP server không cần LLM)
results/            eval.csv, eval.png
logs/               trace các lần chạy thật
docs/               hướng dẫn làm việc nhóm, git, tool_contract.md (hợp đồng 10 tool)
```

Khai báo dùng AI: `ai-usage.md`. Hướng dẫn git và phân công chi tiết: `docs/huong-dan-nhom.md`.
