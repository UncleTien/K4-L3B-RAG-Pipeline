# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Đình Anh (theo tên file; cần chủ báo cáo xác nhận).
- Mã học viên: 02573.
- Nhóm: Chưa điền.
- Repository: K4-L3B-RAG-Pipeline.
- Branch: 02573-task10-ui-evaluation.

## Phần việc được giao và đã triển khai

Phần dưới được tổng hợp từ công việc thực hiện trong project với sự hỗ trợ của
trợ lý lập trình; thành viên cần review, hiểu và xác nhận trước khi nộp.

| Module/deliverable | Nội dung | Bằng chứng | Trạng thái |
| --- | --- | --- | --- |
| Task 10 | Reorder, context/citation theo ID, dispatch LLM, safe refusal | src/task10_generation.py | Đã implement, test offline |
| Streamlit UI | Query/top_k, answer/sources, lưu và render lịch sử | app.py | Đã kiểm tra UI |
| Tests | Mock retrieval/provider, citation, lỗi và lịch sử chat | tests/test_task10_generation.py; tests/test_app.py | 44 tests liên quan pass |
| Evaluation | Chuẩn bị runner Ragas, A/B và báo cáo skeleton | group_project/evaluation/ | Partial; chưa chạy metrics |

## Quyết định kỹ thuật

1. Citation dùng ID chunk ổn định, không đánh số theo thứ tự context sau reorder.
   Sources giữ thứ tự retrieval và metadata gốc để đối chiếu.
2. Task 10 gọi public retrieve() của Task 9; không viết lại retrieval.
   Evaluation A/B dùng chung generator và tắt PageIndex để so sánh hai cách xếp hạng.

## Kiểm thử và kết quả

- 44 tests Task 10/UI và contract liên quan pass bằng Python toàn máy.
- Streamlit đã khởi động, health endpoint trả ok; đã dừng server thử.
- Retrieval chưa implement trong workspace; CLI Task 10 trả safe refusal.
- Không có kết quả metric hoặc end-to-end với API thật.
- Golden dataset đang là []; hai acceptance tests evaluation chưa đạt.

## Hạn chế và công việc tiếp theo

- Chờ corpus standardized và retrieval hoàn thiện; chốt dependency/model/API.
- Cần xây ít nhất 15 golden cases có evidence thật, chạy A/B và cập nhật RESULT.md.
- Citation hợp lệ về ID không tự chứng minh mọi khẳng định đều được evidence hỗ trợ.

## Xác nhận đóng góp

Chưa ký xác nhận. Thành viên cần kiểm tra nội dung, bổ sung nhóm/ngày và xác nhận
sau khi review code và có thể giải thích hoặc chạy lại trong buổi demo.