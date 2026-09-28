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


_AUTHOR_ROLES = ("지은이", "엮은이", "저자")
_TRANSLATOR_ROLES = ("옮긴이", "역자")
# 이름 뒤에 공백으로 붙는 명시적 역할 표기만 인정한다. 그 밖의 표기는 추측하지 않는다.
_AUTHOR_SUFFIXES = ("지음", "저", "공저", "엮음", "글")
_TRANSLATOR_SUFFIXES = ("옮김", "역", "번역", "공역", "공옮김")


def _parse_authors(raw: str | None) -> tuple[str | None, str | None]:
    """저자 문자열에서 저자/역자를 분리한다.

    지원 형식: '지은이: A ;옮긴이: B', 'A 지음 ;B 옮김', 'A,B 옮김'.
    역할 표기가 없는 이름은 저자로 두고, 역자는 명시적 표기가 있을 때만 분리한다.
    """
    if not raw:
        return None, None
    authors: list[str] = []
    translators: list[str] = []

    def add(target: list[str], name: str) -> None:
        name = name.strip()
        if name and name not in target:
            target.append(name)

    for segment in raw.split(";"):
        segment = segment.strip()
        if not segment:
            continue
        if ":" in segment:
            role, names = (x.strip() for x in segment.split(":", 1))
            if role in _TRANSLATOR_ROLES:
                for name in names.split(","):
                    add(translators, name)
            elif role in _AUTHOR_ROLES or not authors:
                for name in names.split(","):
                    add(authors, name)
            continue
        for token in segment.split(","):
            token = token.strip()
            name, _, marker = token.rpartition(" ")
            marker = marker.replace("[", "").replace("]", "")  # '[지음]', '[공]옮김'
            if name and marker in _TRANSLATOR_SUFFIXES:
                add(translators, name)
            elif name and marker in _AUTHOR_SUFFIXES:
                add(authors, name)
            else:
                add(authors, token)
    return ", ".join(authors) or None, ", ".join(translators) or None


def _normalize_isbn13(raw: str) -> str | None:
    """공백·하이픈을 뺀 값이 978/979로 시작하는 13자리 숫자면 ISBN-13으로 본다."""
    digits = raw.replace("-", "").replace(" ", "")
    if len(digits) == 13 and digits.isdigit() and digits.startswith(("978", "979")):
        return digits
    return None


def search_books(keyword: str, auth_key: str, page_size: int = 10) -> list[dict]:
    """제목(또는 ISBN-13)으로 도서를 검색해 3.1(Book) 구조에 맞는 후보 목록을 반환한다.

    srchBooks의 `keyword`는 제목 검색이 아니어서 신간이 누락되므로
    `title`, ISBN-13 형태 입력은 `isbn13` 파라미터를 쓴다.
    """
    if not auth_key:
        raise LibraryAPIError("DATA4LIBRARY_AUTH_KEY가 설정되지 않았습니다.")
    if not keyword or not keyword.strip():
        return []

    query = keyword.strip()
    isbn13 = _normalize_isbn13(query)
    search_param = {"isbn13": isbn13} if isbn13 else {"title": query}

    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "authKey": auth_key,
                **search_param,
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
                # 아래 값은 DB에 칸이 없거나 개인 카테고리 체계와 달라 참고로만 보여준다.
                "publication_year": (doc.get("publication_year") or "").strip() or None,
                "class_no": (doc.get("class_no") or "").strip() or None,
                "class_nm": (doc.get("class_nm") or "").strip() or None,
            }
        )
    return candidates
