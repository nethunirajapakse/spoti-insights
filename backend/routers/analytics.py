from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services import auth_service, spotify_api_service
from backend.exceptions import UserNotFoundError, RefreshTokenMissingError
from backend.dependencies import get_current_user 
from backend.models.user import User 
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

async def get_spotify_access_token_for_authenticated_user(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> str:
    """
    Dependency that retrieves a valid Spotify access token for the authenticated user.
    It uses the refresh token stored in the database.
    """
    try:
        # Refresh the user's Spotify access token using the stored refresh token.
        token_data = await auth_service.refresh_user_spotify_access_token(db, current_user.spotify_id)
        return token_data["access_token"]
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authenticated user '{current_user.spotify_id}' not found in DB."
        )
    except RefreshTokenMissingError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Refresh token missing for user '{current_user.spotify_id}'. Please re-authenticate with Spotify."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to obtain Spotify access token: {e}"
        )


@router.get("/top-items/{item_type}", summary="Get a user's top artists or tracks")
async def get_user_top_items_endpoint(
    item_type: str, 
    time_range: str = Query("medium_term", description="Over what time frame the data is calculated. Valid values: long_term, medium_term, short_term"),
    limit: int = Query(10, ge=1, le=50, description="The number of entities to return. Default: 10. Minimum: 1. Maximum: 50."),
    access_token: str = Depends(get_spotify_access_token_for_authenticated_user)
) -> Dict[str, Any]:
    """
    Retrieves the authenticated user's top artists or tracks from Spotify.
    """
    try:
        top_items = await spotify_api_service.get_user_top_items(access_token, item_type, time_range, limit)
        return top_items
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/playlists", summary="Get a user's playlists")
async def get_user_playlists_endpoint(
    limit: int = Query(20, ge=1, le=50, description="The number of playlists to return. Default: 20. Minimum: 1. Maximum: 50."),
    offset: int = Query(0, ge=0, description="The index of the first playlist to return."),
    access_token: str = Depends(get_spotify_access_token_for_authenticated_user) 
) -> Dict[str, Any]:
    """
    Retrieves the authenticated user's playlists from Spotify.
    """
    try:
        playlists = await spotify_api_service.get_user_playlists(access_token, limit, offset)
        return playlists
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/recently-played", summary="Get a user's recently played tracks")
async def get_user_recently_played_endpoint(
    limit: int = Query(20, ge=1, le=50, description="The number of tracks to return. Default: 20. Minimum: 1. Maximum: 50."),
    access_token: str = Depends(get_spotify_access_token_for_authenticated_user)
) -> Dict[str, Any]:
    """
    Retrieves the authenticated user's recently played tracks from Spotify.
    """
    try:
        recently_played = await spotify_api_service.get_recently_played_tracks(access_token, limit)
        return recently_played
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")