from pathlib import Path
from pypdf import PdfReader

PDF_DIR = Path("data/landing/legal")

for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
    reader = PdfReader(str(pdf_path))

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    print("=" * 80)
    print(f"File: {pdf_path.name}")
    print(f"Pages: {len(reader.pages)}")
    print(f"Characters: {len(text):,}")
    print(f"Has text: {bool(text.strip())}")
    print(f"Has Vietnamese text: {'CỘNG HÒA' in text or 'Điều' in text}")

    print("\nPreview:")
    print(text[:1000])