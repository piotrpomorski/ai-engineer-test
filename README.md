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

This solution implements an end-to-end pipeline for extracting legal clauses from charter party PDF documents using Claude Vision API.

### Pipeline Architecture

```
PDF Document
     |
     v
[PDF Handler] -- Extracts pages 6-39 and encodes to base64
     |
     v
[Claude API] -- Extracts clauses with structured output
     |
     v
[Pydantic Validation] -- Validates and transforms response
     |
     v
JSON Output (output.json)
```

### Key Features

- **In-memory processing**: No temporary files written to disk
- **Automatic retry logic**: Handles transient API errors with exponential backoff
- **Pydantic validation**: Ensures output conforms to expected schema
- **Structured logging**: Step-by-step progress with debug mode for troubleshooting
- **Strike-through exclusion**: Explicitly instructs API to skip deleted text

---

## Prerequisites

- **Python 3.13+**
- **Anthropic API key** (sign up at https://console.anthropic.com)

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

Set your Anthropic API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Alternatively, create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your-api-key-here
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

Expect approximately 30-60 seconds for the 34-page document. The majority of time is spent on the Claude API call processing all images.

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
|   |-- pdf_handler.py       # PDF page extraction
|   |-- models.py            # Pydantic models and transformation
|   |-- api/
|       |-- __init__.py
|       |-- client.py        # Claude API client with retry logic
|       |-- vision.py        # PDF request builder
|       |-- prompts.py       # Extraction prompt templates
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
| `src/pdf_handler.py` | Extracts page ranges and encodes PDF to base64. |
| `src/models.py` | Pydantic models for output validation and transformation. |
| `src/api/client.py` | Claude API client with retry logic. |
| `src/api/vision.py` | Builds PDF document API request payloads. |
| `src/api/prompts.py` | Prompt templates for clause extraction. |

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

### "ANTHROPIC_API_KEY environment variable not set"

Set your API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```


### "Response truncated due to max_tokens limit"

The document produced more text than expected. This is rare with the default 8192 token limit.

### API timeout errors

The default timeout is 300 seconds (5 minutes). For very slow connections, the pipeline will retry automatically up to 3 times.
