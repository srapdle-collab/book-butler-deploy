from __future__ import annotations

import json
import sqlite3
import unicodedata
from pathlib import Path

import pytest

from lib import illustration_categories as subject
from lib import db, reading_chunks as chunks
from lib import approval_diagnostics
from test_activity_inputs_app import fetch_one, isolated_app, open_detail


FIXTURE_SNAPSHOT = Path(__file__).parent / "fixtures" / "illustration_categories.json"
FIXTURE_CASES = Path(__file__).parents[1] / "config" / "illustration_recommendation_fixtures.json"


def test_load_requires_nfc_canonical_names_and_unique_categories(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({
        "version": 1, "generatedAt": "2026-09-28T00:00:00+09:00",
        "categories": [{"canonical": unicodedata.normalize("NFD", "기도"), "aliases": [], "keywords": []}],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="NFC"):
        subject.load_snapshot(path)


def test_snapshot_rejects_overlong_or_ambiguous_alias_dictionary(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({
        "version": 1, "generatedAt": "2026-09-28T00:00:00+09:00",
        "categories": [
            {"canonical": "용서", "aliases": [f"별칭{i}" for i in range(9)], "keywords": []},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="8개"):
        subject.load_snapshot(path)
    path.write_text(json.dumps({
        "version": 1, "generatedAt": "2026-09-28T00:00:00+09:00",
        "categories": [
            {"canonical": "용서", "aliases": ["화해"], "keywords": []},
            {"canonical": "사랑", "aliases": ["화해"], "keywords": []},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="alias"):
        subject.load_snapshot(path)


def test_recommendation_fixture_is_the_shared_contract():
    snapshot = subject.load_snapshot(FIXTURE_SNAPSHOT)
    cases = json.loads(FIXTURE_CASES.read_text(encoding="utf-8"))["cases"]
    for case in cases:
        assert subject.recommend(snapshot, **case["input"]) == case["recommendations"], case["id"]


def test_recommendation_uses_snapshot_order_caps_at_three_and_defaults_only_strong_matches(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps({
        "version": 1, "generatedAt": "2026-09-28T00:00:00+09:00",
        "categories": [
            {"canonical": name, "aliases": [], "keywords": []}
            for name in ("하나", "둘", "셋", "넷")
        ],
    }, ensure_ascii=False), encoding="utf-8")
    snapshot = subject.load_snapshot(snapshot_path)
    assert subject.recommend(snapshot, originalText="넷 셋 둘 하나", userNote="", tags=[]) == [
        {"canonical": "하나", "score": 2, "defaultChecked": False},
        {"canonical": "둘", "score": 2, "defaultChecked": False},
        {"canonical": "셋", "score": 2, "defaultChecked": False},
    ]


def test_keyword_score_is_capped_at_two_per_category(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({
        "version": 1, "generatedAt": "2026-09-28T00:00:00+09:00",
        "categories": [{"canonical": "기도 주제", "aliases": [], "keywords": ["간구", "중보", "기도회"]}],
    }, ensure_ascii=False), encoding="utf-8")
    snapshot = subject.load_snapshot(path)
    assert subject.recommend(snapshot, originalText="간구와 중보 기도회", userNote="", tags=[]) == [
        {"canonical": "기도 주제", "score": 2, "defaultChecked": False},
    ]


def test_canonical_selection_rejects_aliases_and_keeps_snapshot_order():
    snapshot = subject.load_snapshot(FIXTURE_SNAPSHOT)
    assert subject.canonicalize_selection(snapshot, ["기도", "용서", "기도"]) == ["용서", "기도"]
    with pytest.raises(ValueError, match="실제 카테고리"):
        subject.canonicalize_selection(snapshot, ["관계"])
    assert subject.canonicalize_selection(snapshot, []) == []


def test_chunk_save_and_later_approval_store_only_snapshot_canonical_names(isolated_app, monkeypatch):
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
        original_text="카테고리 검증", user_note="", tags=[], illustration_tags=["기도", "용서", "기도"],
        content_types=[],
    )
    assert saved["illustration_tags"] == ["용서", "기도"]
    with pytest.raises(ValueError, match="실제 카테고리"):
        chunks.set_illustration_tags(conn, saved["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID,
                                     illustration_tags=["관계"])
    with pytest.raises(ValueError, match="실제 카테고리"):
        chunks.save(
            conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
            original_text="자유 입력 금지", user_note="", tags=[], illustration_tags=["임의 예화 태그"],
            content_types=[], allow_duplicate=True,
        )
    cleared = chunks.set_illustration_tags(conn, saved["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID,
                                            illustration_tags=[])
    assert cleared["illustration_tags"] == []
    conn.close()


def test_existing_legacy_tag_is_only_replaced_by_explicit_category_approval(isolated_app, monkeypatch):
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
        original_text="기존 조각", user_note="", tags=[], illustration_tags=[], content_types=[],
    )
    conn.execute("UPDATE reading_chunks SET illustration_tags=? WHERE chunk_id=?", ('["과거 자유 입력"]', saved["chunk_id"]))
    conn.commit()
    edited = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", chunk_id=saved["chunk_id"],
        read_date="2026-09-28", original_text="기존 조각 수정", user_note="", tags=[],
        illustration_tags=None, content_types=[],
    )
    assert edited["illustration_tags"] == ["과거 자유 입력"]
    approved = chunks.set_illustration_tags(conn, saved["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID,
                                             illustration_tags=["기도"])
    assert approved["illustration_tags"] == ["기도"]
    conn.close()


def test_chunk_ui_saves_empty_then_requires_explicit_category_approval(isolated_app, monkeypatch):
    db_path, _ = isolated_app
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    at = open_detail()
    at.button(key="open_reading_chunk").click().run()
    at.text_area(key="chunk_input_original_text").set_value("기도로 간구한다.")
    at.text_input(key="chunk_input_tags").set_value("묵상")
    assert not any(item.key == "chunk_input_illustration_tags" for item in at.text_input)
    at.button(key="save_reading_chunk").click().run()
    chunk_id = fetch_one(db_path, "SELECT chunk_id FROM reading_chunks")[0]
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ("[]",)
    assert any(item.value == "예화창고로 보낼까요?" for item in at.subheader)
    selection_key = f"chunk_category_selection_{chunk_id}"
    assert at.multiselect(key=selection_key).value == ["기도"]
    at.multiselect(key=selection_key).set_value(["기도", "용서"])
    at.button(key=f"chunk_category_send_{chunk_id}").click().run()
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ('["용서", "기도"]',)


def test_category_ui_allows_explicit_no_send_for_existing_chunk(isolated_app, monkeypatch):
    db_path, _ = isolated_app
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
        original_text="기도", user_note="", tags=[], illustration_tags=["기도"], content_types=[],
    )
    conn.execute("UPDATE reading_chunks SET source_app='today-library' WHERE chunk_id=?", (saved["chunk_id"],))
    conn.commit()
    conn.close()
    at = open_detail()
    at.button(key=f"chunk_category_open_{saved['chunk_id']}").click().run()
    at.button(key=f"chunk_category_skip_{saved['chunk_id']}").click().run()
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ("[]",)


def test_existing_chunk_category_button_updates_matching_chunk_across_rerun(isolated_app, monkeypatch):
    db_path, _ = isolated_app
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1",
        chunk_id="b0135692-7893-4f6a-b049-b198f30933a3", read_date="2026-09-28",
        original_text="기존 희망 책 조각", user_note="", tags=[], illustration_tags=[], content_types=[],
    )
    conn.close()
    chunk_id = saved["chunk_id"]
    before = fetch_one(db_path, "SELECT illustration_tags, updated_at FROM reading_chunks")

    at = open_detail()
    at.button(key=f"chunk_category_open_{chunk_id}").click().run()
    selection_key = f"chunk_category_selection_{chunk_id}"
    at.multiselect(key=selection_key).set_value(["기도"])
    at.button(key=f"chunk_category_send_{chunk_id}").click().run()

    after = fetch_one(db_path, "SELECT illustration_tags, updated_at FROM reading_chunks")
    assert not at.exception
    assert before[0] == "[]"
    assert after[0] == '["기도"]'
    assert after[1] != before[1]
    assert not any(item.value == "예화창고로 보낼까요?" for item in at.subheader)


def test_existing_chunk_send_shows_verified_diagnostic_after_rerun(isolated_app, monkeypatch):
    db_path, _ = isolated_app
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
        original_text="기존 조각", user_note="", tags=[], illustration_tags=[], content_types=[],
    )
    conn.close()
    chunk_id = saved["chunk_id"]
    at = open_detail()
    at.button(key=f"chunk_category_open_{chunk_id}").click().run()
    assert any("save_attempted: NO" in item.value for item in at.markdown)
    at.multiselect(key=f"chunk_category_selection_{chunk_id}").set_value(["기도"])
    at.button(key=f"chunk_category_send_{chunk_id}").click().run()
    visible = "\n".join(item.value for item in at.markdown)
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ('["기도"]',)
    for field in ("save_attempted: YES", "set_illustration_tags_called: YES",
                  "db_update_success: YES", "postwrite_verify_success: YES",
                  "saved_tags_count: 1", "failure_stage: none", f"target_chunk_id: {chunk_id[:8]}"):
        assert field in visible


def test_approval_diagnostic_distinguishes_wrong_owner_without_write(isolated_app, monkeypatch):
    db_path, _ = isolated_app
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
        original_text="기존 조각", user_note="", tags=[], illustration_tags=[], content_types=[],
    )
    diagnostic = approval_diagnostics.new_attempt(saved["chunk_id"])
    with pytest.raises(ValueError):
        chunks.set_illustration_tags(conn, saved["chunk_id"], owner_id="other-owner",
                                     illustration_tags=["기도"], diagnostic=diagnostic)
    conn.close()
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ("[]",)
    assert diagnostic["failure_stage"] == "find_chunk"
    assert diagnostic["db_update_success"] == "NO"


def test_chunk_send_reports_update_failure_without_success_notice(isolated_app, monkeypatch):
    db_path, _ = isolated_app
    monkeypatch.setattr(subject, "DEFAULT_SNAPSHOT", FIXTURE_SNAPSHOT)
    conn = db.get_connection()
    saved = chunks.save(
        conn, owner_id=chunks.LOCAL_OWNER_ID, book_id="book-1", read_date="2026-09-28",
        original_text="기존 조각", user_note="", tags=[], illustration_tags=[], content_types=[],
    )
    conn.close()
    with sqlite3.connect(db_path) as fixture_conn:
        fixture_conn.execute("CREATE TRIGGER deny_category_update BEFORE UPDATE OF illustration_tags "
                             "ON reading_chunks BEGIN SELECT RAISE(IGNORE); END")
    chunk_id = saved["chunk_id"]
    at = open_detail()
    at.button(key=f"chunk_category_open_{chunk_id}").click().run()
    at.multiselect(key=f"chunk_category_selection_{chunk_id}").set_value(["기도"])
    at.button(key=f"chunk_category_send_{chunk_id}").click().run()
    visible = "\n".join(item.value for item in at.markdown)
    assert not at.exception
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ("[]",)
    assert "save_attempted: YES" in visible
    assert "db_update_success: NO" in visible
    assert "postwrite_verify_success: NO" in visible
    assert "failure_stage: db_update" in visible
    assert not any("카테고리를 저장했습니다" in item.value for item in at.markdown)


def test_ambiguous_category_word_is_suggested_without_preapproval(isolated_app):
    """A real existing-folder word must offer choices, never choose for David."""
    db_path, _ = isolated_app
    snapshot = subject.load_snapshot()
    candidates = subject.recommend(
        snapshot, originalText="성경 전체의 작은 이야기를 새롭게 해석한다.",
        userNote="", tags=["설교", "성경해석"],
    )
    assert candidates == [
        {"canonical": "성경, 말씀", "score": 1, "defaultChecked": False},
        {"canonical": "성경,말씀묵상", "score": 1, "defaultChecked": False},
    ]

    at = open_detail()
    at.button(key="open_reading_chunk").click().run()
    at.text_area(key="chunk_input_original_text").set_value("성경 전체의 작은 이야기를 새롭게 해석한다.")
    at.button(key="save_reading_chunk").click().run()
    chunk_id = fetch_one(db_path, "SELECT chunk_id FROM reading_chunks")[0]
    assert at.multiselect(key=f"chunk_category_selection_{chunk_id}").value == []
    assert fetch_one(db_path, "SELECT illustration_tags FROM reading_chunks") == ("[]",)


def test_refresh_snapshot_reads_directory_names_only_excludes_managed_folders_and_preserves_dictionary(tmp_path):
    root = tmp_path / "예화창고"
    root.mkdir()
    for name in ("용서", "기도", "독서조각", "읽담", "_읽담_검증전용_20260927", ".hidden"):
        (root / unicodedata.normalize("NFD", name)).mkdir()
    (root / "not-a-folder.txt").write_text("human text must not be read", encoding="utf-8")
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({
        "version": 1, "generatedAt": "old",
        "categories": [
            {"canonical": "용서", "aliases": ["용서하다"], "keywords": ["화해"]},
            {"canonical": "이전", "aliases": ["old"], "keywords": []},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    report = subject.refresh_snapshot(root, snapshot, generated_at="2026-09-28T00:00:00+09:00")
    updated = subject.load_snapshot(snapshot)
    assert [entry["canonical"] for entry in updated["categories"]] == ["기도", "용서"]
    assert next(entry for entry in updated["categories"] if entry["canonical"] == "용서")["aliases"] == ["용서하다"]
    assert report["added"] == ["기도"]
    assert report["removed"] == ["이전"]
    assert report["ignored"] == [".hidden", "_읽담_검증전용_20260927", "독서조각", "읽담"]
    assert report["renameCandidates"] == []


def test_checked_in_snapshot_has_the_63_actual_canonical_categories():
    snapshot = subject.load_snapshot()
    names = subject.canonical_names(snapshot)
    assert len(names) == 63
    assert "교회" in names and "사명" in names


def test_david_approved_keyword_narrowing_changes_only_the_three_terms():
    snapshot = subject.load_snapshot()
    entries = {entry["canonical"]: entry for entry in snapshot["categories"]}
    assert entries["그리스도인의 삶"]["keywords"] == ["일상 신앙", "그리스도인의 삶의 방식"]
    assert entries["시간"]["keywords"] == ["시간의 우선순위"]
    assert entries["위선"]["keywords"] == ["겉과 속", "위선의 가면"]

    for original, excluded in (("삶의 방식", "그리스도인의 삶"), ("세월", "시간"), ("가면", "위선")):
        candidates = subject.recommend(snapshot, originalText=original, userNote="", tags=[])
        assert excluded not in [item["canonical"] for item in candidates]
