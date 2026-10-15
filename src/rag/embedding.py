import os 
import requests
import numpy as np 
import time 
import random
import hashlib
from dotenv import load_dotenv

load_dotenv()

JINA_URL = "https://api.jina.ai/v1/embeddings"
MODEL_NAME = "jina-embeddings-v3"
TASK_PASSAGE = "retrieval.passage"             # dùng khi embed chunk, tài liệu mẫu
TASK_QUERY = "retrieval.query"                 # dùng khi embed câu hỏi, câu hỏi người dùng

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

def _post_jina_with_retry (texts: list[str], task: str, max_retries: int =3)-> list[list[float]]:
    for attempt in range (3): 
        try:
            return _post_jina ( texts, task)
        except requests.exceptions.HTTPError as e: 
            status = e.response.status_code #mã lỗi: 401. 402,...
            co_the_retry = (status == 429) or (status>=500) # chỉ khi gặp lỗi quá tải/lỗi server thì mới retry lại
            if co_the_retry and attempt < max_retries:
                delay = 2 ** attempt + random.uniform(0,1)
                print(f"HTTP {status}. Thử lại sau {delay:.1f}s (lần {attempt+1}/{max_retries})...")
                time.sleep(delay)
            else: 
                raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < max_retries:
                delay = 2 ** attempt + random.uniform(0,1)
                print(f"Lỗi mạng. Thử lại sau {delay:.1f}s (lần {attempt+1}/{max_retries})...")
                time.sleep(delay)
            else: 
                raise

def batch_embed_text (input: list[str], task: str = TASK_PASSAGE, batch_size: int = 32) -> np.ndarray:
    all_vecs= []
    for i in range (0, len(input), batch_size): 
        batch = input [i: i + batch_size]
        vecs = _post_jina_with_retry(batch,task)
        all_vecs.extend(vecs)
    matrix =  np.array(all_vecs, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis = 1, keepdims = True)
    return matrix/norms

def embed_text (text: str, task: str = TASK_QUERY) -> np.ndarray: 
    matrix = batch_embed_text([text], task= task) 
    return matrix [0]

def embed_chunks (chunks: list, batch_size: int = 32) -> np.ndarray:
    texts= [c.content for c in chunks]
    matrix = batch_embed_text(texts, task = TASK_PASSAGE, batch_size= batch_size)
    for i, chunk in enumerate(chunks): 
        chunk.embedding = matrix [i]
    return matrix

def compute_index_hash (chunks: list) -> str: 
    h = hashlib.sha256()
    h.update(f"{MODEL_NAME} | {TASK_PASSAGE}\n".encode("utf-8"))
    for c in chunks: 
        h.update(f"{c.chunk_id}\n{c.content}\n".encode("utf-8"))
    return h.hexdigest()

if __name__ == "__main__":
    from chunking import chunk_all

    chunks = chunk_all("data/docs")
    h1 = compute_index_hash(chunks)
    h2 = compute_index_hash(chunk_all("data/docs"))   # đọc lại từ đầu
    print(h1[:16], len(h1))                           # 16 ký tự đầu, tổng độ dài
    print(h1 == h2)                                   # cùng nội dung → phải True

    chunks[10].content += " "                         # lén thêm 1 dấu cách vào chunk thứ 10
    print(compute_index_hash(chunks) == h1)           # phải False