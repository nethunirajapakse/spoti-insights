import httpx
from typing import Dict, Any
from urllib.parse import urlencode
from backend.core.config import settings
from backend.exceptions.custom_exceptions import SpotifyTokensError
import logging

logger = logging.getLogger(__name__)

# Module-level constants so identical log messages aren't duplicated across
# the three Spotify HTTP helpers (Sonar flagged 3x duplication).
_SPOTIFY_TOKEN_EXCHANGE_FAILED_MSG = "Spotify token exchange failed: %s"
_SPOTIFY_NETWORK_ERROR_MSG = "Network error reaching Spotify: %s"


def get_authorize_url(state: str) -> str:
    """
    Builds the Spotify authorization URL.
    The caller is responsible for generating a cryptographically random state
    value, storing it (e.g. in a short-lived cookie), and passing it here so
    Spotify echoes it back in the callback for CSRF validation.
    """
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": settings.spotify_scopes,
        "state": state,
    }
    return f"{settings.spotify_auth_url}?{urlencode(params)}"


async def get_spotify_tokens(code: str) -> Dict[str, Any]:
    """Exchanges auth code for access/refresh tokens."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.spotify_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.spotify_redirect_uri,
                    "client_id": settings.spotify_client_id,
                    "client_secret": settings.spotify_client_secret,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(_SPOTIFY_TOKEN_EXCHANGE_FAILED_MSG, e.response.status_code)
        raise SpotifyTokensError()
    except httpx.RequestError:
        logger.exception(_SPOTIFY_NETWORK_ERROR_MSG, "get_spotify_tokens")
        raise SpotifyTokensError()


async def refresh_spotify_token(refresh_token: str) -> Dict[str, Any]:
    """Refreshes an expired access token."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.spotify_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.spotify_client_id,
                    "client_secret": settings.spotify_client_secret,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(_SPOTIFY_TOKEN_EXCHANGE_FAILED_MSG, e.response.status_code)
        raise SpotifyTokensError()
    except httpx.RequestError:
        logger.exception(_SPOTIFY_NETWORK_ERROR_MSG, "refresh_spotify_token")
        raise SpotifyTokensError()


async def get_spotify_user_profile(access_token: str) -> Dict[str, Any]:
    """Fetches the current user's Spotify profile."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.spotify_api_base_url}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning(_SPOTIFY_TOKEN_EXCHANGE_FAILED_MSG, e.response.status_code)
        raise SpotifyTokensError()
    except httpx.RequestError:
        logger.exception(_SPOTIFY_NETWORK_ERROR_MSG, "get_spotify_user_profile")
        raise SpotifyTokensError()
