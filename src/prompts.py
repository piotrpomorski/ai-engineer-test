"""Extraction prompt templates for Gemini PDF processing.

This module contains the prompt templates and JSON schemas used for
extracting clauses from contract PDF documents.
"""

CLAUSE_EXTRACTION_PROMPT = """Extract all numbered clauses from this charter party PDF document.

## Instructions

Extract every numbered clause from the document (e.g., "1.", "2.", "14(a)", etc.).

For each clause extract:
- The page number where it appears (for ordering)
- The clause number/identifier exactly as written
- The title or heading (if the clause has one)
- The complete text content

## Critical Requirements

- **COMPLETELY SKIP** any text that is struck through, crossed out, or deleted
- Do NOT create entries for deleted/struck clauses
- Only include clauses with actual substantive text
- Return clauses in the order they appear in the document
- If clause numbers repeat (e.g., addendum sections), keep them all in document order

## Output Format

Return ONLY a valid JSON object with no additional text, explanation, or markdown formatting.

{
  "clauses": [
    {
      "page": 6,
      "clause_number": "1.",
      "title": "Condition of Vessel",
      "text": "Owners shall exercise due diligence..."
    },
    {
      "page": 6,
      "clause_number": "2.",
      "title": "Cleanliness of Tanks", 
      "text": "Whilst loading, carrying and discharging..."
    }
  ]
}

IMPORTANT: Output ONLY the JSON object. No preamble, no explanation, no markdown code blocks."""

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
                        "description": "Page number where clause appears",
                    },
                    "clause_number": {
                        "type": "string",
                        "description": "The clause identifier (e.g., '1.', '14(a)')",
                    },
                    "title": {
                        "type": "string",
                        "description": "Clause title or heading",
                    },
                    "text": {
                        "type": "string",
                        "description": "The complete text of the clause",
                    },
                },
                "required": ["page", "clause_number", "title", "text"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["clauses"],
    "additionalProperties": False,
}
