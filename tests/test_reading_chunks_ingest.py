from __future__ import annotations

from copy import deepcopy
import uuid

from lib import db, reading_chunks as chunks
from test_activity_inputs_app import isolated_app


def payload(**changes):
    value = {
        "schemaVersion": 1, "chunkId": str(uuid.uuid4()), "sourceApp": "today-library",
        "bookId": "book-1", "bookTitle": "읽는 책", "author": None, "isbn": None,
        "readDate": "2026-09-28", "pageStart": 10, "pageEnd": 12, "positionNote": None,
        "minutes": 5, "originalText": "읽은 문장", "userNote": "내 생각", "tags": ["묵상"],
        "illustrationTags": [], "contentTypes": ["meditation"],
        "createdAt": "2026-09-28T00:00:00.000Z", "updatedAt": "2026-09-28T00:00:00.000Z",
    }
    value.update(changes)
    return value


def owner_connection():
    conn = db.get_connection()
    conn.execute("UPDATE books SET owner_id=? WHERE id=?", ("user-1", "book-1"))
    conn.commit()
    return conn


def test_ingest_stores_once_and_does_not_overwrite_or_revive_deleted_chunk(isolated_app):
    conn = owner_connection()
    source = payload()
    first = chunks.ingest(conn, source, owner_id="user-1")
    assert first["result"] == "stored"
    row = chunks.get(conn, source["chunkId"], owner_id="user-1")
    assert row["source_app"] == "today-library" and row["source_ref"] is None
    assert row["book_title"] == "테스트 책" and row["original_text"] == "읽은 문장"
    assert chunks.ingest(conn, payload(**{**source, "originalText": "changed"}), owner_id="user-1")["result"] == "already_stored"
    assert chunks.get(conn, source["chunkId"], owner_id="user-1")["original_text"] == "읽은 문장"
    chunks.soft_delete(conn, source["chunkId"], owner_id="user-1")
    assert chunks.ingest(conn, source, owner_id="user-1")["result"] == "already_stored"
    assert chunks.get(conn, source["chunkId"], owner_id="user-1", include_deleted=True)["deleted_at"]
    conn.close()


def test_book_match_by_isbn_then_normalized_title_author_without_creation(isolated_app):
    conn = owner_connection()
    conn.execute("UPDATE books SET title=?, author=?, isbn=? WHERE id=?", ("  읽는 책 ", "저자 이름", "978-1-234", "book-1"))
    conn.commit()
    isbn = payload(bookId="missing", isbn="9781234", bookTitle="다른 제목", author="다른 저자")
    assert chunks.ingest(conn, isbn, owner_id="user-1")["result"] == "stored"
    title = payload(bookId=None, isbn=None, bookTitle="읽는  책", author=" 저자  이름 ")
    assert chunks.ingest(conn, title, owner_id="user-1")["result"] == "stored"
    missing = payload(bookId=None, isbn=None, bookTitle="없는 책", author=None)
    assert chunks.ingest(conn, missing, owner_id="user-1")["errorCode"] == "book_not_matched"
    assert conn.execute("SELECT count(*) FROM books").fetchone()[0] == 1
    conn.close()


def test_other_owner_collision_and_duplicate_suspicion_preserve_both(isolated_app):
    conn = owner_connection()
    first = payload()
    assert chunks.ingest(conn, first, owner_id="user-1")["result"] == "stored"
    assert chunks.ingest(conn, first, owner_id="user-2")["errorCode"] == "chunk_id_conflict"
    second = deepcopy(first); second["chunkId"] = str(uuid.uuid4())
    result = chunks.ingest(conn, second, owner_id="user-1")
    assert result["result"] == "stored" and result["duplicateSuspected"]
    assert conn.execute("SELECT count(*) FROM reading_chunks").fetchone()[0] == 2
    conn.close()


def test_invalid_payload_returns_rejected_field_without_db_write(isolated_app):
    conn = owner_connection()
    bad = payload(pageStart=30, pageEnd=12)
    result = chunks.ingest(conn, bad, owner_id="user-1")
    assert result["result"] == "rejected" and result["errorCode"] == "invalid_payload"
    assert result["errorField"] == "pageEnd"
    assert conn.execute("SELECT count(*) FROM reading_chunks").fetchone()[0] == 0
    conn.close()
