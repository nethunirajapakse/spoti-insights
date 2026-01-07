from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.schemas.user import UserResponse
from backend.database.connection import get_db
from backend.models.user import User
from backend.core.dependencies import get_current_user
from backend.services import user_service
from backend.exceptions.custom_exceptions import UserNotFoundError

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the profile of the currently authenticated user.
    The user is identified via the 'access_token' cookie.
    """
    return current_user

@router.get("/{spotify_id}", response_model=UserResponse)
def get_user_endpoint(spotify_id: str, db: Session = Depends(get_db)):
    try:
        user = user_service.get_user_by_spotify_id(db, spotify_id)
        return user
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))