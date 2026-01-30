"""Claude Vision API client with retry logic and error classification.

This module provides the ClaudeVisionClient class for sending multi-image
requests to Claude's Vision API with robust error handling.
"""

import os
import sys
from typing import Any


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
