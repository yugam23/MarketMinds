"""
Input Sanitization Module
Provides functions to validate and sanitize user inputs.
"""
import re
from fastapi import HTTPException, status

def validate_symbol(symbol: str) -> str:
    """
    Validate and sanitize trading symbol.
    
    Rules:
    - Uppercase
    - 1-10 characters
    - Alphanumeric, hyphen, and period only
    
    Args:
        symbol: The stock/crypto symbol to validate
        
    Returns:
        Sanitized symbol string
        
    Raises:
        HTTPException(400): If symbol format is invalid
    """
    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol cannot be empty"
        )
        
    # Remove whitespace
    clean_symbol = symbol.strip().upper()
    
    # Check length
    if len(clean_symbol) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol too long (max 10 chars)"
        )
        
    # Check format (A-Z, 0-9, -, .)
    # Examples: AAPL, BTC-USD, RELIANCE.NS
    if not re.match(r'^[A-Z0-9.-]+$', clean_symbol):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid symbol format: {clean_symbol}"
        )
        
    return clean_symbol
