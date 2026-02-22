import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def _normalize_database_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _resolve_connect_args(database_url: str) -> dict:
    connect_args = {}
    if not database_url.startswith("postgresql+psycopg2://"):
        return connect_args

    sslmode = (settings.DB_SSLMODE or "").strip()
    # Em produção com Supabase/Render, SSL é necessário.
    if not sslmode and ("supabase.co" in database_url or os.getenv("RENDER")):
        sslmode = "require"

    if sslmode:
        connect_args["sslmode"] = sslmode

    return connect_args


DATABASE_URL = _normalize_database_url(settings.DATABASE_URL)
CONNECT_ARGS = _resolve_connect_args(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=CONNECT_ARGS,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
