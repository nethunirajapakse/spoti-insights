from sqlalchemy.orm import Session
from backend.auth import spotify_auth
from backend.services import user_service
from backend.schemas.user import UserCreate, UserResponse
from typing import Dict, Any
from backend.exceptions import (
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError,
    UserNotFoundError,
    RefreshTokenMissingError
)
from backend.auth.jwt_utils import create_access_token

async def handle_spotify_callback(code: str, db: Session) -> UserResponse:
    """
    Handles the Spotify authentication callback, exchanges code for tokens,
    fetches user profile, and creates or updates the user in the database.
    Generates and returns a JWT for session management.
    """
    if not code:
        raise AuthorizationCodeMissingError()

    token_info: Dict[str, Any] = await spotify_auth.get_spotify_tokens(code)
    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")

    if not access_token or not refresh_token:
        raise SpotifyTokensError()

    spotify_user_profile: Dict[str, Any] = await spotify_auth.get_spotify_user_profile(access_token)
    spotify_id = spotify_user_profile.get("id")
    display_name = spotify_user_profile.get("display_name")
    email = spotify_user_profile.get("email")

    if not spotify_id:
        raise SpotifyUserIDMissingError()

    try:
        db_user = user_service.get_user_by_spotify_id(db, spotify_id)
        updated_user = user_service.update_user_login_and_token(
            db, spotify_id, refresh_token, display_name, email
        )
        db_user = updated_user
    except UserNotFoundError:
        new_user_data = UserCreate(
            spotify_id=spotify_id,
            display_name=display_name,
            email=email,
            refresh_token=refresh_token
        )
        created_user = user_service.create_user(db, new_user_data)
        db_user = created_user 

    jwt_data = {"sub": db_user.spotify_id, "user_id": db_user.id}
    jwt_token = create_access_token(data=jwt_data)

    response = UserResponse.from_orm(db_user)
    response.token = jwt_token
    return response


async def refresh_user_spotify_access_token(db: Session, spotify_id: str) -> Dict[str, Any]:
    """
    Refreshes the Spotify access token for a given user.
    Raises UserNotFoundError or RefreshTokenMissingError on failure.
    """
    db_user = user_service.get_user_by_spotify_id(db, spotify_id)

    if not db_user.refresh_token:
        raise RefreshTokenMissingError()

    new_tokens = await spotify_auth.refresh_spotify_token(db_user.refresh_token)

    if not new_tokens:
        raise SpotifyTokensError("No tokens returned from Spotify during refresh.")
    if "access_token" not in new_tokens:
        raise SpotifyTokensError("access_token missing from Spotify response during refresh.")

    if "refresh_token" in new_tokens and new_tokens["refresh_token"] != db_user.refresh_token:
        user_service.update_user_refresh_token(db, spotify_id, new_tokens["refresh_token"])

    return new_tokens
