"""검색 결과 선택 시 새 책 추가 폼 서지정보 자동입력 회귀 테스트.

실제 도서관정보나루 srchBooks 응답(《희망을 짓는다는 것》)을 fixture로 쓴다.
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


def _fields(at):
    return {name: at.text_input(key=f"add_book_{name}").value
            for name in ("title", "subtitle", "author", "translator", "publisher", "isbn")}


HOPE = {
    "title": "희망을 짓는다는 것",
    "subtitle": "성경의 언어로 쌓아 올린 51편의 메시지",
    "author": "엘렌 데이비스",
    "translator": "윤상필",
    "publisher": "한국성서유니온선교회",
    "isbn": "9788932550817",
}


def test_real_hope_record_parses_author_translator_and_extra_fields(upstream):
    [hope, _] = library_api.search_books("희망을 짓는다는 것", "key")
    assert {k: hope[k] for k in HOPE} == HOPE
    assert hope["cover_url"].startswith("https://shopping-phinf.pstatic.net/")
    assert hope["publication_year"] == "2026"
    assert hope["class_no"] == "235.2"
    assert hope["class_nm"] == "종교 > 기독교 > 포교, 교육, 교화활동, 목회학"


def test_missing_upstream_values_are_not_guessed(upstream):
    [_, second] = library_api.search_books("두 번째", "key")
    assert second["subtitle"] is None
    assert second["cover_url"] is None
    assert second["class_nm"] is None and second["class_no"] is None
    assert second["author"] == "홍길동"
    assert second["translator"] == "김역자, 이역자"
    assert "pages" not in second


@pytest.mark.parametrize("raw,expected", [
    ("엘렌 데이비스,윤상필 옮김", ("엘렌 데이비스", "윤상필")),
    ("엘렌 데이비스, 윤상필 옮김", ("엘렌 데이비스", "윤상필")),
    ("C. S. 루이스 지음 ;홍종락 옮김", ("C. S. 루이스", "홍종락")),
    ("존 스토트 저 ; 정옥배 역", ("존 스토트", "정옥배")),
    ("지은이: 엘렌 데이비스 ;옮긴이: 윤상필", ("엘렌 데이비스", "윤상필")),
    ("옮긴이: 김역자, 이역자", (None, "김역자, 이역자")),
    ("한강 지음", ("한강", None)),
    ("E.H. 카 [지음],김택현 옮김", ("E.H. 카", "김택현")),
    ("C.S. 루이스, 이종태 [공]옮김", ("C.S. 루이스", "이종태")),
    ("헤르만 헤세 글,정여울 옮김", ("헤르만 헤세", "정여울")),
    ("한상경 글·사진", ("한상경 글·사진", None)),  # 모르는 표기는 원문 그대로 둔다.
    ("유발 하라리", ("유발 하라리", None)),
    ("김옮김", ("김옮김", None)),  # 공백으로 구분된 표기만 역할로 본다.
    ("", (None, None)),
])
def test_author_translator_split_only_on_explicit_markers(raw, expected):
    assert library_api._parse_authors(raw) == expected


def test_selecting_search_result_fills_empty_fields(isolated_app, upstream):
    at = _search(AppTest.from_file(APP_PATH).run())
    assert not at.exception
    assert _fields(at) == HOPE


def test_switching_candidate_replaces_autofilled_but_keeps_user_edits(isolated_app, upstream):
    at = _search(AppTest.from_file(APP_PATH).run())
    at.text_input(key="add_book_title").set_value("내가 고친 제목").run()
    at.radio(key="add_book_pick").set_value(1).run()
    fields = _fields(at)
    assert fields["title"] == "내가 고친 제목"
    assert fields["author"] == "홍길동"
    assert fields["translator"] == "김역자, 이역자"
    assert fields["publisher"] == "두번째출판사"
    assert fields["isbn"] == "9791100000002"
    assert fields["subtitle"] == ""  # upstream에 없으면 이전 후보 값도 남기지 않는다.


def test_prior_manual_input_is_not_overwritten(isolated_app, upstream):
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key="add_book_publisher").set_value("직접 입력한 출판사").run()
    _search(at)
    fields = _fields(at)
    assert fields["publisher"] == "직접 입력한 출판사"
    assert fields["title"] == HOPE["title"]


def test_saving_selected_result_persists_bibliographic_fields(isolated_app, upstream):
    at = _search(AppTest.from_file(APP_PATH).run())
    at.button(key="add_book_submit").click().run()
    assert not at.exception
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM books WHERE isbn = ?", (HOPE["isbn"],)).fetchone()
    assert row is not None
    assert {k: row[k] for k in HOPE} == HOPE
    assert row["cover_url"].startswith("https://shopping-phinf.pstatic.net/")
    assert row["category"] is None  # KDC 분류를 개인 카테고리로 추측 저장하지 않는다.
    assert row["pages"] is None  # upstream이 쪽수를 주지 않는다.
