# Đọc playbook data/docs/*.md (front matter + thân bài) và cắt thành chunk theo mục "##".
# chunk_fixed() là cách cắt cố định 512 ký tự từ bài lab, chỉ để so sánh; project dùng chunk_by_section().
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "docs"   # đường dẫn tuyệt đối: chạy từ thư mục nào cũng đúng
SKIP_SECTIONS = ("Tham khảo", "Lịch sử thay đổi")

@dataclass
class Document:
    "A full document to be indexed and searched."
    content: str
    doc_id: str = ""
    title: str = ""
    source: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None

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

    # Tách phần metadata nằm giữa 2 dòng --- (doc_id, version, status...) khỏi thân bài
    parts = text.split("---", 2) # thành 3 phần, [ '', 'metadata...', 'thân bài...' ] tương ứng part 0-1-2
    meta = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, _ , value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, parts[2]
        

def load_document(path: str | Path) -> Document:
    # Đọc 1 file .md thành Document (doc_id, title lấy từ front matter)
    text = Path(path).read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    return Document (
        content= body,
        doc_id = meta["doc_id"],
        title= meta["title"],
        source= str(path),
        metadata= meta,
    )


    

# AI hỗ trợ viết hàm này
def split_sections(body: str) -> list[tuple[str, str]]: 
    """Cắt thân bài thành danh sách (tiêu đề mục, nội dung mục)."""
    sections = []
    heading = None 
    lines = []

    for line in body.splitlines(): 
        if line.startswith("## "):
            if heading is not None: 
                content = "\n".join(lines).strip()
                sections.append((heading,content))
            heading = line.strip()
            lines = []
        else:
            lines.append(line)

    if heading is not None: 
        content = "\n".join(lines).strip()
        sections.append((heading, content))

    return sections

# Lý do chunking theo mục "##" (không cắt cố định 512 ký tự như chunk_fixed):
# 1. Mỗi mục của playbook là 1 quy định trọn vẹn (ngưỡng, mức độ, cách xử lý); cắt giữa chừng sẽ tách con số khỏi ngữ cảnh của nó.
# 2. Mỗi chunk được gắn tiêu đề "[SEC-xx vX.Y — tên]" để LLM luôn thấy phiên bản và trích đúng nguồn, tránh nhầm SEC-01 cũ với SEC-02 mới.
# 3. Bỏ mục "Tham khảo" và "Lịch sử thay đổi" vì chỉ là nhiễu khi tìm kiếm.
# 4. Playbook ngắn nên 10 file chỉ ra 57 chunk, mỗi chunk vừa đủ để nhúng và đọc trong 1 lần.
def chunk_by_section(doc: Document) -> list[DocumentChunk]:
    chunks = []
    for heading, text in split_sections (doc.content) :
        if any(s in heading for s in SKIP_SECTIONS):
            continue

        header = f"[{doc.doc_id} v{doc.metadata['version']} — {doc.title}]"
        chunks.append(
            DocumentChunk(
                content= header + "\n" + heading + "\n" + text,
                chunk_id = f"{doc.doc_id}#{len(chunks)}"  ,
                doc_id = doc.doc_id,
                chunk_index= len(chunks),
                metadata={**doc.metadata, "section": heading},
            )
        )

    return chunks

def chunk_all(docs_dir: str | Path = DOCS_DIR) -> list[DocumentChunk]:
    # Chunk mọi file *.md trong thư mục, nên KHÔNG để file .md nào khác ngoài playbook vào data/docs/
    all_chunks = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        doc = load_document (path)
        chunks = chunk_by_section(doc)
        all_chunks.extend(chunks)

    return all_chunks

if __name__ == "__main__":
    chunks = chunk_all()
   