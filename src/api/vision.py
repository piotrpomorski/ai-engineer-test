"""Vision request builder for multi-image Claude API calls.

This module provides utilities for constructing vision API requests
with proper content array structure and payload size validation.
"""

from typing import Any

from src.api.prompts import PAGE_LABEL_TEMPLATE, CLAUSE_EXTRACTION_PROMPT


# Maximum payload size for Claude API requests (32 MB)
MAX_PAYLOAD_SIZE_MB = 32
MAX_PAYLOAD_SIZE_BYTES = MAX_PAYLOAD_SIZE_MB * 1024 * 1024


def build_vision_request(pdf_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build multi-image content array with page labels for Claude Vision API.

    Creates a content array with alternating text labels and images,
    following the recommended pattern of placing images before the final prompt.

    Args:
        pdf_pages: List of page dictionaries from PDFConverter.convert()
            Each dict must contain:
            - page_number: int - The page number in the document
            - image_base64: str - Base64-encoded PNG image data

    Returns:
        Content array ready for Claude API messages parameter:
        [
            {"type": "text", "text": "Page 6:"},
            {"type": "image", "source": {...}},
            {"type": "text", "text": "Page 7:"},
            {"type": "image", "source": {...}},
            ...
            {"type": "text", "text": "<extraction prompt>"}
        ]

    Raises:
        ValueError: If pdf_pages is empty or missing required fields

    Example:
        >>> pages = [{"page_number": 6, "image_base64": "..."}]
        >>> content = build_vision_request(pages)
        >>> len(content)
        3  # label + image + prompt
    """
    if not pdf_pages:
        raise ValueError("pdf_pages cannot be empty")

    content: list[dict[str, Any]] = []

    # Add each page with explicit label followed by image
    for page in pdf_pages:
        # Validate required fields
        if "page_number" not in page:
            raise ValueError("Each page must have 'page_number' field")
        if "image_base64" not in page:
            raise ValueError("Each page must have 'image_base64' field")

        # Add text label for page context
        content.append({
            "type": "text",
            "text": PAGE_LABEL_TEMPLATE.format(page_number=page["page_number"])
        })

        # Add image with base64 source
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": page["image_base64"]
            }
        })

    # Add final extraction prompt at the end
    content.append({
        "type": "text",
        "text": CLAUSE_EXTRACTION_PROMPT
    })

    return content


def calculate_payload_size(pdf_pages: list[dict[str, Any]]) -> int:
    """Calculate the total payload size of all images.

    Args:
        pdf_pages: List of page dictionaries from PDFConverter.convert()
            If 'size_kb' field is present, uses it directly.
            Otherwise, estimates from base64 string length.

    Returns:
        Total payload size in bytes

    Example:
        >>> pages = [{"page_number": 6, "image_base64": "...", "size_kb": 378.5}]
        >>> size = calculate_payload_size(pages)
        >>> print(f"{size / 1024 / 1024:.2f} MB")
    """
    total_bytes = 0

    for page in pdf_pages:
        if "size_kb" in page:
            # Use provided size if available
            total_bytes += int(page["size_kb"] * 1024)
        elif "image_base64" in page:
            # Estimate from base64 length (base64 is ~4/3 of original size)
            base64_len = len(page["image_base64"])
            original_bytes = int(base64_len * 3 / 4)
            total_bytes += original_bytes

    return total_bytes


def validate_payload_size(pdf_pages: list[dict[str, Any]]) -> None:
    """Validate that total payload is under the 32 MB API limit.

    Args:
        pdf_pages: List of page dictionaries from PDFConverter.convert()

    Raises:
        ValueError: If total payload exceeds 32 MB limit

    Example:
        >>> pages = converter.convert("document.pdf")
        >>> validate_payload_size(pages)  # Raises if > 32 MB
    """
    total_bytes = calculate_payload_size(pdf_pages)
    total_mb = total_bytes / 1024 / 1024

    if total_bytes > MAX_PAYLOAD_SIZE_BYTES:
        raise ValueError(
            f"Total payload size ({total_mb:.2f} MB) exceeds "
            f"API limit of {MAX_PAYLOAD_SIZE_MB} MB. "
            f"Consider reducing image resolution or batching pages."
        )
