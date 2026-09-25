"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium

-> Dùng Firecrawl or bất cứ công cụ nào bạn quen
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# 6 bài viết về thuế thương mại điện tử — đã crawl thủ công và lưu sẵn
# dưới dạng JSON trong data/landing/news/. Danh sách URL này dùng để
# crawl lại hoặc bổ sung nếu cần.
ARTICLE_URLS = [
    "https://thuvienphapluat.vn/phap-luat-doanh-nghiep/bai-viet/link-dang-ky-thue-ke-khai-nop-thue-tu-hoat-dong-thuong-mai-dien-tu-nam-2025-10686.html",
    "https://thuvienphapluat.vn/phap-luat-doanh-nghiep/bai-viet/tai-lieu-cong-bo-thong-tin-thuong-mai-dien-tu-doi-voi-ho-kinh-doanh-10687.html",
    "https://thuvienphapluat.vn/phap-luat-doanh-nghiep/bai-viet/ke-khai-thue-ho-kinh-doanh-san-thuong-mai-dien-tu-10688.html",
    "https://thuvienphapluat.vn/phap-luat-doanh-nghiep/bai-viet/dang-ky-ma-so-thue-thuong-mai-dien-tu-10689.html",
    "https://thuvienphapluat.vn/phap-luat-doanh-nghiep/bai-viet/hoa-don-dien-tu-ho-kinh-doanh-2026-10690.html",
    "https://thuvienphapluat.vn/phap-luat-doanh-nghiep/bai-viet/cong-van-4062-dang-ky-thue-hoa-don-10691.html",
]


async def crawl_article(url: str) -> dict:
    """Crawl một URL và trả về dict với url, title, date_crawled, content_markdown."""
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        title = result.metadata.get("title", "Unknown") if result.metadata else "Unknown"
        # Ưu tiên markdown đã được fit (loại boilerplate), fallback sang raw markdown
        content = (
            result.markdown_v2.fit_markdown
            if hasattr(result, "markdown_v2") and result.markdown_v2
            else result.markdown or ""
        )
        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().strftime("%Y-%m-%d"),
            "content_markdown": content,
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON.

    Nếu file JSON đã tồn tại (từ lần crawl trước), bỏ qua để tránh ghi đè
    dữ liệu đã được kiểm tra thủ công.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        output = DATA_DIR / f"article_{index:02d}.json"
        if output.exists():
            print(f"Skip (exists): {output.name}")
            continue
        try:
            article = await crawl_article(url)
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


def list_crawled_articles() -> None:
    """Liệt kê các bài đã crawl trong DATA_DIR."""
    articles = sorted(DATA_DIR.glob("*.json"))
    print(f"Tìm thấy {len(articles)} bài viết trong {DATA_DIR}:")
    for path in articles:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            print(f"  ✓ {path.name}  — {data.get('title', 'N/A')[:60]}")
        except Exception:
            print(f"  ✗ {path.name}  (lỗi đọc JSON)")


if __name__ == "__main__":
    list_crawled_articles()
    asyncio.run(crawl_all())
