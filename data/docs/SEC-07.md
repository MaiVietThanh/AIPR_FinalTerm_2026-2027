---
doc_id: SEC-07
title: Chính sách mật khẩu và khoá tài khoản
version: 1.0
date: 2025-05-20
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này quy định yêu cầu mật khẩu và cơ chế khoá tài khoản khi đăng nhập sai nhiều lần trên các dịch vụ của UTE (SSH, VPN, cổng web nội bộ). Tài liệu áp dụng cho mọi tài khoản trong hệ thống đăng nhập của UTE (nhân viên, quản trị viên, tài khoản cấp cho đối tác), bất kể lần đăng nhập đến từ IP nội bộ, IP đối tác hay IP bên ngoài. Tài liệu chỉ nói về khoá tài khoản người dùng, không nói về chặn địa chỉ IP.

## 2. Phân biệt khoá tài khoản và chặn IP

Khoá tài khoản và chặn IP là hai biện pháp khác nhau:
- Khoá tài khoản tác động lên một username. Số lần sai được đếm theo tài khoản, từ bất kỳ địa chỉ IP nào. Khi bị khoá, chính chủ tài khoản cũng không đăng nhập được.
- Chặn IP tác động lên một địa chỉ IP nguồn. Số lần sai được đếm theo IP, trên bất kỳ tài khoản nào. Việc chặn IP được quy định trong playbook brute-force đang hiệu lực, không thuộc tài liệu này.

Một sự việc có thể kích hoạt cả hai biện pháp, ví dụ một IP thử sai nhiều lần vào cùng một tài khoản.

## 3. Ngưỡng khoá tài khoản

Tài khoản bị khoá tạm thời khi có 5 lần đăng nhập thất bại liên tiếp trong vòng 15 phút. Bộ đếm được đặt lại về 0 khi đăng nhập thành công hoặc sau 15 phút không có lần sai nào.

## 4. Thời gian khoá

- Tài khoản thông thường bị khoá 30 phút, sau đó tự động mở khoá.
- Tài khoản quản trị (`admin`, `root`, `administrator`) bị khoá cho đến khi trưởng ca SOC xác minh và mở khoá thủ công.

## 5. Yêu cầu mật khẩu

- Mật khẩu dài tối thiểu 12 ký tự.
- Không được dùng mật khẩu nằm trong danh sách mật khẩu phổ biến hoặc đã bị lộ.
- Không dùng lại mật khẩu của tài khoản khác hoặc dịch vụ khác.
- Tài khoản quản trị bắt buộc dùng xác thực đa yếu tố (MFA).

## 6. Giới hạn của khoá tài khoản

Khoá tài khoản không ngăn được tấn công password spraying, vì kẻ tấn công chỉ thử một vài mật khẩu trên mỗi tài khoản để không chạm ngưỡng khoá. Loại tấn công này được phát hiện bằng cách đếm số lần sai theo địa chỉ IP nguồn trên nhiều tài khoản.

## 7. Tham khảo

- MITRE ATT&CK M1036 Account Use Policies: https://attack.mitre.org/mitigations/M1036/
- OWASP Authentication Cheat Sheet, mục Account Lockout: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- NIST SP 800-63B, mục 3.2.2 Rate Limiting (Throttling): https://pages.nist.gov/800-63-4/sp800-63b.html
