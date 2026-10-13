---
doc_id: SEC-09
title: Playbook xử lý tấn công password spraying
version: 1.0
date: 2026-03-01
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này quy định cách đội SOC phát hiện và xử lý tấn công password spraying vào các dịch vụ đăng nhập của UTE (SSH, VPN, cổng web nội bộ). Tài liệu bổ sung cho playbook brute-force SEC-02, vì password spraying có thể không vượt ngưỡng của SEC-02.

## 2. Định nghĩa password spraying

Password spraying là hành vi thử một hoặc vài mật khẩu phổ biến trên rất nhiều tài khoản khác nhau. Mỗi tài khoản chỉ bị thử sai một vài lần nên không chạm ngưỡng khoá tài khoản của SEC-07. Dấu hiệu trong log là một địa chỉ IP đăng nhập thất bại vào nhiều username khác nhau, thường rải trong khoảng thời gian dài hơn brute-force.

## 3. Cách đếm và ngưỡng phát hiện

Số liệu được đếm theo địa chỉ IP nguồn trong một cửa sổ 30 phút liên tục bất kỳ. Một địa chỉ IP bị coi là đang password spraying khi đăng nhập thất bại vào từ 10 username khác nhau trở lên trong cửa sổ 30 phút. Chỉ đếm số username khác nhau có ít nhất một lần thất bại, không đếm tổng số lần thất bại.

## 4. Mức độ nghiêm trọng và thời gian chặn

| Điều kiện | Mức | Thời gian chặn |
|---|---|---|
| Vượt ngưỡng ở mục 3 | High | 24 giờ (1440 phút) |
| Vượt ngưỡng và có thử vào tài khoản quản trị (`admin`, `root`, `administrator`) | Critical | 7 ngày (10080 phút) |

Nếu cùng địa chỉ IP đó cũng vượt ngưỡng brute-force của SEC-02, xếp mức theo cả SEC-04 và bảng trên rồi chọn mức cao nhất.

## 5. Hành động xử lý

- IP bên ngoài mức High: chặn IP theo thời gian ở mục 4 và tạo sự cố trạng thái `open`.
- IP bên ngoài mức Critical: chặn IP theo thời gian ở mục 4 và tạo sự cố trạng thái `escalated`.
- IP nội bộ hoặc đối tác (theo SEC-03): không chặn, tạo sự cố trạng thái `escalated` theo SEC-05.

Không khoá các tài khoản bị thử sai, vì chủ tài khoản không có lỗi và mỗi tài khoản chưa chạm ngưỡng của SEC-07.

## 6. Khi có lần đăng nhập thành công

Nếu trong các username bị thử có tài khoản đăng nhập thành công từ chính địa chỉ IP đó, tài khoản này có thể đã bị chiếm. Ngoài xử lý ở mục 5, phải xử lý tài khoản đó theo playbook tài khoản bị chiếm SEC-10.

## 7. Xác minh sau khi xử lý

Sau khi chặn IP hoặc tạo sự cố, phải kiểm tra lại danh sách chặn hoặc sự cố vừa tạo để xác nhận thay đổi đã được ghi nhận. Sự cố phải ghi số username khác nhau bị thử, khung thời gian và mã tài liệu làm căn cứ.

## 8. Tham khảo

- MITRE ATT&CK T1110.003 Password Spraying: https://attack.mitre.org/techniques/T1110/003/
- MITRE ATT&CK M1036 Account Use Policies: https://attack.mitre.org/mitigations/M1036/
- OWASP Authentication Cheat Sheet, mục Protect Against Automated Attacks: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
