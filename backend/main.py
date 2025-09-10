

from fastapi import FastAPI
from backend.controllers import user_controller, auth_controller # Import auth_controller

app = FastAPI(title="Spoti-Insights API")

# Include routers
app.include_router(user_controller.router)
app.include_router(auth_controller.router) # Include the new auth router

@app.get("/")
def root():
    return {"message": "FastAPI + PostgreSQL connection working!"}
