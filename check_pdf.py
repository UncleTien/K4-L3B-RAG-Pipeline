from pathlib import Path
from pypdf import PdfReader

folder = Path("data/landing/legal")

for pdf_path in folder.glob("*.pdf"):
    print(f"\n===== {pdf_path.name} =====")

    try:
        reader = PdfReader(str(pdf_path))

        print(f"So trang: {len(reader.pages)}")

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        print(f"So ky tu text: {len(text.strip())}")
        print("Preview:")
        print(repr(text[:300]))

    except Exception as error:
        print(f"ERROR: {error}")