from fastapi import FastAPI
from backend.routers import auth, user, analytics
from backend.config.middleware import configure_middleware
from backend.utils.openapi import customize_openapi 

app = FastAPI(title="Spoti-Insights API")

configure_middleware(app)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "FastAPI + PostgreSQL connection working!"}

app.openapi = lambda: customize_openapi(app)
