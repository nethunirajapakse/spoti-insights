from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.services import auth_service, spotify_auth_service
from backend.database.connection import get_db

router = APIRouter(prefix="/public/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login():
    auth_url = spotify_auth_service.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback")
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    try:
        # 1. Call your service to get the tokens
        access_token, refresh_token = await auth_service.handle_spotify_callback(code, db)

        # 2. Define where the user should go after successful login
        frontend_dashboard_url = "http://127.0.0.1:5173/dashboard"
        response = RedirectResponse(url=frontend_dashboard_url)

        # 3. Set cookies
        # httponly=True prevents JS from reading the cookie
        # samesite="lax" is required for cross-site redirects
        # secure=False for localhost, set to True in production (HTTPS)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True, 
            max_age=3600, # 1 hour
            samesite="lax",
            secure=False  
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=2592000, # 30 days
            samesite="lax",
            secure=False
        )

        return response

    except Exception as e:
        # On error, redirect back to login with an error parameter
        return RedirectResponse(url=f"http://localhost:5173/login?error={str(e)}")
    