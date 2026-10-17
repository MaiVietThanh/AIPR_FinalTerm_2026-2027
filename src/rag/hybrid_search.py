# Dựa trên bài lab W4 (w4/ex2_1_hybrid_search.py), chỉnh lại cho khớp search.py:
#   - embed_text lấy từ embedding.py (Jina) thay vì Vector_Store của lớp
#   - thêm tham số only_active để chỉ xét tài liệu status=active
#   - matrix đã chuẩn hoá độ dài nên cosine = tích vô hướng (matrix @ q)
import string
import numpy as np
from rank_bm25 import BM25Okapi
from embedding import embed_text

PUNCT = string.punctuation + "—–“”‘’…"          # dấu câu ASCII + dấu tiếng Việt/Word


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("/", " ")        # chữ thường; "lần/5" → "lần 5"
    tokens = text.split()                        # tách theo khoảng trắng thành list từ
    tokens = [t.strip(PUNCT) for t in tokens]    # bỏ dấu câu dính ở hai đầu từ
    return [t for t in tokens if t]   

def normalise_scores(scores: list[float]) -> list[float]:
    # Min-max: đưa điểm BM25 về khoảng 0..1 để cộng được với cosine
    if not scores:                                    # list rỗng → trả rỗng
        return []
    min_s = min(scores)                               # điểm thấp nhất
    max_s = max(scores)                               # điểm cao nhất
    if max_s == min_s:                                # mọi điểm bằng nhau (thường là toàn 0: không khớp từ nào)
        return [0.0] * len(scores)                  
    return [(s - min_s) / (max_s - min_s) for s in scores]   # thấp nhất → 0, cao nhất → 1     

def build_bm25_index(chunks: list) -> BM25Okapi:
    tokenized = [tokenize(c.content) for c in chunks]  # mỗi chunk → list token
    return BM25Okapi(tokenized)

def hybrid_search(
    query: str,
    chunks: list,
    matrix,                                           # ma trận (57, 1024) từ load_or_build_index
    bm25_index: BM25Okapi,
    top_k: int = 3,
    only_active: bool = True,
    w_bm25: float = 0.3,
    w_vector: float = 0.7,
) -> list[tuple[int, float]]:
    # Điểm hybrid = 0.3 * BM25 (đã chuẩn hoá) + 0.7 * cosine. Trả về [(vị trí chunk, điểm)] giảm dần
    if not chunks:
        return []

    # 0. Chọn ứng viên TRƯỚC khi chuẩn hoá
    if only_active:
        candidates = [i for i, c in enumerate(chunks)
                      if c.metadata.get("status") == "active"]   # chỉ giữ vị trí các chunk active
    else:
        candidates = list(range(len(chunks)))                    # giữ tất cả: 0, 1, ..., 56
    if not candidates:
        return []

    # 1. Điểm BM25: tính cho cả 57 chunk, rồi chỉ lấy ứng viên, rồi min-max
    bm25_all = bm25_index.get_scores(tokenize(query))            # numpy array dài 57
    bm25_raw = [float(bm25_all[i]) for i in candidates]          # chỉ điểm của ứng viên
    bm25_norm = normalise_scores(bm25_raw)                       # min-max TRONG nhóm ứng viên

    # 2. Điểm vector: cosine thô, KHÔNG min-max (giữ ý nghĩa tuyệt đối cho ngưỡng no_answer)
    q = embed_text(query)                                        # (1024,), task query
    cos_all = matrix @ q                                         # 57 điểm cosine cùng lúc
    cos_raw = [float(cos_all[i]) for i in candidates]            # chỉ điểm của ứng viên

    # 3. Trộn điểm theo trọng số
    results = []
    for idx, b, v in zip(candidates, bm25_norm, cos_raw):        # duyệt song song 3 list cùng độ dài
        results.append((idx, w_bm25 * b + w_vector * v))         # (vị trí chunk, điểm hybrid)

    # 4. Sắp giảm dần, lấy top_k (giống session 2)
    results.sort(key=lambda item: item[1], reverse=True)
    return results[:top_k]
