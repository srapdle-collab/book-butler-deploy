"""Actual preflight/maintenance on isolated PostgreSQL WASM; never network/Secrets.

python -B tests/audit/pg_preflight_check.py /tmp/.../pglite/dist/index.js
"""
from contextlib import contextmanager
import hashlib
import json
import sys
from unittest.mock import patch

from pg_service_check import Bridge, Readonly, ROOT
from lib import schema_maintenance as maintenance
from lib.schema_preflight import inspect_schema_read_only, require_schema


class TransactionBridge(Bridge):
    @contextmanager
    def transaction(self):
        self.execute("BEGIN")
        try:
            yield
        except BaseException:
            self.execute("ROLLBACK")
            raise
        else:
            self.execute("COMMIT")


def snapshot(conn):
    state = {}
    for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename!='reading_chunks' ORDER BY tablename").fetchall():
        table = row["tablename"]
        state[table] = dict(
            rows=conn.execute(f'SELECT row_to_json(t) AS row FROM "{table}" t ORDER BY row_to_json(t)::text').fetchall(),
            columns=conn.execute("SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (table,)).fetchall(),
            constraints=conn.execute("SELECT conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid=%s::regclass ORDER BY conname", (table,)).fetchall())
    return {table: dict(count=len(value["rows"]), sha256=hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()) for table, value in state.items()}


def main():
    conn = TransactionBridge(sys.argv[1])
    cases = []
    try:
        conn.execute("CREATE ROLE anon NOLOGIN")
        conn.execute("CREATE ROLE authenticated NOLOGIN")
        conn.execute("CREATE ROLE service_role NOLOGIN BYPASSRLS")
        conn.execute("ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role")
        conn.execute("INSERT INTO books(id,title,author,isbn,current_page,owner_id) SELECT 'b'||i,'TEST 한글 책 '||i,'TEST 저자','978'||lpad(i::text,10,'0'),i%100,'TEST-owner' FROM generate_series(0,704) i")
        conn.execute("INSERT INTO activities(id,book_id,kind,text,quote,page,date,owner_id,updated_at) SELECT 'a'||i,'b'||(i%705),i%8,E'TEST 원문\\n한글 %_'||i,CASE WHEN i%2=0 THEN 'TEST 인용' END,i%100,1700000000+i,'TEST-owner',1700000000000000000+i FROM generate_series(0,5665) i")
        for statement in [
            "INSERT INTO photo_manifest VALUES('TEST.png','cover','b0','[]')",
            "INSERT INTO source_book_state VALUES('b0',1,1,'읽는 중','TEST')",
            "INSERT INTO app_migrations VALUES('TEST-baseline',1700000000)",
            "INSERT INTO deletion_page_effect VALUES('a0',0,1)",
            "INSERT INTO reading_sessions VALUES('s','b0',1700000000,1700000010,0,'saved','a0')",
            "INSERT INTO profiles VALUES('TEST-owner','test@example.invalid','TEST',1)",
            "INSERT INTO reading_groups VALUES('g','TEST','TEST-owner',1)",
            "INSERT INTO group_members VALUES('g','TEST-owner','owner',1)",
            "INSERT INTO group_invites VALUES('t','g','TEST-owner',1,NULL,NULL)",
            "INSERT INTO daily_checkins(id,group_id,user_id,checked_on,is_read,created_at,updated_at) VALUES('c','g','TEST-owner','2026-09-26',1,1,1)",
            "INSERT INTO checkin_reactions VALUES('c','TEST-owner','❤️',1)",
            "INSERT INTO checkin_comments VALUES('comment','c','TEST-owner','TEST',1)",
        ]:
            conn.execute(statement)
        before = snapshot(conn)
        for _ in range(4):
            readonly = Readonly(conn)
            try:
                assert require_schema(readonly).status == "OK"
            finally:
                readonly.close()
        cases.append("normal + repeated READ ONLY preflight: PASS")
        variations = [
            ("DROP TABLE reading_chunks", "MISSING_TABLE"),
            ("ALTER TABLE reading_chunks DROP COLUMN minutes", "MISSING_COLUMN"),
            ("DROP INDEX idx_reading_chunks_owner", "MISSING_INDEX"),
            ("ALTER TABLE reading_chunks ALTER COLUMN minutes TYPE bigint", "UNSUPPORTED_SCHEMA"),
            ("ALTER TABLE reading_chunks ALTER COLUMN owner_id DROP NOT NULL", "UNSUPPORTED_SCHEMA"),
            ("ALTER TABLE reading_chunks ALTER COLUMN tags SET DEFAULT '{}'", "UNSUPPORTED_SCHEMA"),
            ("ALTER TABLE reading_chunks DROP CONSTRAINT reading_chunks_source_app_check", "UNSUPPORTED_SCHEMA"),
            ("ALTER TABLE reading_chunks ADD COLUMN future_version TEXT", "UNSUPPORTED_SCHEMA"),
            ("CREATE TEMP TABLE books(id TEXT)", "UNSUPPORTED_SCHEMA"),
        ]
        for ddl, expected in variations:
            conn.execute("BEGIN")
            conn.execute(ddl)
            report = inspect_schema_read_only(conn)
            assert expected in {i.status for i in report.issues}, report.to_dict()
            conn.execute("ROLLBACK")
            cases.append(f"{ddl}: {expected}, no repair, PASS")
        conn.execute("BEGIN")
        conn.execute("DROP INDEX idx_reading_chunks_owner")
        conn.execute("CREATE INDEX idx_reading_chunks_owner ON reading_chunks(book_title)")
        report = inspect_schema_read_only(conn)
        assert report.status == "INDEX_DEFINITION_MISMATCH", report.to_dict()
        assert not maintenance.plan_reading_chunks(conn)["applicable"]
        assert "book_title" in conn.execute("SELECT pg_get_indexdef('idx_reading_chunks_owner'::regclass) AS definition").fetchone()["definition"]
        conn.execute("ROLLBACK")
        cases.append("AUDIT-01 wrong same-name index detected without repair: PASS")
        conn.execute("DROP TABLE reading_chunks")
        plan = maintenance.plan_reading_chunks(conn)
        assert plan["applicable"] and len(plan["statements"]) == 9
        assert conn.execute("SELECT to_regclass('public.reading_chunks') AS name").fetchone()["name"] is None
        execute = conn.execute
        def fail_midway(statement, params=()):
            if statement.startswith("CREATE INDEX idx_reading_chunks_owner"):
                raise RuntimeError("TEST injected mid-DDL failure")
            return execute(statement, params)
        with patch.object(conn, "execute", fail_midway):
            try:
                maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
            except RuntimeError as error:
                assert "TEST injected" in str(error)
            else:
                raise AssertionError("Expected failure")
        assert conn.execute("SELECT to_regclass('public.reading_chunks') AS name").fetchone()["name"] is None
        assert snapshot(conn) == before
        cases.append("mid-DDL failure rolls back table and all indexes: PASS")

        def skip_service_role_revoke(statement, params=()):
            if statement == "REVOKE ALL PRIVILEGES ON TABLE public.reading_chunks FROM service_role":
                return None
            return execute(statement, params)
        with patch.object(conn, "execute", skip_service_role_revoke):
            try:
                maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
            except maintenance.SecurityPostcheckFailed as error:
                assert error.report["privileges"]["service_role"]["SELECT"] is True
            else:
                raise AssertionError("Expected security post-check failure")
        assert conn.execute("SELECT to_regclass('public.reading_chunks') AS name").fetchone()["name"] is None
        assert snapshot(conn) == before
        cases.append("missing REVOKE is caught by post-check and rolls back entire plan: PASS")

        maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
        assert require_schema(conn).ok
        security = maintenance.inspect_reading_chunks_security(conn)
        assert security["ok"] and security["rls_enabled"] and not security["policies"]
        assert all(not allowed for role in maintenance.EXTERNAL_TABLE_ROLES
                   for allowed in security["privileges"][role].values())
        assert all(security["app_role"]["privileges"].values())
        conn.execute("CREATE POLICY unexpected_test_policy ON reading_chunks FOR SELECT USING (true)")
        assert maintenance.inspect_reading_chunks_security(conn)["ok"] is False
        conn.execute("DROP POLICY unexpected_test_policy ON reading_chunks")
        for _ in range(3):
            noop = maintenance.plan_reading_chunks(conn)
            assert noop["statements"] == []
            maintenance.apply_reading_chunks(conn, approved_plan_sha256=noop["plan_sha256"])
        cases.append("approved 9-DDL atomic private-default plan + repeated secure no-op plans: PASS")
        conn.execute("DROP INDEX idx_reading_chunks_owner")
        plan = maintenance.plan_reading_chunks(conn)
        assert plan["applicable"] and len(plan["statements"]) == 1
        maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
        assert require_schema(conn).ok and snapshot(conn) == before
        cases.append("missing-index-only approved plan + checksums: PASS")
        print(json.dumps(dict(result="PASS", engine="PostgreSQL WASM; NOT Supabase/PgBouncer/psycopg wire", cases=cases,
                              legacy_checksums_before=before, legacy_checksums_after=snapshot(conn)), ensure_ascii=False, indent=2))
    finally:
        conn.stop()


if __name__ == "__main__":
    main()
