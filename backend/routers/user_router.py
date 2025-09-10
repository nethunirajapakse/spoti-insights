from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.services import user_service
from backend.schemas.user import UserResponse
from backend.database.connection import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{spotify_id}", response_model=UserResponse)
def get_user_endpoint(spotify_id: str, db: Session = Depends(get_db)):
    user = user_service.get_user_by_spotify_id(db, spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
