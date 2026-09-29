"""Offline pre-deployment audit. Never connects to Supabase or the real archive.

Historical initializer limitations are not the normal application startup path.
The historical initializer requires commit 51e5b0c in the local Git history.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from lib import db, schema, reading_chunks as chunks
from lib import schema_maintenance as maintenance
from lib.schema_preflight import inspect_schema_read_only, SchemaNotReady
from migration.load_db import SCHEMA
from test_activity_inputs_app import isolated_app, open_detail
from test_reading_chunks import _export_module, _save, _ids


def historical_schema():
    source = subprocess.check_output(
        ["git", "show", "51e5b0c:lib/schema.py"],
        cwd=Path(__file__).resolve().parents[1], text=True,
    )
    namespace = {}
    exec(compile(source, "historical_schema_51e5b0c", "exec"), namespace)
    return namespace


def fingerprint(conn):
    result = {}
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name != 'reading_chunks' ORDER BY name"
    ).fetchall()
    for (table,) in tables:
        columns = [tuple(row) for row in conn.execute(f'PRAGMA table_info("{table}")')]
        rows = sorted((tuple(row) for row in conn.execute(f'SELECT * FROM "{table}"')), key=repr)
        foreign_keys = [tuple(row) for row in conn.execute(f'PRAGMA foreign_key_list("{table}")')]
        payload = json.dumps([columns, foreign_keys, rows], ensure_ascii=False).encode()
        result[table] = (len(rows), hashlib.sha256(payload).hexdigest())
    return result


def populated_legacy(path):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    historical_schema()["ensure_schema"](conn)
    conn.executemany(
        "INSERT INTO books(id,title,author,isbn,current_page,owner_id) VALUES(?,?,?,?,?,?)",
        [(f"b{i}", f"TEST 합성 책 {i}", "검증 저자", f"978{i:010d}", i % 100, "audit-owner") for i in range(705)],
    )
    conn.executemany(
        "INSERT INTO activities(id,book_id,kind,text,quote,page,date,owner_id,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
        [(f"a{i}", f"b{i % 705}", i % 8, f"TEST 원문 {i}\n한글, '인용' %_", None if i % 2 else "합성 인용", i % 100, 1700000000+i, "audit-owner", 1700000000000000000+i) for i in range(5666)],
    )
    conn.execute("INSERT INTO photo_manifest VALUES('TEST.png','cover','b0','[]')")
    conn.execute("INSERT INTO source_book_state VALUES('b0',1,1,'읽는 중','TEST')")
    conn.execute("INSERT INTO app_migrations VALUES('TEST-baseline',1700000000)")
    conn.execute("INSERT INTO reading_sessions VALUES('s','b0',1700000000,1700000010,0,'saved','a0')")
    conn.execute("INSERT INTO profiles VALUES('audit-owner','test@example.invalid','TEST',1)")
    conn.execute("INSERT INTO reading_groups VALUES('g','TEST','audit-owner',1)")
    conn.execute("INSERT INTO group_members VALUES('g','audit-owner','owner',1)")
    conn.execute("INSERT INTO group_invites VALUES('t','g','audit-owner',1,NULL,NULL)")
    conn.execute("INSERT INTO daily_checkins(id,group_id,user_id,checked_on,is_read,created_at,updated_at) VALUES('c','g','audit-owner','2026-09-26',1,1,1)")
    conn.execute("INSERT INTO checkin_reactions VALUES('c','audit-owner','❤️',1)")
    conn.execute("INSERT INTO checkin_comments VALUES('comment','c','audit-owner','TEST',1)")
    conn.execute("INSERT INTO deletion_page_effect VALUES('a0',0,1)")
    conn.commit()
    return conn


def test_705_books_5666_records_all_existing_tables_unchanged_after_restart(tmp_path, record_property):
    path = tmp_path / "synthetic.sqlite"
    conn = populated_legacy(path)
    before = fingerprint(conn)
    for _ in range(3):
        maintenance.initialize_schema(conn, approved=True)
        assert fingerprint(conn) == before
    conn.close()
    for _ in range(3):
        reopened = db.get_connection(path)
        reopened.row_factory = None
        assert fingerprint(reopened) == before
        assert reopened.execute("PRAGMA foreign_key_check").fetchall() == []
        assert reopened.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        reopened.close()
    record_property("legacy_table_fingerprints", json.dumps(before, ensure_ascii=False))


def test_empty_sqlite_is_not_bootstrapped(tmp_path):
    path = tmp_path / "empty.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        db.get_connection(path)
    assert not path.exists()
    sqlite3.connect(path).close()
    with pytest.raises(SchemaNotReady):
        db.get_connection(path)


def test_partial_chunk_table_fails_without_repair_and_preserves_old_data(tmp_path):
    conn = populated_legacy(tmp_path / "partial.sqlite")
    before = fingerprint(conn)
    conn.execute("CREATE TABLE reading_chunks(chunk_id TEXT PRIMARY KEY)")
    conn.commit()
    with pytest.raises(sqlite3.OperationalError, match="no such column"):
        maintenance.initialize_schema(conn, approved=True)
    assert fingerprint(conn) == before
    assert len(conn.execute("PRAGMA table_info(reading_chunks)").fetchall()) == 1
    conn.close()


def test_missing_chunk_index_recreated_by_explicit_bootstrap(tmp_path):
    conn = populated_legacy(tmp_path / "missing-index.sqlite")
    maintenance.initialize_schema(conn, approved=True)
    conn.execute("DROP INDEX idx_reading_chunks_owner")  # disposable synthetic DB only
    before = fingerprint(conn)
    maintenance.initialize_schema(conn, approved=True)
    assert conn.execute("SELECT name FROM sqlite_master WHERE name='idx_reading_chunks_owner'").fetchone()
    assert fingerprint(conn) == before
    conn.close()


def test_wrong_same_named_index_is_detected(tmp_path):
    conn = populated_legacy(tmp_path / "wrong-index.sqlite")
    maintenance.initialize_schema(conn, approved=True)
    conn.execute("DROP INDEX idx_reading_chunks_owner")
    conn.execute("CREATE INDEX idx_reading_chunks_owner ON reading_chunks(book_title)")
    maintenance.initialize_schema(conn, approved=True)
    columns = [row[2] for row in conn.execute("PRAGMA index_info(idx_reading_chunks_owner)")]
    report = inspect_schema_read_only(conn)
    assert any(i.status == "INDEX_DEFINITION_MISMATCH" and i.object == "idx_reading_chunks_owner" for i in report.issues)
    conn.close()
    assert columns == ["book_title"]  # AUDIT-01: detect, never silently repair.


class RecordingPostgres:
    """Statement recorder only: does NOT simulate PostgreSQL type/lock/RLS semantics."""
    backend = "postgres"

    def __init__(self, fail_on=None):
        self.statements = []
        self.fail_on = fail_on

    def execute(self, statement):
        if self.fail_on and self.fail_on in statement:
            raise RuntimeError("TEST injected DDL failure")
        self.statements.append(statement.strip())


def test_postgres_sql_delta_is_exactly_one_table_and_three_indexes():
    current, old = RecordingPostgres(), RecordingPostgres()
    maintenance.initialize_schema(current, approved=True)
    historical_schema()["ensure_schema"](old)
    added = [s for s in current.statements if s not in old.statements]
    assert len(current.statements) == 31
    assert len(old.statements) == 27
    assert len(added) == 4
    assert all("reading_chunks" in s for s in added)
    assert all(s.startswith("CREATE") for s in added)
    assert all(s in current.statements for s in old.statements)
    assert not any(s.startswith(("INSERT", "UPDATE", "DELETE", "DROP")) for s in current.statements)


def test_postgres_initializer_replays_and_has_no_transaction_control():
    recorder = RecordingPostgres()
    maintenance.initialize_schema(recorder, approved=True)
    first = recorder.statements[:]
    maintenance.initialize_schema(recorder, approved=True)
    assert recorder.statements == first * 2
    failing = RecordingPostgres("idx_reading_chunks_owner")
    with pytest.raises(RuntimeError, match="injected"):
        maintenance.initialize_schema(failing, approved=True)
    assert any(s.startswith("CREATE TABLE IF NOT EXISTS reading_chunks") for s in failing.statements)
    assert not any(s.startswith(("BEGIN", "ROLLBACK", "COMMIT")) for s in failing.statements)


@pytest.mark.parametrize("overrides", [
    {"original_text":"", "user_note":""}, {"read_date":"2026-02-30"},
    {"page_start":-1}, {"page_start":10,"page_end":2}, {"minutes":-1},
    {"content_types":["invalid"]},
])
def test_invalid_input_rejected_without_inserting(isolated_app, overrides):
    conn = db.get_connection()
    with pytest.raises(ValueError):
        _save(conn, **overrides)
    assert conn.execute("SELECT COUNT(*) FROM reading_chunks").fetchone()[0] == 0
    conn.close()


def test_null_metadata_long_korean_multiline_and_reexport(isolated_app, tmp_path):
    conn = db.get_connection()
    conn.execute("UPDATE books SET isbn=NULL,title=? WHERE id='book-1'", ("한글 / : ? 제목 " * 20,))
    row = _save(conn, minutes=None, page_start=None, page_end=None, original_text="긴 한글 메모\n" * 20000)
    conn.close()
    exporter = _export_module()
    assert exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())["written"] == 1
    path = next((tmp_path / "독서조각").rglob("*.txt"))
    text = path.read_text()
    assert "ISBN: 미입력" in text and "읽은 시간: 미입력" in text
    assert "출처 앱: 읽담 (readdam)" in text and row["original_text"] in text
    assert ":" not in path.name and "?" not in path.name
    assert exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())["written"] == 0


def test_ui_edit_filter_and_soft_delete(isolated_app):
    conn = db.get_connection()
    row = _save(conn)
    conn.close()
    at = open_detail()
    at.text_input(key="chunk_tag_filter").set_value("없는태그").run()
    assert any("이 태그에 맞는 읽은 조각이 없습니다." in item.value for item in at.get("caption"))
    assert not any(button.key == f"chunk_edit_{row['chunk_id']}" for button in at.button)
    at.text_input(key="chunk_tag_filter").set_value("용서").run()
    at.button(key=f"chunk_edit_{row['chunk_id']}").click().run()
    at.text_area(key="chunk_input_user_note").set_value("TEST 수정")
    at.button(key="save_reading_chunk").click().run()
    assert not at.exception
    at.button(key=f"chunk_edit_{row['chunk_id']}").click().run()
    at.text_area(key="chunk_input_user_note").set_value("TEST 재수정")
    at.button(key="save_reading_chunk").click().run()
    assert not at.exception
    at.button(key=f"chunk_delete_{row['chunk_id']}").click().run()
    at.button(key=f"chunk_delete_confirm_{row['chunk_id']}").click().run()
    assert not at.exception
    conn = db.get_connection()
    deleted = chunks.get(conn, row["chunk_id"], include_deleted=True, owner_id=chunks.LOCAL_OWNER_ID)
    assert deleted["user_note"] == "TEST 재수정" and deleted["deleted_at"]
    conn.close()


def test_ui_edit_then_fresh_session_delete(isolated_app):
    conn = db.get_connection()
    row = _save(conn)
    conn.close()
    at = open_detail()
    at.button(key=f"chunk_edit_{row['chunk_id']}").click().run()
    at.text_area(key="chunk_input_user_note").set_value("TEST 새 세션 수정")
    at.button(key="save_reading_chunk").click().run()
    assert not at.exception
    conn = db.get_connection()
    assert chunks.get(conn, row["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID)["user_note"] == "TEST 새 세션 수정"
    conn.close()
    at = open_detail()
    at.button(key=f"chunk_delete_{row['chunk_id']}").click().run()
    at.button(key=f"chunk_delete_confirm_{row['chunk_id']}").click().run()
    assert not at.exception
    conn = db.get_connection()
    assert chunks.get(conn, row["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID) is None
    assert chunks.get(conn, row["chunk_id"], include_deleted=True, owner_id=chunks.LOCAL_OWNER_ID)["deleted_at"]
    conn.close()


def test_cross_book_existing_id_rejected(isolated_app):
    conn = db.get_connection()
    row = _save(conn)
    conn.execute("INSERT INTO books(id,title,owner_id) VALUES('other','TEST other book','other-owner')")
    conn.commit()
    with pytest.raises(ValueError):
        _save(conn, chunk_id=row["chunk_id"], book_id="other", user_note="TEST wrong book")
    conn.close()


def test_export_never_initializes_schema(isolated_app, tmp_path, monkeypatch):
    conn = db.get_connection()
    _save(conn)
    conn.close()
    def forbidden(conn):
        pytest.fail("export invoked ensure_schema")
    monkeypatch.setattr(maintenance, "initialize_schema", forbidden)
    _export_module().export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())


def test_index_write_failure_preserves_previous_index(isolated_app, tmp_path, monkeypatch):
    conn = db.get_connection()
    row = _save(conn)
    exporter = _export_module()
    exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    index = tmp_path / "독서조각" / "_index.csv"
    before = index.read_bytes()
    _save(conn, chunk_id=row["chunk_id"], user_note="TEST update")
    original = csv.DictWriter.writerow
    def failing(self, rowdict):
        if rowdict.get("chunkId") != "chunkId":
            raise OSError("TEST interrupted index data write")
        return original(self, rowdict)
    with monkeypatch.context() as scoped:
        scoped.setattr(csv.DictWriter, "writerow", failing)
        with pytest.raises(OSError):
            exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    assert index.read_bytes() == before
    conn.close()


@pytest.mark.parametrize("tag,stored,should_match", [('a_b','axb',False), ('a%b','axxxb',False), ('인용"태그','인용"태그',True)])
def test_exact_special_character_tag_filter(isolated_app, tag, stored, should_match):
    conn = db.get_connection()
    _save(conn, tags=[stored], illustration_tags=[])
    result = bool(chunks.list_for_book(conn, "book-1", tag=tag, owner_id=chunks.LOCAL_OWNER_ID))
    conn.close()
    assert result == should_match


def test_same_chunk_id_does_not_add_rows(isolated_app):
    conn = db.get_connection()
    row = _save(conn)
    for _ in range(5):
        _save(conn, chunk_id=row["chunk_id"])
    assert conn.execute("SELECT COUNT(*) FROM reading_chunks").fetchone()[0] == 1
    conn.close()


def index_rows(root):
    with (root / "독서조각" / "_index.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_date_pages_edit_moves_one_txt_and_missing_txt_is_rebuilt(isolated_app, tmp_path):
    conn = db.get_connection()
    row = _save(conn)
    exporter = _export_module()
    exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    previous = next((tmp_path / "독서조각").rglob("*.txt"))
    _save(conn, chunk_id=row["chunk_id"], read_date="2027-01-01", page_start=60, page_end=65, user_note="TEST v2")
    result = exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    assert result["moved"] == 1 and result["written"] == 1 and not previous.exists()
    current = tmp_path / "독서조각" / index_rows(tmp_path)[0]["상대경로"]
    assert "2027/2027-01" in current.as_posix() and "p60-65" in current.name
    current.unlink()  # test-generated tmp_path file only
    assert exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())["written"] == 1 and current.exists()
    conn.close()


def test_unindexed_existing_file_is_not_overwritten(isolated_app, tmp_path):
    conn = db.get_connection()
    row = _save(conn)
    conn.close()
    exporter = _export_module()
    target = tmp_path / "독서조각" / exporter.relative_path_for(row)
    target.parent.mkdir(parents=True)
    target.write_text("TEST existing sentinel")
    with pytest.raises(RuntimeError, match="덮어쓰지"):
        exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    assert target.read_text() == "TEST existing sentinel"


def test_eight_character_collision_uses_twelve_characters(isolated_app, tmp_path):
    conn = db.get_connection()
    for i, prefix in enumerate(["abcdef12-aaaa", "abcdef12-bbbb"]):
        _save(conn, chunk_id=prefix+"-4000-8000-000000000001", user_note=f"TEST {i}")
    conn.close()
    exporter = _export_module()
    assert exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())["written"] == 2
    assert len(list((tmp_path / "독서조각").rglob("*.txt"))) == 2
    assert exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())["written"] == 0


def test_duplicate_index_row_rejected(isolated_app, tmp_path):
    conn = db.get_connection()
    _save(conn)
    conn.close()
    exporter = _export_module()
    exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    index = tmp_path / "독서조각" / "_index.csv"
    with index.open("a") as handle:
        handle.write(index.read_text().splitlines(keepends=True)[1])
    with pytest.raises(RuntimeError):
        exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())


def test_changed_indexed_txt_detected(isolated_app, tmp_path):
    conn = db.get_connection()
    _save(conn)
    conn.close()
    exporter = _export_module()
    exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    path = next((tmp_path / "독서조각").rglob("*.txt"))
    path.write_text("TEST damaged content")
    with pytest.raises(RuntimeError):
        exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())


def test_retry_after_index_write_failure(isolated_app, tmp_path, monkeypatch):
    conn = db.get_connection()
    _save(conn)
    conn.close()
    exporter = _export_module()
    writer = exporter.write_index
    def fail(*args):
        raise OSError("TEST index write failure")
    monkeypatch.setattr(exporter, "write_index", fail)
    with pytest.raises(OSError):
        exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    monkeypatch.setattr(exporter, "write_index", writer)
    exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    assert len(index_rows(tmp_path)) == 1


def test_deleted_path_collision_does_not_overwrite(isolated_app, tmp_path):
    conn = db.get_connection()
    exporter = _export_module()
    rows = [_save(conn, chunk_id=f"abcdef12-abcd-4000-8000-{i:012d}", read_date=f"2026-09-{i:02d}", user_note=f"TEST {i}") for i in [1,2,3]]
    # Same deleted basename can arise from different prior date directories.
    exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    archive = tmp_path / "독서조각"
    victim = archive / "_삭제됨" / exporter.filename_for(rows[0], 12)
    short = archive / "_삭제됨" / exporter.filename_for(rows[0], 8)
    victim.parent.mkdir()
    victim.write_text("TEST protected collision sentinel")
    short.write_text("TEST shorter collision sentinel")
    chunks.soft_delete(conn, rows[0]["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID)
    try:
        exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    except RuntimeError:
        pass
    assert victim.read_text() == "TEST protected collision sentinel"
    conn.close()


def test_missing_source_app_rejected_by_db(isolated_app):
    conn = db.get_connection()
    row = _save(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE reading_chunks SET source_app=NULL WHERE chunk_id=?", (row["chunk_id"],))
    conn.rollback()
    conn.close()


def test_old_initializer_accepts_new_schema_without_altering_data(tmp_path):
    conn = populated_legacy(tmp_path / "rollback.sqlite")
    maintenance.initialize_schema(conn, approved=True)
    before = fingerprint(conn)
    historical_schema()["ensure_schema"](conn)
    assert fingerprint(conn) == before
    assert conn.execute("SELECT COUNT(*) FROM reading_chunks").fetchone()[0] == 0
    conn.close()
