import base64
import logging
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

MAX_PDF_SIZE_MB = 32
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024


class PDFExtractionError(Exception):
    pass


class PDFHandler:
    def __init__(self) -> None:
        self.pdf_data: dict[str, Any] = {}

    def extract_pages(
        self, pdf_path: str, first_page: int = 6, last_page: int = 39
    ) -> dict[str, Any]:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(
                f"PDF file not found: {pdf_path}. "
                f"Please verify the file path and ensure the file exists."
            )

        logger.info(f"Extracting pages {first_page}-{last_page} from PDF: {pdf_path}")

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            logger.debug(f"PDF has {total_pages} total pages")

            if last_page > total_pages:
                raise PDFExtractionError(
                    f"Requested last page {last_page} exceeds total pages {total_pages}"
                )

            writer = PdfWriter()
            for page_num in range(first_page - 1, last_page):
                writer.add_page(reader.pages[page_num])

            from io import BytesIO

            pdf_buffer = BytesIO()
            writer.write(pdf_buffer)
            pdf_bytes = pdf_buffer.getvalue()
            size_kb = len(pdf_bytes) / 1024
            size_mb = size_kb / 1024

            if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
                raise PDFExtractionError(
                    f"Extracted PDF size ({size_mb:.2f} MB) exceeds "
                    f"API limit of {MAX_PDF_SIZE_MB} MB"
                )

            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            base64_kb = len(pdf_base64) / 1024

            logger.info(
                f"Extracted {last_page - first_page + 1} pages: "
                f"{size_kb:.1f} KB raw, {base64_kb:.1f} KB base64"
            )

            self.pdf_data = {
                "pdf_base64": pdf_base64,
                "page_range": (first_page, last_page),
                "size_kb": size_kb,
                "total_pages": last_page - first_page + 1,
            }

            return self.pdf_data

        except Exception as e:
            if isinstance(e, (FileNotFoundError, PDFExtractionError)):
                raise
            raise PDFExtractionError(f"Failed to extract pages from PDF: {e}") from e


def main(pdf_path: str, first_page: int = 6, last_page: int = 39) -> None:
    handler = PDFHandler()
    pdf_data = handler.extract_pages(pdf_path, first_page, last_page)

    print(f"\nExtracted {pdf_data['total_pages']} pages from PDF")
    print(f"Page range: {pdf_data['page_range'][0]}-{pdf_data['page_range'][1]}")
    print(f"Size: {pdf_data['size_kb']:.2f} KB")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.pdf_handler <pdf_path> [first_page] [last_page]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    first_page = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    last_page = int(sys.argv[3]) if len(sys.argv) > 3 else 39

    try:
        main(pdf_path, first_page, last_page)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except PDFExtractionError as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
