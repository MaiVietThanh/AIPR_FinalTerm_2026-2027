---
doc_id: SEC-01
title: Playbook xử lý tấn công brute-force đăng nhập
version: 1.0
date: 2025-03-01
owner: Phòng An ninh thông tin UTE
status: superseded
superseded_by: SEC-02
---

## 1. Mục đích và phạm vi

Tài liệu này quy định cách đội SOC phát hiện và xử lý tấn công brute-force vào các dịch vụ đăng nhập của UTE (SSH, VPN, cổng web nội bộ). Phạm vi chỉ gồm tấn công dò mật khẩu qua đăng nhập. Các loại tấn công khác không thuộc tài liệu này.

Lưu ý: phiên bản 1.0 đã hết hiệu lực từ ngày 2026-01-15 và được thay thế bởi SEC-02 phiên bản 2.0.

## 2. Định nghĩa brute-force

Brute-force đăng nhập là hành vi thử liên tục nhiều mật khẩu để đoán đúng thông tin đăng nhập của một hoặc nhiều tài khoản. Dấu hiệu nhận biết trong log là nhiều lần đăng nhập thất bại liên tiếp xuất phát từ cùng một địa chỉ IP trong thời gian ngắn.

## 3. Ngưỡng phát hiện

Một địa chỉ IP bị coi là đang tấn công brute-force khi có từ 10 lần đăng nhập thất bại trở lên trong cửa sổ 5 phút. Chỉ đếm các bản ghi có kết quả thất bại; đăng nhập thành công không được tính.

## 4. Hành động xử lý

Mọi địa chỉ IP vượt ngưỡng ở mục 3 đều bị đưa vào danh sách chặn (blocklist) trong 24 giờ. Phiên bản này không phân biệt IP nội bộ, IP đối tác hay IP bên ngoài, và không phân mức độ nghiêm trọng.

## 5. Ghi nhận

Sau khi chặn, chuyên viên SOC ghi lại địa chỉ IP, số lần thất bại và thời điểm chặn vào sổ theo dõi sự cố.

## 6. Tham khảo

- MITRE ATT&CK T1110 Brute Force: https://attack.mitre.org/techniques/T1110/
- NIST SP 800-61 Rev. 2, Computer Security Incident Handling Guide (2012): https://csrc.nist.gov/pubs/sp/800/61/r2/final
