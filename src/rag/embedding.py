import os 
import requests
import numpy as np 
from dotenv import load_dotenv

load_dotenv()

JINA_URL = "https://api.jina.ai/v1/embeddings"
MODEL_NAME = "jina-embeddings-v3"
TASK_PASSAGE = "retrieval.passage"             # dùng khi embed chunk
TASK_QUERY = "retrieval.query"                 # dùng khi embed câu hỏi

def _post_jina (texts: list[str], task: str, timeout: int =60) -> list[list[float]]:
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        raise ValueError("Thiếu JINA_API_KEY trong file .env")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": MODEL_NAME,
        "task": task,
        "normalized": True,
        "input": [{"text": t} for t in texts],
    }
    resp = requests.post(JINA_URL, headers=headers, json= payload,timeout=timeout)
    resp.raise_for_status()

    data = resp.json()["data"]
    data = sorted(data, key = lambda x: x["index"])
    return [x["embedding"] for x in data]

def batch_embed_text (input: list[str], task: str = TASK_PASSAGE, batch_size: int = 32) -> np.ndarray:
    all_vecs= []
    for i in range (0, len(input), batch_size): 
        batch = input [i: i + batch_size]
        vecs = _post_jina(batch,task)
        all_vecs.extend(vecs)
    matrix =  np.array(all_vecs, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis = 1, keepdims = True)
    return matrix/norms


if __name__ == "__main__":
    sentences = [
        "Ngưỡng chặn IP theo SEC-02 là 5 lần thất bại trong 5 phút",
        "Dải IP nội bộ của UTE gồm 10.0.0.0/8",
        "Tài khoản admin bị nhắm thì mức Critical",
        "Password spraying là thử nhiều username trong 30 phút",
        "Bỏ chặn IP theo quy trình SEC-06",
    ]
    M_nho = batch_embed_text(sentences, batch_size=2)    # 3 lần gọi API
    M_lon = batch_embed_text(sentences, batch_size=32)   # 1 lần gọi API
    print(M_nho.shape)                                   # kích thước ma trận
    print(np.linalg.norm(M_nho, axis=1))                 # độ dài từng hàng
    print(np.allclose(M_nho, M_lon, atol=1e-3))          # chia batch có làm lệch thứ tự không?