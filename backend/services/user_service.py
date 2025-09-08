from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserBase
from datetime import datetime

def get_user_by_spotify_id(db: Session, spotify_id: str):
    return db.query(User).filter(User.spotify_id == spotify_id).first()

def create_user(db: Session, user: UserBase, refresh_token: str):
    db_user = User(
        spotify_id=user.spotify_id,
        refresh_token=refresh_token,
        display_name=user.display_name,
        email=user.email,
        last_login=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
