<<<<<<< Updated upstream
=======
# Lấy từ bài lab W4 (w4/ex2_1_hybrid_search.py), chỉnh lại cho khớp search.py:
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
    tokens = text.split()                        # tách theo khoảng trắng
    tokens = [t.strip(PUNCT) for t in tokens]    # bỏ dấu câu dính ở hai đầu từ
    return [t for t in tokens if t]


def normalise_scores(scores) -> list[float]:
    """Đưa điểm về [0, 1] bằng min-max (giống lab W4)."""
    scores = list(scores)
    if not scores:
        return []
    min_s, max_s = min(scores), max(scores)
    if max_s == min_s:
        return [1.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


def build_bm25_index(chunks: list) -> BM25Okapi:
    """Dựng chỉ mục BM25 từ nội dung các chunk."""
    return BM25Okapi([tokenize(c.content) for c in chunks])


def hybrid_search(query: str, chunks: list, matrix, bm25: BM25Okapi, top_k: int = 3,
                  only_active: bool = True, w_bm25: float = 0.3,
                  w_vector: float = 0.7) -> list[tuple[int, float]]:
    """Kết hợp điểm BM25 (từ khoá) và cosine (ngữ nghĩa). Trả về [(chỉ số chunk, điểm)]."""
    if only_active:
        candidates = [i for i, c in enumerate(chunks) if c.metadata.get("status") == "active"]
    else:
        candidates = list(range(len(chunks)))
    if not candidates:
        return []

    bm25_all = bm25.get_scores(tokenize(query))
    q = np.asarray(embed_text(query), dtype=float)
    cos_all = matrix @ q

    # chuẩn hoá trên đúng tập ứng viên, để tài liệu cũ không làm lệch thang điểm
    norm_bm25 = normalise_scores(bm25_all[i] for i in candidates)
    norm_vec = normalise_scores(cos_all[i] for i in candidates)

    results = [(i, w_bm25 * b + w_vector * v)
               for i, b, v in zip(candidates, norm_bm25, norm_vec)]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
>>>>>>> Stashed changes
