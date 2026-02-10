"""
Input Sanitization
Utilities for sanitizing user input.
"""

import bleach


def sanitize_text(text: str) -> str:
    """Sanitize text input to prevent XSS."""
    if not text:
        return ""
    return bleach.clean(text, strip=True)
