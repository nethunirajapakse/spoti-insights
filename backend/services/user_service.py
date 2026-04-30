from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate
from datetime import datetime, timezone
from typing import Optional
from backend.exceptions.custom_exceptions import UserNotFoundError
from backend.services.encryption_service import encrypt_token, decrypt_token


def get_user_by_spotify_id(db: Session, spotify_id: str) -> User:
    """
    Retrieves a user by their Spotify ID.
    Raises UserNotFoundError if the user does not exist.
    """
    user = db.query(User).filter(User.spotify_id == spotify_id).first()
    if not user:
        raise UserNotFoundError(f"User with Spotify ID '{spotify_id}' not found.")
    return user


def get_user_by_spotify_id_or_none(db: Session, spotify_id: str) -> Optional[User]:
    """
    Retrieves a user by their Spotify ID.
    Returns None instead of raising if the user does not exist.
    Use this when you want an explicit if/else branch rather than
    exception-as-control-flow.
    """
    return db.query(User).filter(User.spotify_id == spotify_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        spotify_id=user.spotify_id,
        display_name=user.display_name,         # was missing in original
        email=user.email,
        spotify_refresh_token=encrypt_token(user.spotify_refresh_token),
        last_login=datetime.now(timezone.utc),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_login_and_token(
    db: Session,
    spotify_id: str,
    spotify_refresh_token: str,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
) -> User:
    """
    Updates a user's login time, Spotify refresh token, and optionally
    display name / email.
    Raises UserNotFoundError if the user does not exist.
    """
    db_user = get_user_by_spotify_id(db, spotify_id)
    db_user.spotify_refresh_token = encrypt_token(spotify_refresh_token)
    db_user.last_login = datetime.now(timezone.utc)
    if display_name:
        db_user.display_name = display_name
    if email:
        db_user.email = email               # was db_user.email typo in original
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_refresh_token(db: Session, spotify_id: str, new_token: str) -> User:
    db_user = get_user_by_spotify_id(db, spotify_id)
    db_user.spotify_refresh_token = encrypt_token(new_token)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_decrypted_refresh_token(db_user: User) -> str:
    """Decrypts and returns the stored Spotify refresh token."""
    return decrypt_token(db_user.spotify_refresh_token)
