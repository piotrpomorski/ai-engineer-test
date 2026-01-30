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
        raise ValueError("Raw response must be a dictionary")

    if "clauses" not in raw_data:
        raise ValueError("Raw response missing 'clauses' key")

    if not isinstance(raw_data["clauses"], list):
        raise ValueError("Raw response 'clauses' must be an array")

    logger.info(
        f"Raw response validation passed: {len(raw_data['clauses'])} clauses found"
    )


def transform_raw_to_output(raw_data: dict[str, Any]) -> list[Clause]:
    """Transform raw API response into final output format.

    Takes the raw Claude API response structure (with page numbers, clause_number)
    and converts it to the clean output format (id, title, text only).

    Args:
        raw_data: Dict {"clauses": [{"page": int, "clause_number": str, "text": str}]}

    Returns:
        List of Clause objects ready for JSON serialization

    Notes:
        - Preserves clause order from API response (no sorting)
        - Extracts title from first line of text (up to newline or period)
        - Skips clauses with empty/None text
        - Warns if fewer than 10 clauses (suggests extraction failure)
    """
    clauses: list[Clause] = []
    raw_clauses = raw_data.get("clauses", [])

    for raw_clause in raw_clauses:
        # Skip clauses with empty text
        text = raw_clause.get("text", "").strip()
        if not text:
            clause_num = raw_clause.get("clause_number", "unknown")
            logger.warning(f"Skipping clause {clause_num} with empty text")
            continue

        # Extract id from clause_number
        clause_id = raw_clause.get("clause_number", "").strip()

        # Extract title from first line of text (up to first newline/period)
        first_line = text.split("\n")[0]
        title = first_line.split(".")[0].strip()

        # Create Clause object
        clause = Clause(id=clause_id, title=title, text=text)
        clauses.append(clause)

    # Warn if fewer than 10 clauses (suggests extraction failure)
    if len(clauses) < 10:
        logger.warning(f"Only {len(clauses)} clauses extracted - may indicate failure")

    logger.info(f"Transformed {len(clauses)} clauses to output format")
    return clauses
