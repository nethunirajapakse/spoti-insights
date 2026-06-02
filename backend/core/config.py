from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # App configuration
    app_name: str = Field(default="Spotify Analytics API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_description: str = Field(
        default="""
#### Provides authentication and analytics for Spotify users.

### Features
* **Authentication**: OAuth2 flow with Spotify
* **User Management**: Get user profiles and data  
* **Analytics**: Access top tracks, artists, playlists, and listening history

### Authentication
Most endpoints require authentication. Include your access token via:
- **Cookie**: `access_token` (automatically sent by browsers)
- **Header**: `Authorization: Bearer <your_token>` (for API clients)

### Getting Started
1. Use `/public/auth/spotify/login` to initiate OAuth flow
2. After successful authentication, you'll receive access and refresh tokens
3. Use the access token for authenticated endpoints
4. Refresh your token using `/public/auth/refresh` when it expires

### Rate Limiting
All endpoints are rate-limited to prevent abuse. Limits vary by endpoint.
        """,
        alias="APP_DESCRIPTION"
    )
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # OpenAPI/Swagger configuration
    docs_url: str = Field(default="/api/docs", alias="DOCS_URL")
    redoc_url: str = Field(default="/api/redoc", alias="REDOC_URL")
    openapi_url: str = Field(default="/api/openapi.json", alias="OPENAPI_URL")
    
    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")  # Required
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS and Cookies
    frontend_url: str = Field(alias="FRONTEND_URL")
    cookie_domain: Optional[str] = Field(default=None, alias="COOKIE_DOMAIN")

    # Cookie Expiration Times
    oauth_state_max_age: int = Field(default=300, alias="OAUTH_STATE_MAX_AGE")

    @property
    def access_token_max_age(self) -> int:
        """Cookie lifetime matches the JWT lifetime exactly."""
        return self.access_token_expire_minutes * 60

    @property
    def refresh_token_max_age(self) -> int:
        """Cookie lifetime matches the JWT lifetime exactly."""
        return self.refresh_token_expire_days * 86400

    # Database
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Redis 
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # Redis configuration (caching and rate limiting)
    redis_max_connections: int = Field(default=20, alias="REDIS_MAX_CONNECTIONS")
    redis_socket_connect_timeout: int = Field(default=5, alias="REDIS_SOCKET_CONNECT_TIMEOUT")  # seconds
    redis_health_check_interval: int = Field(default=30, alias="REDIS_HEALTH_CHECK_INTERVAL")  # seconds
    
    # Spotify API
    spotify_client_id: Optional[str] = Field(default=None, alias="SPOTIFY_CLIENT_ID")
    spotify_client_secret: Optional[str] = Field(default=None, alias="SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str = Field(..., alias="SPOTIFY_REDIRECT_URI")
    
    # Spotify API Endpoints (Constants)
    spotify_auth_url: str = "https://accounts.spotify.com/authorize"
    spotify_token_url: str = "https://accounts.spotify.com/api/token"
    spotify_api_base_url: str = "https://api.spotify.com/v1"
    
    # Spotify Scopes
    spotify_scopes: str = (
        "user-read-private user-read-email user-top-read "
        "user-library-read playlist-read-private "
        "playlist-read-collaborative user-read-recently-played"
    )
    
    # Resend API Configuration
    resend_api_key: Optional[str] = Field(default=None, alias="RESEND_API_KEY")
    destination_email: Optional[str] = Field(default=None, alias="DESTINATION_EMAIL")

    # Computed properties
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def cookie_secure(self) -> bool:
        """Enable secure cookies in production."""
        return self.is_production
    
    @property
    def cookie_samesite(self) -> str:
        """Set SameSite cookie policy based on environment."""
        return "none" if self.is_production else "lax"
    
    @property
    def log_level(self) -> str:
        """Set log level based on environment."""
        return "INFO" if self.is_production else "DEBUG"
    
    @property
    def allowed_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        return [self.frontend_url]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )


# Create a singleton instance
settings = Settings()


# OpenAPI Tag Metadata
OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Health check and status endpoints to verify API availability"
    },
    {
        "name": "Authentication",
        "description": "OAuth2 authentication with Spotify, token management, and user session handling"
    },
    {
        "name": "Users",
        "description": "User profile management and retrieval operations"
    },
    {
        "name": "Analytics",
        "description": "Spotify listening analytics including top tracks, artists, playlists, and listening history"
    },
]

# Swagger UI Configuration
SWAGGER_UI_PARAMETERS = {
    "deepLinking": True,
    "displayRequestDuration": True,
    "filter": True,
    "showExtensions": True,
    "showCommonExtensions": True,
    "persistAuthorization": True,
}
