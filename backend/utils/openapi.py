from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def customize_openapi(app: FastAPI):
    """
    Customizes the OpenAPI schema.
    - Preserves title, version, description from FastAPI initialization
    - Adds security schemes (Bearer token + Cookie auth)
    - Automatically applies security to non-public endpoints
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # Add security schemes
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    
    # Bearer token authentication
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT access token (without 'Bearer' prefix)"
    }
    
    # Cookie authentication
    openapi_schema["components"]["securitySchemes"]["CookieAuth"] = {
        "type": "apiKey",
        "in": "cookie",
        "name": "access_token",
        "description": "Session cookie authentication (automatically handled by browser)"
    }

    # Apply security to non-public endpoints automatically
    for path, path_item in openapi_schema["paths"].items():
        # Skip public endpoints (don't require auth)
        if not path.startswith("/public") and not path.startswith("/health") and path != "/":
            for method in ["get", "put", "post", "delete", "options", "head", "patch", "trace"]:
                if method in path_item:
                    # Add both auth methods (user can use either)
                    path_item[method].setdefault("security", []).extend([
                        {"BearerAuth": []},
                        {"CookieAuth": []}
                    ])

    # Cache the schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema
