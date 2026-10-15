import ipaddress
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LOG_FILE = DATA / "auth_logs" / "auth_logs.csv"
STATE_DIR = DATA / "state"

# Đồng hồ cố định: mọi tool coi đây là "bây giờ", cùng mốc với seed_logs.py
NOW = datetime(2026, 10, 1, 10, 0, 0)

# Theo SEC-03 v1.3
INTERNAL_NETS = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
PARTNER_NETS = [ipaddress.ip_network("198.51.100.0/24")]

def classify_ip(ip):
    """Trả về 'internal', 'partner' hoặc 'external'. IP sai định dạng thì báo ValueError."""
    addr = ipaddress.ip_address(ip)
    if any(addr in net for net in INTERNAL_NETS):
        return "internal"
    if any(addr in net for net in PARTNER_NETS):
        return "partner"
    return "external"

if __name__ == "__main__":
    for ip in ["203.0.113.7", "10.0.5.12", "172.16.3.9", "192.168.1.25", "198.51.100.20", "192.0.2.44"]:
        print(f"{ip:16} {classify_ip(ip)}")
    print("LOG_FILE tồn tại:", LOG_FILE.exists())