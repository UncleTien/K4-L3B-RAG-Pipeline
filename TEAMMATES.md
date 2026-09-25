# TEAMMATES

## 1. Thông tin thành viên

| Thành viên | Họ và tên | Mã học viên | Vai trò | Nhánh Git |
|---|---|---|---|---|
| Member 1 | Nguyễn Lê Phước Tiến | 2A202602616 | Data Collection, Normalization, Chunking & Indexing | `PhuocTien` |
| Member 2 | Đinh Kim Thái | 2A202602417 | Retrieval, BM25, RRF & Fallback | `thaidinh` |
| Member 3 | Nguyễn Đình An | 2A202602573 | Generation, Citation, UI & Evaluation | `02573-task10-ui-evaluation` |

> **Lưu ý:** Cập nhật họ tên đầy đủ và mã học viên chính xác của Thái và An trước khi nộp bài.

---

## 2. Phân công công việc

### Member 1 — Nguyễn Lê Phước Tiến

**Nhánh:** `PhuocTien`

**Phụ trách:** Thu thập dữ liệu, chuẩn hóa tài liệu, chia chunk và lập chỉ mục.

#### Công việc chính

- Thu thập tối thiểu:
  - 3 tài liệu pháp luật/PDF hoặc DOCX.
  - 5 bài viết hoặc trang thông tin liên quan đến pháp luật cho hộ kinh doanh.
- Lưu dữ liệu vào đúng thư mục:
  - `data/landing/legal/`
  - `data/landing/news/`
- Chuẩn hóa dữ liệu sang Markdown.
- Đảm bảo dữ liệu có metadata:
  - `source`
  - `title`
  - `doc_type`
  - `url`
  - `chunk_index`
- Triển khai hoặc hoàn thiện:
  - Document loading.
  - Markdown normalization.
  - Chunking.
  - Embedding.
  - ChromaDB/vector indexing.
- Đảm bảo mỗi chunk có:
  - `id` duy nhất và ổn định.
  - `content` không rỗng.
  - Metadata đầy đủ.
  - `chunk_index` hợp lệ.
- Kiểm tra việc re-index không tạo dữ liệu trùng lặp.

#### Bàn giao

- Bộ tài liệu đầu vào đã được chuẩn hóa.
- Các chunk có schema đúng theo `docs/MODULE_CONTRACTS.md`.
- Vector store đã được tạo và có thể sử dụng cho semantic search.
- Hướng dẫn chạy pipeline ingestion/indexing.
- Commit rõ ràng trên nhánh `PhuocTien`.

---

### Member 2 — Thái

**Nhánh:** `thaidinh`

**Phụ trách:** Retrieval, BM25, RRF, PageIndex và fallback.

#### Công việc chính

- Triển khai hoặc hoàn thiện semantic/dense search.
- Triển khai BM25/lexical search trên cùng tập chunk.
- Đảm bảo dense search và BM25 trả về cùng schema `SearchResult`.
- Triển khai Reciprocal Rank Fusion (RRF):
  - Kết hợp kết quả dense và BM25.
  - Fuse đúng một lần.
  - Sử dụng công thức RRF theo tài liệu module contract.
  - Không tạo kết quả trùng `id`.
- Tích hợp PageIndex search nếu có.
- Xây dựng retrieval pipeline.
- Triển khai fallback khi kết quả truy hồi không đủ tin cậy.
- Sử dụng điểm cosine gốc của dense search khi kiểm tra threshold fallback.
- Calibrate threshold bằng:
  - Câu hỏi trong miền dữ liệu.
  - Câu hỏi ngoài miền dữ liệu.
- Đảm bảo kết quả:
  - Không trùng ID.
  - Không vượt quá `top_k`.
  - Được sắp xếp theo score giảm dần.

#### Bàn giao

- Dense search hoạt động.
- BM25 hoạt động.
- RRF hoạt động đúng.
- Fallback được kiểm thử với câu hỏi in-domain và out-of-domain.
- Có test cho retrieval pipeline.
- Commit rõ ràng trên nhánh `thaidinh`.

---

### Member 3 — An

**Nhánh:** `02573-task10-ui-evaluation`

**Phụ trách:** Generation, citation, Streamlit UI và evaluation.

#### Công việc chính

- Triển khai generation pipeline.
- Reorder context trước khi gửi cho LLM nhưng không làm mất `id` và metadata.
- Format context có:
  - Nội dung chunk.
  - Tiêu đề tài liệu.
  - Nguồn hoặc URL.
- Tạo câu trả lời có citation.
- Đảm bảo citation ánh xạ được đến danh sách `sources`.
- Triển khai safe refusal khi không đủ bằng chứng.
- Xử lý lỗi provider/API để UI không bị crash.
- Hoàn thiện Streamlit chatbot:
  - Hiển thị câu trả lời.
  - Hiển thị nguồn được sử dụng.
  - Hiển thị retrieval method và score khi phù hợp.
- Tạo golden dataset tối thiểu 15 câu hỏi và câu trả lời tham chiếu.
- Đánh giá tối thiểu 4 metrics:
  - Faithfulness.
  - Answer relevance.
  - Context recall.
  - Context precision.
- So sánh:
  - Dense-only.
  - Hybrid + RRF.
- Phân tích lỗi và cập nhật:
  - `group_project/evaluation/RESULT.md`

#### Bàn giao

- Generation có citation.
- Safe refusal hoạt động.
- Streamlit UI chạy được end-to-end.
- Golden dataset có tối thiểu 15 câu hỏi.
- Báo cáo evaluation có 4 metrics và A/B comparison.
- Commit rõ ràng trên nhánh `02573-task10-ui-evaluation`.

---

## 3. Công việc chung của cả nhóm

Các thành viên cùng phối hợp thực hiện:

- Review code của nhau trước khi merge.
- Chạy test trước khi push:
  ```bash
  pytest tests/test_contracts.py -q
  pytest tests/test_acceptance.py -q
  pytest -q
  ```
- Kiểm tra pipeline end-to-end:
  ```text
  Documents
      ↓
  Markdown normalization
      ↓
  Chunking
      ↓
  Embedding + Vector DB
      ↓
  Dense search + BM25
      ↓
  RRF
      ↓
  Fallback
      ↓
  Context formatting
      ↓
  LLM generation
      ↓
  Citation + Streamlit UI
  ```
- Cùng xây dựng và kiểm tra golden dataset.
- Kiểm tra hai trường hợp demo:
  1. Câu hỏi nằm trong phạm vi dữ liệu.
  2. Câu hỏi ngoài phạm vi dữ liệu.
- Không commit API key hoặc thông tin bí mật.
- Cập nhật README và hướng dẫn chạy dự án.
- Mỗi thành viên ghi lại commit và phần đóng góp để hoàn thành individual report.

---

## 5. Checklist hoàn thành dự án

### Dữ liệu

- [x] Có ít nhất 3 tài liệu pháp luật.
- [x] Có ít nhất 5 bài viết/trang thông tin.
- [x] Dữ liệu được chuẩn hóa về Markdown.
- [x] Metadata đầy đủ và nhất quán.

### Indexing và Retrieval

- [x] Chunking hoạt động.
- [x] Embedding hoạt động.
- [x] ChromaDB/vector store hoạt động.
- [x] Dense search hoạt động.
- [x] BM25 hoạt động.
- [x] RRF hoạt động.
- [x] Fallback hoạt động.
- [x] Threshold được kiểm tra trên in-domain và out-of-domain queries.

### Generation và UI

- [x] Generation pipeline hoạt động.
- [x] Context được format rõ ràng.
- [x] Citation trỏ đúng về nguồn.
- [x] Safe refusal hoạt động.
- [x] Streamlit chatbot chạy được.
- [x] UI hiển thị nguồn được sử dụng.

### Evaluation và tài liệu

- [x] Có ít nhất 15 golden questions.
- [x] Đánh giá 4 metrics.
- [x] Có so sánh dense-only và hybrid + RRF.
- [x] Có error analysis.
- [x] Đã cập nhật `RESULT.md`.
- [x] Đã cập nhật README.
- [x] Mỗi thành viên hoàn thành individual report.
