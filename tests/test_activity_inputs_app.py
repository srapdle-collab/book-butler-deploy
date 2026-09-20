import base64
import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from migration.load_db import SCHEMA


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    db_path = tmp_path / "book_butler.db"
    photos_dir = tmp_path / "photos"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.execute(
        """
        INSERT INTO books (
            id, title, author, publisher, isbn, subtitle, translator,
            category, pages, current_page, rating, status, read_count,
            start_date, finish_date, cover_photo, cover_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "book-1", "테스트 책", "저자", "출판사", "123", None, None,
            "신앙", 200, 10, 0, "읽는 중", 0, 1_700_000_000, None, None, None,
        ),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("BOOK_BUTLER_DB_PATH", str(db_path))
    monkeypatch.setenv("BOOK_BUTLER_PHOTOS_DIR", str(photos_dir))
    # 실제 .env의 잠금 설정이 AppTest용 임시 앱으로 흘러들지 않게 한다.
    monkeypatch.setenv("BOOK_BUTLER_APP_PASSWORD", "")
    return db_path, photos_dir


def open_detail() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["view"] = "책 상세"
    at.session_state["selected_book_id"] = "book-1"
    at.run()
    assert not at.exception
    return at


def fetch_one(db_path: Path, query: str):
    conn = sqlite3.connect(db_path)
    row = conn.execute(query).fetchone()
    conn.close()
    return row


def test_progress_form_inserts_numeric_kind_and_updates_current_page(isolated_app):
    """진도 저장이 문자열 kind를 쓰거나 현재 페이지를 갱신하지 않는 회귀를 막는다."""
    db_path, _ = isolated_app
    at = open_detail()
    at.button(key="open_progress").click().run()
    at.number_input(key="progress_page").set_value(25)
    at.number_input(key="progress_minutes").set_value(12)
    at.button(key="save_progress").click().run()
    assert not at.exception

    row = fetch_one(
        db_path,
        "SELECT kind, typeof(kind), text, page, pages_read, minutes_read "
        "FROM activities WHERE kind = 4",
    )
    assert row == (4, "integer", "15쪽을 12분 동안 읽었습니다", 25, 15, 12)
    assert fetch_one(db_path, "SELECT current_page FROM books WHERE id = 'book-1'") == (25,)


def test_quote_form_inserts_numeric_kind_2(isolated_app):
    """인용문이 text 칸이나 문자열 kind로 저장되는 회귀를 막는다."""
    db_path, _ = isolated_app
    at = open_detail()
    at.button(key="open_quote").click().run()
    at.number_input(key="quote_page").set_value(31)
    at.text_area(key="quote_text").set_value("기억할 문장")
    at.button(key="save_quote").click().run()
    assert not at.exception

    assert fetch_one(
        db_path, "SELECT kind, typeof(kind), quote, text, page FROM activities"
    ) == (2, "integer", "기억할 문장", None, 31)


def test_note_form_inserts_numeric_kind_0(isolated_app):
    """메모가 인용문으로 뒤바뀌거나 문자열 kind로 저장되는 회귀를 막는다."""
    db_path, _ = isolated_app
    at = open_detail()
    at.button(key="open_note").click().run()
    at.number_input(key="note_page").set_value(42)
    at.text_area(key="note_text").set_value("오늘의 메모")
    at.button(key="save_note").click().run()
    assert not at.exception

    assert fetch_one(
        db_path, "SELECT kind, typeof(kind), text, quote, page FROM activities"
    ) == (0, "integer", "오늘의 메모", None, 42)


def test_photo_form_inserts_numeric_kind_1_and_writes_file(isolated_app):
    """사진 DB 행만 생기고 실제 파일이 저장되지 않는 회귀를 막는다."""
    db_path, photos_dir = isolated_app
    script = f'''\
from unittest.mock import patch
import streamlit as st

class UploadedPhoto:
    name = "reading.png"
    type = "image/png"
    def getvalue(self):
        return {PNG_BYTES!r}

with patch.object(st, "file_uploader", return_value=UploadedPhoto()):
    exec(compile(open({str(APP_PATH)!r}, encoding="utf-8").read(), {str(APP_PATH)!r}, "exec"))
'''
    at = AppTest.from_string(script, default_timeout=10)
    at.session_state["view"] = "책 상세"
    at.session_state["selected_book_id"] = "book-1"
    at.run()
    assert not at.exception
    at.button(key="open_photo").click().run()
    at.number_input(key="photo_page").set_value(55)
    at.button(key="save_photo").click().run()
    assert not at.exception

    row = fetch_one(
        db_path, "SELECT kind, typeof(kind), photo, page FROM activities"
    )
    assert row[0:2] == (1, "integer")
    assert row[2].startswith("photos/")
    assert row[3] == 55
    saved = photos_dir / Path(row[2]).name
    assert saved.read_bytes() == PNG_BYTES


def test_management_menu_changes_status_and_edits_book(isolated_app):
    """책 관리 폼이 화면에만 반영되고 DB를 갱신하지 않는 회귀를 막는다."""
    db_path, _ = isolated_app
    at = open_detail()
    at.selectbox(key="manage_status").select("완독")
    at.button(key="save_status").click().run()
    assert not at.exception
    status = fetch_one(
        db_path,
        "SELECT status, read_count, finish_date FROM books WHERE id = 'book-1'",
    )
    assert status[0:2] == ("완독", 1)
    assert status[2] is not None
    assert fetch_one(db_path, "SELECT kind, typeof(kind) FROM activities WHERE kind = 5") == (5, "integer")

    at.text_input(key="edit_title").set_value("수정한 책")
    at.text_input(key="edit_category").set_value("성경연구")
    at.number_input(key="edit_pages").set_value(240)
    at.button(key="save_book_info").click().run()
    assert not at.exception
    assert fetch_one(
        db_path,
        "SELECT title, category, pages FROM books WHERE id = 'book-1'",
    ) == ("수정한 책", "성경연구", 240)
