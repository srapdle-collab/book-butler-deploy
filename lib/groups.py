"""읽담 소그룹의 초대·인증·피드 데이터 접근 계층."""
from __future__ import annotations

import secrets
import time
import uuid
from typing import Any

from lib import database
from lib.auth import AuthUser


class GroupAccessError(ValueError):
    """그룹원이 아닌 사용자가 그룹 데이터를 열려고 할 때 발생한다."""


def _now(now: int | None = None) -> int:
    return int(time.time()) if now is None else now


def _as_dict(row) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def ensure_profile(conn, user: AuthUser, *, now: int | None = None) -> None:
    database.execute(
        conn,
        """INSERT INTO profiles (id, email, display_name, created_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET email=excluded.email, display_name=excluded.display_name""",
        (user.id, user.email, user.display_name, _now(now)),
    )
    conn.commit()


def _require_member(conn, group_id: str, user_id: str) -> None:
    row = database.execute(
        conn,
        "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    ).fetchone()
    if row is None:
        raise GroupAccessError("이 소그룹의 구성원만 볼 수 있습니다.")


def create_group(conn, user: AuthUser, name: str, *, now: int | None = None) -> dict[str, Any]:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("소그룹 이름을 입력해주세요.")
    group_id = str(uuid.uuid4())
    created_at = _now(now)
    with database.transaction(conn):
        database.execute(
            conn,
            "INSERT INTO reading_groups (id, name, owner_id, created_at) VALUES (?, ?, ?, ?)",
            (group_id, clean_name, user.id, created_at),
        )
        database.execute(
            conn,
            "INSERT INTO group_members (group_id, user_id, role, joined_at) VALUES (?, ?, 'owner', ?)",
            (group_id, user.id, created_at),
        )
    return {"id": group_id, "name": clean_name, "owner_id": user.id, "created_at": created_at}


def list_groups(conn, user_id: str) -> list[dict[str, Any]]:
    rows = database.execute(
        conn,
        """SELECT g.*, gm.role FROM reading_groups g
           JOIN group_members gm ON gm.group_id = g.id
           WHERE gm.user_id = ? ORDER BY g.created_at DESC""",
        (user_id,),
    ).fetchall()
    return [_as_dict(row) for row in rows]


def create_invite(conn, group_id: str, user_id: str, *, now: int | None = None) -> str:
    _require_member(conn, group_id, user_id)
    role_row = database.execute(
        conn, "SELECT role FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id)
    ).fetchone()
    if _as_dict(role_row).get("role") != "owner":
        raise GroupAccessError("소그룹장만 초대 링크를 만들 수 있습니다.")
    token = secrets.token_urlsafe(24)
    database.execute(
        conn,
        "INSERT INTO group_invites (token, group_id, created_by, created_at) VALUES (?, ?, ?, ?)",
        (token, group_id, user_id, _now(now)),
    )
    conn.commit()
    return token


def join_invite(conn, token: str, user_id: str, *, now: int | None = None) -> str:
    with database.transaction(conn):
        invite = database.execute(
            conn, "SELECT * FROM group_invites WHERE token = ?", (token,)
        ).fetchone()
        if invite is None or _as_dict(invite).get("used_at") is not None:
            raise GroupAccessError("이미 사용되었거나 유효하지 않은 초대 링크입니다.")
        group_id = _as_dict(invite)["group_id"]
        database.execute(
            conn,
            "INSERT INTO group_members (group_id, user_id, role, joined_at) VALUES (?, ?, 'member', ?)",
            (group_id, user_id, _now(now)),
        )
        database.execute(
            conn, "UPDATE group_invites SET used_at = ?, used_by = ? WHERE token = ? AND used_at IS NULL",
            (_now(now), user_id, token),
        )
    return group_id


def save_checkin(
    conn,
    group_id: str,
    user_id: str,
    *,
    is_read: bool,
    note: str,
    attachment: dict[str, Any] | None = None,
    checked_on: str,
    now: int | None = None,
) -> str:
    _require_member(conn, group_id, user_id)
    clean_note = note.strip()
    if not is_read and not clean_note:
        raise ValueError("읽기 체크 또는 한줄소감 중 하나를 남겨주세요.")
    attachment = attachment or {}
    values = (
        attachment.get("kind"), attachment.get("body"), attachment.get("book_title"),
        attachment.get("page"), attachment.get("photo"),
    )
    timestamp = _now(now)
    with database.transaction(conn):
        existing = database.execute(
            conn,
            "SELECT id FROM daily_checkins WHERE group_id = ? AND user_id = ? AND checked_on = ?",
            (group_id, user_id, checked_on),
        ).fetchone()
        if existing is None:
            checkin_id = str(uuid.uuid4())
            database.execute(
                conn,
                """INSERT INTO daily_checkins (
                    id, group_id, user_id, checked_on, is_read, note,
                    attachment_kind, attachment_body, attachment_book_title, attachment_page, attachment_photo,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (checkin_id, group_id, user_id, checked_on, int(is_read), clean_note, *values, timestamp, timestamp),
            )
        else:
            checkin_id = _as_dict(existing)["id"]
            database.execute(
                conn,
                """UPDATE daily_checkins SET is_read = ?, note = ?, attachment_kind = ?, attachment_body = ?,
                    attachment_book_title = ?, attachment_page = ?, attachment_photo = ?, updated_at = ?
                    WHERE id = ?""",
                (int(is_read), clean_note, *values, timestamp, checkin_id),
            )
    return checkin_id


def group_feed(conn, group_id: str, user_id: str, *, checked_on: str) -> list[dict[str, Any]]:
    _require_member(conn, group_id, user_id)
    rows = database.execute(
        conn,
        """SELECT c.*, COALESCE(p.display_name, p.email) AS display_name,
                  (SELECT COUNT(*) FROM checkin_reactions r WHERE r.checkin_id = c.id) AS reaction_count,
                  EXISTS(SELECT 1 FROM checkin_reactions r WHERE r.checkin_id = c.id AND r.user_id = ?) AS reacted
           FROM daily_checkins c JOIN profiles p ON p.id = c.user_id
           WHERE c.group_id = ? AND c.checked_on = ? ORDER BY c.created_at DESC, c.id DESC""",
        (user_id, group_id, checked_on),
    ).fetchall()
    return [_as_dict(row) for row in rows]


def _checkin_group_for_member(conn, checkin_id: str, user_id: str) -> str:
    row = database.execute(conn, "SELECT group_id FROM daily_checkins WHERE id = ?", (checkin_id,)).fetchone()
    if row is None:
        raise ValueError("인증 기록을 찾을 수 없습니다.")
    group_id = _as_dict(row)["group_id"]
    _require_member(conn, group_id, user_id)
    return group_id


def toggle_reaction(conn, checkin_id: str, user_id: str, *, now: int | None = None) -> bool:
    _checkin_group_for_member(conn, checkin_id, user_id)
    with database.transaction(conn):
        current = database.execute(
            conn, "SELECT 1 FROM checkin_reactions WHERE checkin_id = ? AND user_id = ?", (checkin_id, user_id)
        ).fetchone()
        if current is not None:
            database.execute(
                conn, "DELETE FROM checkin_reactions WHERE checkin_id = ? AND user_id = ?", (checkin_id, user_id)
            )
            return False
        database.execute(
            conn, "INSERT INTO checkin_reactions (checkin_id, user_id, created_at) VALUES (?, ?, ?)",
            (checkin_id, user_id, _now(now)),
        )
        return True


def add_comment(conn, checkin_id: str, user_id: str, body: str, *, now: int | None = None) -> str:
    _checkin_group_for_member(conn, checkin_id, user_id)
    clean_body = body.strip()
    if not clean_body:
        raise ValueError("댓글 내용을 입력해주세요.")
    comment_id = str(uuid.uuid4())
    database.execute(
        conn,
        "INSERT INTO checkin_comments (id, checkin_id, user_id, body, created_at) VALUES (?, ?, ?, ?, ?)",
        (comment_id, checkin_id, user_id, clean_body, _now(now)),
    )
    conn.commit()
    return comment_id


def list_comments(conn, checkin_id: str, user_id: str) -> list[dict[str, Any]]:
    _checkin_group_for_member(conn, checkin_id, user_id)
    rows = database.execute(
        conn,
        """SELECT c.id, c.body, COALESCE(p.display_name, p.email) AS display_name
           FROM checkin_comments c JOIN profiles p ON p.id = c.user_id
           WHERE c.checkin_id = ? ORDER BY c.created_at ASC, c.id ASC""",
        (checkin_id,),
    ).fetchall()
    return [_as_dict(row) for row in rows]
