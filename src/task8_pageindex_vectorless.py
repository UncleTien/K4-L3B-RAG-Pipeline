"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


import json


CACHE_FILE = Path(__file__).parent.parent / "data" / "pageindex_cache.json"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        print("PAGEINDEX_API_KEY not set. Skipping upload.")
        return

    try:
        from pageindex import PageIndexClient
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    except Exception as e:
        print(f"Cannot initialize PageIndexClient: {e}")
        return

    mapping: dict[str, str] = {}
    if CACHE_FILE.exists():
        try:
            mapping = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            mapping = {}

    for path in STANDARDIZED_DIR.rglob("*.md"):
        source_key = path.name
        if source_key in mapping:
            continue
        try:
            doc = client.submit_document(file_path=str(path))
            doc_id = doc.get("document_id") or doc.get("id") or str(doc)
            mapping[source_key] = doc_id
            print(f"Uploaded {path.name} -> {doc_id}")
        except Exception as e:
            print(f"Failed to upload {path.name}: {e}")

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Cached {len(mapping)} documents for PageIndex.")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0 or not query.strip() or not PAGEINDEX_API_KEY:
        return []

    try:
        from pageindex import PageIndexClient
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)

        response = client.submit_query(query=query)
        raw_items = []
        if isinstance(response, dict):
            raw_items = response.get("results") or response.get("nodes") or []
        elif isinstance(response, list):
            raw_items = response

        results: list[dict] = []
        for rank, item in enumerate(raw_items[:top_k], 1):
            if isinstance(item, dict):
                item_id = str(item.get("id") or f"pageindex-chunk-{rank}")
                content = item.get("text") or item.get("content") or ""
                score = float(item.get("score", 1.0 / rank))
                metadata = item.get("metadata") or {
                    "source": "pageindex",
                    "title": "PageIndex Result",
                    "doc_type": "legal",
                    "url": None,
                    "chunk_index": rank,
                }
            else:
                item_id = f"pageindex-chunk-{rank}"
                content = str(item)
                score = 1.0 / rank
                metadata = {
                    "source": "pageindex",
                    "title": "PageIndex Result",
                    "doc_type": "legal",
                    "url": None,
                    "chunk_index": rank,
                }

            if "chunk_index" not in metadata:
                metadata["chunk_index"] = rank
            if "source" not in metadata:
                metadata["source"] = "pageindex"
            if "title" not in metadata:
                metadata["title"] = "PageIndex Result"
            if "doc_type" not in metadata:
                metadata["doc_type"] = "legal"
            if "url" not in metadata:
                metadata["url"] = None

            results.append({
                "id": item_id,
                "content": content,
                "score": score,
                "metadata": metadata,
                "retrieval_method": "pageindex",
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    except Exception as e:
        print(f"PageIndex error: {e}")
        return []


if __name__ == "__main__":
    upload_documents()
