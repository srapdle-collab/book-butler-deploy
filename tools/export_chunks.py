#!/usr/bin/env python3
"""읽담 reading_chunks를 사람이 보관하는 UTF-8 txt로 내보낸다.

예: python tools/export_chunks.py --output-root /Volumes/Archive --owner-id OWNER --chunk-id UUID

명시한 보관 루트의 ``독서조각/``만 만들고 관리한다. 예화창고는 실제 위치와
구조를 확인하는 다음 단계 전까지 전혀 건드리지 않는다.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from lib import db
from lib import reading_chunks as chunks
from lib.schema_preflight import require_schema

INDEX_HEADERS = ["chunkId", "상대경로", "updatedAt", "contentHash", "예화창고 경로들"]
INVALID_FILENAME = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]+')


def safe_title(value: str | None) -> str:
    title = INVALID_FILENAME.sub(" ", value or "제목 없음")
    title = " ".join(title.split()).strip(". ")
    return (title or "제목 없음")[:40]


def filename_for(chunk, length: int = 8) -> str:
    page_start, page_end = chunk["page_start"], chunk["page_end"]
    page = ""
    if page_start is not None and page_end is not None:
        page = f"_p{page_start}" if page_start == page_end else f"_p{page_start}-{page_end}"
    return f"{chunk['read_date']}_{safe_title(chunk['book_title'])}{page}_{chunk['chunk_id'][:length]}.txt"


def relative_path_for(chunk, length: int = 8) -> Path:
    year, month, _ = chunk["read_date"].split("-", 2)
    return Path(year) / f"{year}-{month}" / filename_for(chunk, length)


def _source_label(source_app: str) -> str:
    return {"readdam": "읽담", "today-library": "오늘의 서재"}.get(source_app, source_app)


def _content_type_labels(values) -> str:
    return ", ".join(chunks.CONTENT_TYPES.get(value, value) for value in values) or "없음"


def render_txt(chunk) -> str:
    page_start, page_end = chunk["page_start"], chunk["page_end"]
    if page_start is not None and page_end is not None:
        range_label = f"{page_start}쪽" if page_start == page_end else f"{page_start}–{page_end}쪽"
    else:
        range_label = chunk["position_note"] or "미입력"
    lines = [
        f"제목: {chunk['book_title']}",
        f"저자: {chunk['author'] or '미상'}",
        f"ISBN: {chunk['isbn'] or '미입력'}",
        f"읽은 날짜: {chunk['read_date']}",
        f"읽은 범위: {range_label}",
        f"읽은 시간: {str(chunk['minutes']) + '분' if chunk['minutes'] is not None else '미입력'}",
        f"콘텐츠 타입: {_content_type_labels(chunk['content_types'])}",
        f"태그: {', '.join(chunk['tags']) or '없음'}",
        f"예화 태그: {', '.join(chunk['illustration_tags']) or '없음'}",
        "",
        "[읽은 조각]",
        chunk["original_text"] or "",
        "",
        "[내 메모]",
        chunk["user_note"] or "",
        "",
        "---",
        f"chunkId: {chunk['chunk_id']}",
        f"출처 앱: {_source_label(chunk['source_app'])} ({chunk['source_app']})",
        f"수정: {chunk['updated_at']}",
        "",
    ]
    return "\n".join(lines)


def _safe_path(root: Path, relative: str) -> Path:
    raw = root / relative
    if raw.is_symlink():
        raise RuntimeError("심볼릭 링크 파일은 내보내기 대상이 될 수 없습니다.")
    candidate = raw.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"목록 파일의 상대경로가 안전하지 않습니다: {relative}") from exc
    return candidate


def read_index(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != INDEX_HEADERS:
            raise RuntimeError("_index.csv 헤더가 예상과 달라 안전하게 갱신할 수 없습니다.")
        result, paths = {}, set()
        for row in reader:
            if (set(row) != set(INDEX_HEADERS) or any(row[k] is None for k in INDEX_HEADERS)
                    or not all(row[k] for k in INDEX_HEADERS[:4])
                    or row["chunkId"] in result or row["상대경로"] in paths):
                raise RuntimeError("_index.csv 중복 또는 잘못된 행을 발견했습니다.")
            _safe_path(path.parent, row["상대경로"])
            result[row["chunkId"]] = row
            paths.add(row["상대경로"])
        return result


def _index_bytes(rows):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=INDEX_HEADERS)
    writer.writeheader()
    for chunk_id in sorted(rows):
        writer.writerow(rows[chunk_id])
    return handle.getvalue().encode("utf-8")


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _file_hash(path):
    return _digest(path.read_bytes()) if path.exists() else None


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path, data, *, replace=True):
    """Same-directory staged write. New destinations use link/no-clobber."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".readdam-tmp-", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            os.replace(staged, path)
        else:
            # Unlike rename/replace, link fails if another file already exists.
            os.link(staged, path)
            staged.unlink()
        _sync_directory(path.parent)
    finally:
        if staged.exists():
            staged.unlink()


def write_index(path: Path, rows: dict[str, dict[str, str]]) -> None:
    _atomic_write(path, _index_bytes(rows))


def _target_for(chunk, known_paths: dict[str, str]) -> Path:
    for length in (8, 12, len(chunk["chunk_id"])):
        target = relative_path_for(chunk, length)
        if known_paths.get(target.as_posix()) in (None, chunk["chunk_id"]):
            return target
    raise RuntimeError("파일명 충돌을 해결할 수 없습니다.")


def _selected_chunks(owner_id, chunk_ids):
    if not owner_id or not chunk_ids or any(not isinstance(item, str) or not item for item in chunk_ids):
        raise ValueError("owner-id와 하나 이상의 chunk-id를 명시해야 합니다.")
    conn = db.get_readonly_connection()
    try:
        require_schema(conn)
        rows = []
        for chunk_id in sorted(set(chunk_ids)):
            row = chunks.get(conn, chunk_id, owner_id=owner_id, include_deleted=True)
            if row is None:
                raise ValueError("요청한 조각이 없거나 해당 사용자의 조각이 아닙니다.")
            rows.append(row)
        return rows
    finally:
        conn.close()


def _plan(archive, rows, owner_id):
    index_path = _safe_path(archive, "_index.csv")
    state_path = _safe_path(archive, ".export-state.json")
    index = read_index(index_path)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    known_paths = {row["상대경로"]: chunk_id for chunk_id, row in index.items()}
    operations, cleanup = [], []
    result = dict(written=0, moved=0, deleted=0, total=len(rows))
    for chunk in rows:
        chunk_id = chunk["chunk_id"]
        old = index.get(chunk_id)
        old_relative = old.get("상대경로") if old else ""
        old_path = _safe_path(archive, old_relative) if old_relative else None
        old_bytes = old_path.read_bytes() if old_path and old_path.exists() else None
        receipt = state.get(chunk_id)
        rendered = render_txt(chunk).encode("utf-8")
        if receipt and receipt["owner_id"] != owner_id:
            raise RuntimeError("보관 목록의 소유자가 일치하지 않습니다.")
        if old_bytes is not None:
            if receipt:
                if receipt["path"] != old_relative or receipt["sha256"] != _digest(old_bytes):
                    raise RuntimeError("기존 txt가 외부에서 변경되었습니다. 덮어쓰지 않습니다.")
            elif old_bytes != rendered:
                # Legacy index has no byte digest: never guess ownership of modified text.
                raise RuntimeError("기존 txt 무결성을 확인할 수 없습니다. 덮어쓰지 않습니다.")
        if chunk["deleted_at"]:
            result["deleted"] += 1
            if not old:
                continue
            if old_bytes is None:
                raise RuntimeError("삭제 보관할 기존 txt가 없습니다. 자동으로 대체하지 않습니다.")
            rendered = old_bytes  # preserve the last exported version, not a new tombstone body
            target = Path(old_relative)
            if not old_relative.startswith("_삭제됨/"):
                target = Path("_삭제됨") / old_path.name
                suffix = 0
                while target.as_posix() in known_paths or _safe_path(archive, target.as_posix()).exists():
                    suffix += 1
                    target = Path("_삭제됨") / f"{Path(filename_for(chunk, len(chunk_id))).stem}_{suffix}.txt"
        else:
            target = _target_for(chunk, known_paths)
        relative = target.as_posix()
        destination = _safe_path(archive, relative)
        same_path = relative == old_relative
        if not same_path and destination.exists():
            raise RuntimeError("목록에 없는 기존 파일을 덮어쓰지 않습니다.")
        expected = _digest(old_bytes) if same_path and old_bytes is not None else None
        if expected != _digest(rendered):
            operations.append(dict(path=relative, before=expected, text=rendered.decode("utf-8")))
            if not chunk["deleted_at"]:
                result["written"] += 1
        if old_bytes is not None and not same_path:
            cleanup.append(dict(path=old_relative, sha256=_digest(old_bytes)))
            result["moved"] += 1
        index[chunk_id] = {
            "chunkId": chunk_id, "상대경로": relative,
            "updatedAt": chunk["updated_at"], "contentHash": chunk["content_hash"],
            "예화창고 경로들": old["예화창고 경로들"] if old else "",
        }
        state[chunk_id] = dict(owner_id=owner_id, path=relative, sha256=_digest(rendered))
        known_paths[relative] = chunk_id
    return dict(version=1, owner_id=owner_id, chunk_ids=sorted(row["chunk_id"] for row in rows),
                index_before=_file_hash(index_path), state_before=_file_hash(state_path),
                index=index, state=state, operations=operations, cleanup=cleanup, result=result)


def _complete(archive, plan):
    index_path = _safe_path(archive, "_index.csv")
    state_path = _safe_path(archive, ".export-state.json")
    for path, before, after in [(index_path, plan["index_before"], _index_bytes(plan["index"])),
                                 (state_path, plan["state_before"], _json_bytes(plan["state"]))]:
        if _file_hash(path) not in (before, _digest(after)):
            raise RuntimeError("내보내기 도중 목록이 변경되었습니다. 복구를 중단합니다.")
    # Validate every remaining file before making any further change on recovery.
    for operation in plan["operations"]:
        actual = _file_hash(_safe_path(archive, operation["path"]))
        if actual not in (operation["before"], _digest(operation["text"].encode("utf-8"))):
            raise RuntimeError("내보내기 도중 txt가 변경되었습니다. 복구를 중단합니다.")
    for old in plan["cleanup"]:
        if _file_hash(_safe_path(archive, old["path"])) not in (None, old["sha256"]):
            raise RuntimeError("이전 txt가 변경되었습니다. 삭제하지 않습니다.")
    for operation in plan["operations"]:
        path = _safe_path(archive, operation["path"])
        data = operation["text"].encode("utf-8")
        if _file_hash(path) != _digest(data):
            _atomic_write(path, data, replace=operation["before"] is not None)
    _atomic_write(state_path, _json_bytes(plan["state"]))
    write_index(index_path, plan["index"])
    # Only after an intact new index is durable may an old managed path be removed.
    for old in plan["cleanup"]:
        path = _safe_path(archive, old["path"])
        if path.exists():
            if _file_hash(path) != old["sha256"]:
                raise RuntimeError("이전 txt가 변경되었습니다. 삭제하지 않습니다.")
            path.unlink()
            _sync_directory(path.parent)
    pending = _safe_path(archive, ".export-pending.json")
    pending.unlink()
    _sync_directory(archive)


def export(output_root: Path, *, owner_id: str, chunk_ids: list[str]) -> dict[str, int]:
    """Explicit selection, read-only DB snapshot, single writer, recoverable file transaction.

    The local lock does not coordinate different iCloud devices: use one exporting device.
    A pending journal is replayed only by the identical owner/ID selection.
    """
    rows = _selected_chunks(owner_id, chunk_ids)  # validate all IDs before touching files
    archive = output_root.resolve() / "독서조각"
    if archive.is_symlink():
        raise RuntimeError("독서조각 보관 폴더가 심볼릭 링크입니다. 내보내지 않습니다.")
    archive.mkdir(parents=True, exist_ok=True)
    lock_path = _safe_path(archive, ".export.lock")
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("다른 내보내기가 실행 중입니다.") from exc
        pending = _safe_path(archive, ".export-pending.json")
        if pending.exists():
            previous = json.loads(pending.read_text(encoding="utf-8"))
            if (previous["version"] != 1 or previous["owner_id"] != owner_id
                    or previous["chunk_ids"] != sorted(set(chunk_ids))):
                raise RuntimeError("미완료 내보내기는 같은 사용자/조각 선택으로 먼저 복구해야 합니다.")
            _complete(archive, previous)
        plan = _plan(archive, rows, owner_id)
        _atomic_write(pending, _json_bytes(plan), replace=False)
        _complete(archive, plan)
        return plan["result"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path, help="독서조각을 만들 명시적 보관 루트")
    parser.add_argument("--owner-id", required=True, help="검증된 요청 사용자 ID (인증을 대신하지 않음)")
    parser.add_argument("--chunk-id", required=True, action="append", help="내보낼 조각 ID; 여러 개는 옵션 반복")
    args = parser.parse_args()
    load_dotenv()
    result = export(args.output_root, owner_id=args.owner_id, chunk_ids=args.chunk_id)
    print(f"내보내기 완료: {result['written']}개 작성, {result['moved']}개 이동, {result['deleted']}개 삭제 처리 ({result['total']}개 조각)")


if __name__ == "__main__":
    main()
