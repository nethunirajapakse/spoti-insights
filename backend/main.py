from fastapi import FastAPI
from backend.routers import auth
from backend.routers import user
from backend.config.middleware import configure_middleware

app = FastAPI(title="Spoti-Insights API")

configure_middleware(app)

app.include_router(auth.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "FastAPI + PostgreSQL connection working!"}
