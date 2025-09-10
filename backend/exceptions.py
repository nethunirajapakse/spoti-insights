class SpotifyAuthError(Exception):
    """Base exception for Spotify authentication related errors."""
    pass

class AuthorizationCodeMissingError(SpotifyAuthError):
    """Raised when the Spotify authorization code is missing."""
    def __init__(self, message="Authorization code not provided."):
        self.message = message
        super().__init__(self.message)

class SpotifyTokensError(SpotifyAuthError):
    """Raised when Spotify access or refresh tokens cannot be retrieved."""
    def __init__(self, message="Failed to retrieve Spotify tokens."):
        self.message = message
        super().__init__(self.message)

class SpotifyUserIDMissingError(SpotifyAuthError):
    """Raised when the Spotify user ID cannot be retrieved from the profile."""
    def __init__(self, message="Failed to retrieve Spotify user ID."):
        self.message = message
        super().__init__(self.message)

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database."""
    def __init__(self, message="User not found."):
        self.message = message
        super().__init__(self.message)

class RefreshTokenMissingError(SpotifyAuthError):
    """Raised when a user's refresh token is missing in the database."""
    def __init__(self, message="Refresh token not found for this user. User needs to re-authenticate."):
        self.message = message
        super().__init__(self.message)