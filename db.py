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


def get_engine():
    """Return a SQLAlchemy engine, or None if DATABASE_URL is not set."""
    url = _get_db_url()
    if not url:
        return None
    try:
        engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=2)
        return engine
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
