import sqlite3

import pytest

from lib.auth import AuthUser
from lib.schema import ensure_schema
from migration.load_db import SCHEMA


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    ensure_schema(conn)
    return conn


def test_group_invite_checkin_feed_reaction_and_comment():
    from lib import groups

    conn = _conn()
    owner = AuthUser(id="owner-id", email="owner@example.com", display_name="모임장")
    member = AuthUser(id="member-id", email="member@example.com", display_name="독자")
    outsider = AuthUser(id="outsider-id", email="outsider@example.com")
    groups.ensure_profile(conn, owner)
    groups.ensure_profile(conn, member)
    groups.ensure_profile(conn, outsider)

    group = groups.create_group(conn, owner, "월요 읽담")
    invite = groups.create_invite(conn, group["id"], owner.id)
    assert groups.join_invite(conn, invite, member.id) == group["id"]
    with pytest.raises(groups.GroupAccessError):
        groups.join_invite(conn, invite, outsider.id)

    owner_checkin = groups.save_checkin(
        conn, group["id"], owner.id, is_read=True, note="오늘도 읽었습니다.",
        attachment={"kind": 2, "body": "기억할 문장", "book_title": "개인 책", "page": 12},
        checked_on="2026-09-21", now=100,
    )
    member_checkin = groups.save_checkin(
        conn, group["id"], member.id, is_read=True, note="짧은 소감", checked_on="2026-09-21", now=200,
    )
    feed = groups.group_feed(conn, group["id"], member.id, checked_on="2026-09-21")
    assert [item["id"] for item in feed] == [member_checkin, owner_checkin]
    assert feed[1]["attachment_body"] == "기억할 문장"
    assert feed[1]["attachment_book_title"] == "개인 책"

    assert groups.toggle_reaction(conn, owner_checkin, member.id, now=300) is True
    assert groups.toggle_reaction(conn, owner_checkin, member.id, now=301) is False
    comment_id = groups.add_comment(conn, owner_checkin, member.id, "함께 읽어서 좋아요", now=302)
    comments = groups.list_comments(conn, owner_checkin, member.id)
    assert comments == [{"id": comment_id, "body": "함께 읽어서 좋아요", "display_name": "독자"}]

    with pytest.raises(groups.GroupAccessError):
        groups.group_feed(conn, group["id"], outsider.id, checked_on="2026-09-21")
