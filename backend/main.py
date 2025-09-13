from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.routers import auth, user, analytics
from backend.config.middleware import configure_middleware
from backend.utils.openapi import customize_openapi
from backend.services import spotify_api_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for managing the lifespan of the FastAPI application.
    Initializes and closes the Spotify HTTP client.
    """
    spotify_api_service.init_spotify_client()
    print("Spotify HTTP client initialized.")
    yield

    await spotify_api_service.close_spotify_client()
    print("Spotify HTTP client closed.")

app = FastAPI(title="Spoti-Insights API", lifespan=lifespan)

configure_middleware(app)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "FastAPI + PostgreSQL connection working!"}

app.openapi = lambda: customize_openapi(app)
