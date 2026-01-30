# Charter Party Document Parser

## What This Is

A Python application that parses a maritime charter party PDF document and extracts legal clauses in structured JSON format using Claude's vision capabilities. Built as an AI engineering coding challenge to demonstrate PDF processing with modern LLM capabilities.

## Core Value

Accurately extract all numbered legal clauses from the document, excluding strike-through text, in the correct order.

## Current State

**Version:** v1 (shipped 2026-01-30)
**Codebase:** 1,052 lines of Python across 8 source files
**Tech stack:** Python 3.13+, Anthropic SDK, pdf2image, Pillow, Pydantic

The v1 release delivers a complete end-to-end pipeline:
1. Convert PDF pages 6-39 to images at 150 DPI
2. Send multi-image batch to Claude Vision API with page labels
3. Extract clauses with id, title, text (excluding strikethrough)
4. Output clean JSON to output.json

Code quality: mypy strict mode, black formatting, ruff linting all pass.

## Requirements

### Validated

- Parse PDF pages 6-39 (Part II: Legal clauses) — v1
- Convert PDF pages to images for Claude vision processing — v1
- Extract clause ID (numbered identifier like "1", "2", "3") — v1
- Extract clause title/heading — v1
- Extract full clause text content — v1
- Exclude strike-through text from extraction — v1
- Preserve clause order as they appear in document — v1
- Output structured JSON to file (output.json) — v1
- Validate extracted clauses (count verification, schema validation) — v1
- Code should be runnable locally with clear instructions — v1

### Active

(None — v1 complete)

### Out of Scope

- Part I (Particulars/Details) — explicitly excluded per requirements
- Web interface or API — this is a CLI tool
- Support for other document types — single document focus
- API key management — user provides their own key via environment
- Confidence scores — not required per final spec

## Context

**Document:** `voyage-charter-example.pdf` - A voyage charter party agreement (standard maritime contract) containing legal provisions across pages 6-39.

**Technical approach:** PDF-to-image conversion followed by Claude vision processing. This approach was chosen because:
- Strike-through text is visually detectable but hard to extract via text libraries
- Legal document layouts are complex and benefit from visual understanding
- Demonstrates modern LLM capabilities for a coding challenge

**Dependencies:**
- anthropic (Claude API SDK with built-in retry)
- pdf2image (PDF to image conversion)
- Pillow (image processing)
- pydantic (schema validation)
- Python 3.13+

## Constraints

- **LLM**: Claude claude-sonnet-4-5 via Anthropic SDK
- **Python**: 3.13+ (per pyproject.toml)
- **Security**: No API keys in code — use ANTHROPIC_API_KEY environment variable
- **Output**: JSON file only (output.json)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PDF vision over text extraction | Strike-through detection, layout preservation, demonstrates modern LLM capabilities | Good — correctly identifies and excludes strikethrough text |
| 150 DPI resolution | Balance image quality with API token cost | Good — 1275x1650 pixels provides clear text while staying under limits |
| In-memory processing | Avoid filesystem complexity and temp file cleanup | Good — no temp files, clean pipeline |
| max_retries=3 via SDK | SDK handles exponential backoff automatically | Good — reliable API calls without custom retry logic |
| Pydantic for validation | Type-safe schema enforcement | Good — catches malformed data early |
| mypy strict mode | Maximum type safety | Good — all 8 files pass with zero errors |

---
*Last updated: 2026-01-30 after v1 milestone*
