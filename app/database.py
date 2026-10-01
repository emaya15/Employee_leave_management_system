# app/database.py
# Everything about the database connection lives here:
#   engine  -> the connection to MySQL
#   SessionLocal -> creates a "session" (a conversation with the database)
#   Base -> the parent class of all our models
#   get_db -> gives each request its own session and closes it afterwards
from sqlalchemy import Column, DateTime, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# pool_pre_ping=True checks the connection is alive before using it
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


class TimestampMixin:
    """Add this to a model to get created_at and updated_at columns."""

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


def get_db():
    """FastAPI dependency: open a session, hand it over, always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
