"""자동 export는 합성 DB와 임시 카테고리만 사용한다."""
from __future__ import annotations

import hashlib
import json

import pytest

from lib import db, reading_chunks as chunks
from test_activity_inputs_app import isolated_app
from test_reading_chunks import _save
from tools import export_pipeline


OWNER = chunks.LOCAL_OWNER_ID


def tree(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_all_chunks_dry_run_and_repeat_without_writes(isolated_app, tmp_path):
    (tmp_path / "용서").mkdir()
    conn = db.get_connection()
    first = _save(conn, original_text="첫 조각", illustration_tags=["용서"])
    second = _save(conn, original_text="둘째 조각", illustration_tags=[])
    conn.close()
    before = tree(tmp_path)
    preview = export_pipeline.run(tmp_path, owner_id=OWNER, dry_run=True)
    assert tree(tmp_path) == before
    assert preview["base"]["written"] == 2
    assert preview["illustrations"]["CREATE"] == 1
    assert not (tmp_path / "독서조각").exists()
    result = export_pipeline.run(tmp_path, owner_id=OWNER)
    assert result["base"]["written"] == 2
    assert len(list((tmp_path / "독서조각").rglob("*.txt"))) == 2
    assert len(list((tmp_path / "용서" / "읽담").glob("*.txt"))) == 1
    assert first["chunk_id"][:8] in next((tmp_path / "용서" / "읽담").glob("*.txt")).name
    assert second["chunk_id"] in (tmp_path / "독서조각" / "_index.csv").read_text()
    after = tree(tmp_path)
    index = tmp_path / "독서조각" / "_index.csv"
    unchanged_mtime = index.stat().st_mtime_ns
    again = export_pipeline.run(tmp_path, owner_id=OWNER)
    assert again["base"]["written"] == again["illustrations"]["CREATE"] == 0
    assert tree(tmp_path) == after
    assert index.stat().st_mtime_ns == unchanged_mtime


def test_change_tag_soft_delete_and_person_file(isolated_app, tmp_path):
    for name in ("용서", "기도"):
        (tmp_path / name).mkdir()
    person = tmp_path / "기도" / "사람.txt"
    person.write_text("사람 자료")
    conn = db.get_connection()
    row = _save(conn, illustration_tags=["용서"])
    conn.close()
    export_pipeline.run(tmp_path, owner_id=OWNER)
    conn = db.get_connection()
    _save(conn, chunk_id=row["chunk_id"], original_text="수정된 조각", illustration_tags=["기도"])
    conn.close()
    preview = export_pipeline.run(tmp_path, owner_id=OWNER, dry_run=True)
    assert preview["illustrations"]["CREATE"] == 1
    assert preview["illustrations"]["DELETE"] == 1
    export_pipeline.run(tmp_path, owner_id=OWNER)
    assert not list((tmp_path / "용서" / "읽담").glob("*.txt"))
    assert len(list((tmp_path / "기도" / "읽담").glob("*.txt"))) == 1
    conn = db.get_connection()
    chunks.soft_delete(conn, row["chunk_id"], owner_id=OWNER)
    conn.close()
    export_pipeline.run(tmp_path, owner_id=OWNER)
    assert not (tmp_path / "기도" / "읽담").exists()
    assert len(list((tmp_path / "독서조각" / "_삭제됨").glob("*.txt"))) == 1
    assert person.read_text() == "사람 자료"


def test_conflict_prevents_base_write(isolated_app, tmp_path):
    (tmp_path / "용서").mkdir()
    conn = db.get_connection()
    _save(conn, illustration_tags=["용서"])
    conn.close()
    preview = export_pipeline.run(tmp_path, owner_id=OWNER, dry_run=True)
    target = tmp_path / preview["actions"][0]["relativePath"]
    target.parent.mkdir()
    target.write_text("사람 파일")
    before = tree(tmp_path)
    with pytest.raises(RuntimeError, match="충돌"):
        export_pipeline.run(tmp_path, owner_id=OWNER)
    assert tree(tmp_path) == before


def test_owner_from_exact_profile_and_missing_setting(isolated_app, monkeypatch):
    monkeypatch.delenv("READDAM_OWNER_EMAIL", raising=False)
    with pytest.raises(ValueError, match="READDAM_OWNER_EMAIL"):
        export_pipeline.resolve_owner_id()
    conn = db.get_connection()
    conn.execute("INSERT INTO profiles VALUES('owner-1','owner@example.invalid','Owner',1)")
    conn.commit()
    conn.close()
    monkeypatch.setenv("READDAM_OWNER_EMAIL", "Owner@Example.Invalid")
    assert export_pipeline.resolve_owner_id() == "owner-1"


def test_pending_requires_recovery_before_dry_run(isolated_app, tmp_path):
    (tmp_path / "용서").mkdir()
    conn = db.get_connection()
    _save(conn, illustration_tags=["용서"])
    conn.close()
    archive = tmp_path / "독서조각"
    archive.mkdir()
    (archive / ".export-pending.json").write_text(json.dumps({"version": 1, "owner_id": OWNER, "chunk_ids": ["x"]}))
    with pytest.raises(RuntimeError, match="미완료"):
        export_pipeline.run(tmp_path, owner_id=OWNER, dry_run=True)


def test_resume_old_selection_then_export_new_chunk(isolated_app, tmp_path, monkeypatch):
    (tmp_path / "용서").mkdir()
    conn = db.get_connection()
    _save(conn, original_text="첫 조각", illustration_tags=["용서"])
    conn.close()
    writer = export_pipeline.base.write_index

    def interrupted(*args):
        raise OSError("TEST interrupted")

    monkeypatch.setattr(export_pipeline.base, "write_index", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        export_pipeline.run(tmp_path, owner_id=OWNER)
    monkeypatch.setattr(export_pipeline.base, "write_index", writer)
    conn = db.get_connection()
    _save(conn, original_text="새 조각", illustration_tags=["용서"])
    conn.close()
    result = export_pipeline.run(tmp_path, owner_id=OWNER)
    assert result["illustrations"]["CREATE"] == 2
    assert len(list((tmp_path / "용서" / "읽담").glob("*.txt"))) == 2
    assert not (tmp_path / "독서조각" / ".export-pending.json").exists()
