"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().

Embedding providers (đặt trong .env):
    EMBEDDING_PROVIDER=sentence_transformers   # local, BAAI/bge-m3 (dim=1024)
    EMBEDDING_PROVIDER=chroma_default          # local ONNX all-MiniLM-L6-v2 (dim=384)
    EMBEDDING_PROVIDER=openai                  # cần OPENAI_API_KEY
    EMBEDDING_PROVIDER=gemini                  # cần GEMINI_API_KEY
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


# ---------------------------------------------------------------------------
# Embedding — dispatch theo EMBEDDING_PROVIDER
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_st_model():
    """Load SentenceTransformer model một lần duy nhất (cached)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _get_chroma_default_ef():
    """Load ChromaDB DefaultEmbeddingFunction (ONNX all-MiniLM-L6-v2, dim=384)."""
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed danh sách văn bản, dispatch theo EMBEDDING_PROVIDER trong .env.

    Providers hỗ trợ:
        - sentence_transformers (default): BAAI/bge-m3, local, dim=1024
        - chroma_default: ONNX all-MiniLM-L6-v2, local, dim=384 (không cần torch)
        - openai: text-embedding-3-small hoặc EMBEDDING_MODEL trong .env
        - gemini: models/text-embedding-004
    """
    provider = EMBEDDING_PROVIDER.lower()

    if provider == "sentence_transformers":
        model = _get_st_model()
        return model.encode(texts, show_progress_bar=False).tolist()

    if provider == "chroma_default":
        ef = _get_chroma_default_ef()
        return [list(v) for v in ef(texts)]

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model_name = EMBEDDING_MODEL or "text-embedding-3-small"
        response = client.embeddings.create(input=texts, model=model_name)
        return [item.embedding for item in response.data]

    if provider == "gemini":
        from google import genai as google_genai
        client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        model_name = EMBEDDING_MODEL or "models/text-embedding-004"
        result = client.models.embed_content(
            model=model_name,
            contents=texts,
        )
        return [e.values for e in result.embeddings]

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER='{provider}'. "
        "Use: sentence_transformers | chroma_default | openai | gemini"
    )


# ---------------------------------------------------------------------------
# ChromaDB collection
# ---------------------------------------------------------------------------

def get_collection():
    """Mở hoặc tạo Chroma persistent collection với cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_documents() -> list[dict]:
    """Đọc tất cả .md trong data/standardized/ và trả về list[Document].

    ID là relative path từ STANDARDIZED_DIR, e.g. "legal/filename.md".
    doc_type được suy ra từ tên thư mục cha (legal | news).
    url được lấy từ dòng **Source:** trong file news; None cho legal.
    """
    documents: list[dict] = []

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if path.stat().st_size == 0:
            continue

        rel = path.relative_to(STANDARDIZED_DIR)
        parts = rel.parts  # ("legal", "filename.md") hoặc ("news", "article.md")
        doc_type = parts[0] if len(parts) > 1 and parts[0] in {"legal", "news"} else "legal"

        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        # Trích url từ dòng **Source:** (chỉ có ở news files)
        url: str | None = None
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("**Source:**"):
                url = stripped.replace("**Source:**", "").strip()
                break

        documents.append({
            "id": rel.as_posix(),
            "content": content,
            "metadata": {
                "source": path.name,
                "title": path.stem,
                "doc_type": doc_type,
                "url": url,
            },
        })

    return documents


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia mỗi Document thành các Chunk bằng RecursiveCharacterTextSplitter.

    - id format: "{doc_id}::chunk-{index}" — ổn định, duy nhất
    - metadata kế thừa từ document gốc + thêm chunk_index
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []
    for document in documents:
        texts = splitter.split_text(document["content"])
        for index, text in enumerate(texts):
            text = text.strip()
            if not text:
                continue
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": index,
                },
            })

    return chunks


# ---------------------------------------------------------------------------
# Embedding chunks
# ---------------------------------------------------------------------------

def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm trường embedding vào từng chunk (batch để tiết kiệm bộ nhớ)."""
    BATCH_SIZE = 64
    result = [dict(chunk) for chunk in chunks]  # copy tránh mutate gốc

    for start in range(0, len(result), BATCH_SIZE):
        batch = result[start : start + BATCH_SIZE]
        vectors = embed_texts([c["content"] for c in batch])
        for chunk, vector in zip(batch, vectors):
            chunk["embedding"] = vector

    return result


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert tất cả chunks vào ChromaDB (idempotent nhờ upsert theo id).

    Batch theo BATCH_SIZE để tránh OOM với corpus lớn.
    """
    BATCH_SIZE = 256
    collection = get_collection()

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )

    print(f"Upserted {len(chunks)} chunks into collection '{COLLECTION_NAME}'.")


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("Loading documents...")
    documents = load_documents()
    print(f"  Loaded {len(documents)} documents.")

    print("Chunking documents...")
    chunks = chunk_documents(documents)
    print(f"  Created {len(chunks)} chunks.")

    print(f"Embedding chunks (provider={EMBEDDING_PROVIDER}, model={EMBEDDING_MODEL})...")
    embedded_chunks = embed_chunks(chunks)
    print(f"  Embedded {len(embedded_chunks)} chunks.")

    print("Indexing to ChromaDB...")
    index_to_vectorstore(embedded_chunks)
    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
