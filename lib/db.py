"""도서비서 SQLite DB 접근 헬퍼."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "book_butler.db"
PHOTOS_DIR = BASE_DIR / "migration" / "output" / "photos"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def photo_path(filename: str | None) -> Path | None:
    if not filename:
        return None
    path = PHOTOS_DIR / filename
    return path if path.exists() else None


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
    query += " ORDER BY title"
    return pd.read_sql_query(query, conn, params=params)


def get_book(conn: sqlite3.Connection, book_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def list_activities(conn: sqlite3.Connection, book_id: str) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT * FROM activities WHERE book_id = ? ORDER BY date",
        conn,
        params=[book_id],
    )


def all_activities(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM activities ORDER BY date", conn)


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


def book_counts_by_category(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT category, COUNT(*) AS count FROM books GROUP BY category ORDER BY count DESC",
        conn,
    )
