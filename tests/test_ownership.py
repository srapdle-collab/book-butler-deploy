import sqlite3

from lib.auth import AuthUser
from lib.schema import ensure_schema
from migration.load_db import SCHEMA


def test_legacy_library_is_claimed_only_by_configured_owner(monkeypatch):
    from lib import ownership

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    ensure_schema(conn)
    conn.execute("INSERT INTO books (id, title) VALUES ('book-1', '개인 책')")
    conn.execute(
        "INSERT INTO activities (id, book_id, kind, page, date) VALUES ('activity-1', 'book-1', 2, 12, 1)"
    )
    conn.commit()
    monkeypatch.setenv("READDAM_OWNER_EMAIL", "owner@example.com")

    stranger = AuthUser(id="stranger-id", email="stranger@example.com")
    assert ownership.claim_legacy_library(conn, stranger) is False
    assert conn.execute("SELECT owner_id FROM books").fetchone()[0] is None

    owner = AuthUser(id="owner-id", email="owner@example.com")
    assert ownership.claim_legacy_library(conn, owner) is True
    assert conn.execute("SELECT owner_id FROM books").fetchone()[0] == "owner-id"
    assert conn.execute("SELECT owner_id FROM activities").fetchone()[0] == "owner-id"
    assert ownership.has_personal_library(conn, owner.id) is True
    assert ownership.has_personal_library(conn, stranger.id) is False
