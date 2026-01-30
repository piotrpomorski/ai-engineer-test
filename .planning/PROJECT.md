# Charter Party Document Parser

## What This Is

A Python application that parses a maritime charter party PDF document and extracts legal clauses in structured JSON format using Claude's vision capabilities. Built as an AI engineering coding challenge to demonstrate PDF processing with modern LLM capabilities.

## Core Value

Accurately extract all numbered legal clauses from the document, excluding strike-through text, in the correct order.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Parse PDF pages 6-39 (Part II: Legal clauses)
- [ ] Convert PDF pages to images for Claude vision processing
- [ ] Extract clause ID (numbered identifier like "1", "2", "3")
- [ ] Extract clause title/heading
- [ ] Extract full clause text content
- [ ] Exclude strike-through text from extraction
- [ ] Preserve clause order as they appear in document
- [ ] Output structured JSON to file (output.json)
- [ ] Validate extracted clauses (count verification, schema validation)
- [ ] Code should be runnable locally with clear instructions

### Out of Scope

- Part I (Particulars/Details) — explicitly excluded per requirements
- Web interface or API — this is a CLI tool
- Support for other document types — single document focus
- API key management — user provides their own key via environment

## Context

**Document:** `voyage-charter-example.pdf` - A voyage charter party agreement (standard maritime contract) containing legal provisions across pages 6-39.

**Technical approach:** PDF-to-image conversion followed by Claude vision processing. This approach was chosen because:
- Strike-through text is visually detectable but hard to extract via text libraries
- Legal document layouts are complex and benefit from visual understanding
- Demonstrates modern LLM capabilities for a coding challenge

**Dependencies already configured:**
- langchain==1.2.7
- langchain-anthropic==1.3.1
- langchain-community==0.4.1
- Python 3.13+

## Constraints

- **LLM**: Claude via langchain-anthropic (already in dependencies)
- **Python**: 3.13+ (per pyproject.toml)
- **Security**: No API keys in code — use environment variables
- **Output**: JSON file only (output.json)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PDF vision over text extraction | Strike-through detection, layout preservation, demonstrates modern LLM capabilities | — Pending |
| Single-pass extraction per page | Simpler implementation, Claude can handle full page context | — Pending |
| langchain for LLM orchestration | Already in dependencies, good abstraction layer | — Pending |

---
*Last updated: 2025-01-30 after initialization*
