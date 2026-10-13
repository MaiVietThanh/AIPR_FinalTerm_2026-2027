---
doc_id: SEC-10
title: Playbook xử lý tài khoản bị chiếm
version: 1.0
date: 2026-03-01
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này quy định cách đội SOC phát hiện và xử lý tài khoản có dấu hiệu bị chiếm, tức là kẻ tấn công đã đoán đúng mật khẩu và đăng nhập thành công. Đây là tình huống nghiêm trọng hơn brute-force hay password spraying, vì kẻ tấn công đã vào được hệ thống.

## 2. Dấu hiệu tài khoản bị chiếm

Một tài khoản được coi là có dấu hiệu bị chiếm khi có từ 5 lần đăng nhập thất bại trở lên trong vòng 15 phút, sau đó có một lần đăng nhập thành công vào chính tài khoản đó từ cùng địa chỉ IP với các lần thất bại.

Đăng nhập thành công từ một IP khác với các lần thất bại không được coi là dấu hiệu bị chiếm theo tài liệu này.

## 3. Mức độ nghiêm trọng

Mọi trường hợp tài khoản bị chiếm đều được xếp mức Critical, bất kể số lần thất bại trước đó.

## 4. Hành động xử lý với IP bên ngoài

Khi địa chỉ IP là IP bên ngoài (theo SEC-03):
- Khoá tài khoản bị chiếm. Tài khoản bị khoá cho đến khi trưởng ca SOC xác minh với chủ tài khoản và mở khoá thủ công, không tự mở sau 30 phút như quy định thông thường của SEC-07.
- Chặn địa chỉ IP trong 7 ngày (10080 phút).
- Tạo sự cố trạng thái `escalated` để trưởng ca xác minh và yêu cầu chủ tài khoản đổi mật khẩu.

## 5. Hành động xử lý với IP nội bộ hoặc đối tác

Khi địa chỉ IP thuộc dải nội bộ hoặc đối tác (theo SEC-03), sự việc có thể chỉ là nhân viên nhập sai mật khẩu nhiều lần rồi nhớ ra. Vì vậy:
- Không chặn IP và không khoá tài khoản.
- Tạo sự cố trạng thái `escalated` để trưởng ca liên hệ chủ tài khoản xác minh.

## 6. Xác minh sau khi xử lý

Sau khi khoá tài khoản, phải kiểm tra lại trạng thái tài khoản để xác nhận đã bị khoá. Sau khi chặn IP hoặc tạo sự cố, phải kiểm tra lại danh sách chặn hoặc sự cố vừa tạo. Sự cố phải ghi username bị chiếm, địa chỉ IP, số lần thất bại, thời điểm đăng nhập thành công và mã tài liệu làm căn cứ.

## 7. Tham khảo

- MITRE ATT&CK T1110 Brute Force, phần phát hiện "nhiều lần thất bại rồi thành công": https://attack.mitre.org/techniques/T1110/
- MITRE ATT&CK M1018 User Account Management và M1032 Multi-factor Authentication (liệt kê trong T1110)
- NIST SP 800-61 Rev. 3 (2025): https://csrc.nist.gov/pubs/sp/800/61/r3/final
