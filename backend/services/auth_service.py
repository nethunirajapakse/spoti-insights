from sqlalchemy.orm import Session
from backend.services import spotify_auth_service, user_service
from backend.schemas.user import UserCreate
from backend.core.jwt_utils import create_access_token, create_refresh_token, decode_access_token
from typing import Dict, Any
from backend.exceptions.custom_exceptions import (
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError,
    UserNotFoundError,
    RefreshTokenMissingError
)
import logging

logger = logging.getLogger(__name__)


async def handle_spotify_callback(code: str, db: Session):
    """
    Handle Spotify OAuth callback and create/update user.
    Returns JWT access token and refresh token.
    """
    if not code:
        raise AuthorizationCodeMissingError()

    # Exchange code for Spotify tokens
    token_info: Dict[str, Any] = await spotify_auth_service.get_spotify_tokens(code)
    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")

    if not access_token or not refresh_token:
        raise SpotifyTokensError()

    # Get Spotify profile
    profile: Dict[str, Any] = await spotify_auth_service.get_spotify_user_profile(access_token)
    spotify_id = profile.get("id")
    display_name = profile.get("display_name")
    email = profile.get("email")

    if not spotify_id:
        raise SpotifyUserIDMissingError()

    # Create or update user in DB
    try:
        db_user = user_service.get_user_by_spotify_id(db, spotify_id)
        db_user = user_service.update_user_login_and_token(
            db, spotify_id, refresh_token, display_name, email
        )
    except UserNotFoundError:
        new_user = UserCreate(
            spotify_id=spotify_id,
            display_name=display_name,
            email=email,
            spotify_refresh_token=refresh_token
        )
        db_user = user_service.create_user(db, new_user)

    jwt_token = create_access_token({"sub": db_user.spotify_id, "user_id": db_user.id})
    app_refresh_token = create_refresh_token({"sub": db_user.spotify_id, "user_id": db_user.id})

    return jwt_token, app_refresh_token

async def refresh_user_spotify_access_token(db: Session, spotify_id: str) -> Dict[str, Any]:
    """
    Refresh Spotify access token using stored refresh token.
    This is used when making Spotify API calls, not for our JWT tokens.
    """
    db_user = user_service.get_user_by_spotify_id(db, spotify_id)
    
    if not db_user.spotify_refresh_token:
        raise RefreshTokenMissingError()
    
    decrypted_token = user_service.get_decrypted_refresh_token(db_user)
    new_tokens = await spotify_auth_service.refresh_spotify_token(decrypted_token)
    
    if "refresh_token" in new_tokens:
        user_service.update_user_refresh_token(
            db, spotify_id, new_tokens["refresh_token"]
        )
    
    return new_tokens

async def refresh_access_token(refresh_token: str) -> dict:
    """
    Validates our application's refresh token and returns a new JWT access token.
    This is for refreshing the user's session in our app.
    """
    try:
        payload = decode_access_token(refresh_token)
        spotify_id = payload.get("sub")
        user_id = payload.get("user_id")

        if not spotify_id or not user_id:
            raise ValueError("Invalid token payload")
        
        access_token = create_access_token({
            "sub": spotify_id, 
            "user_id": user_id
        })
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    except Exception as e:
        logger.error(f"Failed to refresh access token: {str(e)}")
        raise Exception(f"Token refresh failed: {str(e)}")
