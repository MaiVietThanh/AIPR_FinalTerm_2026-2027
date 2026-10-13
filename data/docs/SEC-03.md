---
doc_id: SEC-03
title: Danh mục dải IP nội bộ và đối tác
version: 1.3
date: 2026-02-01
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này liệt kê các dải địa chỉ IP được coi là nội bộ hoặc đối tác của UTE. Đội SOC dùng danh mục này để quyết định một địa chỉ IP có được phép chặn hay không theo playbook brute-force SEC-02.

## 2. Dải IP nội bộ

Các dải sau là mạng nội bộ của UTE, theo chuẩn địa chỉ riêng RFC 1918:

| Dải (CIDR) | Phạm vi địa chỉ | Sử dụng |
|---|---|---|
| 10.0.0.0/8 | 10.0.0.0 – 10.255.255.255 | Máy trạm và máy chủ văn phòng |
| 172.16.0.0/12 | 172.16.0.0 – 172.31.255.255 | Mạng lab và môi trường thử nghiệm |
| 192.168.0.0/16 | 192.168.0.0 – 192.168.255.255 | Wi-Fi văn phòng và VPN nhân viên |

Lỗi đăng nhập từ dải nội bộ thường do nhân viên nhập sai mật khẩu, máy bị nhiễm mã độc hoặc tài khoản bị lạm dụng từ bên trong. Vì vậy không chặn tự động mà phải để con người điều tra.

## 3. Dải IP đối tác

| Dải (CIDR) | Đối tác | Ghi chú |
|---|---|---|
| 198.51.100.0/24 | Công ty Đối tác X (dịch vụ tích hợp hệ thống) | Kết nối VPN site-to-site vào hệ thống UTE |

Chặn IP đối tác có thể làm gián đoạn dịch vụ đang chạy theo hợp đồng, nên mọi sự việc liên quan đến dải này phải leo thang cho con người.

## 4. Cách phân loại một địa chỉ IP

Một địa chỉ IP được phân loại như sau:
- Thuộc một trong các dải ở mục 2: IP nội bộ.
- Thuộc dải ở mục 3: IP đối tác.
- Không thuộc dải nào ở mục 2 và mục 3: IP bên ngoài.

Chỉ IP bên ngoài mới được đưa vào danh sách chặn. IP nội bộ và IP đối tác được xử lý theo mục 6 của SEC-02 và quy trình leo thang SEC-05.

## 5. Lịch sử thay đổi

- 1.3 (2026-02-01): bổ sung dải 172.16.0.0/12 cho mạng lab.
- 1.2 (2025-09-10): bổ sung dải đối tác 198.51.100.0/24.
- 1.0 (2025-03-01): ban hành lần đầu với dải 10.0.0.0/8 và 192.168.0.0/16.

## 6. Tham khảo

- RFC 1918, Address Allocation for Private Internets: https://www.rfc-editor.org/rfc/rfc1918
- RFC 5737, IPv4 Address Blocks Reserved for Documentation: https://www.rfc-editor.org/rfc/rfc5737
- MITRE ATT&CK M1036 Account Use Policies: https://attack.mitre.org/mitigations/M1036/
