"""
Token caching module for Spotify access tokens.
Caches tokens in memory with expiry tracking to avoid unnecessary refreshes.
"""
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
import threading

class TokenCache:
    """
    Thread-safe in-memory cache for Spotify access tokens.
    Stores tokens with expiry times to minimize API calls.
    """
    
    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def get(self, user_id: str) -> Optional[str]:
        """
        Retrieve a valid access token from cache.
        
        Args:
            user_id: The user's ID (spotify_id or internal ID)
            
        Returns:
            Valid access token if cached and not expired, None otherwise
        """
        with self._lock:
            if user_id not in self._cache:
                return None
            
            cached_data = self._cache[user_id]
            
            # Check if token has expired based on precomputed expires_at (which includes a dynamic safety buffer from set)
            if datetime.now(timezone.utc) >= cached_data['expires_at']:
                # Token expired, remove from cache
                del self._cache[user_id]
                return None
            
            return cached_data['access_token']
    
    def set(self, user_id: str, access_token: str, expires_in: int):
        """
        Store or update a user's access token in the cache with an adjusted expiry time.

        Args:
            user_id: The user's ID (spotify_id or internal ID).
            access_token: The Spotify access token to cache.
            expires_in: The token lifetime in seconds as reported by Spotify.

        Buffer logic:
            To reduce the risk of using an access token that is about to expire,
            a safety buffer is subtracted from the provided lifetime before
            computing the cached expiry time:

            - Start with 10% of the reported lifetime (expires_in * 0.1).
            - Clamp this requested buffer to the range [10, 300] seconds.
            - Ensure the final buffer is never more than half of the total
              lifetime (expires_in / 2).

            The effective lifetime stored in the cache is:
                max(1, expires_in - buffer_seconds)
            so that the token is considered expired slightly before Spotify
            would report it as expired, and it is never shorter than 1 second.
        """
        with self._lock:
            # Use 10% of lifetime as buffer, but keep it between 10s and 300s
            # And ensure the buffer is never more than half the total lifetime
            requested_buffer = max(10, min(300, int(expires_in * 0.1)))
            buffer_seconds = min(requested_buffer, expires_in // 2)

            effective_lifetime = max(1, expires_in - buffer_seconds)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=effective_lifetime)
            
            self._cache[user_id] = {
                'access_token': access_token,
                'expires_at': expires_at
            }

    def invalidate(self, user_id: str):
        """
        Remove a token from cache (e.g., after logout or token revocation).
        
        Args:
            user_id: The user's ID (spotify_id or internal ID)
        """
        with self._lock:
            if user_id in self._cache:
                del self._cache[user_id]
    
    def clear(self):
        """Clear all cached tokens."""
        with self._lock:
            self._cache.clear()

# Global cache instance
_token_cache = TokenCache()

def get_token_cache() -> TokenCache:
    """Get the global token cache instance."""
    return _token_cache