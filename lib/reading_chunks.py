"""읽담의 독립적인 '읽은 조각' 저장소.

기존 activities의 kind 체계와 통계는 건드리지 않는다. 조각은 이후 다른 앱과
동기화할 수 있도록 별도 UUID와 스냅샷 메타데이터를 가진다.
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import re
import unicodedata
from zoneinfo import ZoneInfo
import uuid

from lib import database
from lib import illustration_categories

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


def canonical_illustration_tags(values) -> list[str]:
    """Store only snapshot-backed NFC canonical category names."""
    if values in (None, []):
        return []
    snapshot = illustration_categories.load_snapshot()
    return illustration_categories.canonicalize_selection(snapshot, values)


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
    # Pre-policy records can contain legacy free text.  A normal body edit must
    # not silently rewrite that value; the dedicated approval panel resolves it.
    illustration_tags = (existing["illustration_tags"] if existing is not None and illustration_tags is None
                         else canonical_illustration_tags(illustration_tags or []))
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


def set_illustration_tags(conn, chunk_id: str, *, owner_id: str, illustration_tags) -> dict:
    """Approve a snapshot-backed category choice without changing the chunk body.

    This intentionally accepts both 읽담 and today-library chunks: reading chunk
    categorization is finalized only in 읽담.
    """
    selected = canonical_illustration_tags(illustration_tags or [])
    current = get(conn, chunk_id, owner_id=owner_id)
    if current is None:
        raise ValueError("읽은 조각을 찾을 수 없습니다.")
    cursor = database.execute(
        conn,
        "UPDATE reading_chunks SET illustration_tags=?, updated_at=? WHERE chunk_id=? AND owner_id=? AND deleted_at IS NULL",
        (json.dumps(selected, ensure_ascii=False), now_iso(), chunk_id, owner_id),
    )
    if cursor.rowcount != 1:
        raise ValueError("예화 카테고리를 저장하지 못했습니다.")
    conn.commit()
    return get(conn, chunk_id, owner_id=owner_id)


def soft_delete(conn, chunk_id: str, *, owner_id: str):
    chunk = get(conn, chunk_id, owner_id=owner_id)
    if chunk is None:
        raise ValueError("읽은 조각을 찾을 수 없습니다.")
    cursor = database.execute(conn, "UPDATE reading_chunks SET deleted_at=?, updated_at=? WHERE chunk_id=? AND owner_id=? AND book_id=? AND deleted_at IS NULL", (now_iso(), now_iso(), chunk_id, owner_id, chunk["book_id"]))
    if cursor.rowcount != 1:
        raise ValueError("읽은 조각이 변경되어 삭제하지 못했습니다.")
    conn.commit()


def _incoming_error(payload) -> str | None:
    """Return the first invalid schemaVersion 1 field without echoing its value."""
    if not isinstance(payload, dict):
        return "payload"
    if type(payload.get("schemaVersion")) is not int or payload["schemaVersion"] != 1:
        return "schemaVersion"
    chunk_id = payload.get("chunkId")
    try:
        parsed = uuid.UUID(chunk_id)
        if parsed.version != 4 or str(parsed) != chunk_id:
            return "chunkId"
    except (TypeError, ValueError, AttributeError):
        return "chunkId"
    if payload.get("sourceApp") != "today-library":
        return "sourceApp"
    for field, limit, required in (
        ("bookId", 100, False), ("bookTitle", 500, True), ("author", 300, False),
        ("isbn", 100, False), ("positionNote", 300, False),
        ("originalText", 50000, False), ("userNote", 50000, False),
    ):
        value = payload.get(field)
        if value is None and not required:
            continue
        if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
            return field
    try:
        if date.fromisoformat(payload.get("readDate")).isoformat() != payload["readDate"]:
            return "readDate"
    except (TypeError, ValueError):
        return "readDate"
    for field in ("pageStart", "pageEnd", "minutes"):
        value = payload.get(field)
        if value is not None and (type(value) is not int or value < 0 or value > 100000):
            return field
    if payload.get("pageStart") is not None and payload.get("pageEnd") is not None and payload["pageStart"] > payload["pageEnd"]:
        return "pageEnd"
    if not (payload.get("originalText") or "").strip() and not (payload.get("userNote") or "").strip():
        return "originalText"
    for field in ("tags", "illustrationTags", "contentTypes"):
        values = payload.get(field)
        if not isinstance(values, list) or len(values) > 40 or any(not isinstance(value, str) or not value.strip() or len(value) > 100 for value in values):
            return field
    if any(value not in CONTENT_TYPES for value in payload["contentTypes"]):
        return "contentTypes"
    for field in ("createdAt", "updatedAt"):
        value = payload.get(field)
        try:
            if not isinstance(value, str) or not datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo:
                return field
        except ValueError:
            return field
    return None


def _match_incoming_book(conn, payload, owner_id):
    rows = database.execute(conn, "SELECT id, title, author, isbn, pages, status FROM books WHERE owner_id=?", (owner_id,)).fetchall()
    book_id = payload.get("bookId")
    if book_id:
        for row in rows:
            if row["id"] == book_id:
                return row
    digits = lambda value: re.sub(r"\D", "", value or "")
    isbn = digits(payload.get("isbn"))
    if isbn:
        matches = [row for row in rows if digits(row["isbn"]) == isbn]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None
    normalize = lambda value: " ".join(unicodedata.normalize("NFKC", value or "").casefold().split())
    title, author = normalize(payload["bookTitle"]), normalize(payload.get("author"))
    matches = [row for row in rows if normalize(row["title"]) == title and normalize(row["author"]) == author]
    return matches[0] if len(matches) == 1 else None


def ingest(conn, payload, *, owner_id: str):
    """Store a Today Library chunk without entering save()'s edit path."""
    _require_owner(conn, owner_id)
    field = _incoming_error(payload)
    chunk_id = payload.get("chunkId") if isinstance(payload, dict) else None
    updated_at = payload.get("updatedAt") if isinstance(payload, dict) else None
    receipt = {"chunkId": chunk_id, "payloadUpdatedAt": updated_at}
    if field:
        return {**receipt, "result": "rejected", "errorCode": "invalid_payload", "errorField": field}
    try:
        illustration_tags = canonical_illustration_tags(payload["illustrationTags"])
    except ValueError:
        return {**receipt, "result": "rejected", "errorCode": "invalid_payload", "errorField": "illustrationTags"}

    def existing_owner():
        return database.execute(conn, "SELECT owner_id FROM reading_chunks WHERE chunk_id=?", (chunk_id,)).fetchone()

    existing = existing_owner()
    if existing:
        return {**receipt, "result": "already_stored" if existing["owner_id"] == owner_id else "rejected",
                "errorCode": None if existing["owner_id"] == owner_id else "chunk_id_conflict"}
    book = _match_incoming_book(conn, payload, owner_id)
    if book is None:
        return {**receipt, "result": "rejected", "errorCode": "book_not_matched"}
    digest = content_hash(payload.get("originalText"), payload.get("userNote"))
    try:
        with database.transaction(conn):
            existing = existing_owner()
            if existing:
                return {**receipt, "result": "already_stored" if existing["owner_id"] == owner_id else "rejected",
                        "errorCode": None if existing["owner_id"] == owner_id else "chunk_id_conflict"}
            duplicate = _duplicate(conn, owner_id=owner_id, book_id=book["id"], read_date=payload["readDate"],
                                   page_start=payload.get("pageStart"), page_end=payload.get("pageEnd"), digest=digest)
            database.execute(conn, """INSERT INTO reading_chunks (
                chunk_id, owner_id, book_id, book_title, author, isbn, source_app, source_ref,
                read_date, page_start, page_end, position_note, minutes, original_text, user_note,
                tags, illustration_tags, content_types, content_hash, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'today-library', NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                (chunk_id, owner_id, book["id"], book["title"], book["author"], book["isbn"],
                 payload["readDate"], payload.get("pageStart"), payload.get("pageEnd"), payload.get("positionNote"),
                 payload.get("minutes"), payload.get("originalText") or None, payload.get("userNote") or None,
                 json.dumps(clean_tags(payload["tags"]), ensure_ascii=False),
                 json.dumps(illustration_tags, ensure_ascii=False),
                 json.dumps(clean_tags(payload["contentTypes"]), ensure_ascii=False), digest,
                 payload["createdAt"], payload["updatedAt"]),
            )
    except Exception:
        existing = existing_owner()
        if existing:
            return {**receipt, "result": "already_stored" if existing["owner_id"] == owner_id else "rejected",
                    "errorCode": None if existing["owner_id"] == owner_id else "chunk_id_conflict"}
        raise
    return {**receipt, "result": "stored", "errorCode": None, "duplicateSuspected": bool(duplicate)}
