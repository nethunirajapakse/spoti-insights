from fastapi import FastAPI
from backend.routers import auth_router
from backend.routers import user_router

app = FastAPI(title="Spoti-Insights API")

app.include_router(auth_router.router)
app.include_router(user_router.router)

@app.get("/")
def root():
    return {"message": "FastAPI + PostgreSQL connection working!"}

