"""Failure injection uses tmp_path only, never the user's iCloud archive."""
import fcntl
import json
from pathlib import Path

import pytest

from lib import db, reading_chunks as chunks
from test_activity_inputs_app import isolated_app
from test_reading_chunks import _export_module, _save
from test_reading_chunks_audit import fingerprint


@pytest.fixture
def export_case(isolated_app, tmp_path):
    conn = db.get_connection()
    row = _save(conn)
    exporter = _export_module()
    root = tmp_path / "Mobile Documents" / "com~apple~CloudDocs" / "TEST 예화창고"
    def run(ids=None, owner=chunks.LOCAL_OWNER_ID):
        return exporter.export(root, owner_id=owner, chunk_ids=ids if ids is not None else [row["chunk_id"]])
    yield conn, row, exporter, root, run
    conn.close()


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*.txt")}


def verify(root, row, exporter):
    archive = root / "독서조각"
    index = exporter.read_index(archive / "_index.csv")
    path = archive / index[row["chunk_id"]]["상대경로"]
    assert path.is_file()
    assert index[row["chunk_id"]]["updatedAt"] == row["updated_at"]
    assert index[row["chunk_id"]]["contentHash"] == row["content_hash"]
    if not row["deleted_at"]:
        assert path.read_text() == exporter.render_txt(row)
    assert not (archive / ".export-pending.json").exists()
    assert not list(archive.rglob(".readdam-tmp-*"))
    return path


def test_selection_is_explicit_complete_and_owner_scoped(export_case):
    conn, row, exporter, root, run = export_case
    other = _save(conn, user_note="TEST not selected")
    for ids, owner in [([], chunks.LOCAL_OWNER_ID), ([row["chunk_id"], "missing"], chunks.LOCAL_OWNER_ID), ([row["chunk_id"]], "foreign")]:
        with pytest.raises(ValueError):
            run(ids, owner)
        assert not root.exists()
    with pytest.raises(TypeError):
        exporter.export(root)
    assert run([row["chunk_id"], row["chunk_id"]])["total"] == 1
    assert len(files(root)) == 1
    assert other["chunk_id"] not in exporter.read_index(root / "독서조각" / "_index.csv")


@pytest.mark.parametrize("change", ["create", "update", "move", "delete"])
def test_index_failure_then_fresh_module_recovers_all_operations(export_case, monkeypatch, change):
    conn, row, exporter, root, run = export_case
    archive = root / "독서조각"
    before_index = None
    if change != "create":
        run()
        before_index = (archive / "_index.csv").read_bytes()
    if change in ("update", "move"):
        values = dict(user_note="TEST revised\n한글 100% _ \"quote\"")
        if change == "move":
            values.update(read_date="2027-01-01", page_start=100, page_end=110)
        row = _save(conn, chunk_id=row["chunk_id"], **values)
    if change == "delete":
        chunks.soft_delete(conn, row["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID)
        row = chunks.get(conn, row["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID, include_deleted=True)
    def fail(*args):
        raise OSError("TEST index interruption")
    monkeypatch.setattr(exporter, "write_index", fail)
    with pytest.raises(OSError):
        run()
    assert (archive / ".export-pending.json").exists()
    assert ((archive / "_index.csv").read_bytes() if (archive / "_index.csv").exists() else None) == before_index
    # Reload mimics a restarted CLI process; no in-memory recovery state is retained.
    fresh = _export_module()
    fresh.export(root, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=[row["chunk_id"]])
    verify(root, row, fresh)
    assert len(files(root)) == 1
    assert fresh.export(root, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=[row["chunk_id"]])["written"] == 0


@pytest.mark.parametrize("stage", ["txt", "state", "index"])
def test_atomic_replace_failure_preserves_previous_destination(export_case, monkeypatch, stage):
    conn, row, exporter, root, run = export_case
    run()
    target = verify(root, row, exporter)
    archive = root / "독서조각"
    protected = {"txt": target, "state": archive / ".export-state.json", "index": archive / "_index.csv"}[stage]
    before = protected.read_bytes()
    row = _save(conn, chunk_id=row["chunk_id"], user_note="TEST atomic update")
    replace = exporter.os.replace
    def fail(source, destination):
        if Path(destination) == protected:
            raise OSError("TEST replace failure")
        return replace(source, destination)
    with monkeypatch.context() as scoped:
        scoped.setattr(exporter.os, "replace", fail)
        with pytest.raises(OSError):
            run()
    assert protected.read_bytes() == before
    run()
    verify(root, row, exporter)


def test_failure_after_committed_index_before_old_path_cleanup_recovers(export_case, monkeypatch):
    conn, row, exporter, root, run = export_case
    run()
    previous = verify(root, row, exporter)
    row = _save(conn, chunk_id=row["chunk_id"], read_date="2027-02-01")
    unlink = Path.unlink
    def fail(path, *args, **kwargs):
        if path == previous:
            raise OSError("TEST crash after committed index")
        return unlink(path, *args, **kwargs)
    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "unlink", fail)
        with pytest.raises(OSError):
            run()
    assert len(files(root)) == 2
    run()
    assert len(files(root)) == 1 and not previous.exists()
    verify(root, row, exporter)


def test_local_lock_rejects_second_writer(export_case):
    _, _, _, root, run = export_case
    run()
    before = files(root)
    with (root / "독서조각" / ".export.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="다른 내보내기"):
            run()
    assert files(root) == before


def test_recovery_does_not_overwrite_external_modification(export_case, monkeypatch):
    _, _, exporter, root, run = export_case
    def fail(*args):
        raise OSError("TEST stop before index")
    monkeypatch.setattr(exporter, "write_index", fail)
    with pytest.raises(OSError):
        run()
    path = next(root.rglob("*.txt"))
    path.write_text("TEST user modification sentinel")
    with pytest.raises(RuntimeError, match="txt가 변경"):
        _export_module().export(root, owner_id=chunks.LOCAL_OWNER_ID, chunk_ids=[json.loads((root / "독서조각" / ".export-pending.json").read_text())["chunk_ids"][0]])
    assert path.read_text() == "TEST user modification sentinel"


def test_pending_selection_must_match(export_case, monkeypatch):
    conn, row, exporter, root, run = export_case
    other = _save(conn, user_note="TEST other")
    def fail(*args):
        raise OSError("TEST index failure")
    monkeypatch.setattr(exporter, "write_index", fail)
    with pytest.raises(OSError):
        run()
    before = files(root)
    with pytest.raises(RuntimeError, match="같은 사용자/조각"):
        run([other["chunk_id"]])
    assert files(root) == before


def test_archive_collision_successfully_uses_unique_path(export_case):
    conn, row, exporter, root, run = export_case
    run()
    destination = root / "독서조각" / "_삭제됨"
    destination.mkdir()
    for length in [8, 12, len(row["chunk_id"])]:
        (destination / exporter.filename_for(row, length)).write_text(f"TEST sentinel {length}")
    for number in [1, 2, 3]:
        (destination / f"{Path(exporter.filename_for(row, len(row['chunk_id']))).stem}_{number}.txt").write_text("TEST numbered sentinel")
    before = {p: p.read_bytes() for p in destination.iterdir()}
    chunks.soft_delete(conn, row["chunk_id"], owner_id=chunks.LOCAL_OWNER_ID)
    assert run()["moved"] == 1
    assert all(p.read_bytes() == value for p, value in before.items())
    assert len(list(destination.iterdir())) == len(before) + 1
    assert run()["moved"] == 0


def test_other_index_rows_and_archive_links_preserved(export_case):
    conn, row, exporter, root, run = export_case
    other = _save(conn, user_note="TEST other")
    run([row["chunk_id"], other["chunk_id"]])
    path = root / "독서조각" / "_index.csv"
    index = exporter.read_index(path)
    index[row["chunk_id"]]["예화창고 경로들"] = "TEST 외부 경로"
    exporter.write_index(path, index)
    other_before = index[other["chunk_id"]].copy()
    other_file = root / "독서조각" / other_before["상대경로"]
    other_bytes = other_file.read_bytes()
    _save(conn, chunk_id=row["chunk_id"], user_note="TEST chosen update")
    run()
    after = exporter.read_index(path)
    assert after[other["chunk_id"]] == other_before and other_file.read_bytes() == other_bytes
    assert after[row["chunk_id"]]["예화창고 경로들"] == "TEST 외부 경로"


def test_legacy_index_adoption_is_conservative(export_case):
    conn, row, exporter, root, run = export_case
    run()
    state = root / "독서조각" / ".export-state.json"
    state.unlink()  # synthetic legacy format, not a user file
    assert run()["written"] == 0
    assert state.exists()
    state.unlink()
    before = files(root)
    _save(conn, chunk_id=row["chunk_id"], user_note="TEST legacy changed DB")
    with pytest.raises(RuntimeError, match="무결성"):
        run()
    assert files(root) == before


def test_full_id_collision_extension_and_checksum_preservation(export_case):
    conn, _, exporter, root, run = export_case
    before = fingerprint(conn)
    ids = []
    for number in range(3):
        row = _save(conn, chunk_id=f"abcdef12-abcd-4000-8000-{number:012d}", user_note=f"TEST collision {number}")
        ids.append(row["chunk_id"])
    assert run(ids)["written"] == 3
    assert len(files(root)) == 3
    assert run(ids)["written"] == 0
    assert fingerprint(conn) == before


def test_archive_symlink_never_writes_outside_root(export_case, tmp_path):
    _, _, _, root, run = export_case
    outside = tmp_path / "TEST outside"
    outside.mkdir()
    root.mkdir(parents=True)
    (root / "독서조각").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="심볼릭 링크"):
        run()
    assert list(outside.iterdir()) == []


def test_failed_new_file_publication_never_overwrites_racing_file(export_case, monkeypatch):
    _, _, exporter, root, run = export_case
    link = exporter.os.link
    def race(source, destination):
        if str(destination).endswith(".txt"):
            Path(destination).write_text("TEST concurrent file sentinel")
        return link(source, destination)
    with monkeypatch.context() as scoped:
        scoped.setattr(exporter.os, "link", race)
        with pytest.raises(FileExistsError):
            run()
    path = next(root.rglob("*.txt"))
    assert path.read_text() == "TEST concurrent file sentinel"
    with pytest.raises(RuntimeError, match="txt가 변경"):
        run()
    assert path.read_text() == "TEST concurrent file sentinel"
