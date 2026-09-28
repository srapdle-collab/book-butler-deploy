"""Synthetic SQLite only: schema inspection cannot repair or mutate anything."""
from contextlib import contextmanager
import json
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from lib import db, schema_maintenance as maintenance
from lib.schema_preflight import inspect_schema_read_only, require_schema, SchemaNotReady
from test_activity_inputs_app import isolated_app, APP_PATH
from test_reading_chunks_audit import populated_legacy, fingerprint


@pytest.fixture
def ready(tmp_path):
    path = tmp_path / "TEST-preflight.sqlite"
    conn = populated_legacy(path)
    maintenance.initialize_schema(conn, approved=True)
    yield conn, path
    conn.close()


def test_repeated_preflight_readonly_no_ddl_dml_checksums(ready):
    conn, path = ready
    before = fingerprint(conn), path.read_bytes()
    statements = []
    conn.set_trace_callback(statements.append)
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_PRAGMA}
    conn.set_authorizer(lambda action, *args: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
    for _ in range(4):
        assert require_schema(conn).status == "OK"
    # Python 3.9 sqlite callback removal does not accept None reliably.
    conn.set_authorizer(lambda *args: sqlite3.SQLITE_OK)
    conn.set_trace_callback(None)
    assert all(s.lstrip().upper().startswith(("SELECT", "PRAGMA")) for s in statements)
    assert (fingerprint(conn), path.read_bytes()) == before
    for _ in range(3):
        reopened = db.get_connection(path)
        reopened.close()
    assert path.read_bytes() == before[1]


@pytest.mark.parametrize("ddl,status", [
    ("DROP TABLE reading_chunks", "MISSING_TABLE"),
    ("ALTER TABLE reading_chunks DROP COLUMN minutes", "MISSING_COLUMN"),
    ("DROP INDEX idx_reading_chunks_owner", "MISSING_INDEX"),
    ("ALTER TABLE reading_chunks ADD COLUMN unsupported_version TEXT", "UNSUPPORTED_SCHEMA"),
    ("CREATE TEMP TABLE books(id TEXT)", "UNSUPPORTED_SCHEMA"),
])
def test_schema_drift_blocks_without_repair(ready, ddl, status):
    conn, path = ready
    conn.execute(ddl)
    conn.commit()
    before = path.read_bytes(), fingerprint(conn)
    with pytest.raises(SchemaNotReady) as failure:
        require_schema(conn)
    assert status in {i.status for i in failure.value.report.issues}
    assert (path.read_bytes(), fingerprint(conn)) == before


@pytest.mark.parametrize("definition", [
    "ON reading_chunks(book_title)",
    "ON reading_chunks(owner_id, deleted_at, updated_at)",
    "ON reading_chunks(owner_id, updated_at DESC, deleted_at)",
    "ON reading_chunks(owner_id, deleted_at, updated_at DESC) WHERE deleted_at IS NULL",
    "ON books(owner_id)",
])
def test_same_index_name_definition_mismatch_audit_01(ready, definition):
    conn, path = ready
    conn.execute("DROP INDEX idx_reading_chunks_owner")
    conn.execute("CREATE INDEX idx_reading_chunks_owner " + definition)
    conn.commit()
    before = path.read_bytes()
    report = inspect_schema_read_only(conn)
    assert any(i.status == "INDEX_DEFINITION_MISMATCH" and i.object == "idx_reading_chunks_owner" for i in report.issues)
    plan = maintenance.plan_reading_chunks(conn)
    assert not plan["applicable"] and not plan["statements"]
    with pytest.raises(PermissionError):
        maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
    assert path.read_bytes() == before


@pytest.mark.parametrize("old,new", [
    ("owner_id TEXT NOT NULL", "owner_id TEXT"),
    ("minutes INTEGER", "minutes TEXT"),
    ("DEFAULT '[]'", "DEFAULT '{}'"),
    ("source_ref TEXT UNIQUE", "source_ref TEXT"),
    ("REFERENCES books(id)", "REFERENCES books(id) ON DELETE CASCADE"),
    ("CHECK(source_app IN ('readdam', 'today-library'))", "CHECK(source_app IN ('readdam', 'today-library') OR 1=1)"),
])
def test_chunk_structure_contract_not_just_column_names(ready, old, new):
    conn, _ = ready
    ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='reading_chunks'").fetchone()[0]
    assert old in ddl
    conn.execute("DROP TABLE reading_chunks")
    conn.execute(ddl.replace(old, new))
    report = inspect_schema_read_only(conn)
    assert "UNSUPPORTED_SCHEMA" in {i.status for i in report.issues}


def test_unknown_metadata_error_sanitized_no_repair():
    class Broken:
        def execute(self, *_):
            raise RuntimeError("postgresql://SECRET@test/password")
    report = inspect_schema_read_only(Broken())
    assert report.status == "UNKNOWN_ERROR"
    assert "SECRET" not in json.dumps(report.to_dict())


def test_explicit_additive_maintenance_approval_and_replay(tmp_path):
    conn = populated_legacy(tmp_path / "TEST-existing.sqlite")
    before = fingerprint(conn)
    plan = maintenance.plan_reading_chunks(conn)
    assert plan["applicable"] and len(plan["statements"]) == 4
    assert all(s.startswith("CREATE") and "reading_chunks" in s for s in plan["statements"])
    with pytest.raises(PermissionError):
        maintenance.initialize_schema(conn)
    with pytest.raises(PermissionError):
        maintenance.apply_reading_chunks(conn, approved_plan_sha256="NOT-APPROVED")
    assert inspect_schema_read_only(conn).status == "MISSING_TABLE"
    maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
    assert require_schema(conn).ok and fingerprint(conn) == before
    # Stale plans must be reviewed again, not blindly reapplied.
    with pytest.raises(PermissionError):
        maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
    noop = maintenance.plan_reading_chunks(conn)
    assert noop["statements"] == []
    maintenance.apply_reading_chunks(conn, approved_plan_sha256=noop["plan_sha256"])
    conn.execute("DROP INDEX idx_reading_chunks_owner")
    plan = maintenance.plan_reading_chunks(conn)
    assert len(plan["statements"]) == 1
    maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
    assert require_schema(conn).ok and fingerprint(conn) == before
    conn.close()


def test_postgres_missing_table_plan_creates_then_locks_external_roles(monkeypatch):
    report = SimpleNamespace(
        issues=(SimpleNamespace(status="MISSING_TABLE", object="reading_chunks"),),
        to_dict=lambda: {"status": "MISSING_TABLE", "issues": []},
    )
    conn = SimpleNamespace(backend="postgres")
    monkeypatch.setattr(maintenance, "inspect_schema_read_only", lambda _: report)

    plan = maintenance.plan_reading_chunks(conn)

    assert plan["applicable"]
    assert len(plan["statements"]) == 9
    assert plan["statements"][0].startswith("CREATE TABLE public.reading_chunks")
    assert [statement.split()[2] for statement in plan["statements"][1:4]] == [
        "idx_reading_chunks_book",
        "idx_reading_chunks_owner",
        "idx_reading_chunks_duplicate",
    ]
    assert plan["statements"][4] == "ALTER TABLE public.reading_chunks ENABLE ROW LEVEL SECURITY"
    assert plan["statements"][5:] == [
        "REVOKE ALL PRIVILEGES ON TABLE public.reading_chunks FROM PUBLIC",
        "REVOKE ALL PRIVILEGES ON TABLE public.reading_chunks FROM anon",
        "REVOKE ALL PRIVILEGES ON TABLE public.reading_chunks FROM authenticated",
        "REVOKE ALL PRIVILEGES ON TABLE public.reading_chunks FROM service_role",
    ]


def test_postgres_security_postcheck_runs_inside_same_transaction(monkeypatch):
    events = []

    class Connection:
        backend = "postgres"

        @contextmanager
        def transaction(self):
            events.append("BEGIN")
            try:
                yield
            except BaseException:
                events.append("ROLLBACK")
                raise
            else:
                events.append("COMMIT")

        def execute(self, statement, params=()):
            assert events[0] == "BEGIN" and "COMMIT" not in events and "ROLLBACK" not in events
            events.append(statement)

    plan = {
        "applicable": True,
        "plan_sha256": "approved",
        "statements": ["CREATE TABLE public.reading_chunks(id text)", "ALTER TABLE public.reading_chunks ENABLE ROW LEVEL SECURITY"],
    }
    monkeypatch.setattr(maintenance, "plan_reading_chunks", lambda _: plan)
    monkeypatch.setattr(maintenance, "require_schema", lambda _: events.append("STRUCTURE_POSTCHECK"))
    monkeypatch.setattr(maintenance, "require_reading_chunks_security", lambda _: events.append("SECURITY_POSTCHECK"))

    maintenance.apply_reading_chunks(Connection(), approved_plan_sha256="approved")

    assert events == [
        "BEGIN",
        "CREATE TABLE public.reading_chunks(id text)",
        "ALTER TABLE public.reading_chunks ENABLE ROW LEVEL SECURITY",
        "STRUCTURE_POSTCHECK",
        "SECURITY_POSTCHECK",
        "COMMIT",
    ]


def test_postgres_security_postcheck_failure_rolls_back(monkeypatch):
    events = []

    class Connection:
        backend = "postgres"

        @contextmanager
        def transaction(self):
            events.append("BEGIN")
            try:
                yield
            except BaseException:
                events.append("ROLLBACK")
                raise
            else:
                events.append("COMMIT")

        def execute(self, statement, params=()):
            events.append(statement)

    plan = {"applicable": True, "plan_sha256": "approved", "statements": ["CREATE TABLE public.reading_chunks(id text)"]}
    monkeypatch.setattr(maintenance, "plan_reading_chunks", lambda _: plan)
    monkeypatch.setattr(maintenance, "require_schema", lambda _: None)
    monkeypatch.setattr(
        maintenance,
        "require_reading_chunks_security",
        lambda _: (_ for _ in ()).throw(RuntimeError("TEST security post-check failure")),
    )

    with pytest.raises(RuntimeError, match="security post-check"):
        maintenance.apply_reading_chunks(Connection(), approved_plan_sha256="approved")
    assert events[-1] == "ROLLBACK"
    assert "COMMIT" not in events


def test_maintenance_failure_rolls_back_entire_additive_plan(tmp_path, monkeypatch):
    conn = populated_legacy(tmp_path / "TEST-rollback.sqlite")
    before = fingerprint(conn)
    plan = maintenance.plan_reading_chunks(conn)
    def fail(_):
        raise RuntimeError("TEST post-DDL failure")
    monkeypatch.setattr(maintenance, "require_schema", fail)
    with pytest.raises(RuntimeError, match="TEST"):
        maintenance.apply_reading_chunks(conn, approved_plan_sha256=plan["plan_sha256"])
    assert inspect_schema_read_only(conn).status == "MISSING_TABLE"
    assert fingerprint(conn) == before
    conn.close()


def test_empty_or_partial_legacy_schema_not_automatically_bootstrapped(tmp_path):
    conn = sqlite3.connect(tmp_path / "TEST-empty.sqlite")
    plan = maintenance.plan_reading_chunks(conn)
    assert not plan["applicable"] and plan["statements"] == []
    conn.execute("CREATE TABLE reading_chunks(chunk_id TEXT PRIMARY KEY)")
    assert not maintenance.plan_reading_chunks(conn)["applicable"]
    conn.close()


def test_missing_table_with_index_name_collision_is_blocked(ready):
    conn, _ = ready
    conn.execute("DROP TABLE reading_chunks")
    conn.execute("CREATE INDEX idx_reading_chunks_owner ON books(owner_id)")
    report = inspect_schema_read_only(conn)
    assert "INDEX_DEFINITION_MISMATCH" in {i.status for i in report.issues}
    assert not maintenance.plan_reading_chunks(conn)["applicable"]


def test_cli_plan_readonly_and_explicit_application(tmp_path):
    path = tmp_path / "TEST-cli.sqlite"
    conn = populated_legacy(path)
    conn.close()
    before = path.read_bytes()
    def run(tool, *extra):
        return subprocess.run([sys.executable, "-B", f"tools/{tool}.py", "--sqlite", str(path), *extra],
                              cwd=APP_PATH.parent, capture_output=True, text=True)
    missing = run("schema_preflight")
    assert missing.returncode == 2 and json.loads(missing.stdout)["status"] == "MISSING_TABLE"
    plan = json.loads(run("schema_maintenance").stdout)
    assert path.read_bytes() == before
    assert run("schema_maintenance", "--apply").returncode == 2
    assert path.read_bytes() == before
    assert run("schema_maintenance", "--apply", "--approve-plan", plan["plan_sha256"]).returncode == 0
    assert run("schema_preflight").returncode == 0


@pytest.mark.parametrize("view", ["책장", "책 상세", "통계", "타임라인"])
def test_app_views_never_call_schema_mutation(isolated_app, monkeypatch, view):
    traced = []
    connect = db.connect
    def recording(*args, **kwargs):
        conn = connect(*args, **kwargs)
        conn.set_trace_callback(traced.append)
        return conn
    monkeypatch.setattr(db, "connect", recording)
    monkeypatch.setattr(maintenance, "initialize_schema", lambda *a, **k: pytest.fail("automatic init"))
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["view"] = view
    at.session_state["selected_book_id"] = "book-1"
    at.run()
    assert not at.exception and not at.error
    assert traced and not any(s.lstrip().upper().startswith(("CREATE", "ALTER", "DROP", "REINDEX")) for s in traced)


def test_app_schema_failure_stops_before_user_data_changes(isolated_app):
    path, _ = isolated_app
    conn = sqlite3.connect(path)
    conn.execute("DROP INDEX idx_reading_chunks_owner")
    conn.commit()
    conn.close()
    before = path.read_bytes()
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not at.exception
    assert any("MISSING_INDEX" in item.value for item in at.error)
    assert path.read_bytes() == before


def test_login_then_render_has_no_ddl(isolated_app, monkeypatch):
    from lib import auth, ownership
    path, _ = isolated_app
    conn = sqlite3.connect(path)
    conn.execute("UPDATE books SET owner_id='TEST-owner'")
    conn.commit()
    conn.close()
    before = path.read_bytes()
    traced = []
    connect = db.connect
    def recording(*args, **kwargs):
        conn = connect(*args, **kwargs)
        conn.set_trace_callback(traced.append)
        return conn
    monkeypatch.setattr(db, "connect", recording)
    monkeypatch.setattr(auth, "is_configured", lambda: True)
    monkeypatch.setattr(auth, "sign_in", lambda *args: auth.AuthSession(
        auth.AuthUser("TEST-owner", "test@example.invalid"), "TEST-token", "TEST-refresh", 9999999999
    ))
    # No external authentication service or owner-email secret lookup.
    monkeypatch.setattr(ownership, "configured_owner_email", lambda: "")
    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not traced  # Login screen stops before DB connection.
    at.text_input(key="login_email").set_value("test@example.invalid")
    at.text_input(key="login_password").set_value("TEST-password")
    at.button(key="sign_in").click().run()
    assert not at.exception and not at.error
    assert traced and not any(s.lstrip().upper().startswith(("CREATE", "ALTER", "DROP", "REINDEX")) for s in traced)
    assert path.read_bytes() == before


def test_export_drift_stops_before_archive_files(isolated_app, tmp_path):
    from tools.export_chunks import export
    path, _ = isolated_app
    conn = sqlite3.connect(path)
    conn.execute("DROP INDEX idx_reading_chunks_owner")
    conn.close()
    archive = tmp_path / "TEST-archive"
    with pytest.raises(SchemaNotReady):
        export(archive, owner_id="local-owner", chunk_ids=["TEST-id"])
    assert not archive.exists() or not list(archive.rglob("*.txt"))
