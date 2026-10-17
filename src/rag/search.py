<<<<<<< Updated upstream
=======
from embedding import embed_text, load_or_build_index
from hybrid_search import build_bm25_index, hybrid_search

DENSE_THRESHOLD = 0.40
HYBRID_THRESHOLD = 0.40

# Load index MỘT LẦN khi file được import (giống Week7: STORE = VectorStore(); STORE.load(...))
CHUNKS, MATRIX = load_or_build_index()                 # đọc cache .npy (hoặc build nếu playbook đổi)
BM25 = build_bm25_index(CHUNKS)                        # dựng BM25 một lần (session 2 build_bm25_index)


# ==== Dense search: dựa trên Week3 VectorStore.search ====
def dense_search(query: str, chunks: list, matrix, top_k: int = 3,
                 only_active: bool = True) -> list[tuple[int, float]]:
    if top_k <= 0:                                                   # top_k <= 0 → trả rỗng
        return []
    if only_active:                                                  # mở rộng: chỉ lấy chunk active
        candidates = [i for i, c in enumerate(chunks)
                      if c.metadata.get("status") == "active"]
    else:
        candidates = list(range(len(chunks)))
    q = embed_text(query)                                           
    cos_all = matrix @ q                                            
    results = [(i, float(cos_all[i])) for i in candidates]          
    results.sort(key=lambda item: item[1], reverse=True)            
    return results[:top_k]                                          


# Đổi vị trí, điểm
def _to_dict(chunk, score: float) -> dict:
    md = chunk.metadata                                              # front-matter + "section" (từ chunking.py)
    return {
        "chunk_id": chunk.chunk_id,                                  # "SEC-02#3"
        "doc_id": chunk.doc_id,                                      # "SEC-02"
        "version": str(md.get("version", "")),                       # "2.0"
        "status": md.get("status", ""),                              # "active" / "superseded"
        "title": md.get("title", ""),
        "section": md.get("section", ""),                            # heading ## của mục
        "text": chunk.content,                                       # nội dung cho LLM đọc
        "score": round(score, 4),
    }


# Hàm chính sử dụng
def search(query: str, mode: str = "hybrid", top_k: int = 3,
           only_active: bool = True, min_score: float | None = None) -> list[dict]:
    if mode not in ("dense", "hybrid"):                              # chặn giá trị lạ do LLM truyền
        raise ValueError(f"mode phải là 'dense' hoặc 'hybrid', nhận được: {mode!r}")
    top_k = max(1, min(int(top_k), 8))                               # Week7: max(1, min(top_k, 8))

    if mode == "dense":
        ranked = dense_search(query, CHUNKS, MATRIX, top_k, only_active)
    else:
        ranked = hybrid_search(query, CHUNKS, MATRIX, BM25,          # session 2 hybrid_search
                               top_k=top_k, only_active=only_active)

    if min_score is None:                                            # không truyền → ngưỡng mặc định của chế độ
        min_score = DENSE_THRESHOLD if mode == "dense" else HYBRID_THRESHOLD
    ranked = [(i, s) for i, s in ranked if s >= min_score]           # Week3 search_with_threshold: score >= min_score

    return [_to_dict(CHUNKS[i], s) for i, s in ranked]               # list rỗng = không tìm thấy (Week7)

>>>>>>> Stashed changes
