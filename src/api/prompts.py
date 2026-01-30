"""Extraction prompt templates for Claude PDF API.

This module contains the prompt templates and JSON schemas used for
extracting clauses from contract PDF documents.
"""

CLAUSE_EXTRACTION_PROMPT = """Extract all numbered clauses from this PDF document (pages 6-39).

<instructions>
<task>
Identify every numbered clause in the document (e.g., "1.", "2.", "3." or "Clause 1", etc.)
</task>

<for_each_clause>
Extract the following information:
- The page number where it appears in the PDF
- The clause number/identifier exactly as written in the document
- The complete text of the clause, even if it spans multiple lines
</for_each_clause>
</instructions>

<critical_requirements>
- EXCLUDE any text that has strikethrough formatting (crossed-out text)
- Include ONLY visible, non-struck text
- Preserve the exact clause numbering from the document
- Do not skip or combine clauses
</critical_requirements>

<output_format>
Return the results as a JSON object with the exact structure specified in the schema.
</output_format>"""

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
