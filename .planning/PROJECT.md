# Charter Party Document Parser

## What This Is

A Python application that parses a maritime voyage charter party PDF and extracts legal clauses (Part II, pages 6-39) into structured JSON using Claude as the LLM. Built as an AI engineer coding challenge submission that demonstrates clean Python code and accurate document extraction.

## Core Value

Accurately extract every legal clause from the charter party PDF with correct IDs, titles, and full text — excluding struck-through text — in document order.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Extract legal clauses from Part II of the charter party PDF (pages 6-39)
- [ ] For each clause, extract: id (clause number), title (heading), text (full content)
- [ ] Output structured JSON to a file on disk
- [ ] Exclude struck-through text from extraction
- [ ] Return clauses in document order
- [ ] Use Claude (Anthropic) as the LLM via langchain-anthropic
- [ ] Code structured as separate Python files (not a package, not a single script)
- [ ] Code quality demonstrates strong Python skills
- [ ] Runnable locally (no hardcoded API keys)
- [ ] Include output JSON in the final submission

### Out of Scope

- Part I (Particulars/Details section) — explicitly excluded by requirements
- Web UI or API server — this is a CLI/script tool
- Support for arbitrary PDFs — built specifically for the voyage charter party document
- OAuth or multi-model support — Claude only, API key via environment variable

## Context

- This is a coding challenge submission for an AI engineer role
- The PDF is a standard maritime voyage charter party agreement
- The document has two parts: Part I (particulars, skip) and Part II (legal clauses, extract)
- Project already has pyproject.toml with langchain, langchain-anthropic, langchain-community dependencies
- Python 3.13, managed with uv
- The PDF is included in the repo: `voyage-charter-example.pdf`
- API key should be read from environment (`.env` file exists)

## Constraints

- **LLM**: Claude via langchain-anthropic — already installed as dependency
- **Python**: 3.13+ — specified in .python-version
- **Package manager**: uv — already configured
- **No API keys in code**: Must use environment variables
- **Submission**: Push to GitHub, invite reviewers

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Claude as LLM | Already installed, multimodal capable for PDF processing | — Pending |
| Separate Python files | Clean organization without over-engineering into a package | — Pending |
| JSON file output | Reviewers can inspect results; included in submission | — Pending |

---
*Last updated: 2026-01-30 after initialization*
