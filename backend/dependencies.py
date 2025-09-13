from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.auth.jwt_utils import decode_access_token
from backend.services import user_service
from backend.models.user import User
from backend.exceptions import UserNotFoundError

security_scheme = HTTPBearer(scheme_name="BearerAuth") 

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user based on a JWT.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    spotify_id: str = payload.get("sub")
    
    if spotify_id is None:
        raise credentials_exception
    
    try:
        user = user_service.get_user_by_spotify_id(db, spotify_id)
    except UserNotFoundError:
        raise credentials_exception
    
    return user
