from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services import auth_service, spotify_api_service
from backend.exceptions.custom_exceptions import UserNotFoundError, RefreshTokenMissingError
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.services.token_cache import get_token_cache
from typing import Dict, Any
from backend.services.spotify_api_service import SpotifyTopItemType, SpotifyTimeRange
from backend.services.spotify_api_service import DEFAULT_SPOTIFY_LIMIT, MAX_SPOTIFY_LIMIT
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

async def get_spotify_access_token_for_authenticated_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    Dependency that retrieves a valid Spotify access token for the authenticated user.
    Uses cached token if available and valid, otherwise refreshes it.
    """
    cache = get_token_cache()
    
    # Try to get cached token first
    cached_token = cache.get(current_user.spotify_id)
    if cached_token:
        logger.debug(f"Using cached Spotify token for user {current_user.spotify_id}")
        return cached_token
    
    # No valid cached token, refresh it
    logger.info(f"Refreshing Spotify token for user {current_user.spotify_id}")
    try:
        # Refresh the user's Spotify access token using the stored refresh token
        token_data = await auth_service.refresh_user_spotify_access_token(db, current_user.spotify_id)
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour if not provided
        
        # Cache the new token
        cache.set(current_user.spotify_id, access_token, expires_in)
        
        return access_token
        
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
        logger.error(f"Failed to obtain Spotify access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to obtain Spotify access token: {e}"
        )


async def handle_spotify_api_call_with_retry(
    spotify_api_func,
    current_user: User,
    db: Session,
    *args,
    **kwargs
):
    """
    Wrapper function to handle Spotify API calls with automatic token refresh on 401.
    
    Args:
        spotify_api_func: The Spotify API function to call
        current_user: The authenticated user
        db: Database session
        *args, **kwargs: Arguments to pass to the spotify_api_func
        
    Returns:
        The result from the Spotify API call
        
    Raises:
        SpotifyAPIError: If the API call fails after retry
    """
    cache = get_token_cache()
    
    # Get the access token (might be cached)
    access_token = await get_spotify_access_token_for_authenticated_user(current_user, db)
    
    try:
        # Try the API call with current token
        return await spotify_api_func(access_token, *args, **kwargs)
        
    except spotify_api_service.SpotifyAPIError as e:
        # If we get a 401, the cached token might be invalid
        if e.status_code == 401:
            logger.warning(f"Got 401 from Spotify API for user {current_user.spotify_id}, invalidating cache and retrying")
            
            # Invalidate cached token
            cache.invalidate(current_user.spotify_id)
            
            # Force refresh a new token
            try:
                token_data = await auth_service.refresh_user_spotify_access_token(db, current_user.spotify_id)
                new_access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                
                # Cache the new token
                cache.set(current_user.spotify_id, new_access_token, expires_in)
                
                # Retry the API call with new token
                return await spotify_api_func(new_access_token, *args, **kwargs)
                
            except Exception as refresh_error:
                logger.error(f"Failed to refresh token after 401: {refresh_error}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh Spotify access token. Please re-authenticate."
                )
        
        # For other errors, re-raise
        raise

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
