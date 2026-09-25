"""SQLite와 Postgres가 함께 쓰는 작은 DB 호환 계층."""
from __future__ import annotations

import os
from contextlib import contextmanager
from urllib.parse import quote

import pandas as pd


def database_url_from_env() -> str | None:
    """명시 URL을 우선하고 Supabase pooler 환경 변수로 URL을 만든다."""
    explicit = os.environ.get("BOOK_BUTLER_DATABASE_URL", "").strip()
    if explicit:
        return explicit
    required = ("SUPABASE_DB_HOST", "SUPABASE_DB_PORT", "SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_NAME")
    values = {name: os.environ.get(name, "").strip() for name in required}
    if not all(values.values()):
        return None
    return (
        f"postgresql://{quote(values['SUPABASE_DB_USER'], safe='')}:"
        f"{quote(values['SUPABASE_DB_PASSWORD'], safe='')}@{values['SUPABASE_DB_HOST']}:"
        f"{values['SUPABASE_DB_PORT']}/{values['SUPABASE_DB_NAME']}?sslmode=require"
    )


def is_postgres(conn) -> bool:
    return getattr(conn, "backend", None) == "postgres" or conn.__class__.__module__.startswith("psycopg")


def activity_position(conn) -> str:
    return "position" if is_postgres(conn) else "rowid"

def postgres_sql(sql: str) -> str:
    """이 앱의 DB 쿼리에 쓰인 qmark 바인딩을 psycopg 바인딩으로 바꾼다."""
    return sql.replace("?", "%s")


def sql(conn, query: str) -> str:
    return postgres_sql(query) if is_postgres(conn) else query


def execute(conn, query: str, params=()):
    return conn.execute(sql(conn, query), params)


def read_frame(conn, query: str, params=()):
    if is_postgres(conn):
        # psycopg의 dict row를 DataFrame으로 직접 변환해 열 이름을 보존한다.
        frame = pd.DataFrame(conn.execute(query, params).fetchall())
    else:
        frame = pd.read_sql_query(sql(conn, query), conn, params=params)
    # 한 컬럼의 값이 전부 NULL이면 pandas가 float64/NaN으로 추론해
    # row.get(col)이 참으로 잘못 판정되고 "nan" 문자열이 화면에 그대로
    # 나온다. 모든 컬럼에서 NaN을 None으로 통일해 이 문제를 막는다.
    return frame.where(pd.notna(frame), None)


def scalar(row):
    """sqlite3.Row와 psycopg dict row 모두에서 첫 값을 꺼낸다."""
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def lock_rows(conn, query: str, params=()):
    suffix = " FOR UPDATE" if is_postgres(conn) else ""
    return execute(conn, query + suffix, params)


@contextmanager
def transaction(conn, *, lock_reading: bool = False):
    """SQLite의 즉시 쓰기 잠금과 Postgres의 트랜잭션 잠금을 같은 의도로 제공한다."""
    if is_postgres(conn):
        with conn.transaction():
            if lock_reading:
                conn.execute("SELECT pg_advisory_xact_lock(hashtext('bookbutler:reading-session'))")
            yield
        return
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        yield

class PostgresConnection:
    """qmark SQL을 쓰던 앱 코드를 psycopg 연결 위에서 그대로 실행한다."""
    backend = "postgres"

    def __init__(self, raw):
        self.raw = raw

    def execute(self, query: str, params=()):
        return self.raw.execute(postgres_sql(query), params)

    def executemany(self, query: str, params_seq):
        with self.raw.cursor() as cursor:
            return cursor.executemany(postgres_sql(query), params_seq)

    def transaction(self):
        return self.raw.transaction()

    def commit(self):
        return self.raw.commit()

    def close(self):
        return self.raw.close()
