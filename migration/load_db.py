#!/usr/bin/env python3
"""migration/output의 books.json, activities.json, photo_manifest.json을
도서비서 앱이 쓰는 SQLite DB로 적재한다."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    isbn TEXT,
    subtitle TEXT,
    translator TEXT,
    category TEXT,
    pages INTEGER,
    current_page INTEGER,
    rating INTEGER,
    status TEXT,
    read_count INTEGER,
    start_date INTEGER,
    finish_date INTEGER,
    cover_photo TEXT,
    cover_url TEXT
);

CREATE TABLE activities (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id),
    kind TEXT NOT NULL,
    text TEXT,
    quote TEXT,
    page INTEGER,
    date INTEGER NOT NULL,
    photo TEXT,
    visibility TEXT NOT NULL DEFAULT 'private',
    pages_read INTEGER,
    minutes_read INTEGER
);

CREATE TABLE photo_manifest (
    filename TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    book_id TEXT,
    record_ids TEXT
);

CREATE INDEX idx_activities_book_id ON activities(book_id);
CREATE INDEX idx_activities_date ON activities(date);
CREATE INDEX idx_activities_kind ON activities(kind);
CREATE INDEX idx_books_category ON books(category);
"""

PROGRESS_RE = re.compile(r"^(?:(-?\d+)쪽을 )?(?:(-?\d+)분 동안 )?읽었습니다$")


def parse_progress(text: str | None) -> tuple[int | None, int | None]:
    """progress_log 문장에서 쪽수·분을 역파싱한다."""
    if not text:
        return None, None
    match = PROGRESS_RE.match(text)
    if not match:
        return None, None
    pages, minutes = match.groups()
    return (int(pages) if pages else None, int(minutes) if minutes else None)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def build_db(output_dir: Path, db_path: Path) -> None:
    books = load_json(output_dir / "books.json")
    activities = load_json(output_dir / "activities.json")
    manifest = load_json(output_dir / "photo_manifest.json")

    covers = {m["book_id"]: m["filename"] for m in manifest if m["type"] == "cover"}

    # 주의: 이 스크립트는 DB를 항상 통째로 재생성한다. 앱에서 "새 책 추가"로
    # 입력한 책은 마이그레이션 JSON에 없으므로 재실행 시 함께 삭제된다.
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    conn.executemany(
        """
        INSERT INTO books (
            id, title, author, publisher, isbn, subtitle, translator,
            category, pages, current_page, rating, status, read_count,
            start_date, finish_date, cover_photo, cover_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                b["id"], b["title"], b["author"], b["publisher"], b["isbn"],
                b["subtitle"], b["translator"], b["category"], b["pages"],
                b["currentPage"], b["rating"], b["status"], b["readCount"],
                b["startDate"], b["finishDate"], covers.get(b["id"]), None,
            )
            for b in books
        ],
    )

    activity_rows = []
    for a in activities:
        pages_read, minutes_read = (
            parse_progress(a["text"]) if a["kind"] == "progress_log" else (None, None)
        )
        activity_rows.append(
            (
                a["id"], a["book_id"], a["kind"], a["text"], a["quote"],
                a["page"], a["date"], a["photo"], a["visibility"],
                pages_read, minutes_read,
            )
        )
    conn.executemany(
        """
        INSERT INTO activities (
            id, book_id, kind, text, quote, page, date, photo, visibility,
            pages_read, minutes_read
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        activity_rows,
    )

    conn.executemany(
        "INSERT INTO photo_manifest (filename, type, book_id, record_ids) VALUES (?, ?, ?, ?)",
        [
            (m["filename"], m["type"], m["book_id"], json.dumps(m["record_ids"]))
            for m in manifest
        ],
    )

    conn.commit()

    unparsed = conn.execute(
        "SELECT COUNT(*) FROM activities WHERE kind = 'progress_log' AND pages_read IS NULL AND minutes_read IS NULL"
    ).fetchone()[0]
    total_progress = conn.execute(
        "SELECT COUNT(*) FROM activities WHERE kind = 'progress_log'"
    ).fetchone()[0]
    conn.close()

    print(f"적재 완료: {db_path}")
    print(f"books: {len(books)}건, activities: {len(activity_rows)}건, photo_manifest: {len(manifest)}건")
    if unparsed:
        print(f"경고: progress_log {total_progress}건 중 {unparsed}건은 쪽수·분을 파싱하지 못함")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("migration/output"),
        help="convert_bookswing.py 결과 디렉터리 (기본: migration/output)",
    )
    parser.add_argument(
        "--db-path", type=Path, default=Path("data/book_butler.db"),
        help="생성할 SQLite DB 경로 (기본: data/book_butler.db)",
    )
    args = parser.parse_args()
    build_db(args.output_dir, args.db_path)


if __name__ == "__main__":
    main()
