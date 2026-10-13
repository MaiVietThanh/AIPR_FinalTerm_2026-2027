---
doc_id: SEC-08
title: Bảng thuật ngữ SOC dùng trong các playbook
version: 1.0
date: 2026-01-15
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này giải thích các thuật ngữ dùng trong bộ playbook SEC-01 đến SEC-07 để mọi người trong đội SOC hiểu thống nhất. Tài liệu chỉ định nghĩa thuật ngữ, không quy định ngưỡng hay hành động xử lý.

## 2. Thuật ngữ về các kiểu tấn công đăng nhập

- **Brute-force (MITRE T1110):** thử liên tục nhiều mật khẩu để đoán đúng thông tin đăng nhập.
- **Password guessing (T1110.001):** đoán nhiều mật khẩu trên một tài khoản cụ thể.
- **Password spraying (T1110.003):** thử một hoặc vài mật khẩu phổ biến trên rất nhiều tài khoản khác nhau, để tránh chạm ngưỡng khoá từng tài khoản.
- **Credential stuffing (T1110.004):** dùng các cặp username và mật khẩu bị lộ từ dịch vụ khác để thử đăng nhập, lợi dụng việc người dùng dùng lại mật khẩu.

## 3. Thuật ngữ về phát hiện

- **Đăng nhập thất bại:** một bản ghi trong log đăng nhập có kết quả thất bại (sai mật khẩu hoặc sai username).
- **Cửa sổ thời gian:** khoảng thời gian liên tục dùng để đếm số lần thất bại, ví dụ 5 phút.
- **Ngưỡng:** số lần thất bại tối thiểu trong một cửa sổ thời gian để kết luận là tấn công.
- **Mức độ nghiêm trọng (severity):** mức Medium, High hoặc Critical, dùng để quyết định thời gian chặn và việc leo thang.

## 4. Thuật ngữ về địa chỉ IP

- **IP nội bộ:** địa chỉ thuộc mạng nội bộ của công ty.
- **IP đối tác:** địa chỉ thuộc mạng của đối tác có kết nối hợp đồng với công ty.
- **IP bên ngoài:** địa chỉ không thuộc IP nội bộ và không thuộc IP đối tác.

## 5. Thuật ngữ về xử lý

- **Danh sách chặn (blocklist):** danh sách các địa chỉ IP bị từ chối kết nối trong một khoảng thời gian.
- **Chặn IP:** đưa một địa chỉ IP vào danh sách chặn.
- **Khoá tài khoản:** tạm thời không cho một username đăng nhập, khác với chặn IP.
- **Sự cố (incident):** hồ sơ ghi nhận một sự việc an ninh, có trạng thái `open`, `escalated` hoặc `resolved`.
- **Leo thang (escalation):** chuyển sự việc cho trưởng ca SOC quyết định thay vì tự xử lý.
- **Trưởng ca SOC:** người phụ trách ca trực, có quyền bỏ chặn IP, mở khoá tài khoản quản trị và đóng sự cố đã leo thang.
- **SOC (Security Operations Center):** đội giám sát và ứng phó sự cố an ninh của công ty.

## 6. Tham khảo

- MITRE ATT&CK T1110 Brute Force và các kỹ thuật con: https://attack.mitre.org/techniques/T1110/
- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
