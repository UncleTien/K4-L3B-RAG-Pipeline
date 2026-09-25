# Evaluation Result

**Status: NOT RUN — chưa chạy evaluation.**
TODO: Hoàn thiện corpus, golden dataset và retrieval trước khi đo.
Không có số liệu, xếp hạng cấu hình hay kết luận thực nghiệm ở giai đoạn này.

## Run Information

| Field | Value |
| --- | --- |
| Evaluation date / output artifact | CHƯA CHẠY |
| Framework | Ragas 0.4.3 theo pyproject.toml; chưa kiểm thử runtime |
| Evaluator model | CHƯA CHỌN |
| Generator model/provider | CHƯA XÁC NHẬN |
| Embedding model | Task 4: BAAI/bge-m3; chưa chạy evaluation |
| Corpus/index version | CHƯA CHỐT |
| Reviewed golden cases | 0 |
| top_k | Chưa chốt; runner mặc định 5 |
| Fallback | Tắt cho cả hai nhánh A/B; đánh giá riêng sau |

## Overall Scores

| Metric | Dense-only | Hybrid + RRF | Delta B−A |
| --- | --- | --- | --- |
| Faithfulness | CHƯA CHẠY | CHƯA CHẠY | CHƯA ĐO |
| Answer relevance | CHƯA CHẠY | CHƯA CHẠY | CHƯA ĐO |
| Context recall | CHƯA CHẠY | CHƯA CHẠY | CHƯA ĐO |
| Context precision | CHƯA CHẠY | CHƯA CHẠY | CHƯA ĐO |

TODO: Ghi số case hợp lệ/undefined cho từng metric, số refusal và artifact thật.
Không thay ô chưa chạy bằng 0.

## A/B Comparison

A: Dense-only. B: Hybrid + RRF.
Giữ nguyên golden dataset, corpus/index, generator, evaluator, prompt và top_k.
TODO: Ghi kết quả thực tế và giải thích chênh lệch.
Chưa thể kết luận cấu hình nào tốt hơn. Chưa đo latency/cost.

## Worst Performers

| Rank | Question / case | Config | Four metric scores | Failure stage | Evidence / root cause |
| --- | --- | --- | --- | --- | --- |
| CHƯA XẾP HẠNG | CHƯA CHỌN | CHƯA CHẠY | CHƯA ĐO | CHƯA PHÂN TÍCH | CHƯA CÓ |

TODO: Phân tích ít nhất ba case dựa trên output thật và nguồn đã truy xuất.

## Recommendations

TODO: Đề xuất cải thiện dựa trên lỗi thực nghiệm sau khi chạy.
Chuẩn bị trước: chốt corpus, viết và kiểm tra golden cases, xác nhận interface A/B,
kiểm tra cấu hình model và môi trường. Đây là công việc chuẩn bị, không phải kết luận đo.