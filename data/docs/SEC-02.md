---
doc_id: SEC-02
title: Playbook xử lý tấn công brute-force đăng nhập
version: 2.0
date: 2026-01-15
owner: Phòng An ninh thông tin UTE
status: active
supersedes: SEC-01
---

## 1. Mục đích và phạm vi

Tài liệu này quy định cách đội SOC phát hiện và xử lý tấn công brute-force vào các dịch vụ đăng nhập của UTE (SSH, VPN, cổng web nội bộ). Phạm vi chỉ gồm tấn công dò mật khẩu qua đăng nhập. Các loại tấn công khác (ransomware, DDoS, phishing…) không thuộc tài liệu này.

Phiên bản 2.0 có hiệu lực từ ngày 2026-01-15 và thay thế hoàn toàn SEC-01 phiên bản 1.0.

## 2. Định nghĩa brute-force

Brute-force đăng nhập là hành vi thử liên tục nhiều mật khẩu để đoán đúng thông tin đăng nhập của một hoặc nhiều tài khoản. Dấu hiệu nhận biết trong log là nhiều lần đăng nhập thất bại xuất phát từ cùng một địa chỉ IP trong thời gian ngắn, có thể nhắm vào một hay nhiều username khác nhau.

## 3. Cách đếm số lần thất bại

Số lần thất bại được đếm theo địa chỉ IP nguồn, trong một cửa sổ thời gian 5 phút liên tục bất kỳ. Chỉ đếm các bản ghi có kết quả thất bại; đăng nhập thành công không được tính. Các lần thất bại rải rác trong khoảng thời gian dài hơn 5 phút không được cộng dồn vào cùng một cửa sổ.

## 4. Ngưỡng phát hiện

Một địa chỉ IP bị coi là đang tấn công brute-force khi có từ 5 lần đăng nhập thất bại trở lên trong cửa sổ 5 phút. Dưới ngưỡng này thì không kết luận là tấn công và không thực hiện chặn.

## 5. Xử lý IP bên ngoài

Địa chỉ IP bên ngoài vượt ngưỡng ở mục 4 được đưa vào danh sách chặn (blocklist). Mức độ nghiêm trọng và thời gian chặn không quy định trong tài liệu này mà được xác định theo ma trận severity SEC-04, dựa trên số lần thất bại và tài khoản bị nhắm tới.

## 6. Xử lý IP nội bộ và IP đối tác

Không được chặn địa chỉ IP thuộc dải nội bộ hoặc dải đối tác, kể cả khi vượt ngưỡng. Danh mục các dải này được quy định trong SEC-03. Với các IP này, chuyên viên SOC phải tạo sự cố ở trạng thái leo thang (escalated) và chuyển cho con người xử lý theo quy trình SEC-05.

## 7. Xác minh sau khi xử lý

Sau mỗi lần chặn IP hoặc tạo sự cố, chuyên viên SOC phải kiểm tra lại danh sách chặn hoặc sự cố vừa tạo để xác nhận thay đổi đã được ghi nhận. Bản ghi chặn phải nêu lý do (số lần thất bại, cửa sổ thời gian) và mã tài liệu làm căn cứ.

## 8. Thay đổi so với phiên bản 1.0

- Ngưỡng phát hiện giảm từ 10 xuống 5 lần thất bại trong 5 phút.
- Thời gian chặn không còn cố định 24 giờ mà theo mức độ nghiêm trọng ở SEC-04.
- Bổ sung quy tắc không chặn IP nội bộ và IP đối tác, thay vào đó phải leo thang.
- Bổ sung yêu cầu xác minh sau khi xử lý.

## 9. Tham khảo

- MITRE ATT&CK T1110 Brute Force: https://attack.mitre.org/techniques/T1110/
- MITRE ATT&CK M1036 Account Use Policies: https://attack.mitre.org/mitigations/M1036/
- OWASP Authentication Cheat Sheet, mục Login Throttling: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- NIST SP 800-61 Rev. 3 (2025): https://csrc.nist.gov/pubs/sp/800/61/r3/final
