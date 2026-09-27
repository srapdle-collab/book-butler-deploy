"""Explicit maintenance only. Never imported/called by app connection or preflight.

The historical full initializer is retained for explicit offline bootstrap tools
and synthetic fixtures. Production 1A maintenance uses the narrow plan below.
"""
from lib.schema import POSTGRES_SCHEMA
from lib import database
from lib.schema_preflight import INDEX_DDL, INDEX_TABLE, TABLE_DDL, inspect_schema_read_only, require_schema
import hashlib
import json

EXTERNAL_TABLE_ROLES = ("PUBLIC", "anon", "authenticated", "service_role")
TABLE_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE")


class SecurityPostcheckFailed(RuntimeError):
    def __init__(self, report):
        self.report = report
        super().__init__("reading_chunks 보안 post-check 실패. 전체 maintenance transaction을 중단합니다.")


def _dict_rows(cursor):
    names = [item[0] for item in cursor.description] if getattr(cursor, "description", None) else None
    return [dict(row) if hasattr(row, "keys") else dict(zip(names, row)) for row in cursor.fetchall()]


def _dict_row(cursor):
    rows = _dict_rows(cursor)
    return rows[0] if rows else None


def inspect_reading_chunks_security(conn):
    """Read-only PostgreSQL ACL/RLS post-condition check for the new table."""
    if not database.is_postgres(conn):
        return dict(status="NOT_APPLICABLE", ok=True, backend="sqlite")
    try:
        table = _dict_row(conn.execute("""SELECT c.relrowsecurity AS rls_enabled,
                c.relforcerowsecurity AS rls_forced, owner.rolname AS table_owner,
                current_user AS current_user, session_user AS session_user
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            JOIN pg_catalog.pg_roles owner ON owner.oid=c.relowner
            WHERE n.nspname='public' AND c.relname='reading_chunks' AND c.relkind IN ('r','p')"""))
        if table is None:
            return dict(status="MISSING_TABLE", ok=False, backend="postgres")

        privileges = {}
        public = _dict_row(conn.execute("""SELECT
                COALESCE(bool_or(a.privilege_type='SELECT'), false) AS "SELECT",
                COALESCE(bool_or(a.privilege_type='INSERT'), false) AS "INSERT",
                COALESCE(bool_or(a.privilege_type='UPDATE'), false) AS "UPDATE",
                COALESCE(bool_or(a.privilege_type='DELETE'), false) AS "DELETE"
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            LEFT JOIN LATERAL pg_catalog.aclexplode(
                COALESCE(c.relacl, pg_catalog.acldefault('r', c.relowner))) a ON a.grantee=0
            WHERE n.nspname='public' AND c.relname='reading_chunks'"""))
        privileges["PUBLIC"] = {name: bool(public[name]) for name in TABLE_PRIVILEGES}

        role_rows = _dict_rows(conn.execute("""SELECT r.rolname AS role_name,
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'SELECT') AS "SELECT",
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'INSERT') AS "INSERT",
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'UPDATE') AS "UPDATE",
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'DELETE') AS "DELETE"
            FROM pg_catalog.pg_roles r
            WHERE r.rolname IN ('anon','authenticated','service_role')"""))
        for row in role_rows:
            privileges[row["role_name"]] = {name: bool(row[name]) for name in TABLE_PRIVILEGES}

        app = _dict_row(conn.execute("""SELECT r.rolname AS role_name,
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'SELECT') AS "SELECT",
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'INSERT') AS "INSERT",
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'UPDATE') AS "UPDATE",
                pg_catalog.has_table_privilege(r.oid, 'public.reading_chunks', 'DELETE') AS "DELETE"
            FROM pg_catalog.pg_roles r WHERE r.rolname='postgres'"""))
        policies = _dict_rows(conn.execute("""SELECT policyname, cmd
            FROM pg_catalog.pg_policies
            WHERE schemaname='public' AND tablename='reading_chunks'
            ORDER BY policyname"""))

        external_locked = set(privileges) == set(EXTERNAL_TABLE_ROLES) and all(
            not allowed for role in EXTERNAL_TABLE_ROLES for allowed in privileges[role].values())
        app_access = app is not None and all(bool(app[name]) for name in TABLE_PRIVILEGES)
        identity_matches = (table["table_owner"] == "postgres" and table["current_user"] == "postgres"
                            and table["session_user"] == "postgres")
        ok = bool(table["rls_enabled"] and not policies and external_locked and app_access and identity_matches)
        return dict(status="OK" if ok else "SECURITY_POSTCHECK_FAILED", ok=ok, backend="postgres",
                    rls_enabled=bool(table["rls_enabled"]), rls_forced=bool(table["rls_forced"]),
                    policies=policies, privileges=privileges,
                    app_role=dict(role="postgres", owner=table["table_owner"],
                                  current_user=table["current_user"], session_user=table["session_user"],
                                  privileges={name: bool(app[name]) for name in TABLE_PRIVILEGES} if app else {}))
    except Exception as exc:
        return dict(status="UNKNOWN_ERROR", ok=False, backend="postgres",
                    detail=f"보안 metadata 검사를 완료하지 못했습니다 ({type(exc).__name__}).")


def require_reading_chunks_security(conn):
    report = inspect_reading_chunks_security(conn)
    if not report["ok"]:
        raise SecurityPostcheckFailed(report)
    return report


def initialize_schema(conn, *, approved=False):
    if not approved:
        raise PermissionError("스키마 초기화에는 명시적인 관리 작업 승인이 필요합니다.")
    from lib.database import is_postgres

    if is_postgres(conn):
        for statement in POSTGRES_SCHEMA.split(';'):
            if statement.strip():
                conn.execute(statement)
        return
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='activities'").fetchone():
        return
    activity_columns = {r[1] for r in conn.execute('PRAGMA table_info(activities)')}
    for name, kind in [('event_type', 'TEXT'), ('seconds_read', 'INTEGER'),
                       ('base_page', 'INTEGER'), ('deleted_at', 'INTEGER'), ('updated_at', 'INTEGER'),
                       ('owner_id', 'TEXT')]:
        if name not in activity_columns:
            conn.execute(f'ALTER TABLE activities ADD COLUMN {name} {kind}')
    book_columns = {r[1] for r in conn.execute('PRAGMA table_info(books)')}
    if 'owner_id' not in book_columns:
        conn.execute('ALTER TABLE books ADD COLUMN owner_id TEXT')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS source_book_state (
            book_id TEXT PRIMARY KEY, raw_status INTEGER, raw_reading_now INTEGER,
            inferred_status TEXT, evidence TEXT
        );
        CREATE TABLE IF NOT EXISTS app_migrations (name TEXT PRIMARY KEY, applied_at INTEGER);
        CREATE TABLE IF NOT EXISTS deletion_page_effect (
            activity_id TEXT PRIMARY KEY, page_before INTEGER, page_after INTEGER
        );
        CREATE TABLE IF NOT EXISTS reading_sessions (
            id TEXT PRIMARY KEY, book_id TEXT NOT NULL REFERENCES books(id),
            started_at INTEGER NOT NULL, stopped_at INTEGER, base_page INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('running','stopped','saved','cancelled')),
            activity_id TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_reading
        ON reading_sessions((1)) WHERE state IN ('running','stopped');
        CREATE INDEX IF NOT EXISTS idx_books_owner_id ON books(owner_id);
        CREATE INDEX IF NOT EXISTS idx_activities_owner_id ON activities(owner_id);
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY, email TEXT NOT NULL, display_name TEXT, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reading_groups (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_id TEXT NOT NULL REFERENCES profiles(id),
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS group_members (
            group_id TEXT NOT NULL REFERENCES reading_groups(id), user_id TEXT NOT NULL REFERENCES profiles(id),
            role TEXT NOT NULL CHECK(role IN ('owner','member')), joined_at INTEGER NOT NULL,
            PRIMARY KEY (group_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS group_invites (
            token TEXT PRIMARY KEY, group_id TEXT NOT NULL REFERENCES reading_groups(id),
            created_by TEXT NOT NULL REFERENCES profiles(id), created_at INTEGER NOT NULL,
            used_at INTEGER, used_by TEXT REFERENCES profiles(id)
        );
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id TEXT PRIMARY KEY, group_id TEXT NOT NULL REFERENCES reading_groups(id),
            user_id TEXT NOT NULL REFERENCES profiles(id), checked_on TEXT NOT NULL, is_read INTEGER NOT NULL,
            note TEXT, attachment_kind INTEGER, attachment_body TEXT, attachment_book_title TEXT,
            attachment_page INTEGER, attachment_photo TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            UNIQUE (group_id, user_id, checked_on)
        );
        CREATE TABLE IF NOT EXISTS checkin_reactions (
            checkin_id TEXT NOT NULL REFERENCES daily_checkins(id), user_id TEXT NOT NULL REFERENCES profiles(id),
            emoji TEXT NOT NULL DEFAULT '❤️', created_at INTEGER NOT NULL, PRIMARY KEY (checkin_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS checkin_comments (
            id TEXT PRIMARY KEY, checkin_id TEXT NOT NULL REFERENCES daily_checkins(id),
            user_id TEXT NOT NULL REFERENCES profiles(id), body TEXT NOT NULL, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reading_chunks (
            chunk_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            book_id TEXT REFERENCES books(id),
            book_title TEXT NOT NULL,
            author TEXT,
            isbn TEXT,
            source_app TEXT NOT NULL CHECK(source_app IN ('readdam', 'today-library')),
            source_ref TEXT UNIQUE,
            read_date TEXT NOT NULL,
            page_start INTEGER,
            page_end INTEGER,
            position_note TEXT,
            minutes INTEGER,
            original_text TEXT,
            user_note TEXT,
            tags TEXT NOT NULL DEFAULT '[]',
            illustration_tags TEXT NOT NULL DEFAULT '[]',
            content_types TEXT NOT NULL DEFAULT '[]',
            content_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);
        CREATE INDEX IF NOT EXISTS idx_daily_checkins_feed ON daily_checkins(group_id, checked_on, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_checkin_comments_checkin ON checkin_comments(checkin_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_reading_chunks_book ON reading_chunks(book_id, deleted_at, read_date DESC);
        CREATE INDEX IF NOT EXISTS idx_reading_chunks_owner ON reading_chunks(owner_id, deleted_at, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_reading_chunks_duplicate ON reading_chunks(owner_id, book_id, read_date, page_start, page_end, content_hash);
    ''')
    reaction_columns = {r[1] for r in conn.execute('PRAGMA table_info(checkin_reactions)')}
    if 'emoji' not in reaction_columns:
        conn.execute("ALTER TABLE checkin_reactions ADD COLUMN emoji TEXT NOT NULL DEFAULT '❤️'")
    conn.commit()


def plan_reading_chunks(conn):
    """Plan missing additive 1A objects only. Drift/legacy repairs are never applied."""
    report = inspect_schema_read_only(conn)
    allowed = all(
        (issue.status == "MISSING_TABLE" and issue.object == "reading_chunks") or
        (issue.status == "MISSING_INDEX" and INDEX_TABLE.get(issue.object) == "reading_chunks")
        for issue in report.issues
    )
    statements = []
    if allowed:
        missing_table = any(issue.status == "MISSING_TABLE" for issue in report.issues)
        if missing_table:
            body = TABLE_DDL['reading_chunks']
            target = "reading_chunks"
            if database.is_postgres(conn):
                target = "public.reading_chunks"
                body = body.replace("REFERENCES books(id)", "REFERENCES public.books(id)")
            statements.append(f"CREATE TABLE {target} ({body})")
        for name, ddl in INDEX_DDL.items():
            if INDEX_TABLE[name] == "reading_chunks" and (missing_table or any(issue.object == name for issue in report.issues)):
                if database.is_postgres(conn):
                    ddl = ddl.replace("ON reading_chunks", "ON public.reading_chunks")
                statements.append(ddl.replace(" IF NOT EXISTS", ""))
        if missing_table and database.is_postgres(conn):
            statements.append("ALTER TABLE public.reading_chunks ENABLE ROW LEVEL SECURITY")
            statements.extend(
                f"REVOKE ALL PRIVILEGES ON TABLE public.reading_chunks FROM {role}"
                for role in EXTERNAL_TABLE_ROLES
            )
    plan = dict(preflight=report.to_dict(), applicable=allowed, statements=statements,
                guidance="정확한 계획 승인 후만 적용. 불일치 index/기존 표·컬럼은 별도 검토 필요; 자동 DROP/ALTER/데이터 변환 금지.")
    plan["plan_sha256"] = hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return plan


def apply_reading_chunks(conn, *, approved_plan_sha256):
    """Explicitly approved plan, one transaction; re-inspect before and after DDL."""
    if not approved_plan_sha256:
        raise PermissionError("읽기 전용으로 검토한 계획의 SHA-256 승인이 필요합니다.")
    with database.transaction(conn):
        plan = plan_reading_chunks(conn)
        if not plan["applicable"] or plan["plan_sha256"] != approved_plan_sha256:
            raise PermissionError("승인된 계획과 현재 스키마가 다르거나 자동 적용 금지 대상입니다.")
        for statement in plan["statements"]:
            conn.execute(statement)
        require_schema(conn)
        if database.is_postgres(conn):
            require_reading_chunks_security(conn)
    return plan
