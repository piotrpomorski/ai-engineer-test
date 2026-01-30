"""Vision request builder for PDF document Claude API calls.

This module provides utilities for constructing PDF document API requests
with proper content structure and payload size validation.
"""

from typing import Any

from src.api.prompts import CLAUSE_EXTRACTION_PROMPT

MAX_PAYLOAD_SIZE_MB = 32
MAX_PAYLOAD_SIZE_BYTES = MAX_PAYLOAD_SIZE_MB * 1024 * 1024


def build_vision_request(pdf_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build PDF document content array for Claude API.

    Creates a content array with the PDF document followed by the extraction prompt.

    Args:
        pdf_data: Dictionary from PDFHandler.extract_pages()
            Must contain:
            - pdf_base64: str - Base64-encoded PDF data
            - page_range: tuple - (first_page, last_page)
            - size_kb: float - Size in kilobytes

    Returns:
        Content array ready for Claude API messages parameter:
        [
            {"type": "document", "source": {...}},
            {"type": "text", "text": "<extraction prompt>"}
        ]

    Raises:
        ValueError: If pdf_data is missing required fields

    Example:
        >>> pdf_data = {"pdf_base64": "...", "page_range": (6, 39), "size_kb": 450}
        >>> content = build_vision_request(pdf_data)
        >>> len(content)
        2  # document + prompt
    """
    if not pdf_data:
        raise ValueError("pdf_data cannot be empty")

    required_fields = {"pdf_base64", "page_range", "size_kb"}
    missing = required_fields - set(pdf_data.keys())
    if missing:
        raise ValueError(f"pdf_data missing required fields: {missing}")

    content: list[dict[str, Any]] = [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_data["pdf_base64"],
            },
        },
        {"type": "text", "text": CLAUSE_EXTRACTION_PROMPT},
    ]

    return content


def calculate_payload_size(pdf_data: dict[str, Any]) -> int:
    """Calculate the payload size of the PDF.

    Args:
        pdf_data: Dictionary from PDFHandler.extract_pages()
            Uses 'size_kb' field if present, otherwise estimates from base64 length.

    Returns:
        Payload size in bytes

    Example:
        >>> pdf_data = {"pdf_base64": "...", "size_kb": 450.2}
        >>> size = calculate_payload_size(pdf_data)
        >>> print(f"{size / 1024 / 1024:.2f} MB")
    """
    if "size_kb" in pdf_data:
        return int(pdf_data["size_kb"] * 1024)
    elif "pdf_base64" in pdf_data:
        base64_len = len(pdf_data["pdf_base64"])
        original_bytes = int(base64_len * 3 / 4)
        return original_bytes
    return 0


def validate_payload_size(pdf_data: dict[str, Any]) -> None:
    """Validate that PDF payload is under the 32 MB API limit.

    Args:
        pdf_data: Dictionary from PDFHandler.extract_pages()

    Raises:
        ValueError: If payload exceeds 32 MB limit

    Example:
        >>> pdf_data = handler.extract_pages("document.pdf")
        >>> validate_payload_size(pdf_data)
    """
    total_bytes = calculate_payload_size(pdf_data)
    total_mb = total_bytes / 1024 / 1024

    if total_bytes > MAX_PAYLOAD_SIZE_BYTES:
        raise ValueError(
            f"PDF payload size ({total_mb:.2f} MB) exceeds "
            f"API limit of {MAX_PAYLOAD_SIZE_MB} MB. "
            f"Consider reducing the page range or splitting the document."
        )
