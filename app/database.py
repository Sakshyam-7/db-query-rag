from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass 


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
 
readonly_engine = create_engine(
    settings.DATABASE_URL_READONLY,
    pool_pre_ping=True,
    connect_args={"options": "-c statement_timeout=3000"},
)
ReadOnlySessionLocal = sessionmaker(
    bind=readonly_engine,
    autoflush=False,
    autocommit=False,
)


def get_readonly_db():
    db = ReadOnlySessionLocal()
    try:
        yield db
    finally:
        db.close()