from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

DOCS_DIR = "data/docs"
SKIP_SECTIONS = ("Tham khảo", "Lịch sử thay đổi")

@dataclass
class Document:
    "A full document to be indexed and searched."
    content: str
    doc_id: str = ""
    title: str = ""
    source: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = field(default_factory=dict)

@dataclass 
class DocumentChunk: 
    "A chunk of a document after splitting"
    content: str 
    chunk_id: str = ""
    doc_id: str = ""
    chunk_index: int = 0 
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None

def chunk_fixed (doc:Document, chunk_size: int = 512, overlap: int = 64) -> list[DocumentChunk]:
    if chunk_size <= 0 : 
        raise ValueError ("chunk_size phải lớn hơn 0")
    if overlap < 0 or overlap >= chunk_size : 
        raise ValueError ("Overlap phải >= 0 và nhỏ hơn chunk_size")

    chunks = []
    text = doc.content
    text_length = len (text)
    if text_length == 0 : 
        return chunks 

    start = 0
    chunk_index = 0 
    step = chunk_size - overlap

    while start < text_length : 
        end = min (start + chunk_size, text_length)
        chunk_content = text[start:end]

        if chunk_content.strip():
            chunks.append (
                DocumentChunk (
                    content = chunk_content, 
                    chunk_id = f"{doc.doc_id}_chunk_{chunk_index}", 
                    doc_id = doc.doc_id,
                    chunk_index = chunk_index, 
                    metadata = dict(doc.metadata),
                )
            )
            chunk_index += 1
        if end == text_length:
            break
        start += step
    return chunks

# ===== VIẾT MỚI =====
def parse_front_matter(text: str) -> tuple[dict, str]:

    parts = text.split("---", 2) # thành 3 phần, [ '', 'metadata...', 'thân bài...' ] tương ứng part 0-1-2
    meta = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, _ , value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, parts[2]
        




def load_document(path: str | Path) -> Document:

    pass


def split_sections(body: str) -> list[tuple[str, str]]:

    pass


def chunk_by_section(doc: Document) -> list[DocumentChunk]:

    pass


def chunk_all(docs_dir: str = DOCS_DIR) -> list[DocumentChunk]:
   
    pass


if __name__ == "__main__":
    chunks = chunk_all()
 