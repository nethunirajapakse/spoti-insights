from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.services import user_service
from backend.schemas.user import UserResponse
from backend.database.connection import get_db
from backend.exceptions import UserNotFoundError

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{spotify_id}", response_model=UserResponse)
def get_user_endpoint(spotify_id: str, db: Session = Depends(get_db)):
    try:
        user = user_service.get_user_by_spotify_id(db, spotify_id)
        return user
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))