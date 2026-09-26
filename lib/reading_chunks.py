"""읽담의 독립적인 '읽은 조각' 저장소.

기존 activities의 kind 체계와 통계는 건드리지 않는다. 조각은 이후 다른 앱과
동기화할 수 있도록 별도 UUID와 스냅샷 메타데이터를 가진다.
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from zoneinfo import ZoneInfo
import uuid

from lib import database

KST = ZoneInfo("Asia/Seoul")
LOCAL_OWNER_ID = "local-owner"
CONTENT_TYPES = {
    "illustration": "예화 후보",
    "lecture": "강의 소재",
    "meditation": "묵상 소재",
    "insight": "인사이트",
}


class DuplicateChunk(ValueError):
    """별도 UUID지만 같은 범위·내용인 조각을 사용자가 확인해야 할 때."""

    def __init__(self, existing):
        super().__init__("같은 범위와 내용의 읽은 조각이 이미 있습니다.")
        self.existing = existing


def now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="microseconds")


def today_kst() -> str:
    return datetime.now(KST).date().isoformat()


def normalized_text(value: str | None) -> str:
    return " ".join((value or "").split())


def content_hash(original_text: str | None, user_note: str | None) -> str:
    body = f"{normalized_text(original_text)}\n{normalized_text(user_note)}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def clean_tags(values) -> list[str]:
    """공백 항목과 중복만 없애고, 사용자가 쓴 태그 표기는 보존한다."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        tag = str(value).strip()
        key = tag.casefold()
        if tag and key not in seen:
            result.append(tag)
            seen.add(key)
    return result


def parse_tags(value: str | None) -> list[str]:
    return clean_tags((value or "").replace("\n", ",").split(","))


def _decode(row):
    if row is None:
        return None
    result = dict(row)
    for field in ("tags", "illustration_tags", "content_types"):
        try:
            result[field] = json.loads(result[field] or "[]")
        except (TypeError, json.JSONDecodeError):
            result[field] = []
    return result


def _require_owner(conn, owner_id):
    if not owner_id or (database.is_postgres(conn) and owner_id == LOCAL_OWNER_ID):
        raise ValueError("인증된 사용자 정보가 필요합니다.")


def get(conn, chunk_id: str, *, owner_id: str, include_deleted: bool = False):
    _require_owner(conn, owner_id)
    query = "SELECT * FROM reading_chunks WHERE chunk_id=? AND owner_id=?"
    if not include_deleted:
        query += " AND deleted_at IS NULL"
    result = _decode(database.execute(conn, query, (chunk_id, owner_id)).fetchone())
    if result:
        _book_snapshot(conn, result["book_id"], owner_id)
    return result


def list_for_book(conn, book_id: str, *, owner_id: str, tag: str | None = None, include_deleted: bool = False):
    _book_snapshot(conn, book_id, owner_id)
    query = "SELECT * FROM reading_chunks WHERE book_id=? AND owner_id=?"
    params: list[str] = [book_id, owner_id]
    if not include_deleted:
        query += " AND deleted_at IS NULL"
    query += " ORDER BY read_date DESC, created_at DESC"
    rows = [_decode(row) for row in database.execute(conn, query, params).fetchall()]
    # JSON 문자열에 LIKE를 적용하면 %, _, 인용부호가 오동작한다.
    needle = (tag or "").strip()
    return [row for row in rows if not needle or needle in row["tags"] or needle in row["illustration_tags"]]


def all_chunks(conn, *, owner_id: str, include_deleted: bool = True):
    _require_owner(conn, owner_id)
    query = "SELECT * FROM reading_chunks WHERE owner_id=?"
    if not include_deleted:
        query += " AND deleted_at IS NULL"
    query += " ORDER BY updated_at, chunk_id"
    rows = [_decode(row) for row in database.execute(conn, query, (owner_id,)).fetchall()]
    for row in rows:
        _book_snapshot(conn, row["book_id"], owner_id)
    return rows


def _book_snapshot(conn, book_id: str, owner_id: str):
    _require_owner(conn, owner_id)
    book = database.execute(conn, "SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    local_legacy = book is not None and not database.is_postgres(conn) and owner_id == LOCAL_OWNER_ID and book["owner_id"] is None
    if book is None or (book["owner_id"] != owner_id and not local_legacy):
        raise ValueError("책과 사용자 정보가 일치하지 않습니다.")
    return book


def _validate(*, read_date: str, page_start, page_end, minutes, original_text, user_note, content_types):
    try:
        date.fromisoformat(read_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("읽은 날짜는 YYYY-MM-DD 형식이어야 합니다.") from exc
    if page_start is not None and int(page_start) < 0:
        raise ValueError("시작 페이지는 0 이상이어야 합니다.")
    if page_end is not None and int(page_end) < 0:
        raise ValueError("끝 페이지는 0 이상이어야 합니다.")
    if page_start is not None and page_end is not None and int(page_start) > int(page_end):
        raise ValueError("시작 페이지는 끝 페이지보다 클 수 없습니다.")
    if minutes is not None and int(minutes) < 0:
        raise ValueError("읽은 시간은 0분 이상이어야 합니다.")
    if not (original_text or "").strip() and not (user_note or "").strip():
        raise ValueError("원문 또는 내 메모를 입력해주세요.")
    unsupported = set(content_types or []) - set(CONTENT_TYPES)
    if unsupported:
        raise ValueError("지원하지 않는 콘텐츠 타입입니다.")


def _duplicate(conn, *, owner_id, book_id, read_date, page_start, page_end, digest, excluding=None):
    query = """
        SELECT * FROM reading_chunks
        WHERE owner_id=? AND book_id=? AND read_date=?
          AND (page_start=? OR (page_start IS NULL AND CAST(? AS INTEGER) IS NULL))
          AND (page_end=? OR (page_end IS NULL AND CAST(? AS INTEGER) IS NULL))
          AND content_hash=?
          AND deleted_at IS NULL
    """
    params = [owner_id, book_id, read_date, page_start, page_start, page_end, page_end, digest]
    if excluding:
        query += " AND chunk_id != ?"
        params.append(excluding)
    return _decode(database.execute(conn, query, params).fetchone())


def save(
    conn,
    *,
    owner_id: str,
    book_id: str,
    chunk_id: str | None = None,
    read_date: str | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    position_note: str | None = None,
    minutes: int | None = None,
    original_text: str | None = None,
    user_note: str | None = None,
    tags=None,
    illustration_tags=None,
    content_types=None,
    allow_duplicate: bool = False,
):
    """새 조각을 만들거나, 같은 chunkId의 조각을 수정한다.

    source_app은 읽담 화면에서만 만드는 1차-A 규칙에 따라 항상 ``readdam``이다.
    """
    book = _book_snapshot(conn, book_id, owner_id)
    existing = get(conn, chunk_id, owner_id=owner_id, include_deleted=True) if chunk_id else None
    if chunk_id and existing is None and database.execute(conn, "SELECT chunk_id FROM reading_chunks WHERE chunk_id=?", (chunk_id,)).fetchone():
        raise ValueError("읽은 조각과 사용자 정보가 일치하지 않습니다.")
    if existing and (existing["book_id"] != book_id or existing["deleted_at"]):
        raise ValueError("다른 책의 조각 또는 삭제된 조각은 수정할 수 없습니다.")
    read_date = read_date or (existing and existing["read_date"]) or today_kst()
    page_start = int(page_start) if page_start is not None else None
    page_end = int(page_end) if page_end is not None else None
    minutes = int(minutes) if minutes is not None else None
    original_text = (original_text or "").strip()
    user_note = (user_note or "").strip()
    position_note = (position_note or "").strip() or None
    tags = clean_tags(tags)
    illustration_tags = clean_tags(illustration_tags)
    content_types = clean_tags(content_types)
    _validate(
        read_date=read_date, page_start=page_start, page_end=page_end, minutes=minutes,
        original_text=original_text, user_note=user_note, content_types=content_types,
    )
    digest = content_hash(original_text, user_note)
    duplicate = _duplicate(
        conn, owner_id=owner_id, book_id=book_id, read_date=read_date,
        page_start=page_start, page_end=page_end, digest=digest,
        excluding=chunk_id,
    )
    if duplicate and not allow_duplicate:
        raise DuplicateChunk(duplicate)

    timestamp = now_iso()
    if existing is None:
        chunk_id = chunk_id or str(uuid.uuid4())
        database.execute(
            conn,
            """INSERT INTO reading_chunks (
                chunk_id, owner_id, book_id, book_title, author, isbn, source_app, source_ref,
                read_date, page_start, page_end, position_note, minutes, original_text, user_note,
                tags, illustration_tags, content_types, content_hash, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'readdam', NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                chunk_id, owner_id, book_id, book["title"], book["author"], book["isbn"],
                read_date, page_start, page_end, position_note, minutes, original_text or None,
                user_note or None, json.dumps(tags, ensure_ascii=False),
                json.dumps(illustration_tags, ensure_ascii=False),
                json.dumps(content_types, ensure_ascii=False), digest, timestamp, timestamp,
            ),
        )
    else:
        cursor = database.execute(
            conn,
            """UPDATE reading_chunks SET read_date=?, page_start=?, page_end=?, position_note=?,
                minutes=?, original_text=?, user_note=?, tags=?, illustration_tags=?, content_types=?,
                content_hash=?, updated_at=? WHERE chunk_id=? AND owner_id=? AND book_id=? AND deleted_at IS NULL""",
            (
                read_date, page_start, page_end, position_note, minutes, original_text or None,
                user_note or None, json.dumps(tags, ensure_ascii=False),
                json.dumps(illustration_tags, ensure_ascii=False), json.dumps(content_types, ensure_ascii=False),
                digest, timestamp, chunk_id, owner_id, book_id,
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError("읽은 조각이 변경되어 저장하지 못했습니다.")
    conn.commit()
    return get(conn, chunk_id, owner_id=owner_id, include_deleted=True)


def soft_delete(conn, chunk_id: str, *, owner_id: str):
    chunk = get(conn, chunk_id, owner_id=owner_id)
    if chunk is None:
        raise ValueError("읽은 조각을 찾을 수 없습니다.")
    cursor = database.execute(conn, "UPDATE reading_chunks SET deleted_at=?, updated_at=? WHERE chunk_id=? AND owner_id=? AND book_id=? AND deleted_at IS NULL", (now_iso(), now_iso(), chunk_id, owner_id, chunk["book_id"]))
    if cursor.rowcount != 1:
        raise ValueError("읽은 조각이 변경되어 삭제하지 못했습니다.")
    conn.commit()
