import ipaddress
from datetime import datetime
from pathlib import Path

# Đường dẫn
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LOG_FILE = DATA / "auth_logs" / "auth_logs.csv"
STATE_DIR = DATA / "state"
DOCS_DIR = DATA / "docs"

# Set đồng hồ cố định, mọi tool coi 1/10/2026, 10:00 AM là bây giờ. seed_logs.py sinh log quanh mốc thời gian này
NOW = datetime(2026, 10, 1, 10, 0, 0)

# Dải IP nội bộ và đối tác theo SEC-03 v1.3
INTERNAL_NETS = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
PARTNER_NETS = [ipaddress.ip_network("198.51.100.0/24")]

def classify_ip(ip):
    """Trả về 'internal', 'partner' hoặc 'external'. Nếu sai định dạng thì báo ValueError"""
    address = ipaddress.ip_address(ip.strip())
    if any(address in net for net in INTERNAL_NETS):
        return "internal"
    if any(address in net for net in PARTNER_NETS):
        return "partner"
    return "external"

# Chạy test riêng file này
if __name__ == "__main__":
    for ip in ["203.0.113.7", "10.0.5.12", "172.16.3.9", "172.32.0.1",
               "192.168.1.25", "198.51.100.20", "192.0.2.44"]:
        print(f"{ip:16} {classify_ip(ip)}")
    print("DOCS_DIR tồn tại: ", DOCS_DIR.exists())

    try: classify_ip("10.0.0.999")
    except ValueError as e:
        print("IP sai định dạng ->", e)