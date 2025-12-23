from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.core.jwt_utils import decode_access_token
from backend.services import user_service
from backend.models.user import User
from backend.exceptions.custom_exceptions import UserNotFoundError

async def get_current_user(
    request: Request, # Inject the request to access cookies
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user based on JWT in cookies.
    """
    # 1. Look for the token in the cookies
    token = request.cookies.get("access_token")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
    
    if not token:
        raise credentials_exception

    try:
        # 2. Decode the token (your existing logic)
        payload = decode_access_token(token)
        spotify_id: str = payload.get("sub")
        
        if spotify_id is None:
            raise credentials_exception
        
        # 3. Fetch user from DB
        user = user_service.get_user_by_spotify_id(db, spotify_id)
        return user
        
    except (UserNotFoundError, Exception):
        # Exception covers decoding errors (expired, invalid, etc.)
        raise credentials_exception
    