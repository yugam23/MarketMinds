"""
MarketMinds API Dependencies
Common dependencies for FastAPI routes.
"""

from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.core.database import get_db


# Type alias for database session dependency
DBSession = Annotated[Session, Depends(get_db)]
