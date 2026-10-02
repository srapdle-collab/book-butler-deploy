"""Page-range reading (method A), forgotten-reading expiry, and the 2026-10-02 regression fixes."""
import sqlite3
import time
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from lib import db, reading, records
from test_activity_inputs_app import APP_PATH, fetch_one, isolated_app, open_detail  # noqa: F401

DAY = 24 * 60 * 60


def _add_book(db_path, book_id, title, status="읽는 중", current=0):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT INTO books (id, title, author, category, pages, current_page, rating, status, read_count, start_date)
           VALUES (?, ?, '저자', '신앙', 300, ?, 0, ?, 0, NULL)""",
        (book_id, title, current, status),
    )
    conn.commit()
    conn.close()


def _open_session(db_path, book_id, started_at, state="running", base=0):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO reading_sessions(id,book_id,started_at,stopped_at,base_page,state) VALUES (?,?,?,?,?,?)",
        (f"s-{book_id}", book_id, started_at, started_at + 120 if state == "stopped" else None, base, state),
    )
    conn.commit()
    conn.close()


def test_finish_records_page_range_without_time(isolated_app):
    conn = db.get_connection()
    session = reading.start(conn, "book-1")
    aid = reading.finish(conn, session["id"], 35)
    assert reading.finish(conn, session["id"], 35) == aid
    row = conn.execute(
        "SELECT kind, base_page, page, pages_read, minutes_read, seconds_read, text FROM activities"
    ).fetchone()
    assert tuple(row) == (4, 10, 35, 25, None, None, "10~35쪽, 25쪽을 읽었습니다")
    assert db.get_book(conn, "book-1")["current_page"] == 35
    assert reading.active(conn) is None


def test_reading_left_open_for_a_day_is_cancelled_and_does_not_block(isolated_app):
    db_path, _ = isolated_app
    _add_book(db_path, "book-2", "어제 읽던 책")
    _open_session(db_path, "book-2", int(time.time()) - DAY - 60, state="stopped")
    conn = db.get_connection()
    assert reading.active_fresh(conn) == (None, True)
    assert fetch_one(db_path, "SELECT state FROM reading_sessions WHERE id='s-book-2'") == ("cancelled",)
    assert reading.start(conn, "book-1")["book_id"] == "book-1"


def test_stale_reading_does_not_block_start_or_manual_entry(isolated_app):
    db_path, _ = isolated_app
    _add_book(db_path, "book-2", "어제 읽던 책")
    _open_session(db_path, "book-2", int(time.time()) - DAY - 60)
    conn = db.get_connection()
    db.add_progress(conn, "book-1", 20)
    assert fetch_one(db_path, "SELECT pages_read, minutes_read FROM activities") == (10, None)


def test_fresh_reading_on_another_book_still_blocks_manual_entry(isolated_app):
    db_path, _ = isolated_app
    _add_book(db_path, "book-2", "지금 읽는 책")
    _open_session(db_path, "book-2", int(time.time()) - 60)
    conn = db.get_connection()
    with pytest.raises(ValueError):
        db.add_progress(conn, "book-1", 20)


def test_detail_offers_go_and_cancel_for_another_books_reading(isolated_app):
    db_path, _ = isolated_app
    _add_book(db_path, "book-2", "지금 읽는 책")
    _open_session(db_path, "book-2", int(time.time()) - 60)
    at = open_detail()
    at.button(key="open_progress").click().run()
    assert not at.exception
    assert at.button(key="timer_go")
    at.button(key="timer_cancel_other").click().run()
    assert not at.exception
    assert fetch_one(db_path, "SELECT state FROM reading_sessions WHERE id='s-book-2'") == ("cancelled",)


def test_app_start_finish_flow_has_no_clock_or_pause(isolated_app):
    db_path, _ = isolated_app
    at = open_detail()
    at.button(key="open_progress").click().run()
    at.button(key="timer_start").click().run()
    assert not at.exception
    assert not [b for b in at.button if b.key == "timer_stop"]
    at.number_input(key="timer_page").set_value(40)
    at.button(key="timer_save").click().run()
    assert not at.exception
    assert fetch_one(db_path, "SELECT pages_read, minutes_read, page FROM activities") == (30, None, 40)


def test_open_reading_comes_first_in_resume_row(isolated_app):
    db_path, _ = isolated_app
    for index in range(2, 9):
        _add_book(db_path, f"book-{index}", f"다른 책 {index}")
        conn = db.get_connection()
        db.add_progress(conn, f"book-{index}", 5)
        conn.close()
    _add_book(db_path, "book-silent", "기록 없는 책")
    _open_session(db_path, "book-silent", int(time.time()) - 60)
    at = AppTest.from_file(APP_PATH, default_timeout=15).run()
    assert not at.exception
    resume = [b.key for b in at.button if str(b.key).startswith("resume_cover_")]
    assert resume[0] == "resume_cover_book-silent"


def test_timeless_progress_record_can_be_edited_without_minutes(isolated_app):
    conn = db.get_connection()
    aid = db.add_progress(conn, "book-1", 30)
    records.update(conn, aid, page=32, minutes=None)
    row = conn.execute("SELECT page, pages_read, minutes_read, text FROM activities WHERE id=?", (aid,)).fetchone()
    assert tuple(row) == (32, 22, None, "10~32쪽, 22쪽을 읽었습니다")


def test_migration_moves_activity_identity_past_copied_positions():
    from migration import migrate_to_supabase as migrate

    executed = []
    migrate.sync_activity_position_sequence(SimpleNamespace(execute=lambda sql: executed.append(sql)))
    assert executed == [migrate.ACTIVITY_SEQUENCE_SYNC]
    assert "setval(pg_get_serial_sequence('activities','position')" in executed[0]
    assert "max(position)" in executed[0]


def _fake_postgres(last_value, highest):
    answers = {
        "pg_get_serial_sequence": "public.activities_position_seq",
        "last_value": last_value,
        "max(position)": highest,
    }

    class Cursor:
        def __init__(self, value):
            self.value = value

        def fetchone(self):
            return {"v": self.value}

    class Connection:
        backend = "postgres"

        def execute(self, sql, params=()):
            for needle, value in answers.items():
                if needle in sql:
                    return Cursor(value)
            raise AssertionError(sql)

    return Connection()


def test_sequence_check_flags_the_production_failure_and_passes_when_fixed():
    db.clear_schema_cache()
    assert db.activity_sequence_behind(_fake_postgres(4, 5667)) is True
    db.clear_schema_cache()
    assert db.activity_sequence_behind(_fake_postgres(5667, 5667)) is False
    assert db.activity_sequence_behind(sqlite3.connect(":memory:")) is False
