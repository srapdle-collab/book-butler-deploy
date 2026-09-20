"""도서관정보나루(data4library.kr) 도서 검색 API 클라이언트."""

from __future__ import annotations

import requests

SEARCH_URL = "http://data4library.kr/api/srchBooks"


class LibraryAPIError(Exception):
    pass


def _parse_title(raw: str | None) -> tuple[str | None, str | None]:
    """'제목 :부제' 형태를 제목/부제로 분리한다."""
    if not raw:
        return None, None
    if " :" in raw:
        title, subtitle = raw.split(" :", 1)
        return title.strip(), subtitle.strip() or None
    return raw.strip(), None


def _parse_authors(raw: str | None) -> tuple[str | None, str | None]:
    """'지은이: A ;옮긴이: B' 형태에서 저자/역자를 분리한다."""
    if not raw:
        return None, None
    author = None
    translator = None
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            role, name = part.split(":", 1)
            role, name = role.strip(), name.strip()
        else:
            role, name = "", part
        if role in ("지은이", "엮은이", "저자"):
            author = f"{author}, {name}" if author else name
        elif role in ("옮긴이", "역자"):
            translator = f"{translator}, {name}" if translator else name
        elif author is None:
            author = name
    return author, translator


def search_books(keyword: str, auth_key: str, page_size: int = 10) -> list[dict]:
    """제목 키워드로 도서를 검색해 3.1(Book) 구조에 맞는 후보 목록을 반환한다."""
    if not auth_key:
        raise LibraryAPIError("DATA4LIBRARY_AUTH_KEY가 설정되지 않았습니다.")
    if not keyword or not keyword.strip():
        return []

    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "authKey": auth_key,
                "keyword": keyword.strip(),
                "pageNo": 1,
                "pageSize": page_size,
                "format": "json",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise LibraryAPIError(f"도서관정보나루 API 호출 실패: {exc}") from exc

    payload = data.get("response", {})
    if payload.get("error") or payload.get("errCode"):
        raise LibraryAPIError(payload.get("error") or payload.get("errCode"))

    docs = payload.get("docs", [])
    if not isinstance(docs, list):
        raise LibraryAPIError("도서관정보나루 API 응답 형식이 예상과 다릅니다.")

    candidates = []
    for entry in docs:
        doc = entry.get("doc", {}) if isinstance(entry, dict) else {}
        title, subtitle = _parse_title(doc.get("bookname"))
        author, translator = _parse_authors(doc.get("authors"))
        if not title:
            continue
        candidates.append(
            {
                "title": title,
                "subtitle": subtitle,
                "author": author,
                "translator": translator,
                "publisher": doc.get("publisher") or None,
                "isbn": doc.get("isbn13") or None,
                "cover_url": doc.get("bookImageURL") or None,
            }
        )
    return candidates
