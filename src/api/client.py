"""Claude Vision API client with retry logic and error classification.

This module provides the ClaudeVisionClient class for sending multi-image
requests to Claude's Vision API with robust error handling.
"""

import os
import sys
from typing import Any

import anthropic
from anthropic import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
    AuthenticationError,
    BadRequestError,
)


# Error classification for retry logic
TRANSIENT_ERRORS = (RateLimitError, InternalServerError, APIConnectionError, APITimeoutError)
PERMANENT_ERRORS = (AuthenticationError, BadRequestError)


def validate_environment() -> None:
    """Validate required environment variables and dependencies.

    Checks:
    - ANTHROPIC_API_KEY environment variable exists
    - anthropic package is installed

    Raises:
        SystemExit: If validation fails with clear error message
    """
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("Please set your API key: export ANTHROPIC_API_KEY='your-key'", file=sys.stderr)
        sys.exit(1)

    # Check anthropic SDK
    try:
        import anthropic
        print(f"Anthropic SDK version: {anthropic.__version__}")
    except ImportError:
        print("ERROR: anthropic package not installed", file=sys.stderr)
        print("Please install it: pip install anthropic", file=sys.stderr)
        sys.exit(1)


class ClaudeVisionClient:
    """Client for Claude Vision API with retry logic and error classification.

    This client handles multi-image vision requests with built-in retry logic
    for transient errors and fail-fast behavior for permanent errors.

    Attributes:
        client: The underlying Anthropic API client
        model: The Claude model to use (default: claude-sonnet-4-5)
        max_tokens: Maximum tokens for API response (default: 8192)

    Example:
        client = ClaudeVisionClient()
        result = client.extract_clauses(pdf_pages)
    """

    # Default configuration
    DEFAULT_MODEL = "claude-sonnet-4-5"
    DEFAULT_MAX_TOKENS = 8192
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 300.0  # 5 minutes for large multi-image requests

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Claude Vision client.

        Args:
            model: Claude model to use (default: claude-sonnet-4-5)
            max_tokens: Maximum tokens in response (default: 8192)
            max_retries: Number of retries for transient errors (default: 3)
            timeout: Request timeout in seconds (default: 300)

        Raises:
            AuthenticationError: If ANTHROPIC_API_KEY is missing or invalid
        """
        self.model = model
        self.max_tokens = max_tokens

        # Initialize the Anthropic client with retry configuration
        # API key is read automatically from ANTHROPIC_API_KEY environment variable
        self._client = anthropic.Anthropic(
            max_retries=max_retries,
            timeout=timeout,
        )

    @property
    def client(self) -> anthropic.Anthropic:
        """Get the underlying Anthropic client."""
        return self._client

    def extract_clauses(self, pdf_pages: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract clauses from PDF page images using Claude Vision.

        This method will be fully implemented in the next plan. Currently
        validates input and raises NotImplementedError.

        Args:
            pdf_pages: List of page dictionaries from PDFConverter.convert()
                Each dict contains: page_number, image_base64, width, height, size_kb

        Returns:
            Dictionary with extracted clauses:
            {
                "clauses": [
                    {"page": int, "clause_number": str, "text": str},
                    ...
                ]
            }

        Raises:
            ValueError: If pdf_pages is empty or invalid
            NotImplementedError: This method is not yet implemented
        """
        # Validate input
        if not pdf_pages:
            raise ValueError("pdf_pages cannot be empty")

        if not isinstance(pdf_pages, list):
            raise ValueError("pdf_pages must be a list")

        # Validate each page has required fields
        required_fields = {"page_number", "image_base64"}
        for i, page in enumerate(pdf_pages):
            if not isinstance(page, dict):
                raise ValueError(f"pdf_pages[{i}] must be a dictionary")

            missing = required_fields - set(page.keys())
            if missing:
                raise ValueError(f"pdf_pages[{i}] missing required fields: {missing}")

        # Implementation will be added in next plan (02-02)
        raise NotImplementedError(
            "extract_clauses() will be implemented in plan 02-02. "
            f"Input validated: {len(pdf_pages)} pages ready for processing."
        )

    def _classify_error(self, error: Exception) -> str:
        """Classify an API error as transient or permanent.

        Args:
            error: The exception raised by the API call

        Returns:
            "transient" for errors that may succeed on retry,
            "permanent" for errors that will never succeed,
            "unknown" for unclassified errors
        """
        if isinstance(error, TRANSIENT_ERRORS):
            return "transient"
        elif isinstance(error, PERMANENT_ERRORS):
            return "permanent"
        elif isinstance(error, APIError):
            return "unknown"
        else:
            return "unknown"

    def _log_error(self, error: Exception, context: str = "") -> None:
        """Log an API error with request ID for debugging.

        Args:
            error: The exception to log
            context: Additional context about where the error occurred
        """
        error_type = self._classify_error(error)

        # Extract request ID if available
        request_id = "N/A"
        if hasattr(error, "response") and error.response is not None:
            request_id = error.response.headers.get("request-id", "N/A")

        print(
            f"API Error [{error_type}] {context}: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        print(f"  Request ID: {request_id}", file=sys.stderr)
