import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


def extract_json_from_response(text: str) -> str:
    """Extract JSON object from response text.

    Handles responses with:
    - Plain JSON
    - JSON wrapped in ```json ... ```
    - JSON with preamble text before it
    """
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    json_pattern = r'\{[^{}]*"clauses"\s*:\s*\[[\s\S]*\]\s*\}'
    match = re.search(json_pattern, text)
    if match:
        return match.group(0)

    return text.strip()


MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_environment() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("Please set your API key: export GOOGLE_API_KEY='your-key'")
        raise SystemExit(1)


DEFAULT_MODEL = "gemini-3-pro-preview"
FLASH_MODEL = "gemini-3-flash-preview"


class GeminiClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 32768,
        temperature: float = 0.1,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        # Only use thinking_level for non-flash models
        llm_kwargs: dict[str, Any] = {
            "model": model,
            "max_output_tokens": max_tokens,
            "temperature": temperature,
            "api_key": api_key,
        }
        if "flash" not in model.lower():
            llm_kwargs["thinking_level"] = "low"

        self.llm = ChatGoogleGenerativeAI(**llm_kwargs)

        logger.info(f"Initialized Gemini client with model: {model}")

    def extract_clauses(self, pdf_path: str, prompt: str) -> dict[str, Any]:
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        file_size = pdf_file.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"PDF file too large: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB"
            )

        logger.info(f"Loading PDF: {pdf_path} ({file_size / 1024:.1f} KB)")

        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()

        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        content: list[str | dict[Any, Any]] = [
            {
                "type": "file",
                "source_type": "base64",
                "mime_type": "application/pdf",
                "data": pdf_base64,
            },
            {
                "type": "text",
                "text": prompt,
            },
        ]

        message = HumanMessage(content=content)

        logger.info(f"Sending PDF to Gemini ({self.model})...")

        response_text = ""
        try:
            response = self.llm.invoke([message])

            if isinstance(response.content, str):
                response_text = response.content
            elif isinstance(response.content, list):
                response_text = "".join(
                    str(block) if isinstance(block, str) else block.get("text", "")
                    for block in response.content
                )
            else:
                response_text = str(response.content)

            logger.info(f"Received response ({len(response_text)} chars)")

            json_text = extract_json_from_response(response_text)
            result = cast(dict[str, Any], json.loads(json_text))

            clause_count = len(result.get("clauses", []))
            logger.info(f"Extracted {clause_count} clauses")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON in response: {e}") from e
        except Exception as e:
            logger.error(f"Error during Gemini API call: {e}")
            raise

    def extract_clauses_from_bytes(
        self,
        pdf_bytes: bytes,
        prompt: str,
        page_range: tuple[int, int] | None = None,
    ) -> dict[str, Any]:
        """Extract clauses from PDF bytes (for batch processing).

        Args:
            pdf_bytes: PDF file content as bytes
            prompt: Extraction prompt to use
            page_range: Optional (start, end) page tuple for logging

        Returns:
            Dictionary containing extracted clauses

        Raises:
            ValueError: If response is not valid JSON
        """
        if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"PDF bytes too large: {len(pdf_bytes) / (1024*1024):.1f}MB "
                f"> {MAX_FILE_SIZE_MB}MB"
            )

        range_str = f" (pages {page_range[0]}-{page_range[1]})" if page_range else ""
        logger.info(f"Processing PDF bytes{range_str} ({len(pdf_bytes) / 1024:.1f} KB)")

        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        content: list[str | dict[Any, Any]] = [
            {
                "type": "file",
                "source_type": "base64",
                "mime_type": "application/pdf",
                "data": pdf_base64,
            },
            {
                "type": "text",
                "text": prompt,
            },
        ]

        message = HumanMessage(content=content)

        logger.info(f"Sending PDF to Gemini ({self.model})...")

        response_text = ""
        try:
            response = self.llm.invoke([message])

            if isinstance(response.content, str):
                response_text = response.content
            elif isinstance(response.content, list):
                response_text = "".join(
                    str(block) if isinstance(block, str) else block.get("text", "")
                    for block in response.content
                )
            else:
                response_text = str(response.content)

            logger.info(f"Received response ({len(response_text)} chars)")

            json_text = extract_json_from_response(response_text)
            result = cast(dict[str, Any], json.loads(json_text))

            clause_count = len(result.get("clauses", []))
            logger.info(f"Extracted {clause_count} clauses{range_str}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON in response: {e}") from e
        except Exception as e:
            logger.error(f"Error during Gemini API call: {e}")
            raise
