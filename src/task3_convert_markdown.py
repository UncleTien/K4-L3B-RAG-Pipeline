"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.

-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOCX trong landing/legal/ sang Markdown trong standardized/legal/.

    - Dùng MarkItDown để extract text từ PDF.
    - Bỏ qua file đã tồn tại (idempotent).
    - Bỏ qua file rỗng sau khi convert (tránh ghi file không dùng được).
    """
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    converted, skipped, failed = 0, 0, 0

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue

        out_path = output_dir / f"{path.stem}.md"
        if out_path.exists():
            print(f"  Skip (exists): {out_path.name}")
            skipped += 1
            continue

        try:
            result = converter.convert(str(path))
            text = result.text_content.strip()
            if not text:
                print(f"  ✗ Empty output: {path.name} — bỏ qua")
                failed += 1
                continue
            out_path.write_text(text, encoding="utf-8")
            print(f"  ✓ {path.name}  →  {out_path.name}  ({len(text):,} chars)")
            converted += 1
        except Exception as error:
            print(f"  ✗ Error: {path.name} — {error}")
            failed += 1

    print(f"\nlegal: {converted} converted, {skipped} skipped, {failed} failed.")


def convert_news_articles() -> None:
    """Convert JSON trong landing/news/ sang Markdown trong standardized/news/.

    Mỗi file .md bắt đầu bằng header metadata (title, source URL, date),
    sau đó là content_markdown từ JSON. Bỏ qua file đã tồn tại.
    """
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted, skipped, failed = 0, 0, 0

    for path in sorted(news_dir.glob("*.json")):
        out_path = output_dir / f"{path.stem}.md"
        if out_path.exists():
            print(f"  Skip (exists): {out_path.name}")
            skipped += 1
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            title = data.get("title", path.stem)
            url = data.get("url", "")
            date_crawled = data.get("date_crawled", "")
            content = data.get("content_markdown", "").strip()

            if not content:
                print(f"  ✗ Empty content_markdown: {path.name} — bỏ qua")
                failed += 1
                continue

            header = (
                f"# {title}\n\n"
                f"**Source:** {url}\n\n"
                f"**Crawled:** {date_crawled}\n\n"
                f"---\n\n"
            )
            out_path.write_text(header + content, encoding="utf-8")
            print(f"  ✓ {path.name}  →  {out_path.name}  ({len(content):,} chars)")
            converted += 1
        except Exception as error:
            print(f"  ✗ Error: {path.name} — {error}")
            failed += 1

    print(f"\nnews: {converted} converted, {skipped} skipped, {failed} failed.")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Converting legal docs (PDF → Markdown) ===")
    convert_legal_docs()
    print("\n=== Converting news articles (JSON → Markdown) ===")
    convert_news_articles()
    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
