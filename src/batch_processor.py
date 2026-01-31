"""Batched PDF processing for clause extraction.

This module provides dynamic page-range batching to handle large PDFs
without hallucination, while keeping Gemini's native PDF vision for
strikethrough detection.
"""

import io
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from pypdf import PdfReader, PdfWriter

from src.gemini_client import FLASH_MODEL, GeminiClient
from src.prompts import CLAUSE_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    start_page: int = 1
    end_page: int | None = None  # None means process to end of document
    batch_size: int = 10
    overlap: int = 2
    parallel: bool = False
    max_workers: int = 3
    max_retries: int = 3
    retry_delay: float = 2.0  # Base delay for exponential backoff
    model: str = FLASH_MODEL  # Default to Flash for speed in batch processing


@dataclass
class BatchResult:
    """Result from processing a single batch."""

    batch_index: int
    page_range: tuple[int, int]  # (start_page, end_page) - 1-indexed
    clauses: list[dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: str | None = None


class BatchProcessor:
    """Process large PDFs in batches for reliable clause extraction."""

    def __init__(self, config: BatchConfig, client: GeminiClient | None = None):
        """Initialize batch processor.

        Args:
            config: Batch processing configuration
            client: GeminiClient instance (created if not provided)
        """
        self.config = config
        self.client = client or GeminiClient(model=config.model)

    def process(self, pdf_path: str) -> dict[str, Any]:
        """Process a PDF file with batching.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with merged clauses: {"clauses": [...]}

        Raises:
            RuntimeError: If all batches fail
        """
        logger.info(f"Starting batch processing of {pdf_path}")

        # Read the PDF to get total pages
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)

        logger.info(f"PDF has {total_pages} pages")

        # Determine effective page range
        start_page = self.config.start_page
        end_page = self.config.end_page or total_pages

        # Validate page range
        if start_page < 1:
            start_page = 1
        if end_page > total_pages:
            end_page = total_pages
        if start_page > end_page:
            raise ValueError(
                f"Invalid page range: start_page ({start_page}) > end_page ({end_page})"
            )

        logger.info(f"Processing pages {start_page} to {end_page}")

        # Calculate batches
        batches = self._calculate_batches(start_page, end_page)
        logger.info(f"Calculated {len(batches)} batches: {batches}")

        # Process batches
        if self.config.parallel and len(batches) > 1:
            results = self._process_parallel(pdf_path, batches)
        else:
            results = self._process_sequential(pdf_path, batches)

        # Check for complete failure
        successful_results = [r for r in results if r.success]
        if not successful_results:
            failed_ranges = [f"{r.page_range[0]}-{r.page_range[1]}" for r in results]
            raise RuntimeError(
                f"All {len(results)} batches failed. "
                f"Page ranges: {', '.join(failed_ranges)}"
            )

        # Log partial failures
        failed_results = [r for r in results if not r.success]
        if failed_results:
            for r in failed_results:
                page_start, page_end = r.page_range
                logger.warning(
                    f"Batch {r.batch_index} (pages {page_start}-{page_end}) "
                    f"failed: {r.error}"
                )

        # Merge and deduplicate results
        merged_clauses = self._merge_results(results, batches)

        logger.info(
            f"Batch processing complete: {len(merged_clauses)} unique clauses "
            f"from {len(successful_results)}/{len(results)} successful batches"
        )

        return {"clauses": merged_clauses}

    def _calculate_batches(
        self, start_page: int, end_page: int
    ) -> list[tuple[int, int]]:
        """Calculate batch page ranges with overlap.

        Args:
            start_page: First page to process (1-indexed)
            end_page: Last page to process (1-indexed)

        Returns:
            List of (batch_start, batch_end) tuples (1-indexed)

        Example:
            start=6, end=39, batch_size=10, overlap=2
            step = 10 - 2 = 8
            batches = [(6,15), (14,23), (22,31), (30,39)]
        """
        batches: list[tuple[int, int]] = []
        step = self.config.batch_size - self.config.overlap

        if step <= 0:
            raise ValueError(
                f"Invalid config: batch_size ({self.config.batch_size}) "
                f"must be greater than overlap ({self.config.overlap})"
            )

        current_start = start_page
        while current_start <= end_page:
            batch_end = min(current_start + self.config.batch_size - 1, end_page)
            batches.append((current_start, batch_end))

            # Move to next batch start
            current_start += step

            # If we've already covered the end, stop
            if batch_end >= end_page:
                break

        return batches

    def _extract_page_range(
        self, pdf_path: str, start_page: int, end_page: int
    ) -> bytes:
        """Extract a page range from a PDF into bytes.

        Args:
            pdf_path: Path to source PDF
            start_page: First page (1-indexed)
            end_page: Last page (1-indexed)

        Returns:
            PDF bytes containing only the specified pages
        """
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            writer = PdfWriter()

            # pypdf uses 0-indexed pages
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])

            # Write to bytes buffer
            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            return buffer.read()

    def _process_single_batch(
        self, pdf_path: str, batch_index: int, page_range: tuple[int, int]
    ) -> BatchResult:
        """Process a single batch with retry logic.

        Args:
            pdf_path: Path to source PDF
            batch_index: Index of this batch (for logging)
            page_range: (start_page, end_page) tuple

        Returns:
            BatchResult with extracted clauses or error
        """
        start_page, end_page = page_range
        logger.info(f"Processing batch {batch_index}: pages {start_page}-{end_page}")

        last_error: str | None = None

        for attempt in range(self.config.max_retries):
            try:
                # Extract page range to PDF bytes
                pdf_bytes = self._extract_page_range(pdf_path, start_page, end_page)
                logger.debug(f"Batch {batch_index}: extracted {len(pdf_bytes)} bytes")

                # Build prompt with page context
                prompt = self._build_batch_prompt(start_page, end_page)

                # Call Gemini with PDF bytes
                result = self.client.extract_clauses_from_bytes(
                    pdf_bytes, prompt, page_range=(start_page, end_page)
                )

                clauses = result.get("clauses", [])

                # Adjust page numbers from batch-relative to document-absolute
                adjusted_clauses = self._adjust_page_numbers(
                    clauses, start_page, end_page
                )

                logger.info(
                    f"Batch {batch_index}: extracted {len(adjusted_clauses)} clauses"
                )

                return BatchResult(
                    batch_index=batch_index,
                    page_range=page_range,
                    clauses=adjusted_clauses,
                    success=True,
                )

            except Exception as e:
                last_error = str(e)
                retries = self.config.max_retries
                logger.warning(
                    f"Batch {batch_index} attempt {attempt + 1}/{retries} failed: {e}"
                )

                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)

        # All retries exhausted
        return BatchResult(
            batch_index=batch_index,
            page_range=page_range,
            clauses=[],
            success=False,
            error=last_error,
        )

    def _build_batch_prompt(self, start_page: int, end_page: int) -> str:
        """Build prompt with page range context.

        Args:
            start_page: First page in batch (document-absolute)
            end_page: Last page in batch (document-absolute)

        Returns:
            Prompt string with page context
        """
        page_context = (
            f"\n\n**Page Context:** This is a subset of a larger document. "
            f"The pages in this PDF correspond to pages {start_page}-{end_page} "
            f"of the original document. Please report page numbers as they appear "
            f"in the original document (starting from page {start_page})."
        )
        return CLAUSE_EXTRACTION_PROMPT + page_context

    def _adjust_page_numbers(
        self,
        clauses: list[dict[str, Any]],
        batch_start: int,
        batch_end: int,
    ) -> list[dict[str, Any]]:
        """Adjust page numbers from batch-relative to document-absolute.

        The Gemini API receives a PDF subset starting from page 1, but we need
        page numbers relative to the original document.

        Args:
            clauses: List of clause dicts with 'page' field
            batch_start: First page of batch in original document
            batch_end: Last page of batch in original document

        Returns:
            Clauses with adjusted page numbers
        """
        adjusted = []
        for clause in clauses:
            new_clause = clause.copy()

            # The batch PDF starts at page 1, so page 1 in batch = batch_start in doc
            batch_page = clause.get("page", 1)
            doc_page = batch_start + batch_page - 1

            # Clamp to batch range
            doc_page = max(batch_start, min(batch_end, doc_page))
            new_clause["page"] = doc_page

            # Mark source batch for deduplication
            new_clause["_batch_start"] = batch_start
            new_clause["_batch_end"] = batch_end

            adjusted.append(new_clause)

        return adjusted

    def _process_sequential(
        self, pdf_path: str, batches: list[tuple[int, int]]
    ) -> list[BatchResult]:
        """Process batches sequentially.

        Args:
            pdf_path: Path to PDF file
            batches: List of (start_page, end_page) tuples

        Returns:
            List of BatchResult objects
        """
        results = []
        for idx, page_range in enumerate(batches):
            result = self._process_single_batch(pdf_path, idx, page_range)
            results.append(result)
        return results

    def _process_parallel(
        self, pdf_path: str, batches: list[tuple[int, int]]
    ) -> list[BatchResult]:
        """Process batches in parallel.

        Args:
            pdf_path: Path to PDF file
            batches: List of (start_page, end_page) tuples

        Returns:
            List of BatchResult objects
        """
        results: list[BatchResult] = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(
                    self._process_single_batch, pdf_path, idx, page_range
                ): idx
                for idx, page_range in enumerate(batches)
            }

            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch {batch_idx} raised exception: {e}")
                    results.append(
                        BatchResult(
                            batch_index=batch_idx,
                            page_range=batches[batch_idx],
                            success=False,
                            error=str(e),
                        )
                    )

        # Sort by batch index to maintain order
        results.sort(key=lambda r: r.batch_index)
        return results

    def _merge_results(
        self,
        results: list[BatchResult],
        batches: list[tuple[int, int]],
    ) -> list[dict[str, Any]]:
        """Merge and deduplicate clauses from all batches.

        Deduplication strategy:
        1. Primary key: clause_number
        2. For duplicates: prefer version NOT in overlap region
        3. Tie-breaker: prefer longer text (more complete extraction)
        4. Final sort: by page number, then clause_number

        Args:
            results: List of BatchResult objects
            batches: Original batch definitions for overlap detection

        Returns:
            Deduplicated and sorted list of clauses
        """
        # Build overlap regions map
        overlap_pages: set[int] = set()
        for i in range(len(batches) - 1):
            _, batch_end = batches[i]
            next_start, _ = batches[i + 1]
            # Pages in the overlap region
            for page in range(next_start, batch_end + 1):
                overlap_pages.add(page)

        clause_map: dict[str, dict[str, Any]] = {}

        for result in results:
            if not result.success:
                continue

            for clause in result.clauses:
                clause_num = clause.get("clause_number", "")
                if not clause_num:
                    continue

                page = clause.get("page", 0)
                text = clause.get("text", "")
                in_overlap = page in overlap_pages

                dedup_key = f"{page}:{clause_num}"

                if in_overlap:
                    existing = clause_map.get(dedup_key)
                    if existing is None:
                        clause_map[dedup_key] = clause
                    else:
                        existing_text_len = len(existing.get("text", ""))
                        new_text_len = len(text)
                        if new_text_len > existing_text_len:
                            clause_map[dedup_key] = clause
                else:
                    clause_map[dedup_key] = clause

        # Remove internal metadata and sort
        final_clauses = []
        for clause in clause_map.values():
            clean_clause = {k: v for k, v in clause.items() if not k.startswith("_")}
            final_clauses.append(clean_clause)

        # Sort by page, then by clause_number
        def sort_key(c: dict[str, Any]) -> tuple[int, str]:
            return (c.get("page", 0), c.get("clause_number", ""))

        final_clauses.sort(key=sort_key)

        return final_clauses
