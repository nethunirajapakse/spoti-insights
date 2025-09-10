from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    spotify_id: str
    display_name: Optional[str]
    email: Optional[str]

class UserCreate(UserBase):
    refresh_token: str 

class UserResponse(UserBase):
    id: int
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class SpotifyToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str]
    scope: str

class SpotifyUser(BaseModel):
    id: str
    display_name: Optional[str] = None
    email: Optional[str] = None