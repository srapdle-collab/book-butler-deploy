from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from lib import illustration_categories as subject
from lib import db, reading_chunks as chunks
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
    conn.close()
    at = open_detail()
    at.button(key=f"chunk_category_open_{saved['chunk_id']}").click().run()
    at.button(key=f"chunk_category_skip_{saved['chunk_id']}").click().run()
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
