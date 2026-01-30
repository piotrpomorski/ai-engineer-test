"""Extraction prompt templates for Claude Vision API.

This module contains the prompt templates and JSON schemas used for
extracting clauses from contract document images.
"""

# Page label template for explicit page context (requirement API-04)
PAGE_LABEL_TEMPLATE = "Page {page_number}:"

# Comprehensive extraction prompt for clause identification
CLAUSE_EXTRACTION_PROMPT = """Extract all numbered clauses from these contract pages.

INSTRUCTIONS:
1. Identify every numbered clause in the document (e.g., "1.", "2.", "3." or "Clause 1", etc.)
2. For each clause, note:
   - The page number where it appears (use the "Page N:" labels provided)
   - The clause number/identifier exactly as written
   - The complete text of the clause

CRITICAL REQUIREMENTS:
- EXCLUDE any text that has strikethrough formatting (crossed-out text)
- Include ONLY visible, non-struck text
- Preserve the exact clause numbering from the document
- Include the full clause text, even if it spans multiple lines

Return the results as JSON with the exact structure specified."""

# JSON schema for structured output validation
# Guarantees valid JSON response matching this schema
JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "clauses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "The page number where this clause appears"
                    },
                    "clause_number": {
                        "type": "string",
                        "description": "The clause identifier (e.g., '1.', 'Clause 1')"
                    },
                    "text": {
                        "type": "string",
                        "description": "The complete text of the clause"
                    }
                },
                "required": ["page", "clause_number", "text"],
                "additionalProperties": False
            }
        }
    },
    "required": ["clauses"],
    "additionalProperties": False
}
