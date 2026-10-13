---
doc_id: SEC-05
title: Quy trình leo thang sự cố cho con người xử lý
version: 1.1
date: 2026-01-15
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này quy định khi nào đội SOC phải leo thang một sự việc cho con người (trưởng ca SOC) xử lý thay vì tự động chặn, và sự cố leo thang phải có những thông tin gì. Tài liệu áp dụng cho các sự việc đăng nhập bất thường được xử lý theo playbook brute-force SEC-02.

## 2. Các trường hợp bắt buộc leo thang

Phải leo thang khi gặp một trong các trường hợp sau:
- Địa chỉ IP vượt ngưỡng thuộc dải nội bộ hoặc dải đối tác theo SEC-03.
- Sự việc được xếp mức Critical theo SEC-04.

## 3. Thế nào là bằng chứng không đủ

Bằng chứng được coi là không đủ khi:
- Không tìm thấy bản ghi đăng nhập nào của địa chỉ IP cần kiểm tra.
- Không xác định được số lần thất bại hoặc khung thời gian xảy ra.
- Yêu cầu xử lý không nêu rõ địa chỉ IP cụ thể.

Khi bằng chứng không đủ, không được chặn IP, không được suy đoán số liệu và không tạo sự cố, vì sự cố khi đó không có đủ thông tin bắt buộc ở mục 5. Chuyên viên SOC trả lời người yêu cầu, nêu rõ thông tin còn thiếu và cần bổ sung gì để xử lý tiếp.

## 4. Quyết định chặn và trạng thái sự cố

| Loại IP (theo SEC-03) | Mức (theo SEC-04) | Chặn IP | Sự cố |
|---|---|---|---|
| Nội bộ hoặc đối tác | Bất kỳ mức nào | Không chặn | Tạo sự cố trạng thái `escalated` |
| Bên ngoài | Critical | Chặn theo thời gian ở SEC-04 | Tạo sự cố trạng thái `escalated` để trưởng ca quyết định bước tiếp theo |
| Bên ngoài | Medium hoặc High | Chặn theo thời gian ở SEC-04 | Tạo sự cố trạng thái `open` để lưu vết |
| Bất kỳ, nhưng bằng chứng không đủ | Không xếp được mức | Không chặn | Không tạo sự cố, trả lời rõ thông tin còn thiếu (mục 3) |

"IP bên ngoài" là IP không thuộc dải nội bộ và không thuộc dải đối tác trong SEC-03.

Ý nghĩa các trạng thái sự cố được quy định trong SEC-06.

## 5. Thông tin bắt buộc trong sự cố

Mỗi sự cố phải có đủ các thông tin sau:
- Địa chỉ IP nguồn.
- Số lần đăng nhập thất bại.
- Khung thời gian xảy ra (thời điểm bắt đầu và kết thúc).
- Mức độ nghiêm trọng theo SEC-04.
- Mã các tài liệu làm căn cứ (ví dụ SEC-02, SEC-04).
- Tóm tắt hành động đã làm (đã chặn hay chưa chặn, lý do).

Sự cố thiếu một trong các thông tin trên bị coi là chưa hợp lệ.

## 6. Lịch sử thay đổi

- 1.1 (2026-01-15): bổ sung trường hợp leo thang khi sự việc ở mức Critical, cùng lúc với SEC-02 v2.0 và SEC-04.
- 1.0 (2025-11-10): ban hành lần đầu.

## 7. Tham khảo

- NIST SP 800-61 Rev. 3 (2025): https://csrc.nist.gov/pubs/sp/800/61/r3/final
- CISA Federal Government Cybersecurity Incident and Vulnerability Response Playbooks (2021), phần Detection & Analysis và báo cáo leo thang: https://www.cisa.gov/sites/default/files/2023-02/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf
