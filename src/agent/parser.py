# Đọc câu trả lời của LLM và đổi thành Action: gọi tool, trả lời cuối, hoặc lỗi định dạng.
# Model phải trả 1 object JSON: {"action": tên tool, "args": {...}} hoặc {"final_answer": "..."}.
import json
from dataclasses import dataclass, field

@dataclass
class Action:
    kind: str                                  # "tool" | "final" | "error"
    name: str = ""                             # tên tool (khi kind="tool")
    args: dict = field(default_factory=dict)   # tham số tool
    text: str = ""                             # câu trả lời cuối hoặc thông báo lỗi

def _extract_json(text: str):
    # Lấy object JSON đầu tiên trong text; model quên đóng ngoặc } thì thử vá rồi đọc lại
    start = text.find("{")                     # thao tác bỏ qua mọi chữ đứng trước {
    if start == -1:
        return None
    missing = text.count("{") - text.count("}")
    for candidate in (text, text + "}" * max(missing, 0)):   # thử nguyên văn câu sau đó thử vá ngoặc
        try:
            obj, _ = json.JSONDecoder().raw_decode(candidate, start)
            return obj
        except json.JSONDecodeError:
            continue
    return None

def parse_action(text: str) -> Action:
    # JSON hợp lệ -> Action tương ứng; sai định dạng -> Action("error") để loop báo model sửa lại
    obj = _extract_json(text)
    if not isinstance(obj, dict):
        return Action("error", text="Không đọc được JSON. Hãy trả lời đúng 1 object JSON.")
    if "final_answer" in obj:
        return Action("final", text=str(obj["final_answer"]))
    if "action" in obj:
        args = obj.get("args") or {}
        if not isinstance(args, dict):
            return Action("error", text="'args' phải là object JSON.")
        return Action("tool", name=str(obj["action"]), args=args)
    return Action("error", text="JSON phải có 'action' hoặc 'final_answer'.")