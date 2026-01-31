"""Extraction prompt templates for Gemini PDF processing.

This module contains the prompt templates and JSON schemas used for
extracting clauses from contract PDF documents.
"""

CLAUSE_EXTRACTION_PROMPT = """Extract all numbered clauses from this PDF document.

## Instructions

**Task:** Identify every numbered clause in the document
(e.g., "1.", "2.", "3." or "Clause 1", etc.)

**For each clause, extract:**
- The page number where it appears in the PDF
- The clause number/identifier exactly as written in the document
- The complete text of the clause, even if it spans multiple lines

## Critical Requirements

- **EXCLUDE** any text that has strikethrough formatting (crossed-out text)
- Include **ONLY** visible, non-struck text
- Preserve the exact clause numbering from the document
- Do not skip or combine clauses

## Output Format

Return the results as a JSON object with this structure:

```json
{
  "clauses": [
    {
      "page": 6,
      "clause_number": "1.",
      "text": "The complete clause text..."
    }
  ]
}
```"""

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
                        "description": "The page number where this clause appears",
                    },
                    "clause_number": {
                        "type": "string",
                        "description": "The clause identifier (e.g., '1.', 'Clause 1')",
                    },
                    "text": {
                        "type": "string",
                        "description": "The complete text of the clause",
                    },
                },
                "required": ["page", "clause_number", "text"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["clauses"],
    "additionalProperties": False,
}
