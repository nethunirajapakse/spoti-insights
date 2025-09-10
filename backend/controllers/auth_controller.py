from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from backend.auth import spotify_auth
from backend.database.connection import get_db
from backend.services import user_service
from backend.schemas.user import UserCreate, UserResponse, SpotifyUser, SpotifyToken
from typing import Dict, Any
import httpx

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login():
    auth_url = spotify_auth.get_authorize_url()
    # In a real application, you might redirect directly or return the URL for the frontend to navigate
    return {"auth_url": auth_url}

@router.get("/spotify/callback", response_model=UserResponse)
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided."
        )

    try:
        # Exchange authorization code for tokens
        token_info: Dict[str, Any] = await spotify_auth.get_spotify_tokens(code)
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")

        if not access_token or not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Spotify tokens."
            )

        spotify_user_profile: Dict[str, Any] = await spotify_auth.get_spotify_user_profile(access_token)
        spotify_id = spotify_user_profile.get("id")
        display_name = spotify_user_profile.get("display_name")
        email = spotify_user_profile.get("email")

        if not spotify_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Spotify user ID."
            )

        db_user = user_service.get_user_by_spotify_id(db, spotify_id)

        if db_user:
            updated_user = user_service.update_user_login_and_token(
                db, spotify_id, refresh_token, display_name, email
            )
            return updated_user
        else:
            new_user = UserCreate(
                spotify_id=spotify_id,
                display_name=display_name,
                email=email,
                refresh_token=refresh_token 
            )
            created_user = user_service.create_user(db, new_user)
            return created_user

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Spotify API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Example endpoint to get a new access token using the stored refresh token
@router.post("/spotify/refresh_access_token", response_model=SpotifyToken)
async def refresh_access_token_endpoint(spotify_id: str, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_spotify_id(db, spotify_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token not found for this user. User needs to re-authenticate.")

    try:
        new_tokens = await spotify_auth.refresh_spotify_token(db_user.refresh_token)
        # Optionally, update the refresh token if Spotify returns a new one (though not common for Spotify)
        # if "refresh_token" in new_tokens and new_tokens["refresh_token"] != db_user.refresh_token:
        #     user_service.update_user_login_and_token(db, spotify_id, new_tokens["refresh_token"])
        return new_tokens
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Spotify API refresh token error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token refresh: {str(e)}"
        )
