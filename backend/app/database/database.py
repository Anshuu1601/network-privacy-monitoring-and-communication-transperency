"""SQLAlchemy engine, session, and declarative base."""
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_connection_columns()


def _migrate_connection_columns():
    """Add newly-introduced columns to existing SQLite tables without
    destroying current data (ALTER TABLE ADD COLUMN preserves rows)."""
    inspector = inspect(engine)
    if "connections" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("connections")}
    desired = {
        "website": "VARCHAR(255)",
        "domain": "VARCHAR(255)",
        "application": "VARCHAR(128)",
    }
    with engine.begin() as conn:
        for name, coltype in desired.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE connections ADD COLUMN {name} {coltype}"))
