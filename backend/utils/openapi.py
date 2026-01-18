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

    # Generate OpenAPI schema using app's own metadata
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,  # Use description from FastAPI initialization
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # Add security schemes
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    
    # Bearer token authentication (JWT)
    # Note: Cookie auth also uses the same JWT, but Swagger UI works best with Bearer
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT access token. Get it from /public/auth/spotify/login flow or use your existing access_token cookie value."
    }

    # Apply security to non-public endpoints automatically
    for path, path_item in openapi_schema["paths"].items():
        # Skip public endpoints (don't require auth)
        if not path.startswith("/public") and not path.startswith("/health") and path != "/":
            for method in ["get", "put", "post", "delete", "options", "head", "patch", "trace"]:
                if method in path_item:
                    # Apply Bearer auth requirement
                    path_item[method].setdefault("security", []).append({"BearerAuth": []})

    # Cache the schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema
