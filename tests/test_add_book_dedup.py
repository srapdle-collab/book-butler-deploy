"""새 책 추가 시 중복 검사 회귀 테스트.

우선순위: ISBN이 있으면 정규화된 ISBN 동일 여부로 저장을 막는다.
ISBN이 없을 때만 제목+저자 동일 여부로 경고(차단은 아님)한다.
제목만 같거나 ISBN이 다른 판본은 걸리지 않는다.
"""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from lib import db, library_api
from test_activity_inputs_app import isolated_app, APP_PATH  # noqa: F401

FIXTURE = Path(__file__).parent / "fixtures" / "data4library_srchbooks_hope.json"


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def upstream(monkeypatch):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    monkeypatch.setattr(library_api.requests, "get", lambda url, params, timeout: _Response(payload))
    monkeypatch.setenv("DATA4LIBRARY_AUTH_KEY", "test-key")


def _search(at, query="희망을 짓는다는 것"):
    at.text_input(key="add_book_query").set_value(query).run()
    at.button(key="add_book_search_btn").click().run()
    return at


def _book_count(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]


# --- ISBN 정규화 --------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("9788932550817", "9788932550817"),
    ("978-89-325-5081-7", "9788932550817"),
    ("978 89 325 5081 7", "9788932550817"),
    ("89-325-5081-x", "893255081X"),
    (None, None),
    ("", None),
    ("2147483647", None),  # 운영 데이터에서 발견된 잘못된 sentinel 값, 실제 ISBN 아님
])
def test_normalize_isbn(raw, expected):
    assert db.normalize_isbn(raw) == expected


def test_known_invalid_isbn_does_not_flag_unrelated_books_as_duplicate(isolated_app):
    """실제 운영 데이터 감사에서 서로 무관한 책 12권이 '2147483647'이라는
    잘못된 값을 ISBN처럼 공유하고 있었다. 이 값으로는 중복을 판정하지 않는다."""
    conn = db.get_connection()
    db.insert_book(conn, {"title": "완전히 다른 책 A", "isbn": "2147483647"})
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("완전히 다른 책 B").run()
    at.text_input(key="add_book_isbn").set_value("2147483647").run()
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    assert _book_count(conn) == before + 1  # 차단되지 않고 저장됨
    assert not list(at.error)


# --- 검색 결과 표시 (요구사항 1·2·3) --------------------------------------

def test_search_marks_existing_isbn_without_hiding_the_result(isolated_app, upstream):
    conn = db.get_connection()
    db.insert_book(conn, {
        "title": "희망을 짓는다는 것", "author": "엘렌 데이비스",
        "isbn": "9788932550817", "status": "완독",
    })
    at = _search(AppTest.from_file(APP_PATH).run())
    assert not at.exception
    radio = at.radio(key="add_book_pick")
    assert len(radio.options) == 2  # 검색 결과를 숨기지 않는다
    assert radio.options[0].startswith("✓ 이미 내 책장에 있음")
    assert not radio.options[1].startswith("✓")


def test_goto_existing_button_navigates_to_existing_book(isolated_app, upstream):
    conn = db.get_connection()
    existing_id = db.insert_book(conn, {
        "title": "희망을 짓는다는 것", "author": "엘렌 데이비스",
        "isbn": "9788932550817", "status": "완독",
    })
    at = _search(AppTest.from_file(APP_PATH).run())
    at.button(key="add_book_goto_existing_from_search").click().run()
    assert not at.exception
    assert at.session_state["view"] == "책 상세"
    assert at.session_state["selected_book_id"] == existing_id


def test_second_candidate_without_local_match_shows_no_checkmark(isolated_app, upstream):
    conn = db.get_connection()
    db.insert_book(conn, {
        "title": "희망을 짓는다는 것", "author": "엘렌 데이비스",
        "isbn": "9788932550817",
    })
    at = _search(AppTest.from_file(APP_PATH).run())
    at.radio(key="add_book_pick").set_value(1).run()
    assert not [b for b in at.button if b.key == "add_book_goto_existing_from_search"]


# --- 저장 직전 ISBN 차단, UI 우회 방지 (요구사항 4·5) ------------------------

def test_manual_isbn_duplicate_is_blocked_even_without_search(isolated_app):
    """검색을 거치지 않고 수동 입력만으로도 같은 ISBN이면 막혀야 한다."""
    conn = db.get_connection()
    db.insert_book(conn, {"title": "기존 책", "author": "김저자", "isbn": "9788932550817"})
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("전혀 다른 제목").run()
    at.text_input(key="add_book_isbn").set_value("978-89-325-5081-7").run()  # 하이픈 표기 차이
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    assert _book_count(conn) == before
    assert any("이미 같은 ISBN" in e.value for e in at.error)


def test_goto_button_after_isbn_block_navigates_to_existing_book(isolated_app):
    conn = db.get_connection()
    existing_id = db.insert_book(conn, {"title": "기존 책", "author": "김저자", "isbn": "9788932550817"})
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("다른 제목").run()
    at.text_input(key="add_book_isbn").set_value("9788932550817").run()
    at.button(key="add_book_submit").click().run()
    at.button(key="add_book_goto_isbn_dup").click().run()
    assert at.session_state["selected_book_id"] == existing_id


# --- 제목+저자 약한 경고, 차단은 아님 (요구사항 4) --------------------------

def test_title_author_duplicate_without_isbn_requires_confirmation(isolated_app):
    conn = db.get_connection()
    db.insert_book(conn, {"title": "동명이서 테스트", "author": "같은저자"})
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("동명이서 테스트").run()
    at.text_input(key="add_book_author").set_value("같은저자").run()
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    assert _book_count(conn) == before  # 아직 저장 안 됨, 차단이 아니라 확인 대기
    assert any("제목과 저자가 같은 책" in w.value for w in at.warning)
    at.button(key="add_book_save_dup_anyway").click().run()
    assert not at.exception
    assert _book_count(conn) == before + 1  # 확인 후에는 저장됨


def test_title_author_duplicate_cancel_does_not_save(isolated_app):
    conn = db.get_connection()
    db.insert_book(conn, {"title": "동명이서 테스트", "author": "같은저자"})
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("동명이서 테스트").run()
    at.text_input(key="add_book_author").set_value("같은저자").run()
    at.button(key="add_book_submit").click().run()
    at.button(key="add_book_cancel_dup").click().run()
    assert _book_count(conn) == before


def test_title_only_match_with_different_author_does_not_warn_or_block(isolated_app):
    """제목만 같다는 이유로 막거나 경고하지 않는다(동명이서)."""
    conn = db.get_connection()
    db.insert_book(conn, {"title": "동명이서 테스트", "author": "원래저자"})
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("동명이서 테스트").run()
    at.text_input(key="add_book_author").set_value("다른저자").run()
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    assert _book_count(conn) == before + 1  # 경고 없이 바로 저장
    assert not list(at.warning)


def test_different_isbn_same_title_author_is_treated_as_different_edition(isolated_app):
    """ISBN이 다르면(다른 판본) 제목+저자가 같아도 경고하지 않는다."""
    conn = db.get_connection()
    db.insert_book(conn, {
        "title": "같은 제목 다른 판본", "author": "같은저자", "isbn": "1111111111111",
    })
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("같은 제목 다른 판본").run()
    at.text_input(key="add_book_author").set_value("같은저자").run()
    at.text_input(key="add_book_isbn").set_value("2222222222222").run()
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    assert _book_count(conn) == before + 1  # 바로 저장, 경고 없음
    assert not list(at.warning)


def test_no_isbn_and_no_title_author_match_saves_directly(isolated_app):
    conn = db.get_connection()
    before = _book_count(conn)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_title").set_value("완전히 새로운 책").run()
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    assert _book_count(conn) == before + 1
    assert not list(at.warning)
    assert not list(at.error)
