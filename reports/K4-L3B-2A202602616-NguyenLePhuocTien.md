# Individual contribution report

---

## Thông tin

- Họ và tên: Nguyễn Lê Phước Tiến
- Mã học viên: 2A202602616
- Nhóm: 3N
- Repository/branch: https://github.com/UncleTien/K4-L3B-RAG-Pipeline/tree/PhuocTien

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — Thu thập tài liệu pháp lý | Tải thủ công 4 văn bản pháp luật về thuế TMĐT (TT 20/2015, Luật 41/QH15, VBHN 506, NĐ 254/2026); implement `download_documents()` để verify sự hiện diện của các file | `src/task1_collect_legal_docs.py` | Done |
| Task 2 — Crawl bài viết | Điền 6 URL bài viết thuế TMĐT vào `ARTICLE_URLS`; implement `crawl_article()` với Crawl4AI (`AsyncWebCrawler`), ưu tiên `fit_markdown`; `crawl_all()` skip file đã tồn tại | `src/task2_crawl_news.py` | Done |
| Task 3 — Chuẩn hóa Markdown | Implement `convert_legal_docs()` dùng MarkItDown (PDF → MD); implement `convert_news_articles()` (JSON → MD với header metadata); cả hai idempotent; chạy thành công 4 legal + 6 news | `src/task3_convert_markdown.py` | Done |
| Task 4 — Chunking, embedding, indexing | Implement đầy đủ 6 hàm: `load_documents()`, `chunk_documents()`, `embed_texts()` (dispatch 4 provider), `embed_chunks()`, `get_collection()`, `index_to_vectorstore()`; pipeline tạo 1 603 chunks từ 10 documents | `src/task4_chunking_indexing.py` | Done |
| Contract validation | Chạy `pytest tests/test_contracts.py`; 8/15 tests pass (7 còn lại là task 5–10 chưa implement) | `tests/test_contracts.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định: Thiết kế `embed_texts()` với dispatch 4 provider qua biến môi trường**  
   **Lý do/evidence:** Contract yêu cầu task 4 và task 5 dùng chung một hàm embedding duy nhất. Dùng `EMBEDDING_PROVIDER` trong `.env` để tách biệt provider khỏi code, tránh hard-code. Model được cache bằng `@lru_cache(maxsize=1)` để không load lại mỗi lần gọi.  
   **Trade-off:** Provider `sentence_transformers` với `BAAI/bge-m3` (dim=1024) cho chất lượng embedding tốt nhất nhưng cần cài `torch` (~2GB). Fallback `chroma_default` (ONNX all-MiniLM-L6-v2, dim=384) không cần torch nhưng chất lượng thấp hơn và cần download qua mạng.

2. **Quyết định: Chunk ID ổn định dạng `"{doc_id}::chunk-{index}"`**  
   **Lý do/evidence:** ChromaDB dùng `upsert` theo ID — nếu ID thay đổi mỗi lần chạy sẽ tạo duplicate. Dùng relative path từ `data/standardized/` làm `doc_id` (ví dụ `legal/02_2026_41_122_2025_QH15.md`) đảm bảo ID phản ánh nguồn gốc file, không phụ thuộc thứ tự hay timestamp.  
   **Trade-off:** Nếu đổi tên file trong `standardized/`, toàn bộ chunk ID của file đó sẽ thay đổi và ChromaDB sẽ có duplicate. Cần xóa collection và index lại khi rename file.

## Kiểm thử và kết quả

- **Test đã chạy:** `pytest tests/test_contracts.py -v`
- **Kết quả:**
  - `test_chunk_documents_preserves_identity_and_metadata` — PASSED: 1 603 chunks từ 10 docs, max length 498 ≤ 550 (110% × CHUNK_SIZE), mỗi chunk có đủ `id`, `content`, `metadata.chunk_index`.
  - `test_public_function_signatures_are_stable` — PASSED: đúng signature `load_documents()`, `chunk_documents(documents)`.
  - `test_document_validator_accepts_contract` — PASSED.
  - 8/15 tests pass; 7 fail do task 5–10 chưa implement.
- **Kết quả chạy thực tế task 3:** 4 legal MD (71K–318K chars) + 6 news MD (1K chars mỗi file), 0 lỗi.
- **Lỗi đã phát hiện:** `sentence_transformers` chưa được cài trong `.venv` (thiếu `torch`). Xử lý bằng cách thêm provider `chroma_default` làm fallback ONNX, không cần torch.

## Điều còn hạn chế

- **Hạn chế:** Embedding chưa thực sự chạy được end-to-end do `sentence_transformers`/`torch` chưa cài thành công (mạng chậm khi tải ~2GB). Provider `chroma_default` cũng cần download ONNX model (~80MB) qua mạng trước khi dùng được. ChromaDB hiện vẫn chưa có data.
- **Nếu có thêm thời gian:** Cài `sentence-transformers` và chạy `python -m src.task4_chunking_indexing` để index đủ 1 603 chunks với model BAAI/bge-m3 vào ChromaDB, sau đó implement và chạy kiểm thử end-to-end task 5–9.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Nguyễn Lê Phước Tiến
