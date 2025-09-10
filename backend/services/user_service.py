from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate
from datetime import datetime, timezone
from typing import Optional

def get_user_by_spotify_id(db: Session, spotify_id: str):
    return db.query(User).filter(User.spotify_id == spotify_id).first()

def create_user(db: Session, user: UserCreate): 
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

def update_user_login_and_token(db: Session, spotify_id: str, refresh_token: str, display_name: Optional[str] = None, email: Optional[str] = None):
    db_user = get_user_by_spotify_id(db, spotify_id)
    if db_user:
        db_user.refresh_token = refresh_token
        db_user.last_login = datetime.now(timezone.utc)
        if display_name:
            db_user.display_name = display_name
        if email:
            db_user.email = email
        db.commit()
        db.refresh(db_user)
    return db_user
