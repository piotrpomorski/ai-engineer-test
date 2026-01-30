"""PDF to image conversion module.

This module provides functionality to convert PDF pages to in-memory images
optimized for Claude Vision API processing.
"""

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import List

from pdf2image import convert_from_path
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Claude Vision API limits
MAX_IMAGE_DIMENSION = 8000  # pixels


class PDFConversionError(Exception):
    """Raised when PDF conversion fails."""
    pass


class ImageValidationError(Exception):
    """Raised when image dimensions exceed Claude's limits."""
    pass


class PDFConverter:
    """Converts PDF pages to in-memory images optimized for Claude Vision API.

    This converter:
    - Extracts pages 6-39 from a PDF document
    - Converts each page to a PIL Image at 150 DPI
    - Validates image dimensions against Claude's 8000x8000 pixel limit
    - Encodes images to base64 PNG format for API submission
    - Provides structured logging for each page conversion
    """

    def __init__(self):
        """Initialize the PDF converter."""
        self.images = []

    def convert_pdf_to_images(
        self,
        pdf_path: str,
        first_page: int = 6,
        last_page: int = 39,
        dpi: int = 150
    ) -> List[dict]:
        """Convert PDF pages to in-memory images.

        Args:
            pdf_path: Path to the PDF file
            first_page: First page to extract (1-based indexing)
            last_page: Last page to extract (1-based indexing)
            dpi: Resolution for image conversion (default: 150)

        Returns:
            List of dictionaries containing:
                - page_number: Page number (1-based)
                - image_base64: Base64-encoded PNG image
                - width: Image width in pixels
                - height: Image height in pixels
                - size_kb: Image size in kilobytes

        Raises:
            FileNotFoundError: If PDF file does not exist
            PDFConversionError: If conversion fails
            ImageValidationError: If image dimensions exceed limits
        """
        # Validate PDF file exists
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Converting PDF: {pdf_path}")
        logger.info(f"Extracting pages {first_page}-{last_page} at {dpi} DPI")

        try:
            # Convert PDF pages to PIL Images
            pil_images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
        except Exception as e:
            raise PDFConversionError(f"Failed to convert PDF: {e}")

        # Process each image
        self.images = []
        for idx, pil_image in enumerate(pil_images):
            page_number = first_page + idx

            # Validate dimensions
            width, height = pil_image.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ImageValidationError(
                    f"Page {page_number}: Image dimensions {width}x{height} "
                    f"exceed Claude's limit of {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}"
                )

            # Convert to PNG bytes
            img_buffer = BytesIO()
            pil_image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            size_kb = len(img_bytes) / 1024

            # Base64 encode
            image_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # Log conversion
            logger.info(f"Page {page_number}: {width}x{height} pixels, {size_kb:.1f} KB")

            # Store result
            self.images.append({
                'page_number': page_number,
                'image_base64': image_base64,
                'width': width,
                'height': height,
                'size_kb': size_kb
            })

        logger.info(f"Successfully converted {len(self.images)} pages")
        return self.images
