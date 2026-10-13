---
doc_id: SEC-04
title: Ma trận mức độ nghiêm trọng (severity) cho tấn công brute-force
version: 1.0
date: 2026-01-15
owner: Phòng An ninh thông tin UTE
status: active
---

## 1. Mục đích và phạm vi

Tài liệu này quy định cách xếp mức độ nghiêm trọng (severity) của một sự việc brute-force và thời gian chặn tương ứng. Tài liệu ban hành lần đầu cùng ngày với playbook SEC-02 phiên bản 2.0 và được dùng cùng playbook đó: SEC-02 quyết định có phải tấn công hay không, SEC-04 quyết định mức độ và thời gian chặn.

## 2. Số lần thất bại dùng để xếp mức

Số lần thất bại dùng để xếp mức là số lần đăng nhập thất bại lớn nhất của địa chỉ IP trong một cửa sổ 5 phút, đếm theo cách ở mục 3 của SEC-02. Nếu số này dưới 5 thì không phải tấn công brute-force và không xếp mức.

## 3. Ma trận severity

| Mức | Điều kiện | Thời gian chặn | Tạo sự cố (incident) |
|---|---|---|---|
| Medium | 5 – 19 lần thất bại | 1 giờ (60 phút) | Bắt buộc, trạng thái `open` |
| High | 20 – 49 lần thất bại | 24 giờ (1440 phút) | Bắt buộc, trạng thái `open` |
| Critical | Từ 50 lần thất bại trở lên, hoặc có nhắm vào tài khoản quản trị | 7 ngày (10080 phút) | Bắt buộc, trạng thái `escalated` |

## 4. Tài khoản quản trị

Tài khoản quản trị gồm các username: `admin`, `root`, `administrator`. Chỉ cần một IP vượt ngưỡng của SEC-02 và có ít nhất một lần thất bại nhắm vào tài khoản quản trị thì xếp mức Critical, bất kể tổng số lần thất bại.

## 5. Quy tắc khi nhiều điều kiện cùng thoả

Khi một sự việc thoả điều kiện của nhiều mức, luôn chọn mức cao nhất. Ví dụ: 25 lần thất bại (High) nhưng có nhắm vào `root` thì xếp Critical.

## 6. Áp dụng với IP nội bộ và đối tác

IP nội bộ và đối tác (theo SEC-03) vẫn được xếp mức theo ma trận này để ghi vào sự cố, nhưng không áp dụng thời gian chặn. Các IP này không bị chặn mà phải leo thang theo SEC-05.

## 7. Tham khảo

- NIST SP 800-61 Rev. 3 (2025): https://csrc.nist.gov/pubs/sp/800/61/r3/final
- CISA Federal Government Cybersecurity Incident and Vulnerability Response Playbooks (2021), phần xếp mức theo NCISS: https://www.cisa.gov/sites/default/files/2023-02/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf
- MITRE ATT&CK T1110 Brute Force: https://attack.mitre.org/techniques/T1110/
