"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Các tài liệu pháp lý đã thu thập thủ công về thuế thương mại điện tử.
# Nguồn: Tổng cục Thuế Việt Nam và các cơ quan ban hành pháp luật.
LEGAL_DOCUMENTS = [
    {
        "filename": "01_20_2015_TTBKHĐT(12947).pdf",
        "description": "Thông tư 20/2015/TT-BKHĐT hướng dẫn đăng ký doanh nghiệp",
        "source": "Bộ Kế hoạch và Đầu tư",
    },
    {
        "filename": "02_2026_41_122_2025_QH15.pdf",
        "description": "Luật số 41/QH15 sửa đổi các luật thuế 2025",
        "source": "Quốc hội",
    },
    {
        "filename": "03_2026_506_VBHN_29_2026_VBHNNĐBTC.pdf",
        "description": "Văn bản hợp nhất 506/VBHN quản lý thuế thương mại điện tử",
        "source": "Bộ Tài chính",
    },
    {
        "filename": "04_2026_402_254_2026_NĐ-CP.pdf",
        "description": "Nghị định 254/2026/NĐ-CP quy định về hóa đơn điện tử",
        "source": "Chính phủ",
    },
]


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Kiểm tra và liệt kê tài liệu PDF đã thu thập thủ công.

    Các tài liệu pháp lý trong dự án này được tải thủ công từ nguồn công khai
    (Cổng thông tin điện tử của Chính phủ, Tổng cục Thuế) và đặt trực tiếp vào
    data/landing/legal/. Hàm này xác nhận sự hiện diện của các files.
    """
    setup_directory()
    found, missing = [], []

    for doc in LEGAL_DOCUMENTS:
        path = DATA_DIR / doc["filename"]
        if path.exists():
            found.append(doc)
            print(f"  ✓ {doc['filename']}  ({doc['description']})")
        else:
            missing.append(doc)
            print(f"  ✗ MISSING: {doc['filename']}")

    print(f"\nKết quả: {len(found)}/{len(LEGAL_DOCUMENTS)} tài liệu có sẵn.")
    if missing:
        print("Các file còn thiếu cần tải thủ công vào data/landing/legal/:")
        for doc in missing:
            print(f"  - {doc['filename']}  ({doc['source']})")


if __name__ == "__main__":
    download_documents()
