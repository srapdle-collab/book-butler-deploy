"""도서비서 SQLite DB 접근 헬퍼."""

from __future__ import annotations

import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from lib.schema import ensure_schema

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "book_butler.db"
IMPORTED_PHOTOS_DIR = BASE_DIR / "migration" / "output" / "photos"
USER_PHOTOS_DIR = BASE_DIR / "data" / "photos"

KIND_NAME_TO_ID = {
    "quote_with_note": 0,
    "photo": 1,
    "quote": 2,
    "start": 3,
    "progress_log": 4,
    "finish": 5,
    "rating": 6,
    "other": 7,
}


def normalize_kind(value: Any) -> int:
    if isinstance(value, int) and 0 <= value <= 7:
        return value
    if isinstance(value, str):
        if value in KIND_NAME_TO_ID:
            return KIND_NAME_TO_ID[value]
        if value.isdigit() and 0 <= int(value) <= 7:
            return int(value)
    raise ValueError(f"지원하지 않는 activity kind: {value!r}")


def _ensure_numeric_activity_kinds(conn: sqlite3.Connection) -> None:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'activities'"
    ).fetchone()
    if table is None:
        return
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    kind_type = next(row[2].upper() for row in columns if row[1] == "kind")
    if kind_type == "INTEGER":
        return

    rows = conn.execute("SELECT * FROM activities").fetchall()
    converted = [tuple(row[:2]) + (normalize_kind(row[2]),) + tuple(row[3:]) for row in rows]
    conn.execute("BEGIN")
    conn.execute("ALTER TABLE activities RENAME TO activities_legacy_kind")
    conn.execute(
        """
        CREATE TABLE activities (
            id TEXT PRIMARY KEY,
            book_id TEXT NOT NULL REFERENCES books(id),
            kind INTEGER NOT NULL CHECK (kind BETWEEN 0 AND 7),
            text TEXT,
            quote TEXT,
            page INTEGER,
            date INTEGER NOT NULL,
            photo TEXT,
            visibility TEXT NOT NULL DEFAULT 'private',
            pages_read INTEGER,
            minutes_read INTEGER
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO activities (
            id, book_id, kind, text, quote, page, date, photo, visibility,
            pages_read, minutes_read
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        converted,
    )
    conn.execute("DROP TABLE activities_legacy_kind")
    conn.execute("CREATE INDEX idx_activities_book_id ON activities(book_id)")
    conn.execute("CREATE INDEX idx_activities_date ON activities(date)")
    conn.execute("CREATE INDEX idx_activities_kind ON activities(kind)")
    conn.commit()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    configured_path = Path(os.environ.get("BOOK_BUTLER_DB_PATH", DB_PATH))
    conn = sqlite3.connect(db_path or configured_path)
    conn.row_factory = sqlite3.Row
    _ensure_numeric_activity_kinds(conn)
    ensure_schema(conn)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def photo_path(filename: str | None) -> Path | None:
    if not filename:
        return None
    basename = Path(filename).name
    configured = Path(os.environ.get("BOOK_BUTLER_PHOTOS_DIR", USER_PHOTOS_DIR))
    for directory in (configured, IMPORTED_PHOTOS_DIR):
        path = directory / basename
        if path.exists():
            return path
    return None


def cover_source(book) -> str | None:
    """표지로 쓸 이미지 경로/URL. 로컬 파일을 우선하고 없으면 원격 URL을 쓴다."""
    local = photo_path(book["cover_photo"])
    if local:
        return str(local)
    return book["cover_url"] or None


def list_categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT category FROM books WHERE category IS NOT NULL ORDER BY category"
    ).fetchall()
    return [r["category"] for r in rows]


def list_books(
    conn: sqlite3.Connection,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
) -> pd.DataFrame:
    query = "SELECT * FROM books WHERE 1=1"
    params: list[str] = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    if search:
        query += " AND (title LIKE ? OR author LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    query += " ORDER BY COALESCE((SELECT MAX(date) FROM activities WHERE book_id=books.id AND deleted_at IS NULL), start_date, 0) DESC, title"
    return pd.read_sql_query(query, conn, params=params)


def get_book(conn: sqlite3.Connection, book_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def list_activities(conn: sqlite3.Connection, book_id: str) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT * FROM activities WHERE book_id = ? AND deleted_at IS NULL ORDER BY date DESC, rowid DESC",
        conn,
        params=[book_id],
    )


def all_activities(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM activities WHERE deleted_at IS NULL ORDER BY date", conn)


def insert_book(conn: sqlite3.Connection, book: dict[str, Any]) -> str:
    """3.1(Book) 구조에 맞춰 새 책을 저장하고 id를 반환한다."""
    book_id = book.get("id") or str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO books (
            id, title, author, publisher, isbn, subtitle, translator,
            category, pages, current_page, rating, status, read_count,
            start_date, finish_date, cover_photo, cover_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            book_id,
            book["title"],
            book.get("author"),
            book.get("publisher"),
            book.get("isbn"),
            book.get("subtitle"),
            book.get("translator"),
            book.get("category"),
            book.get("pages"),
            book.get("current_page", 0),
            book.get("rating", 0),
            book.get("status", "위시리스트"),
            book.get("read_count", 0),
            book.get("start_date"),
            book.get("finish_date"),
            None,
            book.get("cover_url"),
        ),
    )
    conn.commit()
    return book_id


def insert_activity(
    conn: sqlite3.Connection,
    *,
    book_id: str,
    kind: int,
    page: int,
    text: str | None = None,
    quote: str | None = None,
    photo: str | None = None,
    pages_read: int | None = None,
    minutes_read: int | None = None,
    timestamp: int | None = None,
    commit: bool = True,
) -> str:
    activity_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO activities (
            id, book_id, kind, text, quote, page, date, photo, visibility,
            pages_read, minutes_read
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'private', ?, ?)
        """,
        (
            activity_id,
            book_id,
            normalize_kind(kind),
            text,
            quote,
            page,
            int(time.time()) if timestamp is None else timestamp,
            photo,
            pages_read,
            minutes_read,
        ),
    )
    if commit:
        conn.commit()
    return activity_id


def add_progress(conn: sqlite3.Connection, book_id: str, page: int, minutes: int) -> str:
    from lib.reading import manual
    return manual(conn, book_id, page, minutes)


def validate_page(conn, book_id, page):
    book = get_book(conn, book_id)
    if book is None:
        raise ValueError('책 정보를 찾을 수 없습니다.')
    if page < 0 or (book['pages'] and page > book['pages']):
        raise ValueError('페이지는 0부터 전체 쪽수 사이로 입력해주세요.')


def add_quote(conn: sqlite3.Connection, book_id: str, page: int, quote: str, note: str = '') -> str:
    validate_page(conn, book_id, page)
    cleaned = quote.strip()
    if not cleaned:
        raise ValueError("인용문을 입력해주세요.")
    note = note.strip() or None
    return insert_activity(conn, book_id=book_id, kind=0 if note else 2, page=page, quote=cleaned, text=note)


def add_note(conn: sqlite3.Connection, book_id: str, page: int, text: str) -> str:
    validate_page(conn, book_id, page)
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("메모를 입력해주세요.")
    return insert_activity(conn, book_id=book_id, kind=0, page=page, text=cleaned)


def add_photo(
    conn: sqlite3.Connection,
    book_id: str,
    page: int,
    original_name: str,
    content: bytes,
) -> str:
    validate_page(conn, book_id, page)
    if not content:
        raise ValueError("사진 파일이 비어 있습니다.")
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}:
        raise ValueError("지원하는 이미지 파일을 선택해주세요.")
    photos_dir = Path(os.environ.get("BOOK_BUTLER_PHOTOS_DIR", USER_PHOTOS_DIR))
    photos_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{suffix}"
    destination = photos_dir / filename
    destination.write_bytes(content)
    try:
        return insert_activity(
            conn,
            book_id=book_id,
            kind=1,
            page=page,
            photo=f"photos/{filename}",
        )
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def update_book_status(
    conn: sqlite3.Connection,
    book_id: str,
    status: str,
    timestamp: int | None = None,
) -> None:
    if status not in {"읽는 중", "완독", "읽기 중단"}:
        raise ValueError("지원하지 않는 책 상태입니다.")
    book = get_book(conn, book_id)
    if book is None:
        raise ValueError("책 정보를 찾을 수 없습니다.")
    now = timestamp or int(time.time())
    was_finished = book["status"] == "완독"
    try:
        if status == "완독" and not was_finished:
            conn.execute(
                """
                UPDATE books
                SET status = ?, finish_date = ?, read_count = COALESCE(read_count, 0) + 1
                WHERE id = ?
                """,
                (status, now, book_id),
            )
            insert_activity(
                conn,
                book_id=book_id,
                kind=5,
                page=book["current_page"] or 0,
                timestamp=now,
                commit=False,
            )
        else:
            finish_date = book["finish_date"] if status == "완독" else None
            start_date = book["start_date"] or (now if status == "읽는 중" else None)
            conn.execute(
                "UPDATE books SET status = ?, start_date = ?, finish_date = ? WHERE id = ?",
                (status, start_date, finish_date, book_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def update_book_info(conn: sqlite3.Connection, book_id: str, book: dict[str, Any]) -> None:
    title = (book.get("title") or "").strip()
    if not title:
        raise ValueError("제목을 입력해주세요.")
    pages = int(book.get("pages") or 0)
    current = get_book(conn, book_id)
    if current is None:
        raise ValueError("책 정보를 찾을 수 없습니다.")
    if pages and pages < (current["current_page"] or 0):
        raise ValueError("전체 쪽수는 현재 페이지보다 작을 수 없습니다.")
    conn.execute(
        """
        UPDATE books
        SET title = ?, subtitle = ?, author = ?, translator = ?, publisher = ?,
            isbn = ?, category = ?, pages = ?
        WHERE id = ?
        """,
        (
            title,
            (book.get("subtitle") or "").strip() or None,
            (book.get("author") or "").strip() or None,
            (book.get("translator") or "").strip() or None,
            (book.get("publisher") or "").strip() or None,
            (book.get("isbn") or "").strip() or None,
            (book.get("category") or "").strip() or None,
            pages or None,
            book_id,
        ),
    )
    conn.commit()


def book_counts_by_category(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT category, COUNT(*) AS count FROM books GROUP BY category ORDER BY count DESC",
        conn,
    )
