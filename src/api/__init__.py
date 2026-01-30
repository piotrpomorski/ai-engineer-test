"""Claude Vision API client package.

This package provides the interface for communicating with Claude's Vision API
to extract clauses from PDF document images.

Exports:
    - ClaudeVisionClient: Main client class for Vision API requests
    - validate_environment: Function to check API key and dependencies
"""

# Defer imports to avoid circular dependencies and allow module-level testing
__all__ = ["ClaudeVisionClient", "validate_environment"]


def __getattr__(name: str):
    """Lazy import of module contents."""
    if name == "ClaudeVisionClient":
        from src.api.client import ClaudeVisionClient
        return ClaudeVisionClient
    elif name == "validate_environment":
        from src.api.client import validate_environment
        return validate_environment
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
