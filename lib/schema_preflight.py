"""Read-only structural contract check. No DDL, DML, repair or user-data reads.

v1 is a structural contract, not a version row written into the database.
Definitions come from the existing checked-in DDL; unknown structures fail closed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re

from lib import database
from lib.schema import POSTGRES_SCHEMA

CONTRACT_VERSION = "reading-chunks-1a.v1"


def _parts(text):
    """Split our trusted DDL column list at top-level commas, preserving literals."""
    depth, quoted, start = 0, False, 0
    for i, char in enumerate(text):
        if char == "'":
            quoted = not quoted
        elif not quoted:
            depth += (char == "(") - (char == ")")
            if char == "," and depth == 0:
                yield text[start:i].strip()
                start = i + 1
    yield text[start:].strip()


TABLE_DDL = dict(re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\);", POSTGRES_SCHEMA, re.S))
INDEX_DDL = {match[1]: match[0] for match in re.findall(
    r"(CREATE (?:UNIQUE )?INDEX IF NOT EXISTS (\w+)\s+ON [^;]+);", POSTGRES_SCHEMA)}
INDEX_TABLE = {name: re.search(r"\bON (\w+)", ddl)[1] for name, ddl in INDEX_DDL.items()}


def expected_columns(postgres):
    result = {}
    for table, body in TABLE_DDL.items():
        result[table] = {}
        for part in _parts(body):
            if part.startswith(("PRIMARY KEY", "UNIQUE", "CHECK", "FOREIGN KEY")):
                continue
            name, kind = re.match(r"(\w+) (DOUBLE PRECISION|\w+)", part).groups()
            if not postgres and table == "activities" and name == "position":
                continue
            if not postgres and kind in ("BIGINT", "DOUBLE PRECISION"):
                kind = "INTEGER"
            default = re.search(r"DEFAULT ('[^']*'|\w+)", part)
            result[table][name] = dict(type=kind.lower(), not_null="NOT NULL" in part or (postgres and "PRIMARY KEY" in part),
                                       default=default[1] if default else None)
    return result


def _canonical(sql):
    """Conservative normalization of catalog formatting, not arbitrary SQL equivalence."""
    # PostgreSQL renders IN as = ANY (ARRAY[...]) and supplies text casts.
    sql = re.sub(r"::text\b", "", sql, flags=re.I)
    sql = re.sub(r"=\s*ANY\s*\(\s*ARRAY\s*\[([^]]*)\]\s*\)", r" IN (\1)", sql, flags=re.I)
    sql = re.sub(r"\bIF NOT EXISTS\b|\bUSING btree\b|\bpublic\.", "", sql, flags=re.I)
    # Keep string literals case-sensitive. Other quotes only wrap known identifiers.
    tokens = re.split(r"('(?:''|[^'])*')", sql)
    return "".join(token if i % 2 else re.sub(r'[\s"();]', '', token).lower() for i, token in enumerate(tokens))


def _checks(sql):
    checks = []
    for match in re.finditer(r"\bCHECK\s*\(", sql, re.I):
        depth, quoted = 1, False
        for end in range(match.end(), len(sql)):
            char = sql[end]
            if char == "'":
                quoted = not quoted
            elif not quoted:
                depth += (char == "(") - (char == ")")
            if depth == 0:
                checks.append(_canonical(sql[match.start():end + 1]))
                break
    return checks


@dataclass(frozen=True)
class Issue:
    status: str
    object: str
    detail: str
    expected: str = ""


@dataclass(frozen=True)
class Report:
    backend: str
    issues: tuple[Issue, ...]
    contract_version: str = CONTRACT_VERSION

    @property
    def ok(self):
        return not self.issues

    @property
    def status(self):
        return self.issues[0].status if self.issues else "OK"

    def to_dict(self):
        return dict(status=self.status, backend=self.backend, contract_version=self.contract_version,
                    contract_sha256=hashlib.sha256(POSTGRES_SCHEMA.encode()).hexdigest(),
                    issues=[asdict(issue) for issue in self.issues])


class SchemaNotReady(RuntimeError):
    def __init__(self, report):
        self.report = report
        summary = "; ".join(f"{item.status}: {item.object}" for item in report.issues[:8])
        super().__init__(f"DB 스키마 사전점검 실패 ({summary}). 자동 변경하지 않았습니다. 관리자에게 점검 결과와 승인된 maintenance 계획 검토를 요청하세요.")


def _sqlite_metadata(conn):
    objects = {row["name"]: row for row in _rows(conn.execute(
        "SELECT name,type,tbl_name,sql FROM main.sqlite_master WHERE name NOT LIKE 'sqlite_%'"))}
    temporary = {row["name"] for row in _rows(conn.execute("SELECT name FROM sqlite_temp_master"))}
    tables, indexes = {}, {}
    for table in TABLE_DDL:
        obj = objects.get(table)
        if obj is None:
            continue
        tables[table] = dict(kind=obj["type"], shadowed=table in temporary, sql=obj["sql"], columns={})
        if obj["type"] != "table":
            continue
        for row in _rows(conn.execute(f'PRAGMA main.table_xinfo("{table}")')):
            tables[table]["columns"][row["name"]] = dict(type=row["type"].lower(), not_null=bool(row["notnull"]),
                                                          default=row["dflt_value"], hidden=row["hidden"])
        tables[table]["pk"] = [row["name"] for row in sorted(_rows(conn.execute(f'PRAGMA main.table_info("{table}")')), key=lambda r: r["pk"]) if row["pk"]]
        if table == "reading_chunks":
            tables[table]["fk"] = _rows(conn.execute('PRAGMA main.foreign_key_list("reading_chunks")'))
            unique = []
            for idx in _rows(conn.execute('PRAGMA main.index_list("reading_chunks")')):
                # Names read from metadata are quoted, not interpolated as SQL code.
                quoted = idx["name"].replace('"', '""')
                if idx["unique"] and not idx["partial"]:
                    unique.append([r["name"] for r in _rows(conn.execute(f'PRAGMA main.index_info("{quoted}")'))])
            tables[table]["unique"] = unique
    for name in INDEX_DDL:
        obj = objects.get(name)
        if obj:
            indexes[name] = dict(table=obj["tbl_name"], definition=obj["sql"] or "", valid=obj["type"] == "index")
    return tables, indexes


def _rows(cursor):
    # Both sqlite row_factory modes and psycopg dict rows are supported.
    names = [item[0] for item in cursor.description] if getattr(cursor, "description", None) else None
    return [dict(row) if hasattr(row, "keys") else dict(zip(names, row)) for row in cursor.fetchall()]


def _postgres_metadata(conn):
    tables, indexes = {}, {}
    for row in _rows(conn.execute("""SELECT c.relname AS name, c.oid, c.relkind,
            pg_catalog.to_regclass(c.relname)::oid AS resolved
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')""")):
        if row["name"] in TABLE_DDL:
            tables[row["name"]] = dict(kind="table" if row["relkind"] == "r" else row["relkind"],
                                       shadowed=row["oid"] != row["resolved"], columns={})
    for row in _rows(conn.execute("""SELECT c.relname AS table_name, a.attname AS name,
            pg_catalog.format_type(a.atttypid,a.atttypmod) AS type, a.attnotnull AS not_null,
            pg_catalog.pg_get_expr(d.adbin,d.adrelid) AS "default", a.attgenerated AS generated
        FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
        WHERE n.nspname='public' AND a.attnum>0 AND NOT a.attisdropped""")):
        if row["table_name"] in tables:
            tables[row["table_name"]]["columns"][row["name"]] = row
    for row in _rows(conn.execute("""SELECT i.relname AS name, t.relname AS table_name,
            pg_catalog.pg_get_indexdef(i.oid) AS definition,
            x.indisvalid AND x.indisready AND x.indislive AS valid
        FROM pg_catalog.pg_index x JOIN pg_catalog.pg_class i ON i.oid=x.indexrelid
        JOIN pg_catalog.pg_class t ON t.oid=x.indrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=i.relnamespace WHERE n.nspname='public'""")):
        if row["name"] in INDEX_DDL:
            indexes[row["name"]] = dict(table=row["table_name"], definition=row["definition"], valid=row["valid"])
    if "reading_chunks" in tables:
        tables["reading_chunks"]["constraints"] = _rows(conn.execute("""SELECT k.contype AS type,
                pg_catalog.pg_get_constraintdef(k.oid) AS definition, k.convalidated AS valid,
                k.condeferrable AS deferred
            FROM pg_catalog.pg_constraint k JOIN pg_catalog.pg_class c ON c.oid=k.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='public' AND c.relname='reading_chunks'"""))
    return tables, indexes


def _inspect(conn):
    postgres = database.is_postgres(conn)
    tables, indexes = _postgres_metadata(conn) if postgres else _sqlite_metadata(conn)
    issues = []
    def issue(status, name, detail, expected=""):
        issues.append(Issue(status, name, detail, expected))
    for table, columns in expected_columns(postgres).items():
        actual = tables.get(table)
        if actual is None:
            issue("MISSING_TABLE", table, "필수 테이블이 없습니다.")
            continue
        if actual["kind"] != "table" or actual["shadowed"]:
            issue("UNSUPPORTED_SCHEMA", table, "일반 테이블이 아니거나 search_path/temp 객체에 가려졌습니다.")
            continue
        for name, expected in columns.items():
            column = actual["columns"].get(name)
            if column is None:
                issue("MISSING_COLUMN", f"{table}.{name}", "필수 컬럼이 없습니다.", expected["type"])
            elif column["type"] != expected["type"]:
                issue("UNSUPPORTED_SCHEMA", f"{table}.{name}", "컬럼 타입이 다릅니다.", expected["type"])
            elif table == "reading_chunks" and (column["not_null"] != expected["not_null"]
                    or _canonical(column["default"] or "") != _canonical(expected["default"] or "")
                    or column.get("generated") or column.get("hidden")):
                issue("UNSUPPORTED_SCHEMA", f"{table}.{name}", "NULL/default/generated 규격이 다릅니다.")
        if table == "reading_chunks":
            if set(actual["columns"]) - set(columns):
                issue("UNSUPPORTED_SCHEMA", table, "지원하지 않는 reading_chunks 구조 버전(추가 컬럼)입니다.")
            if postgres:
                required = {"PRIMARY KEY (chunk_id)", "UNIQUE (source_ref)", "FOREIGN KEY (book_id) REFERENCES books(id)",
                            "CHECK (source_app IN ('readdam', 'today-library'))"}
                constraints = actual["constraints"]
                if ({_canonical(row["definition"]) for row in constraints} != {_canonical(item) for item in required}
                        or any(not row["valid"] or row["deferred"] for row in constraints)):
                    issue("UNSUPPORTED_SCHEMA", table, "PK/UNIQUE/FK/CHECK 제약이 다르거나 검증되지 않았습니다.")
            else:
                foreign = actual["fk"]
                valid_fk = len(foreign) == 1 and all(foreign[0][key] == value for key, value in
                    dict(table="books", **{"from": "book_id", "to": "id"}, on_update="NO ACTION", on_delete="NO ACTION").items())
                if (actual["pk"] != ["chunk_id"] or ["source_ref"] not in actual["unique"] or not valid_fk
                        or _checks(actual["sql"]) != [_canonical("CHECK(source_app IN ('readdam', 'today-library'))")]):
                    issue("UNSUPPORTED_SCHEMA", table, "PK/UNIQUE/FK/sourceApp CHECK 규격이 다릅니다.")
    for name, definition in INDEX_DDL.items():
        actual = indexes.get(name)
        if INDEX_TABLE[name] not in tables and actual is None:
            continue
        if actual is None:
            issue("MISSING_INDEX", name, "필수 인덱스가 없습니다.", definition)
        elif (not actual["valid"] or actual["table"] != INDEX_TABLE[name]
              or _canonical(actual["definition"]) != _canonical(definition)):
            issue("INDEX_DEFINITION_MISMATCH", name, "대상/컬럼 순서/정렬/unique/조건/유효성이 다릅니다. 자동 교정 금지.", definition)
    return Report("postgres" if postgres else "sqlite", tuple(issues))


def inspect_schema_read_only(conn):
    try:
        return _inspect(conn)
    except Exception as exc:
        # Do not expose raw driver messages, DSNs, credentials or user rows.
        return Report("postgres" if database.is_postgres(conn) else "sqlite", (
            Issue("UNKNOWN_ERROR", "schema metadata", f"검사를 완료하지 못했습니다 ({type(exc).__name__}). 자동 변경 금지."),))


def require_schema(conn):
    report = inspect_schema_read_only(conn)
    if not report.ok:
        raise SchemaNotReady(report)
    return report
