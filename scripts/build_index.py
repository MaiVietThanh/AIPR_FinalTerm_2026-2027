# Build index RAG từ data/docs -> data/index (embeddings.npy + meta.json).
#   python scripts/build_index.py           dùng lại cache nếu playbook không đổi
#   python scripts/build_index.py --force   bắt build lại (gọi Jina API)
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)                                   # embedding.py dùng đường dẫn tương đối data/index
sys.path.insert(0, str(ROOT / "src" / "rag"))

from embedding import load_or_build_index

chunks, matrix = load_or_build_index(force="--force" in sys.argv)
print(f"Index: {len(chunks)} chunk, ma trận {matrix.shape}")
