from lib import library_api


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _capture(monkeypatch, docs=None):
    calls = []

    def fake_get(url, params, timeout):
        calls.append(params)
        return _Response({"response": {"docs": docs or []}})

    monkeypatch.setattr(library_api.requests, "get", fake_get)
    return calls


def test_title_query_uses_title_param_not_keyword(monkeypatch):
    calls = _capture(monkeypatch)
    library_api.search_books("희망을 짓는다는 것", "key")
    assert calls[0]["title"] == "희망을 짓는다는 것"
    assert "keyword" not in calls[0]
    assert "isbn13" not in calls[0]


def test_partial_title_uses_title_param(monkeypatch):
    calls = _capture(monkeypatch)
    library_api.search_books("  희망을  ", "key")
    assert calls[0]["title"] == "희망을"
    assert "keyword" not in calls[0]


def test_isbn13_query_uses_isbn13_param(monkeypatch):
    calls = _capture(monkeypatch)
    library_api.search_books("9788932550817", "key")
    assert calls[0]["isbn13"] == "9788932550817"
    assert "title" not in calls[0] and "keyword" not in calls[0]


def test_hyphenated_isbn13_is_normalized(monkeypatch):
    calls = _capture(monkeypatch)
    library_api.search_books("978-89-325-5081-7", "key")
    library_api.search_books("978 8932 550817", "key")
    assert [c["isbn13"] for c in calls] == ["9788932550817", "9788932550817"]


def test_numeric_title_that_is_not_isbn13_stays_title(monkeypatch):
    calls = _capture(monkeypatch)
    library_api.search_books("1984", "key")
    assert calls[0]["title"] == "1984"


def test_parsing_and_titleless_filter_are_unchanged(monkeypatch):
    _capture(monkeypatch, docs=[
        {"doc": {
            "bookname": "희망을 짓는다는 것 :성경의 언어로 쌓아 올린 51편의 메시지 ",
            "authors": "지은이: 엘렌 데이비스 ;옮긴이: 윤상필",
            "publisher": "한국성서유니온선교회",
            "isbn13": "9788932550817",
            "bookImageURL": "https://example.test/cover.jpg",
        }},
        {"doc": {"bookname": "", "isbn13": "9780000000000"}},
    ])
    results = library_api.search_books("희망을 짓는다는 것", "key")
    assert results == [{
        "title": "희망을 짓는다는 것",
        "subtitle": "성경의 언어로 쌓아 올린 51편의 메시지",
        "author": "엘렌 데이비스",
        "translator": "윤상필",
        "publisher": "한국성서유니온선교회",
        "isbn": "9788932550817",
        "cover_url": "https://example.test/cover.jpg",
    }]
