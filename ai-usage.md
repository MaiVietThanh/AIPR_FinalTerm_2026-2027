# Khai báo sử dụng AI
Công cụ AI đã dùng: **Claude (Anthropic)**, trong Claude Projects.

Mức độ:
- **AI viết:** AI viết toàn bộ code, thành viên đọc và hiểu code.
- **AI hướng dẫn:** AI giải thích từng bước và đưa đoạn code mẫu, thành viên tự gõ, chạy và sửa lỗi.
- **AI sửa lỗi:** thành viên viết, AI chỉ ra lỗi và đề xuất cách sửa.
- **Tự viết:** thành viên tự viết và tự kiểm tra.

## Tài liệu và dữ liệu

| Phần | Mức độ | Ghi chú |
| --- | --- | --- |
| `data/docs/SEC-01.md` → `SEC-10.md` | AI kiểm tra | AI dựa vào các nguồn tham khảo kiểm tra 10 playbook có bị xung dột với nhau không (MITRE ATT&CK T1110, NIST SP 800-61, NIST SP 800-63B, CISA playbooks, OWASP, RFC 1918/5737); nhóm duyệt ngưỡng và quy tắc xử lý.
| `scripts/seed_logs.py` | AI hướng dẫn | AI đề xuất bảng kịch bản (IP, số lần sai, kết quả mong đợi); Phát viết code sinh CSV |
| `tests/testset.jsonl` | AI hướng dẫn | AI đề xuất 17 câu đầu và 3 câu `no_answer` T18–T20; nhóm kiểm tra `expected_state` khớp với log và playbook |

## Code

| Phần | Người phụ trách | Mức độ | Ghi chú |
| --- | --- | --- | --- |
| `src/rag/chunking.py`, `embedding.py`, `search.py` | Tuyết | Tái dùng code lab |Tuyết tự khai. Đoạn chú thích lý do chunking trong `chunking.py` do AI viết |
| `src/rag/hybrid_search.py` | Tuyết | Tái dùng code lab | Lấy từ bài lab W4 `ex2_1_hybrid_search.py` của môn học, chỉnh cho dữ liệu của nhóm với sự hỗ trợ của AI |
| `src/config.py`, `src/mcp_server/store.py`, `server.py` | Phát | AI hướng dẫn | AI sửa lỗi treo `search_docs` trên Windows (import RAG khi server khởi động) |
| `src/mcp_server/tools.py` | Phát | AI hướng dẫn, AI sửa lỗi | 6 tool đọc và 4 tool ghi theo từng bước; AI thêm `ip_type`, `success_after_fail`, `max_distinct_users_in_30min` vào `count_failed_logins` sau khi phân tích kết quả eval |
| `src/agent/parser.py`, `logger.py` | Thành | AI hướng dẫn |
| `src/agent/loop.py` | Thành | AI hướng dẫn, AI sửa lỗi | AI thêm `MAX_OBS`, cảnh báo khi model viết nhiều lệnh một lượt (`_count_objects`), tổng hợp USAGE từng câu |
| `src/agent/llm.py` | Thành | AI sửa lỗi | AI viết lại phần cấu hình qua `.env`, xử lý 429/hết hạn mức ngày, function calling gốc cho gpt-oss |
| `src/mcp_server/schemas.py` | Phát | AI hướng dẫn | TypedDict cho kết quả 10 tool; FastMCP dùng để sinh outputSchema và kiểm tra kết quả |
| `src/agent/mcp_client.py` | Phát | AI viết | Cầu nối sync/async tới MCP server qua stdio, `openai_tools()` |
| `scripts/ask.py`, `scripts/run_eval.py` | Phát | AI viết | run_eval: reset state mỗi câu, so state, kiểm tra trích nguồn, LLM judge, `--resume` |
| `scripts/build_index.py`,`Makefile`, `reset_state.py`, `README.md` | Thành | AI hướng dẫn | |

## Prompt

| Phần | Mức độ | Ghi chú |
| --- | --- | --- |
| `prompts/system.txt` | AI hướng dẫn | Bản đầu (quy tắc 1–7) AI soạn, nhóm gõ lại; quy tắc 8–16 AI thêm sau khi phân tích các câu eval trượt |
| `prompts/judge.txt` | AI hướng dẫn | Chấm faithfulness theo từng khẳng định, bỏ qua câu từ chối |

## Báo cáo

| Phần | Mức độ | Ghi chú |
| --- | --- | --- |
| `report.docx` | AI hướng dẫn |  |

## Cam kết

Mọi phần do AI viết hoặc hỗ trợ đều đã được thành viên phụ trách đọc hiểu, chạy thử và có thể giải thích khi vấn đáp.
