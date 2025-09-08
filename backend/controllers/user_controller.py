from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.services import user_service
from backend.schemas.user import UserBase, UserResponse
from backend.database.connection import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{spotify_id}", response_model=UserResponse)
def get_user_endpoint(spotify_id: str, db: Session = Depends(get_db)):
    user = user_service.get_user_by_spotify_id(db, spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse)
def create_user_endpoint(user: UserBase, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_spotify_id(db, user.spotify_id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    return user_service.create_user(db, user, refresh_token="dummy_token")
