from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

from lib import db
from lib import reading_chunks as chunks
from test_activity_inputs_app import fetch_one, isolated_app, open_detail


def _save(conn, **overrides):
    values = {
        "owner_id": chunks.LOCAL_OWNER_ID,
        "book_id": "book-1",
        "read_date": "2026-09-26",
        "page_start": 45,
        "page_end": 52,
        "minutes": 12,
        "original_text": "  용서는  \n 관계를  회복한다. ",
        "user_note": "설교에 쓸 수 있다.",
        "tags": ["용서", "관계", "용서"],
        "illustration_tags": ["회복"],
        "content_types": ["illustration", "meditation"],
    }
    values.update(overrides)
    return chunks.save(conn, **values)


def test_chunk_is_additive_and_duplicate_requires_explicit_choice(isolated_app):
    conn = db.get_connection()
    chunk = _save(conn)
    assert chunk["source_app"] == "readdam"
    assert chunk["owner_id"] == chunks.LOCAL_OWNER_ID
    assert chunk["tags"] == ["용서", "관계"]
    assert chunk["content_hash"] == chunks.content_hash(chunk["original_text"], chunk["user_note"])
    assert fetch_one(isolated_app[0], "SELECT COUNT(*) FROM activities") == (0,)
    with pytest.raises(chunks.DuplicateChunk):
        _save(conn)
    duplicate = _save(conn, allow_duplicate=True)
    assert duplicate["chunk_id"] != chunk["chunk_id"]
    assert len(chunks.list_for_book(conn, "book-1", tag="용서", owner_id=chunks.LOCAL_OWNER_ID)) == 2
    assert not chunks.list_for_book(conn, "book-1", tag="없는 태그", owner_id=chunks.LOCAL_OWNER_ID)
    conn.close()


def test_chunk_update_and_soft_delete_are_separate_from_existing_records(isolated_app):
    conn = db.get_connection()
    chunk = _save(conn)
    updated = _save(
        conn, chunk_id=chunk["chunk_id"], page_start=None, page_end=None,
        position_note="전자책 42%", original_text="바뀐 원문", user_note="", tags=["묵상"],
    )
    assert updated["chunk_id"] == chunk["chunk_id"]
    assert updated["position_note"] == "전자책 42%"
    assert updated["page_start"] is None
    assert updated["source_app"] == "readdam"
    chunks.soft_delete(conn, chunk["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID)
    assert chunks.list_for_book(conn, "book-1", owner_id=chunks.LOCAL_OWNER_ID) == []
    deleted = chunks.get(conn, chunk["chunk_id"], include_deleted=True, owner_id=chunks.LOCAL_OWNER_ID)
    assert deleted["deleted_at"]
    assert fetch_one(isolated_app[0], "SELECT COUNT(*) FROM activities") == (0,)
    conn.close()


def test_chunk_input_is_available_in_book_detail_and_saves_metadata(isolated_app):
    at = open_detail()
    at.button(key="open_reading_chunk").click().run()
    at.text_input(key="chunk_input_page_start").set_value("20")
    at.text_input(key="chunk_input_page_end").set_value("23")
    at.text_area(key="chunk_input_original_text").set_value("입력한 원문")
    at.text_area(key="chunk_input_user_note").set_value("입력한 메모")
    at.text_input(key="chunk_input_tags").set_value("묵상, 은혜")
    at.text_input(key="chunk_input_illustration_tags").set_value("회복")
    at.multiselect(key="chunk_input_content_types").set_value(["meditation"])
    at.button(key="save_reading_chunk").click().run()
    assert not at.exception
    assert not at.error, [item.value for item in at.error]
    row = fetch_one(
        isolated_app[0],
        "SELECT source_app, page_start, page_end, original_text, user_note FROM reading_chunks",
    )
    assert row == ("readdam", 20, 23, "입력한 원문", "입력한 메모")


def _export_module():
    script = Path(__file__).parents[1] / "tools" / "export_chunks.py"
    spec = importlib.util.spec_from_file_location("export_chunks", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def _ids():
    """Explicit synthetic selection for export tests (not a product default)."""
    conn = db.get_readonly_connection()
    try:
        return [row["chunk_id"] for row in chunks.all_chunks(conn, owner_id=chunks.LOCAL_OWNER_ID)]
    finally:
        conn.close()


def test_txt_export_is_idempotent_and_moves_only_indexed_deleted_chunk(isolated_app, tmp_path):
    conn = db.get_connection()
    chunk = _save(conn)
    conn.close()
    exporter = _export_module()
    first = exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    archive = tmp_path / "독서조각"
    index_path = archive / "_index.csv"
    with index_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert first == {"written": 1, "moved": 0, "deleted": 0, "total": 1}
    exported = archive / rows[0]["상대경로"]
    assert exported.read_bytes()[:3] != b"\xef\xbb\xbf"
    text = exported.read_text(encoding="utf-8")
    assert "ISBN: 123" in text
    assert "읽은 시간: 12분" in text
    assert "콘텐츠 타입: 예화 후보, 묵상 소재" in text
    assert "출처 앱: 읽담 (readdam)" in text
    assert "chunkId: " + chunk["chunk_id"] in text
    assert exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())["written"] == 0

    conn = db.get_connection()
    chunks.soft_delete(conn, chunk["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID)
    conn.close()
    result = exporter.export(tmp_path, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=_ids())
    assert result["moved"] == 1
    assert not exported.exists()
    assert any((archive / "_삭제됨").glob(f"*{chunk['chunk_id'][:8]}.txt"))
