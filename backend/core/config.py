from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # App configuration
    app_name: str = Field(default="Spoti-Insights API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")  # Required
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS and Cookies
    frontend_url: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_URL")
    cookie_domain: Optional[str] = Field(default=None, alias="COOKIE_DOMAIN")
    
    # Database
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Redis (for rate limiting)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    
    # Spotify API
    spotify_client_id: Optional[str] = Field(default=None, alias="SPOTIFY_CLIENT_ID")
    spotify_client_secret: Optional[str] = Field(default=None, alias="SPOTIFY_CLIENT_SECRET")
    
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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )


# Create a singleton instance
settings = Settings()
