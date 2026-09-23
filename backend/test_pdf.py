import fitz
from pathlib import Path


pdf_path = Path("data/documents/sample.pdf")

document = fitz.open(pdf_path)

print(f"Document: {pdf_path.name}")
print(f"Pages: {len(document)}")
print("-" * 50)

for page_number, page in enumerate(document, start=1):
    text = page.get_text()

    print(f"\nPAGE {page_number}")
    print("-" * 50)
    print(text[:1000])