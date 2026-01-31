"""Pydantic models and transformation functions for clause extraction output.

This module provides:
- Clause model: Final output structure with id, title, text
- transform_raw_to_output: Converts raw API response to clean output format
- validate_raw_response: Validates raw API response structure
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Clause(BaseModel):
    """A single clause extracted from the document.

    This is the final output format with only essential fields.
    """

    id: str = Field(description="Clause identifier (e.g., '1', '14(a)')")
    title: str = Field(description="Clause title/heading extracted from first line")
    text: str = Field(description="Full clause text content")


def validate_raw_response(raw_data: dict[str, Any]) -> None:
    """Validate that raw API response has expected structure.

    Args:
        raw_data: Dictionary from raw_response.json

    Raises:
        ValueError: If structure is malformed
    """
    if not isinstance(raw_data, dict):
        raise ValueError(
            f"Raw response must be a dictionary, got {type(raw_data).__name__}. "
            f"Check that the API returned valid JSON."
        )

    if "clauses" not in raw_data:
        available_keys = list(raw_data.keys())
        raise ValueError(
            f"Raw response missing 'clauses' key. "
            f"Available keys: {available_keys}. "
            f"API response format may have changed."
        )

    if not isinstance(raw_data["clauses"], list):
        raise ValueError(
            f"Raw response 'clauses' must be an array, "
            f"got {type(raw_data['clauses']).__name__}"
        )

    logger.debug("Raw response structure validated")
    logger.info(
        f"Raw response validation passed: {len(raw_data['clauses'])} clauses found"
    )


def transform_raw_to_output(raw_data: dict[str, Any]) -> list[Clause]:
    """Transform raw API response into final output format.

    Takes the raw API response and converts it to clean output format.

    Args:
        raw_data: Dict {"clauses": [{"clause_number": str, "title": str, "text": str}]}

    Returns:
        List of Clause objects in document order

    Notes:
        - Preserves document order (no sorting)
        - Handles duplicate IDs by appending _2, _3, etc.
        - Skips clauses with empty text
    """
    clauses: list[Clause] = []
    raw_clauses = raw_data.get("clauses", [])
    skipped_count = 0
    seen_ids: dict[str, int] = {}

    logger.debug(f"Starting transformation of {len(raw_clauses)} raw clauses")

    for idx, raw_clause in enumerate(raw_clauses):
        text = raw_clause.get("text") or ""
        text = text.strip() if isinstance(text, str) else ""
        if not text:
            clause_num = raw_clause.get("clause_number", "unknown")
            logger.warning(f"Skipping clause {clause_num}: empty text content")
            skipped_count += 1
            continue

        clause_id = raw_clause.get("clause_number") or ""
        clause_id = clause_id.strip() if isinstance(clause_id, str) else str(clause_id)
        if not clause_id:
            logger.warning(f"Raw clause at index {idx} has no clause_number")
            clause_id = f"unknown_{idx}"

        if clause_id in seen_ids:
            seen_ids[clause_id] += 1
            original_id = clause_id
            clause_id = f"{clause_id}_{seen_ids[original_id]}"
            logger.debug(f"Duplicate ID '{original_id}' renamed to '{clause_id}'")
        else:
            seen_ids[clause_id] = 1

        title = raw_clause.get("title") or ""
        title = title.strip() if isinstance(title, str) else str(title)
        if not title:
            title = clause_id

        logger.debug(f"Clause {clause_id}: title='{title[:50]}', text_len={len(text)}")

        clause = Clause(id=clause_id, title=title, text=text)
        clauses.append(clause)

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} clauses with empty text")

    if len(clauses) < 10:
        logger.warning(f"Only {len(clauses)} clauses extracted - may indicate failure")

    logger.info(f"Transformed {len(clauses)} clauses to output format (document order)")
    return clauses
