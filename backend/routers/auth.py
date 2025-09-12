from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.auth import spotify_auth
from backend.database.connection import get_db
from backend.services import auth_service
from backend.schemas.user import UserResponse, SpotifyToken, RefreshTokenRequest
import httpx
from backend.exceptions import ( 
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError,
    UserNotFoundError,
    RefreshTokenMissingError
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login():
    auth_url = spotify_auth.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback", response_model=UserResponse) # UserResponse now contains the JWT
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    try:
        user_response = await auth_service.handle_spotify_callback(code, db)
        return user_response
    except (AuthorizationCodeMissingError, SpotifyTokensError, SpotifyUserIDMissingError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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

# This endpoint refreshes the Spotify access token, NOT the JWT.
# Its utility might decrease if the get_spotify_access_token_for_authenticated_user
# dependency handles this internally.
@router.post(
    "/spotify/refresh_access_token",
    response_model=SpotifyToken,
    deprecated=True  
)
async def refresh_access_token_endpoint(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        new_tokens = await auth_service.refresh_user_spotify_access_token(db, request.spotify_id)
        return new_tokens
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RefreshTokenMissingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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