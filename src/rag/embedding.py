import os 
import sys
import requests
import numpy as np 
import time 
import random
import hashlib
import json
from dotenv import load_dotenv
from chunking import chunk_all
load_dotenv()

JINA_URL = "https://api.jina.ai/v1/embeddings"
MODEL_NAME = "jina-embeddings-v3"
TASK_PASSAGE = "retrieval.passage"             # dùng khi embed chunk, tài liệu mẫu
TASK_QUERY = "retrieval.query"                 # dùng khi embed câu hỏi, câu hỏi người dùng
INDEX_DIR = "data/index"

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
    for attempt in range (max_retries + 1):    # 1 lần đầu + tối đa max_retries lần thử lại
        try:
            return _post_jina ( texts, task)
        except requests.exceptions.HTTPError as e: 
            status = e.response.status_code #mã lỗi: 401. 402,...
            co_the_retry = (status == 429) or (status>=500) # chỉ khi gặp lỗi quá tải/lỗi server thì mới retry lại
            if co_the_retry and attempt < max_retries:
                delay = 2 ** attempt + random.uniform(0,1)
                print(f"HTTP {status}. Thử lại sau {delay:.1f}s (lần {attempt+1}/{max_retries})...", file=sys.stderr)
                time.sleep(delay)
            else: 
                raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < max_retries:
                delay = 2 ** attempt + random.uniform(0,1)
                print(f"Lỗi mạng. Thử lại sau {delay:.1f}s (lần {attempt+1}/{max_retries})...", file=sys.stderr)
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

# AI hỗ trợ
def save_index(matrix: np.ndarray, chunks: list, index_hash: str, index_dir: str = INDEX_DIR) -> None:
    os.makedirs(index_dir, exist_ok=True)                                # tạo data/index nếu chưa có, có rồi thì bỏ qua
    np.save(os.path.join(index_dir, "embeddings.npy"), matrix)           # lưu ma trận (57, 1024) dạng nhị phân
    meta = {
        "hash": index_hash,                                              # dấu vân tay của bộ chunk lúc embed
        "model": MODEL_NAME,                                             # để người đọc file biết dùng model nào
        "task": TASK_PASSAGE,                                            # để người đọc file biết dùng task nào
        "chunk_ids": [c.chunk_id for c in chunks],                       # hàng i trong .npy ứng với chunk_ids[i]
    }
    with open(os.path.join(index_dir, "meta.json"), "w", encoding="utf-8") as f:   # mở file để GHI
        json.dump(meta, f, ensure_ascii=False, indent=2)                 # ghi dict ra JSON, giữ nguyên tiếng Việt

# AI hỗ trợ
def load_index(index_dir: str = INDEX_DIR):
    npy_path = os.path.join(index_dir, "embeddings.npy")                 # đường dẫn file ma trận
    meta_path = os.path.join(index_dir, "meta.json")                     # đường dẫn file meta
    if not (os.path.exists(npy_path) and os.path.exists(meta_path)):     # thiếu 1 trong 2 file
        return None                                                      # nghĩa là chưa có cache
    matrix = np.load(npy_path)                                           # đọc lại ma trận
    with open(meta_path, "r", encoding="utf-8") as f:                    # mở file để ĐỌC
        meta = json.load(f)                                              # JSON → dict
    return matrix, meta                                                  # trả về tuple 2 phần tử


def load_or_build_index(docs_dir: str = "data/docs", index_dir: str = INDEX_DIR,
                        force: bool = False) -> tuple[list, np.ndarray]:
    chunks = chunk_all(docs_dir)                                         # luôn chunk lại từ playbook (nhanh, không tốn API)
    current_hash = compute_index_hash(chunks)                            # hash của playbook HIỆN TẠI

    cached = None if force else load_index(index_dir)                    # force=True → bỏ qua cache, bắt build lại
    if cached is not None:                                               # có cache trên đĩa
        matrix, meta = cached                                            # tách tuple
        if meta["hash"] == current_hash and matrix.shape[0] == len(chunks):   # hash khớp VÀ số hàng khớp
            for i, c in enumerate(chunks):
                c.embedding = matrix[i]                                  # gắn lại vector cho từng chunk
            print(f"[embedding] Dùng cache: {len(chunks)} chunk, không gọi API", file=sys.stderr)
            return chunks, matrix                                        # xong, thoát sớm
        print("[embedding] Playbook hoặc model đã đổi → embed lại", file=sys.stderr)      # có cache nhưng đã cũ

    matrix = embed_chunks(chunks)                                        # gọi Jina (57 chunk → 2 lần gọi)
    save_index(matrix, chunks, current_hash, index_dir)                  # lưu cho lần sau
    print(f"[embedding] Đã build và lưu index: {matrix.shape}", file=sys.stderr)
    return chunks, matrix


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
