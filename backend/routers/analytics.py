from typing import Annotated, Any, Dict
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
import redis.asyncio as redis
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.redis import get_redis, RedisTokenCache
from backend.services import auth_service, spotify_api_service
from backend.exceptions.custom_exceptions import UserNotFoundError, RefreshTokenMissingError
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.services.spotify_api_service import (
    SpotifyTopItemType,
    SpotifyTimeRange,
    DEFAULT_SPOTIFY_LIMIT,
    MAX_SPOTIFY_LIMIT,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Typed dependency aliases.
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
RedisClient = Annotated[redis.Redis | None, Depends(get_redis)]


async def get_spotify_access_token_for_authenticated_user(
    current_user: CurrentUser,
    db: DbSession,
    redis_client: RedisClient,
) -> str:
    user_id = current_user.spotify_id
    cache = RedisTokenCache(redis_client)

    # 1. Fallback if Redis is down initially
    if not redis_client:
        logger.info("Bypassing cache for user %s (Redis Down)", user_id)
        token_data = await auth_service.refresh_user_spotify_access_token(db, user_id)
        return token_data["access_token"]

    # 2. Try Cache
    cached_token = await cache.get_token(user_id)
    if cached_token:
        return cached_token

    # 3. Refresh with Lock (and Lock Connection Fallback)
    try:
        async with cache.get_refresh_lock(user_id):
            # Double-check after acquiring lock
            cached_token = await cache.get_token(user_id)
            if cached_token:
                return cached_token

            token_data = await auth_service.refresh_user_spotify_access_token(db, user_id)
            access_token = token_data["access_token"]
            await cache.set_token(user_id, access_token, token_data.get("expires_in", 3600))
            return access_token

    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        # If lock fails due to Redis connection issue, proceed without lock
        logger.exception("Redis failed during lock for %s, proceeding to direct refresh", user_id)
        token_data = await auth_service.refresh_user_spotify_access_token(db, user_id)
        return token_data["access_token"]
    except UserNotFoundError as e:
        logger.exception("User not found during Spotify token refresh for %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e) or "User not found"
        )
    except RefreshTokenMissingError as e:
        logger.exception("Refresh token missing during Spotify token refresh for %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) or "Refresh token missing"
        )
    except Exception:
        logger.exception("Critical refresh failure for %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh Spotify token"
        )


SpotifyAccessToken = Annotated[str, Depends(get_spotify_access_token_for_authenticated_user)]


@router.get("/top-items/{item_type}", summary="Get a user's top artists or tracks")
async def get_user_top_items_endpoint(
    item_type: SpotifyTopItemType,
    access_token: SpotifyAccessToken,
    time_range: SpotifyTimeRange = Query(
        SpotifyTimeRange.MEDIUM_TERM,
        description="Over what time frame the data is calculated. Valid values: long_term, medium_term, short_term"
    ),
    limit: int = Query(
        DEFAULT_SPOTIFY_LIMIT,
        ge=1,
        le=MAX_SPOTIFY_LIMIT,
        description=f"The number of entities to return. Default: {DEFAULT_SPOTIFY_LIMIT}. Minimum: 1. Maximum: {MAX_SPOTIFY_LIMIT}."
    ),
) -> Dict[str, Any]:
    """
    Retrieves the authenticated user's top artists or tracks from Spotify.
    """
    try:
        top_items = await spotify_api_service.get_user_top_items(
            access_token, item_type, time_range, limit
        )
        return top_items
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.exception("Unexpected error in get_user_top_items")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/playlists", summary="Get a user's playlists")
async def get_user_playlists_endpoint(
    access_token: SpotifyAccessToken,
    limit: int = Query(
        DEFAULT_SPOTIFY_LIMIT,
        ge=1,
        le=MAX_SPOTIFY_LIMIT,
        description=f"The number of playlists to return. Default: {DEFAULT_SPOTIFY_LIMIT}. Minimum: 1. Maximum: {MAX_SPOTIFY_LIMIT}."
    ),
    offset: int = Query(
        0,
        ge=0,
        description="The index of the first playlist to return."
    ),
) -> Dict[str, Any]:
    """
    Retrieves the authenticated user's playlists from Spotify.
    """
    try:
        playlists = await spotify_api_service.get_user_playlists(access_token, limit, offset)
        return playlists
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.exception("Unexpected error in get_user_playlists")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/recently-played", summary="Get a user's recently played tracks")
async def get_user_recently_played_endpoint(
    access_token: SpotifyAccessToken,
    limit: int = Query(
        DEFAULT_SPOTIFY_LIMIT,
        ge=1,
        le=MAX_SPOTIFY_LIMIT,
        description=f"The number of tracks to return. Default: {DEFAULT_SPOTIFY_LIMIT}. Minimum: 1. Maximum: {MAX_SPOTIFY_LIMIT}."
    ),
) -> Dict[str, Any]:
    """
    Retrieves the authenticated user's recently played tracks from Spotify.
    """
    try:
        recently_played = await spotify_api_service.get_recently_played_tracks(access_token, limit)
        return recently_played
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.exception("Unexpected error in get_recently_played")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
