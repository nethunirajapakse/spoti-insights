from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate
from datetime import datetime, timezone
from typing import Optional
from backend.exceptions import UserNotFoundError

def get_user_by_spotify_id(db: Session, spotify_id: str) -> User:
    """
    Retrieves a user by their Spotify ID.
    Raises UserNotFoundError if the user does not exist.
    """
    user = db.query(User).filter(User.spotify_id == spotify_id).first()
    if not user:
        raise UserNotFoundError(f"User with Spotify ID '{spotify_id}' not found.")
    return user

def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        spotify_id=user.spotify_id,
        refresh_token=user.refresh_token,
        display_name=user.display_name,
        email=user.email,
        last_login=datetime.now(timezone.utc)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_login_and_token(
    db: Session,
    spotify_id: str,
    refresh_token: str,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
) -> User:
    """
    Updates a user's login time, refresh token, and optionally display name/email.
    Raises UserNotFoundError if the user does not exist.
    """
    db_user = get_user_by_spotify_id(db, spotify_id)

    db_user.refresh_token = refresh_token
    db_user.last_login = datetime.now(timezone.utc)
    if display_name is not None:
        db_user.display_name = display_name
    if email is not None:
        db_user.email = email
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_refresh_token(db: Session, spotify_id: str, new_refresh_token: str) -> User:
    """
    Updates only the refresh token for a given user.
    Raises UserNotFoundError if the user does not exist.
    """
    db_user = get_user_by_spotify_id(db, spotify_id)

    db_user.refresh_token = new_refresh_token
    db.commit()
    db.refresh(db_user)
    return db_user
