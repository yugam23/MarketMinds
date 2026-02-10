"""
Input sanitization utilities.
"""

import re


def validate_symbol(symbol: str) -> str:
    """
    Validate and sanitize trading symbol.

    Args:
        symbol: The stock/crypto symbol to validate

    Returns:
        The sanitized, uppercase symbol

    Raises:
        ValueError: If the symbol format is invalid
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty")

    # Remove whitespace
    symbol = symbol.strip().upper()

    # Only allow A-Z, 0-9, hyphen, and period
    # Length between 1 and 14 characters to support suffixes (e.g. RELIANCE.NS)
    if not re.match(r"^[A-Z0-9.-]{1,14}$", symbol):
        raise ValueError(f"Invalid symbol format: {symbol}")

    return symbol
