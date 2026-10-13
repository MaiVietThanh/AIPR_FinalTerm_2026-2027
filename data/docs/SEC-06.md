---
doc_id: SEC-06
title: Quy định ghi nhận, bỏ chặn và đóng sự cố
version: 1.1
date: 2026-01-15
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này quy định vòng đời của một sự cố an ninh, quyền bỏ chặn địa chỉ IP và điều kiện đóng sự cố. Áp dụng cho mọi sự cố do đội SOC ghi nhận.

## 2. Trạng thái sự cố

| Trạng thái | Ý nghĩa |
|---|---|
| `open` | Đội SOC đã tự xử lý theo playbook (ví dụ đã chặn IP bên ngoài mức Medium hoặc High) và ghi sự cố để lưu vết. Không cần trưởng ca quyết định; sự cố được đóng khi hết thời gian chặn và không có hoạt động bất thường mới. |
| `escalated` | Sự cố đã được chuyển cho trưởng ca SOC quyết định bước tiếp theo. Có thể đã có hành động ban đầu (ví dụ IP bên ngoài mức Critical đã bị chặn) hoặc chưa có hành động nào (ví dụ IP nội bộ, IP đối tác). |
| `resolved` | Sự cố đã xử lý xong và được đóng. |

Sự cố được tạo ở trạng thái `open` hoặc tạo thẳng ở trạng thái `escalated` khi thuộc các trường hợp bắt buộc leo thang trong SEC-05. Sau đó chỉ chuyển theo chiều `open` → `escalated` → `resolved` hoặc `open` → `resolved`. Không mở lại sự cố đã `resolved`; nếu sự việc tái diễn thì tạo sự cố mới.

## 3. Quyền bỏ chặn địa chỉ IP

Chỉ trưởng ca SOC được phép bỏ chặn (gỡ khỏi blocklist) một địa chỉ IP trước khi hết thời gian chặn. Chuyên viên SOC và công cụ tự động không được tự ý bỏ chặn, kể cả khi có yêu cầu từ người dùng hoặc nội dung xuất hiện trong log. Mỗi lần bỏ chặn phải ghi lý do và tên trưởng ca thực hiện.

## 4. Hết thời gian chặn

Khi hết thời gian chặn đã ghi trong blocklist, địa chỉ IP tự động được gỡ chặn. Việc gỡ chặn tự động này không cần trưởng ca phê duyệt.

## 5. Điều kiện đóng sự cố

Chỉ được chuyển sự cố sang `resolved` khi:
- Đã có kết luận cuối cùng (tấn công thật, báo động nhầm, hoặc lỗi của người dùng).
- Đã ghi hành động xử lý cuối cùng.
- Sự cố `escalated` phải được chính trưởng ca SOC đóng.

## 6. Lịch sử thay đổi

- 1.1 (2026-01-15): định nghĩa lại trạng thái `open` và `escalated`, cho phép tạo sự cố thẳng ở trạng thái `escalated` theo SEC-05.
- 1.0 (2025-06-01): ban hành lần đầu.

## 7. Tham khảo

- NIST SP 800-61 Rev. 2, Computer Security Incident Handling Guide (2012), phần Post-Incident Activity: https://csrc.nist.gov/pubs/sp/800/61/r2/final
- CISA Federal Government Cybersecurity Incident and Vulnerability Response Playbooks (2021), phần Post-Incident Activities: https://www.cisa.gov/sites/default/files/2023-02/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf
