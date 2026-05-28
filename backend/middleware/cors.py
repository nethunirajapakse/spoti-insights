from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings 

def configure_middleware(app: FastAPI):
    origins = [
        settings.frontend_url,
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True, # Required for cookies
        # Add OPTIONS to methods for preflight requests
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
        # Using ["*"] for headers is generally safer for local dev
        allow_headers=["*"], 
    )
