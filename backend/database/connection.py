from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Make SQL echo configurable via environment variable (default: False)
def str2bool(value):
    return str(value).lower() in ("1", "true", "yes", "on")

SQLALCHEMY_ECHO = str2bool(os.getenv("SQLALCHEMY_ECHO", "False"))

engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
