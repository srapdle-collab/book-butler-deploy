"""로컬 SQLite 백업을 Supabase Postgres·Storage로 이관한다.

기본 실행은 읽기 전용 요약이다. 실제 쓰기는 반드시 --apply를 붙인다.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SQLITE_DEFAULT = ROOT / "data" / "book_butler.db"
PHOTOS_DEFAULT = ROOT / "migration" / "output" / "photos"
TABLES = {
    "books": "id",
    "activities": "id",
    "photo_manifest": "filename",
    "source_book_state": "book_id",
    "app_migrations": "name",
    "deletion_page_effect": "activity_id",
    "reading_sessions": "id",
}


def source_table_rows(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    """SQLite 행을 일반 dict로 꺼내며 activities에는 원래 rowid 순서를 보존한다."""
    conn.row_factory = sqlite3.Row
    existing = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not existing:
        return []
    query = f"SELECT rowid AS position, * FROM {table}" if table == "activities" else f"SELECT * FROM {table}"
    return [dict(row) for row in conn.execute(query).fetchall()]


def _upsert(target, table: str, rows: list[dict[str, Any]], key: str) -> int:
    if not rows:
        return 0
    columns = list(rows[0])
    updates = [column for column in columns if column != key]
    update_sql = ", ".join(f"{column}=EXCLUDED.{column}" for column in updates)
    conflict = f"DO UPDATE SET {update_sql}" if update_sql else "DO NOTHING"
    statement = (
        f"INSERT INTO {table} ({', '.join(columns)}) "
        f"VALUES ({', '.join('?' for _ in columns)}) ON CONFLICT ({key}) {conflict}"
    )
    target.executemany(
        statement,
        [tuple(row[column] for column in columns) for row in rows],
    )
    return len(rows)


def photo_jobs(source: sqlite3.Connection, photos_dir: Path) -> list[tuple[Path, str]]:
    """manifest의 표지/기록 구분을 보존해 Storage object key를 만든다."""
    from lib import storage

    jobs: dict[str, Path] = {}
    for row in source_table_rows(source, "photo_manifest"):
        filename = row["filename"]
        path = photos_dir / filename
        if path.exists():
            kind = "cover" if row["type"] == "cover" else "photo"
            jobs[storage.object_key(filename, kind=kind)] = path
    user_photos = ROOT / "data" / "photos"
    if user_photos.exists():
        for path in user_photos.iterdir():
            if path.is_file():
                jobs[storage.object_key(path.name, kind="photo")] = path
    return sorted((path, key) for key, path in jobs.items())


def migrate(sqlite_path: Path, photos_dir: Path, *, apply: bool, verify: bool) -> dict[str, Any]:
    from lib import database, db, storage

    source = sqlite3.connect(sqlite_path)
    source_counts = {table: len(source_table_rows(source, table)) for table in TABLES}
    jobs = photo_jobs(source, photos_dir)
    summary: dict[str, Any] = {"source_counts": source_counts, "photo_candidates": len(jobs)}
    if not apply:
        source.close()
        return summary

    target = db.get_connection()
    try:
        for table, key in TABLES.items():
            _upsert(target, table, source_table_rows(source, table), key)
        storage.ensure_bucket()
        def upload(job: tuple[Path, str]) -> None:
            path, key = job
            storage.upload_photo(key, path.read_bytes())

        # 네트워크 왕복을 병렬화해 이관 중단 없이 빠르게 끝낸다.
        with ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(upload, jobs))
        summary["uploaded_photos"] = len(jobs)
        if verify:
            target_counts = {table: database.scalar(target.execute(f"SELECT COUNT(*) FROM {table}").fetchone()) for table in TABLES}
            summary["target_counts"] = target_counts
            summary["counts_match"] = source_counts == target_counts
            if not summary["counts_match"]:
                raise RuntimeError("Postgres 이관 후 테이블 건수가 원본과 일치하지 않습니다.")
            activity_photo_count = source.execute(
                "SELECT COUNT(*) FROM activities WHERE photo IS NOT NULL AND photo != ''"
            ).fetchone()[0]
            summary["activity_photo_references"] = activity_photo_count
    finally:
        target.close()
        source.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite-path", type=Path, default=SQLITE_DEFAULT)
    parser.add_argument("--photos-dir", type=Path, default=PHOTOS_DEFAULT)
    parser.add_argument("--apply", action="store_true", help="Postgres와 Storage에 실제로 씁니다.")
    parser.add_argument("--verify", action="store_true", help="이관 뒤 테이블 건수를 대조합니다.")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    print(json.dumps(migrate(args.sqlite_path, args.photos_dir, apply=args.apply, verify=args.verify), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
