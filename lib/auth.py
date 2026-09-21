"""Supabase Auth를 Streamlit 세션에서 쓰기 위한 작은 어댑터."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str
    display_name: str | None = None


class AuthError(RuntimeError):
    """로그인/회원가입 요청을 사용자에게 설명 가능한 오류로 바꾼다."""


def _setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except (FileNotFoundError, KeyError):
        return ""


def is_configured() -> bool:
    return bool(_setting("SUPABASE_URL") and _setting("SUPABASE_ANON_KEY"))


def user_from_payload(payload: dict[str, Any]) -> AuthUser:
    user_id = str(payload.get("id") or "").strip()
    email = str(payload.get("email") or "").strip()
    if not user_id or not email:
        raise AuthError("로그인 정보를 확인할 수 없습니다.")
    metadata = payload.get("user_metadata") or {}
    display_name = str(metadata.get("display_name") or metadata.get("name") or "").strip() or None
    return AuthUser(id=user_id, email=email, display_name=display_name)


def _client():
    if not is_configured():
        raise AuthError("로그인 설정이 아직 준비되지 않았습니다.")
    try:
        from supabase import create_client
    except ImportError as exc:  # pragma: no cover - 배포 의존성 설치 실패 방어
        raise AuthError("로그인 모듈을 불러오지 못했습니다.") from exc
    return create_client(_setting("SUPABASE_URL"), _setting("SUPABASE_ANON_KEY"))


def sign_up(email: str, password: str, display_name: str) -> str:
    try:
        response = _client().auth.sign_up({
            "email": email.strip(),
            "password": password,
            "options": {"data": {"display_name": display_name.strip()}},
        })
    except Exception as exc:  # pragma: no cover - Supabase HTTP 오류
        raise AuthError("회원가입을 완료하지 못했습니다. 이메일과 비밀번호를 확인해주세요.") from exc
    if not getattr(response, "user", None):
        raise AuthError("회원가입을 완료하지 못했습니다.")
    return "가입 확인 메일을 보냈습니다. 메일 확인 후 로그인해주세요."


def sign_in(email: str, password: str) -> tuple[AuthUser, str]:
    try:
        response = _client().auth.sign_in_with_password({"email": email.strip(), "password": password})
    except Exception as exc:  # pragma: no cover - Supabase HTTP 오류
        raise AuthError("이메일 또는 비밀번호가 맞지 않습니다.") from exc
    session = getattr(response, "session", None)
    user = getattr(response, "user", None)
    token = getattr(session, "access_token", None)
    if not user or not token:
        raise AuthError("로그인 세션을 만들지 못했습니다.")
    return user_from_payload(user.model_dump() if hasattr(user, "model_dump") else user.__dict__), token


def current_user(access_token: str) -> AuthUser:
    try:
        response = _client().auth.get_user(access_token)
        user = getattr(response, "user", None)
    except Exception as exc:  # pragma: no cover - Supabase HTTP 오류
        raise AuthError("로그인 세션이 만료되었습니다. 다시 로그인해주세요.") from exc
    if not user:
        raise AuthError("로그인 세션이 만료되었습니다. 다시 로그인해주세요.")
    return user_from_payload(user.model_dump() if hasattr(user, "model_dump") else user.__dict__)
