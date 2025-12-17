from sqlalchemy.orm import Session
from backend.services import spotify_auth_service, user_service
from backend.api.schemas.user import UserCreate
from backend.core.jwt_utils import create_access_token, create_refresh_token
from typing import Dict, Any
from backend.exceptions.custom_exceptions import (
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError,
    UserNotFoundError,
    RefreshTokenMissingError
)

async def handle_spotify_callback(code: str, db: Session):
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
    Refreshes the Spotify access token for a given user.
    Raises UserNotFoundError or RefreshTokenMissingError on failure.
    """
    db_user = user_service.get_user_by_spotify_id(db, spotify_id)

    if not db_user.spotify_refresh_token:
        raise RefreshTokenMissingError()

    new_tokens = await spotify_auth_service.refresh_spotify_token(db_user.spotify_refresh_token)

    if "refresh_token" in new_tokens and new_tokens["refresh_token"] != db_user.spotify_refresh_token:
        user_service.update_user_refresh_token(db, spotify_id, new_tokens["refresh_token"])

    return new_tokens
