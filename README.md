# AI Engineer Challenge: Charter Party Document Parser

## Overview

Your task is to build a Python application that parses a maritime charter party document (PDF) and extracts legal clauses in a structured format using LLM capabilities.

## Document

**Source:** https://shippingforum.wordpress.com/wp-content/uploads/2012/09/voyage-charter-example.pdf

This is a voyage charter party agreement - a standard maritime contract used in shipping. The document contains:
- **Part I**: Particulars/Details (skip this section)
- **Part II**: Legal clauses with numbered provisions (**Pages 6-39**)

## Requirements

1. **Extract legal clauses from Part II** of the document (**Pages 6-39**)
2. **For each clause, extract:**
   - `id`: The clause identifier (e.g., "1", "2", "3", etc.)
   - `title`: The clause title/heading
   - `text`: The full clause text content

3. **Output the extracted clauses** in a structured JSON format.
4. Do not include strike-thru text.
5. Clauses should be returned in the order they appear in the document.

**DO include the output json in the final submission**

### Technical Requirements

1. You can use any LLM of your choice.
2. Focus on code quality. It should show your python skills!
3. We should be able to run your code locally.

**DO NOT include your API key in the submission!**

PS. Please publish the solution to your GitHub and invite us to review it.

Any questions shoot and good luck!

---

## Solution Overview

This solution implements an end-to-end pipeline for extracting legal clauses from charter party PDF documents using Google Gemini API with native PDF support.

### Pipeline Architecture

```
PDF Document
     |
     v
[Batch Processor] -- Splits PDF into page ranges (optional)
     |
     v
[Gemini API] -- Native PDF processing with parallel batches
     |
     v
[Merge & Dedupe] -- Combines results, removes duplicates
     |
     v
[Pydantic Validation] -- Validates and transforms response
     |
     v
JSON Output (output.json)
```

### Key Features

- **Native PDF processing**: Gemini processes PDFs directly (no image conversion needed)
- **Parallel batch processing**: Split large PDFs into chunks for faster extraction
- **No system dependencies**: Pure Python, no poppler or external tools required
- **LangChain integration**: Uses LangChain for robust LLM orchestration
- **Large file support**: Handles PDFs up to 100MB
- **Pydantic validation**: Ensures output conforms to expected schema
- **Structured logging**: Step-by-step progress with debug mode for troubleshooting
- **Strike-through exclusion**: Explicitly instructs API to skip deleted text
- **Automatic retry**: Handles transient API errors with exponential backoff

---

## Prerequisites

- **Python 3.13+**
- **Google API key** (sign up at https://aistudio.google.com/apikey)

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai-engineer-test
```

### 2. Install Python dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using uv (recommended):
```bash
uv sync
```

---

## Configuration

### Set API Key

Set your Google API key as an environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Alternatively, create a `.env` file in the project root:
```
GOOGLE_API_KEY=your-api-key-here
```

Note: The `.env` file is gitignored and will not be committed.

---

## Usage

### Basic Usage

Process the included sample document:

```bash
python -m src.main voyage-charter-example.pdf
```

This produces two output files:
- `raw_response.json` - Raw API response (for debugging)
- `output.json` - Final transformed output (the deliverable)

### Recommended: Parallel Batch Processing

For faster and more reliable extraction, use parallel batch processing with Gemini Pro:

```bash
python -m src.main voyage-charter-example.pdf \
  --batch-size 12 \
  --parallel \
  --max-workers 3 \
  --start-page 6 \
  --model gemini-3-pro-preview
```

This splits the PDF into overlapping chunks and processes them in parallel.

### Batch Processing Options

| Option | Description | Default |
|--------|-------------|---------|
| `--batch-size N` | Pages per batch (0 = no batching) | 0 |
| `--parallel` | Process batches in parallel | False |
| `--max-workers N` | Number of parallel workers | 3 |
| `--start-page N` | First page to process (1-indexed) | 1 |
| `--end-page N` | Last page to process | Last page |
| `--model NAME` | Gemini model to use | gemini-3-flash-preview |
| `--overlap N` | Pages of overlap between batches | 2 |

### Custom Output Paths

Specify custom output file paths:

```bash
python -m src.main voyage-charter-example.pdf --output my_raw.json --final-output my_clauses.json
```

### Verbose Mode

Enable debug logging for troubleshooting:

```bash
python -m src.main voyage-charter-example.pdf --verbose
```

### Processing Time

| Mode | Time | Notes |
|------|------|-------|
| Single-pass (Pro) | ~3 min | Most reliable |
| Parallel batches (Pro) | ~1.5 min | Recommended |
| Parallel batches (Flash) | ~1 min | Faster but less consistent |

---

## Output

### Output Files

| File | Purpose |
|------|---------|
| `output.json` | Final deliverable with extracted clauses |
| `raw_response.json` | Debug artifact with raw API response |

### Output Format

The `output.json` file contains an array of clause objects:

```json
[
  {
    "id": "1",
    "title": "Definitions",
    "text": "In this Charter Party, the following terms shall have the meanings..."
  },
  {
    "id": "2",
    "title": "Cargo",
    "text": "The vessel shall carry a full and complete cargo..."
  }
]
```

### Sample Output

See the included `output.json` file for a complete example of successful extraction from the voyage charter document.

---

## Project Structure

```
ai-engineer-test/
|-- src/
|   |-- __init__.py
|   |-- main.py              # Pipeline orchestration and CLI
|   |-- gemini_client.py     # Gemini API client with native PDF support
|   |-- models.py            # Pydantic models and transformation
|   |-- prompts.py           # Extraction prompt templates
|
|-- voyage-charter-example.pdf   # Sample input document
|-- output.json                  # Sample extraction output
|-- requirements.txt             # Python dependencies (pip)
|-- pyproject.toml               # Project configuration (uv)
|-- README.md                    # This file
```

### Module Descriptions

| Module | Description |
|--------|-------------|
| `src/main.py` | Main entry point. Orchestrates the 5-step pipeline. |
| `src/gemini_client.py` | Gemini API client with native PDF processing. |
| `src/batch_processor.py` | Splits PDFs into batches, parallel processing, merge & dedupe. |
| `src/models.py` | Pydantic models for output validation and transformation. |
| `src/prompts.py` | Prompt templates for clause extraction. |

---

## Development

### Code Quality Tools

This project uses strict type checking and formatting:

```bash
# Type checking (mypy strict mode)
mypy src/

# Code formatting
black src/

# Linting
ruff check src/
```

### Run All Checks

```bash
mypy src/ && black --check src/ && ruff check src/
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File/validation error (missing PDF, malformed response) |
| 2 | API error (authentication, rate limit, timeout) |

---

## Troubleshooting

### "GOOGLE_API_KEY environment variable not set"

Set your API key:
```bash
export GOOGLE_API_KEY="your-api-key-here"
```


### "Response truncated due to max_tokens limit"

The document produced more text than expected. This is rare with the default 8192 token limit.

### API errors

If you encounter rate limits or timeout errors, Gemini provides generous free tier limits. Check your quota at https://aistudio.google.com/
