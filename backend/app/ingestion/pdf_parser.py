from pathlib import Path
import pymupdf


def extract_pdf_pages(pdf_path: Path) -> list[dict]:
    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text()

        # Clean repeated spaces/newlines
        text = " ".join(text.split())

        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    document.close()

    return pages