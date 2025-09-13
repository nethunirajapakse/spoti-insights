import httpx
from typing import Dict, Any
from enum import Enum

SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors."""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.message = message

class SpotifyTimeRange(Enum):
    LONG_TERM = "long_term"
    MEDIUM_TERM = "medium_term"
    SHORT_TERM = "short_term"

class SpotifyTopItemType(Enum):
    ARTISTS = "artists"
    TRACKS = "tracks"

DEFAULT_SPOTIFY_LIMIT = 20
MAX_SPOTIFY_LIMIT = 50

async def _make_spotify_request(
    access_token: str,
    method: str,
    url_path: str,
    params: Dict = None,
    json_data: Dict = None
) -> Dict[str, Any]:
    """
    Internal helper to make authenticated requests to the Spotify API.

    Args:
        access_token: The user's Spotify access token.
        method: The HTTP method (e.g., "GET", "POST").
        url_path: The specific API endpoint path (e.g., "/me/top/artists").
        params: Optional dictionary of query parameters.
        json_data: Optional dictionary for JSON request body.

    Returns:
        The JSON response from the Spotify API.

    Raises:
        SpotifyAPIError: If the API call fails or a network error occurs.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method,
                f"{SPOTIFY_API_BASE_URL}{url_path}",
                headers=headers,
                params=params,
                json=json_data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Try to extract error message from JSON, fallback to response text if not JSON
            try:
                error_message = e.response.json().get('error', {}).get('message', e.response.text)
            except ValueError:
                error_message = e.response.text
            detail = (
                f"Spotify API error ({e.response.status_code}): {error_message}"
            )
            raise SpotifyAPIError(detail, e.response.status_code, e.response.text)
        except httpx.RequestError as e:
            raise SpotifyAPIError(f"Network error while requesting Spotify API: {e}")
        except Exception as e:
            raise SpotifyAPIError(f"An unexpected error occurred during Spotify API call: {e}")

async def get_user_top_items(
    access_token: str,
    item_type: SpotifyTopItemType,
    time_range: SpotifyTimeRange = SpotifyTimeRange.MEDIUM_TERM,
    limit: int = DEFAULT_SPOTIFY_LIMIT
) -> Dict[str, Any]:
    """
    Fetches a user's top artists or tracks.

    Args:
        access_token: The user's Spotify access token.
        item_type: The type of item to fetch (artists or tracks).
        time_range: Over what time frame the affinities are computed.
                    ('long_term', 'medium_term', 'short_term').
        limit: The maximum number of items to return (1-50).

    Returns:
        A dictionary containing the user's top items.

    Raises:
        ValueError: If the limit is out of the valid range.
        SpotifyAPIError: If the API call fails.
    """
    if not (1 <= limit <= MAX_SPOTIFY_LIMIT):
        raise ValueError(f"Limit for top items must be between 1 and {MAX_SPOTIFY_LIMIT} (inclusive).")

    params = {
        "time_range": time_range.value,
        "limit": limit
    }
    return await _make_spotify_request(access_token, "GET", f"/me/top/{item_type.value}", params=params)

async def get_user_playlists(
    access_token: str,
    limit: int = DEFAULT_SPOTIFY_LIMIT,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Fetches a user's playlists.

    Args:
        access_token: The user's Spotify access token.
        limit: The maximum number of playlists to return (1-50).
        offset: The index of the first playlist to return.

    Returns:
        A dictionary containing the user's playlists.

    Raises:
        ValueError: If the limit is out of the valid range.
        SpotifyAPIError: If the API call fails.
    """
    if not (1 <= limit <= MAX_SPOTIFY_LIMIT):
        raise ValueError(f"Limit for playlists must be between 1 and {MAX_SPOTIFY_LIMIT} (inclusive).")

    params = {
        "limit": limit,
        "offset": offset
    }
    return await _make_spotify_request(access_token, "GET", "/me/playlists", params=params)

async def get_recently_played_tracks(
    access_token: str,
    limit: int = DEFAULT_SPOTIFY_LIMIT
) -> Dict[str, Any]:
    """
    Fetches a user's recently played tracks.

    Args:
        access_token: The user's Spotify access token.
        limit: The maximum number of tracks to return (1-50).

    Returns:
        A dictionary containing the user's recently played tracks.

    Raises:
        ValueError: If the limit is out of the valid range.
        SpotifyAPIError: If the API call fails.
    """
    if not (1 <= limit <= MAX_SPOTIFY_LIMIT):
        raise ValueError(f"Limit for recently played tracks must be between 1 and {MAX_SPOTIFY_LIMIT} (inclusive).")
    params = {
        "limit": limit
    }
    return await _make_spotify_request(access_token, "GET", "/me/player/recently-played", params=params)

async def get_user_profile(access_token: str) -> Dict[str, Any]:
    """
    Fetches the current user's profile information.

    Args:
        access_token: The user's Spotify access token.

    Returns:
        A dictionary containing the user's profile information.

    Raises:
        SpotifyAPIError: If the API call fails.
    """
    return await _make_spotify_request(access_token, "GET", "/me")
