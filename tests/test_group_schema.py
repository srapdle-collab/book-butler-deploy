import sqlite3

from lib.schema import ensure_schema
from migration.load_db import SCHEMA


def _column_names(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def test_schema_adds_personal_ownership_and_group_tables():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)

    ensure_schema(conn)

    assert "owner_id" in _column_names(conn, "books")
    assert "owner_id" in _column_names(conn, "activities")
    assert {"profiles", "reading_groups", "group_members", "group_invites",
            "daily_checkins", "checkin_reactions", "checkin_comments"}.issubset(
        {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    )
