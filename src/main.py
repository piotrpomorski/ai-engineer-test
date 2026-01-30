"""End-to-end pipeline for Charter Party document clause extraction.

This module provides the main execution pipeline that:
1. Validates environment (API key, dependencies)
2. Converts PDF pages to images
3. Sends images to Claude Vision API
4. Saves raw extraction response
5. Transforms raw response to final output format
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from src.api.client import ClaudeVisionClient, validate_environment
from src.models import transform_raw_to_output, validate_raw_response
from src.pdf_converter import ImageValidationError, PDFConversionError, PDFConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main(
    pdf_path: str,
    output_path: str = "raw_response.json",
    final_output_path: str = "output.json",
) -> dict[str, Any]:
    """Execute the complete clause extraction pipeline.

    Args:
        pdf_path: Path to the PDF file to process
        output_path: Path for raw JSON response (default: raw_response.json)
        final_output_path: Path for final JSON output (default: output.json)

    Returns:
        Dictionary containing extracted clauses

    Raises:
        FileNotFoundError: If PDF file doesn't exist (exit code 1)
        RuntimeError: If API call fails (exit code 2)
        ValueError: If raw response validation fails (exit code 1)
    """
    logger.info("=" * 60)
    logger.info("Charter Party Document Clause Extraction Pipeline")
    logger.info("=" * 60)

    # Step 1: Validate environment
    logger.info("Step 1: Validating environment...")
    validate_environment()
    logger.info("Environment validation passed")

    # Step 2: Convert PDF to images
    logger.info("Step 2: Converting PDF to images...")
    converter = PDFConverter()
    pdf_pages = converter.convert_pdf_to_images(pdf_path)

    # Log conversion summary
    total_pages = len(pdf_pages)
    total_size_mb = sum(p["size_kb"] for p in pdf_pages) / 1024
    logger.info(f"Converted {total_pages} pages, total size: {total_size_mb:.2f} MB")

    # Step 3: Extract clauses via Claude Vision API
    logger.info("Step 3: Sending images to Claude Vision API...")
    client = ClaudeVisionClient()
    result = client.extract_clauses(pdf_pages)

    # Log extraction summary
    clause_count = len(result.get("clauses", []))
    logger.info(f"Extracted {clause_count} clauses from document")

    # Step 4: Save raw response for Phase 3 processing
    logger.info(f"Step 4: Saving raw response to {output_path}...")
    output_file = Path(output_path)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"Raw response saved ({output_file.stat().st_size} bytes)")

    # Step 5: Transform raw response to final output format
    logger.info("Step 5: Transforming to final output format...")
    try:
        validate_raw_response(result)
        clauses = transform_raw_to_output(result)

        # Serialize to JSON
        output_data = [clause.model_dump() for clause in clauses]

        # Write to final output file
        final_output_file = Path(final_output_path)
        with open(final_output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        final_size_kb = final_output_file.stat().st_size / 1024
        logger.info(
            f"Final output saved to {final_output_path} "
            f"({len(clauses)} clauses, {final_size_kb:.2f} KB)"
        )

    except ValueError as e:
        logger.error(f"Raw response validation failed: {e}")
        raise

    # Final summary
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info(f"  - Pages processed: {total_pages}")
    logger.info(f"  - Clauses extracted: {clause_count}")
    logger.info(f"  - Raw output: {output_path}")
    logger.info(f"  - Final output: {final_output_path}")
    logger.info("=" * 60)

    return result


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Extract clauses from Charter Party PDFs using Claude Vision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main voyage-charter-example.pdf
  python -m src.main document.pdf --output clauses.json

Environment variables:
  ANTHROPIC_API_KEY  Your Anthropic API key (required)
        """,
    )

    parser.add_argument(
        "pdf_path",
        nargs="?",
        default="voyage-charter-example.pdf",
        help="Path to the PDF file to process (default: voyage-charter-example.pdf)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="raw_response.json",
        help="Output path for raw JSON response (default: raw_response.json)",
    )

    parser.add_argument(
        "--final-output",
        default="output.json",
        help="Output path for final transformed JSON (default: output.json)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        main(args.pdf_path, args.output, args.final_output)
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)

    except PDFConversionError as e:
        logger.error(f"PDF conversion failed: {e}")
        sys.exit(1)

    except ImageValidationError as e:
        logger.error(f"Image validation failed: {e}")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)

    except SystemExit:
        # Re-raise SystemExit (from validate_environment)
        raise

    except Exception as e:
        logger.error(f"API error: {e}")
        sys.exit(2)
