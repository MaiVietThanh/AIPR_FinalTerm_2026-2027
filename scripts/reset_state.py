# Đưa blocklist/incidents/accounts về trạng thái ban đầu (data/state/*.json).
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "mcp_server"))

from store import reset_state

reset_state()
print("Đã reset data/state về trạng thái ban đầu")
