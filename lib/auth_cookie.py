"""Client-side refresh cookie bridge for Streamlit's read-only request cookies.

The cookie is set by JavaScript and therefore cannot be HttpOnly. Only the
Supabase refresh token is stored; user HTML rendered in the app must be escaped.
"""
from __future__ import annotations

import json
from urllib.parse import quote, unquote

import streamlit as st
import streamlit.components.v1 as components

COOKIE_NAME = "__Host-readdam-refresh"
COOKIE_MAX_AGE = 30 * 24 * 60 * 60


def request_cookie_name_seen() -> bool | None:
    """Inspect only the initial server request, never expose the cookie value.

    None means Streamlit could not provide request cookies at all. This probe
    cannot inspect the browser's current cookie jar or later HTTP requests.
    """
    try:
        return COOKIE_NAME in st.context.cookies
    except Exception:
        return None


def read_refresh_cookie() -> str | None:
    try:
        value = st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None
    if not value or len(value) > 8192:
        return None
    return unquote(value)


def cookie_script(refresh_token: str | None) -> str:
    value = quote(refresh_token, safe="") if refresh_token else ""
    attributes = f"{COOKIE_NAME}={value}; Path=/; Secure; SameSite=Strict; Max-Age={COOKIE_MAX_AGE if refresh_token else 0}"
    # JSON encoding is followed by a script-safe escape for arbitrary tokens.
    literal = json.dumps(attributes).replace("<", "\\u003c")
    return f"<script>window.parent.document.cookie={literal};</script>"


def write_refresh_cookie(refresh_token: str | None) -> None:
    components.html(cookie_script(refresh_token), height=0)
