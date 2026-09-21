"""개인 서재를 인증 계정에 연결하는 경계."""
from __future__ import annotations

import os

from lib import database
from lib.auth import AuthUser


def configured_owner_email() -> str:
    """기존 마이그레이션 서재를 받을 계정의 이메일을 돌려준다."""
    return os.environ.get("READDAM_OWNER_EMAIL", "").strip().casefold()


def claim_legacy_library(conn, user: AuthUser) -> bool:
    """지정된 소유자만 아직 주인 없는 기존 서재를 한 번 연결한다."""
    owner_email = configured_owner_email()
    if not owner_email or user.email.casefold() != owner_email:
        return False
    with database.transaction(conn):
        database.execute(
            conn,
            "UPDATE books SET owner_id = ? WHERE owner_id IS NULL",
            (user.id,),
        )
        database.execute(
            conn,
            "UPDATE activities SET owner_id = ? WHERE owner_id IS NULL",
            (user.id,),
        )
    return has_personal_library(conn, user.id)


def has_personal_library(conn, user_id: str) -> bool:
    row = database.execute(
        conn, "SELECT 1 FROM books WHERE owner_id = ? LIMIT 1", (user_id,)
    ).fetchone()
    return row is not None
