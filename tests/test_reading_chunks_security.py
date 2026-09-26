"""Actor boundaries: all data is synthetic; no production connection."""
import sqlite3

import pytest

from lib import db, database, reading_chunks as chunks
from test_activity_inputs_app import isolated_app
from test_reading_chunks import _save


@pytest.fixture
def owned(isolated_app):
    conn = db.get_connection()
    conn.execute("UPDATE books SET owner_id='alice' WHERE id='book-1'")
    conn.execute("INSERT INTO books(id,title,owner_id) VALUES('alice-book','TEST Alice','alice'),('bob-book','TEST Bob','bob')")
    conn.commit()
    yield conn
    conn.close()


def test_actor_and_book_boundaries(owned):
    row = _save(owned, owner_id="alice")
    before = tuple(owned.execute("SELECT * FROM reading_chunks").fetchone())
    assert chunks.get(owned, row["chunk_id"], owner_id="bob") is None
    for operation in [
        lambda: _save(owned, owner_id="bob"),
        lambda: _save(owned, owner_id="bob", book_id="bob-book", chunk_id=row["chunk_id"]),
        lambda: _save(owned, owner_id="alice", book_id="alice-book", chunk_id=row["chunk_id"]),
        lambda: chunks.soft_delete(owned, row["chunk_id"], owner_id="bob"),
        lambda: chunks.list_for_book(owned, "book-1", owner_id="bob"),
        lambda: _save(owned, owner_id=""),
        lambda: _save(owned, owner_id=chunks.LOCAL_OWNER_ID),
    ]:
        with pytest.raises(ValueError):
            operation()
        assert tuple(owned.execute("SELECT * FROM reading_chunks").fetchone()) == before
    assert chunks.all_chunks(owned, owner_id="bob") == []
    for note in ["TEST first edit", "TEST second edit"]:
        assert _save(owned, owner_id="alice", chunk_id=row["chunk_id"], user_note=note)["user_note"] == note
    chunks.soft_delete(owned, row["chunk_id"], owner_id="alice")
    with pytest.raises(ValueError, match="삭제"):
        _save(owned, owner_id="alice", chunk_id=row["chunk_id"])
    assert chunks.get(owned, row["chunk_id"], owner_id="alice") is None


def test_owner_is_required_and_postgres_has_no_local_fallback(owned):
    with pytest.raises(TypeError):
        chunks.save(owned, book_id="book-1", user_note="TEST")
    class Postgres:
        backend = "postgres"
        def execute(self, *args):
            pytest.fail("invalid actor reached SQL")
    for owner in [None, "", chunks.LOCAL_OWNER_ID]:
        with pytest.raises(ValueError):
            chunks.get(Postgres(), "TEST", owner_id=owner)


def test_inconsistent_existing_chunk_book_owner_is_rejected(owned):
    row = _save(owned, owner_id="alice")
    owned.execute("UPDATE reading_chunks SET book_id='bob-book' WHERE chunk_id=?", (row["chunk_id"],))
    owned.commit()
    with pytest.raises(ValueError):
        chunks.get(owned, row["chunk_id"], owner_id="alice")
    with pytest.raises(ValueError):
        chunks.soft_delete(owned, row["chunk_id"], owner_id="alice")


@pytest.mark.parametrize("start,end", [(None, None), (None, 10), (10, None), (10, 12)])
def test_nullable_duplicate_combinations(owned, start, end):
    _save(owned, owner_id="alice", page_start=start, page_end=end)
    with pytest.raises(chunks.DuplicateChunk):
        _save(owned, owner_id="alice", page_start=start, page_end=end)


def test_readonly_sqlite_denies_mutation_and_does_not_init(isolated_app, monkeypatch, tmp_path):
    conn = db.get_connection()
    _save(conn)
    conn.close()
    from lib import schema_maintenance
    monkeypatch.setattr(schema_maintenance, "initialize_schema", lambda *args: pytest.fail("schema init"))
    conn = db.get_readonly_connection()
    assert chunks.all_chunks(conn, owner_id=chunks.LOCAL_OWNER_ID)
    for sql in ["CREATE TABLE forbidden(id TEXT)", "UPDATE books SET title='forbidden'", "DELETE FROM reading_chunks"]:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(sql)
    conn.close()
    absent = tmp_path / "absent.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        db.get_readonly_connection(absent)
    assert not absent.exists()


def test_readonly_postgres_connection_policy(monkeypatch):
    import psycopg
    calls = []
    class Raw:
        read_only = False
        isolation_level = None
        def execute(self, sql):
            assert self.read_only and self.isolation_level == psycopg.IsolationLevel.REPEATABLE_READ
            calls.append(sql)
            return self
        def fetchone(self):
            return {"transaction_read_only": "on"}
        def close(self):
            calls.append("close")
    def connect(url, **kwargs):
        assert url == "TEST-NO-NETWORK" and kwargs["autocommit"] is False
        return Raw()
    monkeypatch.delenv("BOOK_BUTLER_DB_PATH", raising=False)
    monkeypatch.setattr(database, "database_url_from_env", lambda: "TEST-NO-NETWORK")
    monkeypatch.setattr(psycopg, "connect", connect)
    from lib import schema_maintenance
    monkeypatch.setattr(schema_maintenance, "initialize_schema", lambda *args: pytest.fail("schema init"))
    conn = db.get_readonly_connection()
    conn.close()
    assert calls == ["SHOW transaction_read_only", "close"]
