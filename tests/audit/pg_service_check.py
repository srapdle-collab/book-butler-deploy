"""Run actual Python chunk service + exporter SQL against in-memory PostgreSQL.

No network/secret/env loading. This bridge does NOT replace a psycopg/PgBouncer
integration test. Usage: python -B tests/audit/pg_service_check.py PGLITE_MODULE
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import reading_chunks as chunks
from tools import export_chunks


class Cursor:
    def __init__(self, result):
        self.rows = result["rows"]
        self.rowcount = result["rowcount"]
    def fetchone(self):
        return self.rows[0] if self.rows else None
    def fetchall(self):
        return self.rows


class Bridge:
    backend = "postgres"
    def __init__(self, module):
        self.process = subprocess.Popen(["node", "tests/audit/pg_service_bridge.mjs", module], cwd=ROOT,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        assert json.loads(self.process.stdout.readline()) == {"ready": True}
    def execute(self, sql, params=()):
        self.process.stdin.write(json.dumps(dict(sql=sql, params=params)) + "\n")
        self.process.stdin.flush()
        result = json.loads(self.process.stdout.readline())
        if "error" in result:
            raise RuntimeError(f"{result['code']}: {result['error']}")
        return Cursor(result)
    def commit(self):
        pass  # each bridge query is autocommit unless explicitly BEGIN-ed
    def stop(self):
        self.process.stdin.close()
        assert self.process.wait(timeout=20) == 0
        self.process.stdout.close()


class Readonly:
    backend = "postgres"
    def __init__(self, conn):
        self.conn = conn
        conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        assert conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
    def execute(self, sql, params=()):
        return self.conn.execute(sql, params)
    def close(self):
        self.conn.execute("ROLLBACK")


def rejected(call, error=ValueError):
    try:
        call()
    except error:
        return
    raise AssertionError("Expected operation to be rejected")


def fingerprint(conn):
    state = {}
    for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename!='reading_chunks' ORDER BY tablename").fetchall():
        table = row["tablename"]
        state[table] = conn.execute(f'SELECT row_to_json(t) AS row FROM "{table}" t ORDER BY row_to_json(t)::text').fetchall()
    return hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main():
    conn = Bridge(sys.argv[1])
    try:
        conn.execute("INSERT INTO books(id,title,isbn,owner_id) VALUES ('a','TEST 한글 책','123','alice'),('a2','TEST other Alice',NULL,'alice'),('b','TEST Bob',NULL,'bob')")
        conn.execute("INSERT INTO activities(id,book_id,kind,date,text,owner_id) VALUES ('activity','a',2,1,'TEST unchanged','alice')")
        before = fingerprint(conn)
        def save(**overrides):
            values = dict(owner_id="alice", book_id="a", read_date="2026-09-27", original_text="TEST 원문", user_note="TEST 메모", minutes=12, tags=['a%b', 'a_b', '인용"태그', '\\태그'])
            values.update(overrides)
            return chunks.save(conn, **values)
        row = save()
        rejected(lambda: save(), chunks.DuplicateChunk)
        for start, end in [(None, 10), (10, None), (10, 12)]:
            save(page_start=start, page_end=end)
            rejected(lambda: save(page_start=start, page_end=end), chunks.DuplicateChunk)
        for tag in ['a%b', 'a_b', '인용"태그', '\\태그']:
            assert len(chunks.list_for_book(conn, "a", owner_id="alice", tag=tag)) == 4
        assert not chunks.list_for_book(conn, "a", owner_id="alice", tag="aXb")
        snapshot = conn.execute("SELECT * FROM reading_chunks ORDER BY chunk_id").fetchall()
        for call in [lambda: save(owner_id="bob"),
                     lambda: save(owner_id="bob", book_id="b", chunk_id=row["chunk_id"]),
                     lambda: save(book_id="a2", chunk_id=row["chunk_id"]),
                     lambda: chunks.soft_delete(conn, row["chunk_id"], owner_id="bob"),
                     lambda: chunks.list_for_book(conn, "a", owner_id="bob"),
                     lambda: save(owner_id=chunks.LOCAL_OWNER_ID)]:
            rejected(call)
            assert conn.execute("SELECT * FROM reading_chunks ORDER BY chunk_id").fetchall() == snapshot
        assert chunks.get(conn, row["chunk_id"], owner_id="bob") is None
        for note in ["TEST first edit", "TEST second edit"]:
            row = save(chunk_id=row["chunk_id"], user_note=note)
            assert row["user_note"] == note
        for statement in ["CREATE TABLE forbidden(id int)", "UPDATE books SET title='forbidden'", "DELETE FROM reading_chunks"]:
            readonly = Readonly(conn)
            try:
                rejected(lambda: readonly.execute(statement), RuntimeError)
            finally:
                readonly.close()
        with tempfile.TemporaryDirectory(prefix="readdam-pg-export-") as directory:
            root = Path(directory)
            with patch.object(export_chunks.db, "get_readonly_connection", lambda: Readonly(conn)):
                assert export_chunks.export(root, owner_id="alice", chunk_ids=[row["chunk_id"]])["written"] == 1
                assert export_chunks.export(root, owner_id="alice", chunk_ids=[row["chunk_id"]])["written"] == 0
                assert len(list(root.rglob("*.txt"))) == 1
                chunks.soft_delete(conn, row["chunk_id"], owner_id="alice")
                assert export_chunks.export(root, owner_id="alice", chunk_ids=[row["chunk_id"]])["moved"] == 1
        rejected(lambda: save(chunk_id=row["chunk_id"]))
        assert chunks.get(conn, row["chunk_id"], owner_id="alice") is None
        assert chunks.get(conn, row["chunk_id"], owner_id="alice", include_deleted=True)["deleted_at"]
        after = fingerprint(conn)
        assert before == after
        print(json.dumps(dict(result="PASS", backend="PostgreSQL WASM, actual Python service, not psycopg wire", checksum_before=before, checksum_after=after,
                              checks=["NULL combinations", "owner/book rejection", "CRUD", "special tags", "readonly SQL rejection", "scoped export/reexport/delete", "14 legacy tables unchanged"]), ensure_ascii=False, indent=2))
    finally:
        conn.stop()


if __name__ == "__main__":
    main()
