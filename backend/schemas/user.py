from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    spotify_id: str
    display_name: Optional[str]
    email: Optional[str]

class UserResponse(UserBase):
    id: int
    last_login: Optional[datetime]

    class Config:
        orm_mode = True
