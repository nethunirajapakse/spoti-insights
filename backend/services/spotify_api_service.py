import httpx
from typing import Dict, Any

SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

class SpotifyAPIError(Exception):
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.message = message

async def _make_spotify_request(access_token: str, method: str, url_path: str, params: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
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
                json=json_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            detail = f"Spotify API error ({e.response.status_code}): {e.response.text}"
            raise SpotifyAPIError(detail, e.response.status_code, e.response.text)
        except httpx.RequestError as e:
            raise SpotifyAPIError(f"Network error while requesting Spotify API: {e}")
        except Exception as e:
            raise SpotifyAPIError(f"An unexpected error occurred during Spotify API call: {e}")

async def get_user_top_items(access_token: str, item_type: str, time_range: str = "medium_term", limit: int = 10) -> Dict[str, Any]:
    if item_type not in ["artists", "tracks"]:
        raise ValueError("item_type must be 'artists' or 'tracks'")
    if time_range not in ["long_term", "medium_term", "short_term"]:
        raise ValueError("time_range must be 'long_term', 'medium_term', or 'short_term'")

    params = {
        "time_range": time_range,
        "limit": limit
    }
    return await _make_spotify_request(access_token, "GET", f"/me/top/{item_type}", params=params)

async def get_user_playlists(access_token: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    params = {
        "limit": limit,
        "offset": offset
    }
    return await _make_spotify_request(access_token, "GET", "/me/playlists", params=params)

async def get_recently_played_tracks(access_token: str, limit: int = 20) -> Dict[str, Any]:
    params = {
        "limit": limit
    }
    return await _make_spotify_request(access_token, "GET", "/me/player/recently-played", params=params)

async def get_user_profile(access_token: str) -> Dict[str, Any]:
    return await _make_spotify_request(access_token, "GET", "/me")
