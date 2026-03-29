"""
Event tracking helpers.
All functions fail silently — a DB outage must never break the main app.
"""

import os
import json
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db import get_engine


def upsert_user_on_login(email: str, name: str = None, picture: str = None):
    """
    Insert the user row on first login, or update last_login_at + login_count.
    Also inserts a user_sessions row.
    Returns the new session row id, or None.
    """
    engine = get_engine()
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (email, name, profile_image_url, created_at, last_login_at, login_count, role)
                VALUES (:email, :name, :pic, NOW(), NOW(), 1, 'user')
                ON CONFLICT (email) DO UPDATE
                  SET last_login_at      = NOW(),
                      login_count        = users.login_count + 1,
                      name               = COALESCE(EXCLUDED.name, users.name),
                      profile_image_url  = COALESCE(EXCLUDED.profile_image_url, users.profile_image_url)
            """), {"email": email, "name": name, "pic": picture})

            result = conn.execute(text("""
                INSERT INTO user_sessions (email, login_at)
                VALUES (:email, NOW())
                RETURNING id
            """), {"email": email})
            row = result.fetchone()
            conn.commit()
            return row[0] if row else None
    except SQLAlchemyError:
        return None


def close_user_session(email: str):
    """Set logout_at on the most recent open session for this user."""
    engine = get_engine()
    if engine is None:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE user_sessions
                SET logout_at = NOW()
                WHERE id = (
                    SELECT id FROM user_sessions
                    WHERE email = :email AND logout_at IS NULL
                    ORDER BY login_at DESC
                    LIMIT 1
                )
            """), {"email": email})
            conn.commit()
    except SQLAlchemyError:
        pass


def log_event(
    email: str,
    action_type: str,
    app_id=None,
    selected_countries=None,
    status: str = "ok",
    details: dict = None,
):
    """
    Insert a row into analysis_events.

    action_type examples:
        login, logout, start_analysis, complete_analysis, error
    """
    engine = get_engine()
    if engine is None:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO analysis_events
                    (email, action_type, app_id, selected_countries, status, details, created_at)
                VALUES
                    (:email, :action, :app_id, :countries, :status, :details, NOW())
            """), {
                "email": email,
                "action": action_type,
                "app_id": str(app_id) if app_id is not None else None,
                "countries": ",".join(selected_countries) if selected_countries else None,
                "status": status,
                "details": json.dumps(details, ensure_ascii=False) if details else None,
            })
            conn.commit()
    except SQLAlchemyError:
        pass


def is_admin(email: str) -> bool:
    """Return True if email is in the ADMIN_EMAILS config (comma-separated)."""
    try:
        import streamlit as st
        raw = st.secrets.get("ADMIN_EMAILS", "") or os.getenv("ADMIN_EMAILS", "")
    except Exception:
        raw = os.getenv("ADMIN_EMAILS", "")

    if not raw:
        return False
    admins = {e.strip().lower() for e in raw.split(",") if e.strip()}
    return email.strip().lower() in admins
