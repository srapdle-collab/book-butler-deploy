"""2차 분류 export는 합성 DB와 임시 예화창고에서만 검증한다."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

from lib import db, reading_chunks as chunks
from test_activity_inputs_app import isolated_app
from test_reading_chunks import _export_module, _ids, _save
from tools import export_chunk_illustrations as subject


OWNER = chunks.LOCAL_OWNER_ID


def categories(root, *names):
    for name in names:
        (root / unicodedata.normalize("NFD", name)).mkdir()


def base_export(root):
    _export_module().export(root, owner_id=OWNER, chunk_ids=_ids())


def actions(result, kind):
    return [item for item in result["actions"] if item["action"] == kind]


def tree(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_exact_alias_ambiguous_unmapped_and_no_tags(isolated_app, tmp_path):
    conn = db.get_connection()
    records = [
        _save(conn, original_text=f"내용 {i}", illustration_tags=tags, allow_duplicate=True)
        for i, tags in enumerate([
            ["용서"], ["관계"], ["교회", "사명", "성경", "말씀", "결혼", "이성교제"],
            ["없는태그"], [],
        ])
    ]
    conn.close()
    categories(tmp_path, "용서", "공동체,관계, 교회", "교회", "사명", "성경, 말씀", "성경,말씀묵상",
               "결혼 이성교제", "이성교제,결혼")
    base_export(tmp_path)
    before = tree(tmp_path)
    preview = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    assert tree(tmp_path) == before
    assert {a["chunkId"] for a in actions(preview, "CREATE")} == {records[0]["chunk_id"], records[1]["chunk_id"]}
    assert {a["reason"] for a in actions(preview, "UNMAPPED")} >= {
        "모호한 태그: 교회", "모호한 태그: 사명", "매핑 없음: 없는태그"}
    result = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert len(actions(result, "CREATE")) == 2
    assert len(list((tmp_path / "용서" / "읽담").glob("*.txt"))) == 1
    assert len(list((tmp_path / unicodedata.normalize("NFD", "공동체,관계, 교회") / "읽담").glob("*.txt"))) == 1
    assert not (tmp_path / "교회" / "읽담").exists()
    assert not (tmp_path / "_미분류").exists()
    again = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert not actions(again, "CREATE") and not actions(again, "UPDATE") and not actions(again, "DELETE")


def test_multi_category_dedupe_filename_and_person_file(isolated_app, tmp_path):
    categories(tmp_path, "용서", "공동체,관계, 교회")
    human = tmp_path / "용서" / "사람.txt"
    human.write_text("사람 자료")
    conn = db.get_connection()
    row = _save(conn, illustration_tags=["용서", "관계", "공동체"])
    conn.close()
    base_export(tmp_path)
    result = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert len(actions(result, "CREATE")) == 2
    assert human.read_text() == "사람 자료"
    files = list(tmp_path.rglob("읽담/*.txt"))
    assert len(files) == 2 and len({p.name for p in files}) == 1
    assert row["chunk_id"][:8] in files[0].name
    assert files[0].read_bytes() == files[1].read_bytes()
    assert result["summary"]["dedupe"] == 1


def test_content_and_tag_changes_delete_only_owned_copies(isolated_app, tmp_path):
    categories(tmp_path, "용서", "기도")
    conn = db.get_connection()
    a = _save(conn, original_text="첫 내용", illustration_tags=["용서"])
    b = _save(conn, original_text="다른 내용", illustration_tags=["용서"], allow_duplicate=True)
    conn.close()
    base_export(tmp_path)
    subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    managed = sorted((tmp_path / "용서" / "읽담").glob("*.txt"))
    other = next(path for path in managed if b["chunk_id"][:8] in path.name)
    other_digest = hashlib.sha256(other.read_bytes()).hexdigest()
    conn = db.get_connection()
    _save(conn, chunk_id=a["chunk_id"], original_text="고친 내용", illustration_tags=["용서"])
    conn.close()
    base_export(tmp_path)
    changed = subject.export(tmp_path, owner_id=OWNER, chunk_ids=[a["chunk_id"]])
    assert len(actions(changed, "UPDATE")) == 1
    assert hashlib.sha256(other.read_bytes()).hexdigest() == other_digest
    conn = db.get_connection()
    _save(conn, chunk_id=a["chunk_id"], original_text="고친 내용", illustration_tags=["기도"])
    conn.close()
    base_export(tmp_path)
    moved = subject.export(tmp_path, owner_id=OWNER, chunk_ids=[a["chunk_id"]])
    assert len(actions(moved, "CREATE")) == 1 and len(actions(moved, "DELETE")) == 1
    assert len(list((tmp_path / "용서" / "읽담").glob("*.txt"))) == 1
    assert hashlib.sha256(other.read_bytes()).hexdigest() == other_digest
    conn = db.get_connection()
    chunks.soft_delete(conn, a["chunk_id"], owner_id=OWNER)
    conn.close()
    base_export(tmp_path)
    deleted = subject.export(tmp_path, owner_id=OWNER, chunk_ids=[a["chunk_id"]])
    assert len(actions(deleted, "DELETE")) == 1
    assert not (tmp_path / "기도" / "읽담").exists()
    assert hashlib.sha256(other.read_bytes()).hexdigest() == other_digest


def test_manifest_corruption_and_unowned_conflict_fail_safe(isolated_app, tmp_path):
    categories(tmp_path, "용서")
    conn = db.get_connection()
    row = _save(conn, illustration_tags=["용서"])
    conn.close()
    base_export(tmp_path)
    first = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    path = tmp_path / actions(first, "CREATE")[0]["relativePath"]
    path.write_text("외부 수정")
    before = tree(tmp_path)
    with pytest.raises(RuntimeError, match="변경|무결성"):
        subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert tree(tmp_path) == before
    manifest = tmp_path / "독서조각" / "_illustration_manifest.json"
    manifest.write_text("{broken")
    before = tree(tmp_path)
    with pytest.raises(RuntimeError, match="manifest|목록"):
        subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    assert tree(tmp_path) == before


def test_first_run_conflict_does_not_claim_existing_file(isolated_app, tmp_path):
    categories(tmp_path, "용서")
    conn = db.get_connection()
    row = _save(conn, illustration_tags=["용서"])
    conn.close()
    base_export(tmp_path)
    preview = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    target = tmp_path / actions(preview, "CREATE")[0]["relativePath"]
    target.parent.mkdir()
    target.write_text("사람 파일")
    before = tree(tmp_path)
    conflict = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    assert len(actions(conflict, "CONFLICT")) == 1
    with pytest.raises(RuntimeError, match="충돌"):
        subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert tree(tmp_path) == before


@pytest.mark.parametrize("tag,category", [
    ("관계", "공동체,관계, 교회"), ("공동체", "공동체,관계, 교회"),
    ("비전", "꿈,비전,사명,열정"), ("열정", "꿈,비전,사명,열정"),
    ("말씀묵상", "성경,말씀묵상"), ("영생", "부활,영생"),
    ("하나님나라", "하나님 나라"),
])
def test_approved_explicit_mapping(tag, category):
    physical = unicodedata.normalize("NFD", category)
    mapped, unmapped = subject._map_tags([tag], {physical: None}, {category: [physical]}, subject.ALIASES)
    assert mapped == [physical] and unmapped == []


def test_resume_after_index_write_failure(isolated_app, tmp_path, monkeypatch):
    categories(tmp_path, "용서")
    conn = db.get_connection()
    _save(conn, illustration_tags=["용서"])
    conn.close()
    base_export(tmp_path)
    writer = subject.base.write_index
    def fail(*args):
        raise OSError("TEST interrupted index write")
    monkeypatch.setattr(subject.base, "write_index", fail)
    with pytest.raises(OSError):
        subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    monkeypatch.setattr(subject.base, "write_index", writer)
    assert (tmp_path / "독서조각" / ".illustration-pending.json").exists()
    subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert not (tmp_path / "독서조각" / ".illustration-pending.json").exists()
    assert len(list((tmp_path / "용서" / "읽담").glob("*.txt"))) == 1


def test_missing_base_and_symlink_boundary(isolated_app, tmp_path):
    categories(tmp_path, "용서")
    conn = db.get_connection()
    _save(conn, illustration_tags=["용서"])
    conn.close()
    before = tree(tmp_path)
    result = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    assert len(actions(result, "CONFLICT")) == 1 and tree(tmp_path) == before
    base_export(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "용서" / "읽담").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="심볼릭 링크"):
        subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    assert not list(outside.iterdir())


def test_filename_collision_and_source_db_unchanged(isolated_app, tmp_path):
    categories(tmp_path, "용서")
    conn = db.get_connection()
    for i, prefix in enumerate(("abcdef12-aaaa", "abcdef12-bbbb")):
        _save(conn, chunk_id=prefix + "-4000-8000-000000000001",
              original_text=f"내용 {i}", illustration_tags=["용서"])
    conn.close()
    base_export(tmp_path)
    before_db = hashlib.sha256(isolated_app[0].read_bytes()).hexdigest()
    result = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids())
    assert len(actions(result, "CREATE")) == 2
    assert len({p.name for p in (tmp_path / "용서" / "읽담").glob("*.txt")}) == 2
    assert hashlib.sha256(isolated_app[0].read_bytes()).hexdigest() == before_db


def test_preserved_verification_root_is_not_a_category(isolated_app, tmp_path):
    name = "_읽담_검증전용_20260927_16680d12"
    categories(tmp_path, name)
    conn = db.get_connection()
    _save(conn, illustration_tags=[name])
    conn.close()
    base_export(tmp_path)
    result = subject.export(tmp_path, owner_id=OWNER, chunk_ids=_ids(), dry_run=True)
    assert not actions(result, "CREATE")
    assert len(actions(result, "UNMAPPED")) == 1
    assert not (tmp_path / name / "읽담").exists()


def test_cli_dry_run_then_export_then_identical_retry(isolated_app, tmp_path):
    categories(tmp_path, "용서")
    conn = db.get_connection()
    row = _save(conn, illustration_tags=["용서"])
    conn.close()
    base_export(tmp_path)
    command = [sys.executable, str(Path(__file__).parents[1] / "tools" / "export_chunk_illustrations.py"),
               "--output-root", str(tmp_path), "--owner-id", OWNER]
    before = tree(tmp_path)
    preview = subprocess.run(command + ["--dry-run"], capture_output=True, text=True, check=True)
    assert tree(tmp_path) == before
    assert json.loads(preview.stdout.splitlines()[-1])["summary"]["CREATE"] == 1
    first = subprocess.run(command, capture_output=True, text=True, check=True)
    second = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(first.stdout.splitlines()[-1])["summary"]["CREATE"] == 1
    assert json.loads(second.stdout.splitlines()[-1])["summary"]["SKIP"] == 1
    assert len(list((tmp_path / "용서" / "읽담").glob("*.txt"))) == 1
    assert row["original_text"] not in first.stdout
