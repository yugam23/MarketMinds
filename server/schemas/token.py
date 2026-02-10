"""
Token Schemas
Pydantic models for JWT tokens.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Basic JWT token response."""

    access_token: str
    token_type: str


class TokenWithRefresh(BaseModel):
    """JWT token response with refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class TokenData(BaseModel):
    """Token payload data."""

    email: str | None = None
    token_type: str | None = None  # "access" or "refresh"
