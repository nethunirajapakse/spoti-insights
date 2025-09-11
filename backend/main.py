from fastapi import FastAPI
from backend.routers import auth
from backend.routers import user

app = FastAPI(title="Spoti-Insights API")

app.include_router(auth.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "FastAPI + PostgreSQL connection working!"}
