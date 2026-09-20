import json
import sqlite3

from lib import db
from migration.load_db import SCHEMA, build_db


EXPECTED_KINDS = {
    "quote_with_note": 0,
    "photo": 1,
    "quote": 2,
    "start": 3,
    "progress_log": 4,
    "finish": 5,
    "rating": 6,
    "other": 7,
}


def test_opening_legacy_database_migrates_all_activity_kinds_to_integers(tmp_path):
    """문자열 kind가 남아 새 기록과 통계가 서로 어긋나는 회귀를 막는다."""
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE books (id TEXT PRIMARY KEY, title TEXT NOT NULL);
        CREATE TABLE activities (
            id TEXT PRIMARY KEY,
            book_id TEXT NOT NULL REFERENCES books(id),
            kind TEXT NOT NULL,
            text TEXT,
            quote TEXT,
            page INTEGER,
            date INTEGER NOT NULL,
            photo TEXT,
            visibility TEXT NOT NULL DEFAULT 'private',
            pages_read INTEGER,
            minutes_read INTEGER
        );
        CREATE INDEX idx_activities_book_id ON activities(book_id);
        CREATE INDEX idx_activities_date ON activities(date);
        CREATE INDEX idx_activities_kind ON activities(kind);
        """
    )
    conn.execute(
        "INSERT INTO books (id, title) VALUES (?, ?)",
        ("book-1", "테스트 책"),
    )
    for index, name in enumerate(EXPECTED_KINDS):
        conn.execute(
            "INSERT INTO activities (id, book_id, kind, date) VALUES (?, ?, ?, ?)",
            (f"activity-{index}", "book-1", name, 1_700_000_000 + index),
        )
    conn.commit()
    conn.close()

    migrated = db.get_connection(db_path)
    declared_type = next(
        row[2] for row in migrated.execute("PRAGMA table_info(activities)") if row[1] == "kind"
    )
    rows = migrated.execute(
        "SELECT id, kind, typeof(kind) FROM activities ORDER BY id"
    ).fetchall()
    migrated.close()

    assert declared_type == "INTEGER"
    assert [row[1] for row in rows] == list(range(8))
    assert {row[2] for row in rows} == {"integer"}


def test_build_db_stores_converted_json_kind_as_integer(tmp_path):
    """마이그레이션을 재실행해 문자열 kind DB로 되돌아가는 회귀를 막는다."""
    output = tmp_path / "output"
    output.mkdir()
    book = {
        "id": "book-1", "title": "테스트 책", "author": None,
        "publisher": None, "isbn": None, "subtitle": None,
        "translator": None, "category": None, "pages": 100,
        "currentPage": 10, "rating": 0, "status": "읽는 중",
        "readCount": 0, "startDate": 1_700_000_000, "finishDate": None,
    }
    activity = {
        "id": "activity-1", "book_id": "book-1", "kind": "progress_log",
        "text": "10쪽을 20분 동안 읽었습니다", "quote": None,
        "page": 10, "date": 1_700_000_100, "photo": None,
        "visibility": "private",
    }
    (output / "books.json").write_text(json.dumps([book]), encoding="utf-8")
    (output / "activities.json").write_text(json.dumps([activity]), encoding="utf-8")
    (output / "photo_manifest.json").write_text("[]", encoding="utf-8")
    db_path = tmp_path / "built.db"

    build_db(output, db_path)

    conn = sqlite3.connect(db_path)
    kind, storage_type = conn.execute(
        "SELECT kind, typeof(kind) FROM activities"
    ).fetchone()
    conn.close()
    assert kind == 4
    assert storage_type == "integer"
