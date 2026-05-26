import httpx
from typing import Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

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

_spotify_client: httpx.AsyncClient = None


def init_spotify_client():
    """
    Initializes the global httpx.AsyncClient for Spotify API calls.
    This should be called once during application startup.
    """
    global _spotify_client
    if _spotify_client is None:
        _spotify_client = httpx.AsyncClient(base_url=SPOTIFY_API_BASE_URL)


async def close_spotify_client():
    """
    Closes the global httpx.AsyncClient.
    This should be called once during application shutdown.
    """
    global _spotify_client
    if _spotify_client is not None:
        await _spotify_client.aclose()
        _spotify_client = None


async def _make_spotify_request(
    access_token: str,
    method: str,
    url_path: str,
    params: Dict = None,
    json_data: Dict = None,
) -> Dict[str, Any]:
    """Internal helper to make authenticated requests to the Spotify API."""
    if _spotify_client is None:
        logger.warning("Spotify HTTP client not initialized. Initializing now.")
        init_spotify_client()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = await _spotify_client.request(
            method,
            url_path,
            headers=headers,
            params=params,
            json=json_data,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        try:
            error_message = e.response.json().get("error", {}).get("message", e.response.text)
        except ValueError:
            error_message = e.response.text
        detail = f"Spotify API error ({e.response.status_code}): {error_message}"
        raise SpotifyAPIError(detail, e.response.status_code, e.response.text)
    except httpx.RequestError as e:
        raise SpotifyAPIError(f"Network error while requesting Spotify API: {e}")
    except Exception as e:
        raise SpotifyAPIError(f"An unexpected error occurred during Spotify API call: {e}")


async def get_user_top_items(
    access_token: str,
    item_type: SpotifyTopItemType,
    time_range: SpotifyTimeRange = SpotifyTimeRange.MEDIUM_TERM,
    limit: int = DEFAULT_SPOTIFY_LIMIT,
) -> Dict[str, Any]:
    """Fetches a user's top artists or tracks."""
    if not (1 <= limit <= MAX_SPOTIFY_LIMIT):
        raise ValueError(
            f"Limit for top items must be between 1 and {MAX_SPOTIFY_LIMIT} (inclusive)."
        )

    params = {
        "time_range": time_range.value,
        "limit": limit,
    }
    return await _make_spotify_request(
        access_token, "GET", f"/me/top/{item_type.value}", params=params
    )


async def get_user_playlists(
    access_token: str,
    limit: int = DEFAULT_SPOTIFY_LIMIT,
    offset: int = 0,
) -> Dict[str, Any]:
    """Fetches a user's playlists."""
    if not (1 <= limit <= MAX_SPOTIFY_LIMIT):
        raise ValueError(
            f"Limit for playlists must be between 1 and {MAX_SPOTIFY_LIMIT} (inclusive)."
        )

    params = {
        "limit": limit,
        "offset": offset,
    }
    return await _make_spotify_request(access_token, "GET", "/me/playlists", params=params)


async def get_recently_played_tracks(
    access_token: str,
    limit: int = DEFAULT_SPOTIFY_LIMIT,
    after: Optional[int] = None,
    before: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetches a user's recently played tracks.

    Args:
        access_token: The user's Spotify access token.
        limit: The maximum number of tracks to return (1-50).
        after: Optional Unix-ms timestamp. Returns plays AFTER this time.
        before: Optional Unix-ms timestamp. Returns plays BEFORE this time.
                Spotify treats `after` and `before` as mutually exclusive;
                if both are provided, `after` takes precedence.

    Returns:
        A dictionary containing the user's recently played tracks.

    Raises:
        ValueError: If the limit is out of the valid range.
        SpotifyAPIError: If the API call fails.
    """
    if not (1 <= limit <= MAX_SPOTIFY_LIMIT):
        raise ValueError(
            f"Limit for recently played tracks must be between 1 and {MAX_SPOTIFY_LIMIT} (inclusive)."
        )

    params: Dict[str, Any] = {"limit": limit}
    if after is not None:
        params["after"] = after
    elif before is not None:
        params["before"] = before

    return await _make_spotify_request(
        access_token,
        "GET",
        "/me/player/recently-played",
        params=params,
    )


async def get_user_profile(access_token: str) -> Dict[str, Any]:
    """Fetches the current user's profile information."""
    return await _make_spotify_request(access_token, "GET", "/me")
