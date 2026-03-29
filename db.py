"""
Database connection and schema bootstrap.
Reads DATABASE_URL from Streamlit secrets or environment variables.
Fails gracefully if not configured — the app works without a DB.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def _get_db_url() -> str:
    try:
        import streamlit as st
        return st.secrets.get("DATABASE_URL", "") or os.getenv("DATABASE_URL", "")
    except Exception:
        return os.getenv("DATABASE_URL", "")


def _sanitize_db_url(url: str) -> str:
    """URL 비밀번호의 특수문자([, ] 등)를 percent-encode해서 파싱 오류 방지."""
    from urllib.parse import urlparse, urlunparse, quote
    try:
        parsed = urlparse(url)
        if parsed.password and any(c in parsed.password for c in "[]@"):
            encoded_pw = quote(parsed.password, safe="")
            netloc = f"{parsed.username}:{encoded_pw}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            parsed = parsed._replace(netloc=netloc)
            return urlunparse(parsed)
    except Exception:
        pass
    return url


_engine_cache = None

def get_engine():
    """Return a SQLAlchemy engine, or None if DATABASE_URL is not set."""
    global _engine_cache
    if _engine_cache is not None:
        return _engine_cache
    url = _get_db_url()
    if not url:
        return None
    try:
        url = _sanitize_db_url(url)
        _engine_cache = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=2,
            pool_recycle=300,
        )
        return _engine_cache
    except Exception as e:
        print(f"[DB] Failed to create engine: {e}")
        return None


def init_db():
    """Create tables if they don't exist. Safe to call multiple times."""
    engine = get_engine()
    if engine is None:
        return

    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            email           TEXT UNIQUE NOT NULL,
            name            TEXT,
            profile_image_url TEXT,
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            last_login_at   TIMESTAMPTZ,
            login_count     INTEGER DEFAULT 0,
            role            TEXT DEFAULT 'user'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id          SERIAL PRIMARY KEY,
            email       TEXT NOT NULL,
            login_at    TIMESTAMPTZ DEFAULT NOW(),
            logout_at   TIMESTAMPTZ,
            session_id  TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS analysis_events (
            id                  SERIAL PRIMARY KEY,
            email               TEXT NOT NULL,
            action_type         TEXT NOT NULL,
            app_id              TEXT,
            selected_countries  TEXT,
            status              TEXT DEFAULT 'ok',
            details             JSONB,
            created_at          TIMESTAMPTZ DEFAULT NOW()
        )
        """,
    ]

    try:
        with engine.connect() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
            conn.commit()
    except SQLAlchemyError as e:
        print(f"[DB] Schema init failed: {e}")
