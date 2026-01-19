from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services import auth_service, spotify_api_service
from backend.exceptions.custom_exceptions import UserNotFoundError, RefreshTokenMissingError
from backend.core.dependencies import get_current_user
from backend.models.user import User
from typing import Dict, Any
from backend.services.spotify_api_service import SpotifyTopItemType, SpotifyTimeRange
from backend.services.spotify_api_service import DEFAULT_SPOTIFY_LIMIT, MAX_SPOTIFY_LIMIT
from typing import Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

from backend.database.redis import get_redis

async def get_spotify_access_token_for_authenticated_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
) -> str:
    user_id = current_user.spotify_id
    token_key = f"token:{user_id}"
    lock_key = f"lock:refresh:{user_id}"

    token = await redis.get(token_key)
    if token:
        return token
    async with redis.lock(lock_key, timeout=10):
        token = await redis.get(token_key)
        if token:
            return token

        logger.info(f"Refreshing Spotify token for {user_id}")
        try:
            token_data = await auth_service.refresh_user_spotify_access_token(db, user_id)
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)

            # 3. Store in Redis with a 1-minute safety buffer
            # This handles the "Buffer Logic" problem automatically
            await redis.set(token_key, access_token, ex=max(1, expires_in - 60))
            
            return access_token
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            raise HTTPException(status_code=401, detail="Spotify refresh failed")

@router.get("/top-items/{item_type}", summary="Get a user's top artists or tracks")
async def get_user_top_items_endpoint(
    item_type: SpotifyTopItemType,
    time_range: SpotifyTimeRange = Query(SpotifyTimeRange.MEDIUM_TERM, description="Over what time frame the data is calculated. Valid values: long_term, medium_term, short_term"),
    limit: int = Query(DEFAULT_SPOTIFY_LIMIT, ge=1, le=MAX_SPOTIFY_LIMIT, description=f"The number of entities to return. Default: {DEFAULT_SPOTIFY_LIMIT}. Minimum: 1. Maximum: {MAX_SPOTIFY_LIMIT}."),
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
    limit: int = Query(DEFAULT_SPOTIFY_LIMIT, ge=1, le=MAX_SPOTIFY_LIMIT, description=f"The number of playlists to return. Default: {DEFAULT_SPOTIFY_LIMIT}. Minimum: 1. Maximum: {MAX_SPOTIFY_LIMIT}."),
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
    limit: int = Query(DEFAULT_SPOTIFY_LIMIT, ge=1, le=MAX_SPOTIFY_LIMIT, description=f"The number of tracks to return. Default: {DEFAULT_SPOTIFY_LIMIT}. Minimum: 1. Maximum: {MAX_SPOTIFY_LIMIT}."),
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
