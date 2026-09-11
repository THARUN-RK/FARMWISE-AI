from collections.abc import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .config import settings

class Base(DeclarativeBase):
    pass

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

def ensure_local_schema() -> None:
    """Keep the SQLite demo database usable after additive model changes."""
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "farmers" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("farmers")}
    with engine.begin() as connection:
        for name in ("state", "district"):
            if name not in columns:
                connection.execute(text(f"ALTER TABLE farmers ADD COLUMN {name} VARCHAR(80)"))

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
