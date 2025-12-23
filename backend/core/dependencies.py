from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.core.jwt_utils import decode_access_token
from backend.services import user_service
from backend.models.user import User
from backend.exceptions.custom_exceptions import UserNotFoundError

async def get_current_user(
    request: Request, 
    db: Session = Depends(get_db)
) -> User:
    """
    Hybrid dependency: checks for JWT in the Authorization Header first,
    then falls back to the 'access_token' Cookie.
    """
    token = None

    # 1. Try to extract token from Authorization Header (Postman/Mobile)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # 2. If no header, try to extract from Cookies (Browser)
    if not token:
        token = request.cookies.get("access_token")

    # If still no token, the user is not logged in
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 3. Decode the token
        payload = decode_access_token(token)
        spotify_id: str = payload.get("sub")
        
        if spotify_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
        
        # 4. Fetch the user from the database
        user = user_service.get_user_by_spotify_id(db, spotify_id)
        return user

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    except Exception as e:
        # Catch expired tokens, signature errors, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )
    