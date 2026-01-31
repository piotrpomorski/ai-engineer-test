"""End-to-end pipeline for Charter Party document clause extraction.

This module provides the main execution pipeline that:
1. Validates environment (API key, dependencies)
2. Sends PDF to Gemini API (with optional batching for large documents)
3. Saves raw extraction response
4. Transforms raw response to final output format
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from src.batch_processor import BatchConfig, BatchProcessor
from src.gemini_client import GeminiClient, validate_environment
from src.models import transform_raw_to_output, validate_raw_response
from src.prompts import CLAUSE_EXTRACTION_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main(
    pdf_path: str,
    output_path: str = "raw_response.json",
    final_output_path: str = "output.json",
    batch_config: BatchConfig | None = None,
) -> dict[str, Any]:
    """Execute the complete clause extraction pipeline.

    Args:
        pdf_path: Path to the PDF file to process
        output_path: Path for raw JSON response (default: raw_response.json)
        final_output_path: Path for final JSON output (default: output.json)
        batch_config: Optional batch configuration for large PDFs

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
    logger.info("Step 1/5: Validating environment...")
    validate_environment()
    logger.info("Environment validation passed")

    # Step 2: Validate PDF exists
    logger.info("Step 2/5: Validating PDF file...")
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    size_bytes = pdf_file.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    logger.info(f"PDF file size: {size_kb:.1f} KB ({size_mb:.2f} MB)")

    # Step 3: Extract clauses via Gemini API
    logger.info("Step 3/5: Sending PDF to Gemini API...")

    if batch_config is not None and batch_config.batch_size > 0:
        # Use batch processing for large PDFs
        logger.info(
            f"Using batch processing: batch_size={batch_config.batch_size}, "
            f"overlap={batch_config.overlap}, parallel={batch_config.parallel}"
        )
        processor = BatchProcessor(batch_config)
        result = processor.process(pdf_path)
    else:
        # Standard single-pass processing
        client = GeminiClient()
        result = client.extract_clauses(pdf_path, CLAUSE_EXTRACTION_PROMPT)

    # Log extraction summary
    clause_count = len(result.get("clauses", []))
    logger.info(f"Extracted {clause_count} clauses from PDF")

    # Step 4: Save raw response for Phase 3 processing
    logger.info(f"Step 4/5: Saving raw response to {output_path}...")
    output_file = Path(output_path)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    raw_size_kb = output_file.stat().st_size / 1024
    logger.info(f"Raw response saved ({raw_size_kb:.2f} KB)")

    # Step 5: Transform raw response to final output format
    logger.info("Step 5/5: Transforming to final output format...")
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

    # Final summary
    logger.info("=" * 60)
    logger.info("SUCCESS: Pipeline completed!")
    logger.info("=" * 60)
    logger.info(f"  PDF size:          {size_mb:.2f} MB")
    logger.info(f"  Clauses extracted: {clause_count}")
    logger.info(f"  Raw output:        {output_path} ({raw_size_kb:.2f} KB)")
    logger.info(f"  Final output:      {final_output_path} ({final_size_kb:.2f} KB)")
    logger.info("=" * 60)

    return result


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Extract clauses from Charter Party PDFs using Gemini Vision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic (no batching)
  python -m src.main voyage-charter-example.pdf

  # With batching
  python -m src.main document.pdf --start-page 6 --end-page 39 --batch-size 10

  # All options
  python -m src.main document.pdf \\
    --start-page 6 \\
    --end-page 39 \\
    --batch-size 10 \\
    --overlap 2 \\
    --parallel \\
    --max-workers 3

Environment variables:
  GOOGLE_API_KEY  Your Google API key (required)
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

    # Batching arguments
    batch_group = parser.add_argument_group("batching options")

    batch_group.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="First page to process (1-indexed, default: 1)",
    )

    batch_group.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="Last page to process (default: last page of document)",
    )

    batch_group.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Pages per batch (0 = no batching, default: 0)",
    )

    batch_group.add_argument(
        "--overlap",
        type=int,
        default=2,
        help="Pages of overlap between batches (default: 2)",
    )

    batch_group.add_argument(
        "--parallel",
        action="store_true",
        help="Process batches in parallel",
    )

    batch_group.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum parallel workers (default: 3)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    # Load environment variables from .env file if present
    from dotenv import load_dotenv

    load_dotenv()

    args = parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Build batch config if batching is enabled
    batch_config: BatchConfig | None = None
    if args.batch_size > 0:
        batch_config = BatchConfig(
            start_page=args.start_page,
            end_page=args.end_page,
            batch_size=args.batch_size,
            overlap=args.overlap,
            parallel=args.parallel,
            max_workers=args.max_workers,
        )

    try:
        main(args.pdf_path, args.output, args.final_output, batch_config)
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
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
