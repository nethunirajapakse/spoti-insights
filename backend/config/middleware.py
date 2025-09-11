from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def configure_middleware(app: FastAPI):
    """
    Configures CORS middleware for the given FastAPI application.

    Parameters:
        app (FastAPI): The FastAPI application instance to configure.

    CORS configuration applied:
        - Allowed origins: http://localhost:5173, http://127.0.0.1:5173
        - Allow credentials: True
        - Allowed methods: GET, POST, PUT, DELETE
        - Allowed headers: Authorization, Content-Type
    """
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
