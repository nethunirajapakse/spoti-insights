import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") # Change default for production!
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS  = 7

# Environment-aware configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
COOKIE_SECURE = IS_PRODUCTION  # True in production, False in dev
COOKIE_SAMESITE = "none" if IS_PRODUCTION else "lax"
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", None)  # Set to your domain in prod
