import string
import numpy as np
from rank_bm25 import BM25Okapi

PUNCT = string.punctuation + "—–“”‘’…"          # dấu câu ASCII + dấu tiếng Việt/Word


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("/", " ")        # chữ thường; "lần/5" → "lần 5"
    tokens = text.strip()
    tokens = [t.strip(PUNCT) for t in tokens]
    return [t for t in tokens if t]
