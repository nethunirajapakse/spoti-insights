from sqlalchemy import Column, Integer, String, TIMESTAMP
from backend.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True, nullable=False)
    spotify_refresh_token = Column(String, nullable=False) 
    app_refresh_token = Column(String)
    display_name = Column(String)
    email = Column(String)
    last_login = Column(TIMESTAMP(timezone=True))
