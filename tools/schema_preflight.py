#!/usr/bin/env python3
"""Read-only schema check. Explicit target required; never loads .env or repairs DB."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import db, database
from lib.schema_preflight import inspect_schema_read_only


def target_arguments(parser):
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--sqlite", type=Path, help="존재하는 SQLite 파일 (없으면 생성하지 않음)")
    target.add_argument("--configured-postgres", action="store_true", help="기존 process 환경에 설정된 PostgreSQL. 운영 연결은 별도 승인 필요")


def connect_target(args, *, readonly=True):
    if args.configured_postgres:
        import os
        if os.environ.get("BOOK_BUTLER_DB_PATH") or not database.database_url_from_env():
            raise RuntimeError("PostgreSQL 대상이 명확하지 않습니다. SQLite fallback 금지.")
    return (db.get_readonly_connection if readonly else db.connect)(args.sqlite)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target_arguments(parser)
    args = parser.parse_args()
    try:
        conn = connect_target(args)
        try:
            report = inspect_schema_read_only(conn)
        finally:
            conn.close()
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0 if report.ok else 2
    except Exception:
        print(json.dumps(dict(status="UNKNOWN_ERROR", detail="DB 연결/검사 실패. 자동 변경하지 않았습니다."), ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main())
