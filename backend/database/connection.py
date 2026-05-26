from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def str2bool(value):
    return str(value).lower() in ("1", "true", "yes", "on")


SQLALCHEMY_ECHO = str2bool(os.getenv("SQLALCHEMY_ECHO", "False"))

POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

engine = create_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=POOL_RECYCLE,
)


@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    logger.debug("Connection checked out from pool. Pool status: %s", engine.pool.status())


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Database session error")
        db.rollback()
        raise
    finally:
        db.close()
