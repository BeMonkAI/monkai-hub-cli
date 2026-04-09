# -*- coding: utf-8 -*-
"""Authentication management — Supabase email/password login with local JWT storage."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .config import SUPABASE_ANON_KEY, SUPABASE_URL

_AUTH_DIR = Path.home() / ".monkai-hub"
_AUTH_FILE = _AUTH_DIR / "auth.json"


def _save_session(session: Dict[str, Any]) -> None:
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_FILE.write_text(json.dumps(session, indent=2), encoding="utf-8")


def _load_session() -> Optional[Dict[str, Any]]:
    if not _AUTH_FILE.exists():
        return None
    try:
        return json.loads(_AUTH_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def login(email: str, password: str) -> Dict[str, Any]:
    """Authenticate with Supabase and save JWT locally.

    Returns:
        Dict with user_id, email, access_token, refresh_token, expires_at.

    Raises:
        Exception on auth failure.
    """
    resp = httpx.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

    if resp.status_code != 200:
        detail = resp.json().get("error_description") or resp.json().get("msg") or resp.text
        raise Exception(f"Login failed: {detail}")

    data = resp.json()
    session = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": data.get("expires_at", 0),
        "user_id": data["user"]["id"],
        "email": data["user"]["email"],
    }
    _save_session(session)
    return session


def refresh_token() -> Dict[str, Any]:
    """Refresh the access token using the stored refresh token."""
    session = _load_session()
    if not session or not session.get("refresh_token"):
        raise Exception("Not authenticated. Run 'monkai-hub login' first.")

    resp = httpx.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
        json={"refresh_token": session["refresh_token"]},
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

    if resp.status_code != 200:
        raise Exception("Token refresh failed. Run 'monkai-hub login' again.")

    data = resp.json()
    session.update(
        {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data.get("expires_at", 0),
        }
    )
    _save_session(session)
    return session


def get_token() -> str:
    """Get a valid access token, refreshing if expired.

    Returns:
        JWT access token string.

    Raises:
        Exception if not authenticated.
    """
    session = _load_session()
    if not session:
        raise Exception("Not authenticated. Run 'monkai-hub login' first.")

    # Check expiry (with 60s buffer)
    expires_at = session.get("expires_at", 0)
    if expires_at and time.time() > expires_at - 60:
        session = refresh_token()

    return session["access_token"]


def get_user_id() -> str:
    """Get the authenticated user's ID."""
    session = _load_session()
    if not session:
        raise Exception("Not authenticated. Run 'monkai-hub login' first.")
    return session["user_id"]


def logout() -> None:
    """Remove stored credentials."""
    if _AUTH_FILE.exists():
        _AUTH_FILE.unlink()
