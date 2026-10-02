"""Count network-equivalent round trips per screen action in the owner flow.

Locally every query is in-process SQLite, so wall time hides the production cost.
In production each counted item is a network round trip (Supabase Postgres or
Storage), so these counts are the stable, comparable speed measure.
"""
import os
import sqlite3
import threading
from collections import Counter
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from lib import db, storage
from lib.auth import AuthUser
from lib.schema_maintenance import initialize_schema
from migration.load_db import SCHEMA

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
OWNER = AuthUser("owner-1", "owner@test.example", "Owner")
BOOKS = 30


class Meter:
    def __init__(self):
        self.lock = threading.Lock()
        self.counts = Counter()

    def add(self, name, amount=1):
        with self.lock:
            self.counts[name] += amount

    def take(self):
        with self.lock:
            result, self.counts = dict(self.counts), Counter()
        return result


def _classify(meter, statement):
    text = " ".join(statement.split()).upper()
    if text in ("BEGIN", "COMMIT", "ROLLBACK") or text.startswith(("BEGIN ", "PRAGMA FOREIGN_KEYS", "PRAGMA QUERY_ONLY")):
        return
    meter.add("sql")
    if "SQLITE_MASTER" in text or "SQLITE_SCHEMA" in text or text.startswith("PRAGMA") or "PRAGMA_" in text:
        meter.add("schema_sql")
    if text.startswith("UPDATE BOOKS SET OWNER_ID") or text.startswith("UPDATE ACTIVITIES SET OWNER_ID"):
        meter.add("ownership_update")
    if text.startswith("SELECT * FROM BOOKS WHERE ID"):
        meter.add("get_book")


@pytest.fixture
def owner_app(tmp_path, monkeypatch):
    db_path = tmp_path / "book_butler.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    initialize_schema(conn, approved=True)
    for index in range(1, BOOKS + 1):
        conn.execute(
            """
            INSERT INTO books (id, title, author, publisher, isbn, category, pages, current_page,
                rating, status, read_count, start_date, cover_photo)
            VALUES (?, ?, '저자', '출판사', ?, '신앙', 300, 10, 0, ?, 0, 1700000000, ?)
            """,
            (f"book-{index}", f"책 {index:02d}", f"isbn-{index}", "읽는 중" if index <= 3 else "완독",
             f"cover-{index}.png"),
        )
    conn.commit()
    conn.close()
    for name, value in {
        "BOOK_BUTLER_DB_PATH": str(db_path),
        "BOOK_BUTLER_PHOTOS_DIR": str(tmp_path / "photos"),
        "BOOK_BUTLER_APP_PASSWORD": "",
        "SUPABASE_URL": "https://storage.test.invalid",
        "SUPABASE_ANON_KEY": "anon-test",
        "SUPABASE_SERVICE_ROLE_KEY": "service-test",
        "READDAM_OWNER_EMAIL": OWNER.email,
    }.items():
        monkeypatch.setenv(name, value)

    meter = Meter()
    original_connect = db.connect

    def counted_connect(*args, **kwargs):
        meter.add("db_connect")
        connection = original_connect(*args, **kwargs)
        if isinstance(connection, sqlite3.Connection):
            connection.set_trace_callback(lambda statement: _classify(meter, statement))
        return connection

    class FakeResponse:
        status_code = 200

        def __init__(self, path):
            self.path = path

        def raise_for_status(self):
            return None

        def json(self):
            return {"signedURL": f"/object/sign/{self.path}?token=t"}

    def counted_request(method, url, **kwargs):
        meter.add("storage_sign")
        return FakeResponse(url.rsplit("/sign/", 1)[-1])

    monkeypatch.setattr(db, "connect", counted_connect)
    monkeypatch.setattr(storage.requests, "request", counted_request)
    if hasattr(storage, "clear_signed_url_cache"):
        storage.clear_signed_url_cache()
    if hasattr(db, "clear_schema_cache"):
        db.clear_schema_cache()
    return meter


def _new_session():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.session_state["auth_user"] = OWNER
    at.session_state["auth_refresh_token"] = "refresh-test"
    at.session_state["auth_refresh_at"] = float("inf")
    return at


def measure(meter):
    meter.take()
    at = _new_session()
    at.run()
    assert not at.exception, at.exception
    results = {"1_shelf_first_open": meter.take()}
    at.run()
    assert not at.exception
    results["2_shelf_rerun"] = meter.take()
    at.button(key="shelf_cover_book-1").click().run()
    assert not at.exception
    assert at.session_state["view"] == "책 상세"
    results["3_open_detail"] = meter.take()
    at.button(key="open_progress").click().run()
    assert not at.exception
    results["4_detail_click"] = meter.take()
    return results


def _report(results):
    keys = ["db_connect", "schema_sql", "ownership_update", "get_book", "storage_sign", "sql"]
    lines = ["action".ljust(22) + "".join(k.rjust(18) for k in keys)]
    for action, counts in results.items():
        lines.append(action.ljust(22) + "".join(str(counts.get(k, 0)).rjust(18) for k in keys))
    return "\n".join(lines)


def test_roundtrip_report(owner_app, capsys):
    results = measure(owner_app)
    with capsys.disabled():
        print("\n" + _report(results))
    for action in ("2_shelf_rerun", "3_open_detail", "4_detail_click"):
        counts = results[action]
        assert counts.get("schema_sql", 0) == 0, action
        assert counts.get("ownership_update", 0) == 0, action
        assert counts.get("storage_sign", 0) == 0, action
    assert results["1_shelf_first_open"].get("storage_sign", 0) <= 24
    assert results["3_open_detail"].get("get_book", 0) <= 2
    assert results["4_detail_click"].get("get_book", 0) <= 3


class _FakeInfo:
    def __init__(self, status):
        self.transaction_status = status


class _FakeRaw:
    def __init__(self, status, closed=False, broken=False):
        self.info = _FakeInfo(status)
        self.closed = closed
        self.broken = broken
        self.rolled_back = False

    def rollback(self):
        from psycopg.pq import TransactionStatus
        self.rolled_back = True
        self.info.transaction_status = TransactionStatus.IDLE


class _FakePostgres:
    backend = "postgres"

    def __init__(self, raw):
        self.raw = raw


def test_only_idle_healthy_postgres_connections_are_reused(tmp_path):
    from psycopg.pq import TransactionStatus

    assert db.connection_reusable(_FakePostgres(_FakeRaw(TransactionStatus.IDLE)))
    leftover = _FakeRaw(TransactionStatus.INTRANS)
    assert db.connection_reusable(_FakePostgres(leftover)) and leftover.rolled_back
    assert not db.connection_reusable(_FakePostgres(_FakeRaw(TransactionStatus.IDLE, closed=True)))
    assert not db.connection_reusable(_FakePostgres(_FakeRaw(TransactionStatus.IDLE, broken=True)))
    assert not db.connection_reusable(_FakePostgres(_FakeRaw(TransactionStatus.ACTIVE)))
    assert not db.connection_reusable(sqlite3.connect(tmp_path / "x.db"))


def test_app_keeps_one_reusable_connection_across_reruns(owner_app, monkeypatch):
    """Simulate the production path: a reusable connection is opened once per session."""
    opened = []
    original = db.connect

    def shareable_connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        path = connection.execute("PRAGMA database_list").fetchone()[2]
        connection.close()
        shared = sqlite3.connect(path, check_same_thread=False)
        shared.row_factory = sqlite3.Row
        opened.append(shared)
        return shared

    monkeypatch.setattr(db, "connect", shareable_connect)
    monkeypatch.setattr(db, "connection_reusable", lambda conn: conn in opened)
    at = _new_session()
    at.run()
    at.run()
    at.button(key="shelf_cover_book-1").click().run()
    at.button(key="open_progress").click().run()
    assert not at.exception
    assert len(opened) == 1
