"""읽담 SQLite DB 접근 헬퍼."""

from __future__ import annotations

import os
import io
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from lib.schema import ensure_schema
from lib import database

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


def get_connection(db_path: Path | None = None):
    """테스트/로컬은 SQLite, 배포 환경은 Supabase Postgres에 연결한다."""
    configured_override = os.environ.get("BOOK_BUTLER_DB_PATH") if db_path is None else None
    database_url = database.database_url_from_env() if db_path is None and not configured_override else None
    if database_url:
        from psycopg import connect
        from psycopg.rows import dict_row
        raw = connect(database_url, row_factory=dict_row, autocommit=True)
        conn = database.PostgresConnection(raw)
        ensure_schema(conn)
        return conn
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
    exclude_status: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    group_by_category: bool = False,
) -> pd.DataFrame:
    query = "SELECT * FROM books WHERE 1=1"
    params: list[str] = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    if exclude_status:
        query += " AND status != ?"
        params.append(exclude_status)
    if search:
        query += " AND (title LIKE ? OR author LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    recent_order = "COALESCE((SELECT MAX(date) FROM activities WHERE book_id=books.id AND deleted_at IS NULL), start_date, 0) DESC, title"
    if group_by_category:
        query += f" ORDER BY COALESCE(category, '미분류'), {recent_order}"
    else:
        query += f" ORDER BY {recent_order}"
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, max(offset, 0)])
    return database.read_frame(conn, query, params=params)


def count_books(
    conn: sqlite3.Connection,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    exclude_status: str | None = None,
) -> int:
    query = "SELECT COUNT(*) FROM books WHERE 1=1"
    params: list[str] = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    if exclude_status:
        query += " AND status != ?"
        params.append(exclude_status)
    if search:
        query += " AND (title LIKE ? OR author LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    return int(conn.execute(query, params).fetchone()[0])


def get_book(conn: sqlite3.Connection, book_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def list_activities(conn: sqlite3.Connection, book_id: str) -> pd.DataFrame:
    return database.read_frame(
        conn,
        f"SELECT * FROM activities WHERE book_id = ? AND deleted_at IS NULL "
        f"ORDER BY date DESC, {database.activity_position(conn)} DESC",
        params=[book_id],
    )


def all_activities(conn: sqlite3.Connection) -> pd.DataFrame:
    return database.read_frame(conn, "SELECT * FROM activities WHERE deleted_at IS NULL ORDER BY date")


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
    validate_photo(content)
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


def validate_photo(content):
    from PIL import Image, UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError('읽을 수 있는 PNG/JPEG/GIF/WebP 사진을 선택해주세요.') from exc


def update_book_status(conn, book_id, status, timestamp=None):
    from lib import reading
    if status not in {'읽는 중', '완독', '읽기 중단'}:
        raise ValueError('지원하지 않는 책 상태입니다.')
    now = int(time.time()) if timestamp is None else timestamp
    with database.transaction(conn, lock_reading=True):
        book = database.lock_rows(conn, 'SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
        if book is None:
            raise ValueError('책 정보를 찾을 수 없습니다.')
        if book['status'] == status:
            return
        session = reading.active(conn)
        if session and session['book_id'] == book_id:
            raise ValueError('타이머를 먼저 저장하거나 취소한 후 상태를 변경해주세요.')
        if status == '완독':
            conn.execute('UPDATE books SET status=?,finish_date=?,read_count=COALESCE(read_count,0)+1 WHERE id=?', (status,now,book_id))
        else:
            conn.execute('UPDATE books SET status=?,finish_date=NULL,start_date=COALESCE(start_date,?) WHERE id=?', (status,now if status=='읽는 중' else None,book_id))
        kind,event = {'완독':(5,'completed'),'읽는 중':(3,'reading_started'),'읽기 중단':(7,'stopped')}[status]
        aid = insert_activity(conn,book_id=book_id,kind=kind,page=book['current_page'] or 0,timestamp=now,commit=False)
        conn.execute('UPDATE activities SET event_type=? WHERE id=?',(event,aid))


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
    return database.read_frame(
        conn, "SELECT category, COUNT(*) AS count FROM books GROUP BY category ORDER BY count DESC"
    )
