#!/usr/bin/env python3
"""Reading Chunk의 예화 태그를 기존 카테고리/읽담/에 명시적으로 export한다.

1차-A txt export가 먼저 완료되어야 한다. --dry-run은 DB와 파일을 읽기만 한다.
실제 iCloud 경로 사용은 별도 운영 승인과 사전 점검이 필요하다.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import json
import sys
import unicodedata
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import db, reading_chunks as chunks
from lib.schema_preflight import require_schema
from tools import export_chunks as base

ALIASES = {
    "관계": "공동체,관계, 교회", "공동체": "공동체,관계, 교회",
    "비전": "꿈,비전,사명,열정", "열정": "꿈,비전,사명,열정",
    "말씀묵상": "성경,말씀묵상", "영생": "부활,영생",
    "하나님나라": "하나님 나라",
}
AMBIGUOUS = frozenset({"교회", "사명", "성경", "말씀", "결혼", "이성교제"})
MANIFEST = "_illustration_manifest.json"
PENDING = ".illustration-pending.json"
MAPPING = "_예화창고_태그매핑.csv"
ACTIONS = ("CREATE", "UPDATE", "DELETE", "SKIP", "UNMAPPED", "CONFLICT")


def _nfc(value):
    return unicodedata.normalize("NFC", value.strip())


def _identity(chunk_id, category, relative):
    return base._digest(f"{chunk_id}\0{category}\0{relative}".encode("utf-8"))


def _safe_name(name):
    return (name not in ("", ".", "..", "독서조각") and "/" not in name and "\\" not in name
            and "\x00" not in name)


def _categories(root):
    """List names only; never inspect a human file inside a category."""
    if not root.is_dir():
        raise RuntimeError("예화창고 대상 루트가 존재하지 않습니다.")
    result, normalized = {}, {}
    for item in root.iterdir():
        # The preserved synthetic 1차-A verification roots are not subject categories.
        if (_nfc(item.name) == "독서조각" or _nfc(item.name).startswith("_읽담_검증전용_")
                or not item.is_dir()):
            continue
        if item.is_symlink() or not _safe_name(item.name):
            raise RuntimeError("안전하지 않은 카테고리 경로를 발견했습니다.")
        key = _nfc(item.name)
        normalized.setdefault(key, []).append(item.name)
        result[item.name] = item
    return result, normalized


def _aliases(archive):
    """An optional mapping CSV may restate approved aliases, never add new policy."""
    path = base._safe_path(archive, MAPPING)
    if not path.exists():
        return ALIASES
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["태그", "폴더"]:
            raise RuntimeError("예화 태그 매핑 목록 헤더가 잘못되었습니다.")
        found = {}
        for row in reader:
            if set(row) != {"태그", "폴더"} or not row["태그"] or not row["폴더"]:
                raise RuntimeError("예화 태그 매핑 목록 행이 잘못되었습니다.")
            tag, category = _nfc(row["태그"]), _nfc(row["폴더"])
            if tag in found or ALIASES.get(tag) != category or tag in AMBIGUOUS:
                raise RuntimeError("승인되지 않은 예화 태그 매핑입니다.")
            found[tag] = category
    return ALIASES


def _map_tags(tags, names, normalized, aliases):
    categories, unmapped = set(), []
    for original in tags:
        tag = _nfc(str(original))
        if not tag:
            continue
        if tag in AMBIGUOUS:
            unmapped.append((tag, f"모호한 태그: {tag}"))
            continue
        target = aliases.get(tag, tag)
        matches = normalized.get(target, [])
        if len(matches) == 1:
            categories.add(matches[0])
        else:
            unmapped.append((tag, f"매핑 없음: {tag}" if not matches else f"폴더 이름 충돌: {tag}"))
    return sorted(categories), unmapped


def _managed_path(root, category, relative):
    """Validate the precise category/읽담/file boundary, including symlinks."""
    if not _safe_name(category) or not isinstance(relative, str):
        raise RuntimeError("manifest 경로가 안전하지 않습니다.")
    parts = Path(relative).parts
    if len(parts) != 3 or parts[0] != category or parts[1] != "읽담" or not _safe_name(parts[2]):
        raise RuntimeError("manifest 경로가 읽담 관리 영역 밖입니다.")
    category_path = root / category
    managed_dir = category_path / "읽담"
    if not category_path.is_dir() or category_path.is_symlink() or managed_dir.is_symlink():
        raise RuntimeError("카테고리/읽담 경로가 없거나 심볼릭 링크입니다.")
    return base._safe_path(root, relative)


def _read_manifest(path, root, owner_id):
    if not path.exists():
        return {"version": 1, "owner_id": owner_id, "entries": {}}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("export manifest가 손상되었습니다.") from exc
    if (not isinstance(manifest, dict) or set(manifest) != {"version", "owner_id", "entries"}
            or manifest["version"] != 1 or manifest["owner_id"] != owner_id
            or not isinstance(manifest["entries"], dict)):
        raise RuntimeError("export manifest 형식 또는 소유자가 일치하지 않습니다.")
    seen = set()
    for chunk_id, entries in manifest["entries"].items():
        if not isinstance(chunk_id, str) or not isinstance(entries, list):
            raise RuntimeError("export manifest 항목이 잘못되었습니다.")
        for item in entries:
            if (not isinstance(item, dict)
                    or set(item) != {"category", "relative_path", "sha256", "export_identity"}
                    or not all(isinstance(v, str) and v for v in item.values())):
                raise RuntimeError("export manifest 항목이 잘못되었습니다.")
            relative = item["relative_path"]
            _managed_path(root, item["category"], relative)
            if (relative in seen or item["export_identity"] != _identity(chunk_id, item["category"], relative)
                    or len(item["sha256"]) != 64):
                raise RuntimeError("export manifest의 소유 관계가 불명확합니다.")
            seen.add(relative)
    return manifest


def _read_rows(owner_id, chunk_ids):
    if not owner_id:
        raise ValueError("owner-id가 필요합니다.")
    if chunk_ids is not None and (not chunk_ids or any(not isinstance(x, str) or not x for x in chunk_ids)):
        raise ValueError("chunk-id 선택이 잘못되었습니다.")
    conn = db.get_readonly_connection()
    try:
        require_schema(conn)
        if chunk_ids is None:
            return chunks.all_chunks(conn, owner_id=owner_id, include_deleted=True)
        rows = []
        for chunk_id in sorted(set(chunk_ids)):
            row = chunks.get(conn, chunk_id, owner_id=owner_id, include_deleted=True)
            if row is None:
                raise ValueError("요청한 조각이 없거나 해당 사용자의 조각이 아닙니다.")
            rows.append(row)
        return rows
    finally:
        conn.close()


def _plan(root, rows, owner_id):
    archive = root / "독서조각"
    if archive.is_symlink():
        raise RuntimeError("독서조각 경로가 심볼릭 링크입니다.")
    categories, normalized = _categories(root)
    index_path = base._safe_path(archive, "_index.csv")
    manifest_path = base._safe_path(archive, MANIFEST)
    pending_path = base._safe_path(archive, PENDING)
    if pending_path.exists():
        raise RuntimeError("미완료 분류 export가 있습니다. 같은 선택으로 복구해야 합니다.")
    index = base.read_index(index_path)
    manifest = _read_manifest(manifest_path, root, owner_id)
    aliases = _aliases(archive)
    for chunk_id, entries in manifest["entries"].items():
        try:
            listed = json.loads(index[chunk_id]["예화창고 경로들"] or "[]") if chunk_id in index else None
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("_index.csv의 export 경로 목록이 손상되었습니다.") from exc
        if listed != sorted(item["relative_path"] for item in entries):
            raise RuntimeError("manifest와 _index.csv의 소유 목록이 일치하지 않습니다.")
    for chunk_id, row in index.items():
        if row["예화창고 경로들"] and chunk_id not in manifest["entries"]:
            raise RuntimeError("manifest 없이 기존 export 경로의 소유권을 추정하지 않습니다.")
    actions, writes, cleanup = [], [], []
    entries_by_chunk = dict(manifest["entries"])
    reserved = {item["relative_path"]: chunk_id for chunk_id, items in entries_by_chunk.items() for item in items}
    dedupe, multi_copy = 0, 0
    for row in rows:
        chunk_id = row["chunk_id"]
        old_entries = {item["relative_path"]: item for item in entries_by_chunk.get(chunk_id, [])}
        for item in old_entries.values():
            path = _managed_path(root, item["category"], item["relative_path"])
            if path.exists() and base._file_hash(path) != item["sha256"]:
                raise RuntimeError("읽담 소유 export 파일이 외부에서 변경되었습니다.")
        wanted = {}
        if not row["deleted_at"]:
            mapped, unmapped = _map_tags(row["illustration_tags"], categories, normalized, aliases)
            dedupe += max(0, len([t for t in row["illustration_tags"] if _nfc(t) not in AMBIGUOUS])
                          - len(unmapped) - len(mapped))
            if len(mapped) > 1:
                multi_copy += len(mapped) - 1
            for tag, reason in unmapped:
                actions.append(dict(action="UNMAPPED", chunkId=chunk_id, category=None,
                                    relativePath=None, reason=reason))
            if not row["illustration_tags"]:
                actions.append(dict(action="SKIP", chunkId=chunk_id, category=None,
                                    relativePath=None, reason="예화 태그 없음"))
            if mapped:
                indexed = index.get(chunk_id)
                state_path = base._safe_path(archive, ".export-state.json")
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    raise RuntimeError("1차-A export 상태가 손상되었습니다.") from exc
                rendered = base.render_txt(row).encode("utf-8")
                receipt = state.get(chunk_id)
                if (not indexed or indexed["updatedAt"] != row["updated_at"] or not receipt
                        or receipt.get("owner_id") != owner_id or receipt.get("path") != indexed["상대경로"]
                        or receipt.get("sha256") != base._digest(rendered)
                        or base._file_hash(base._safe_path(archive, indexed["상대경로"])) != base._digest(rendered)):
                    actions.append(dict(action="CONFLICT", chunkId=chunk_id, category=None,
                                        relativePath=None, reason="1차-A txt export 선행 필요"))
                    continue
                else:
                    filename = Path(indexed["상대경로"]).name
                    for category in mapped:
                        relative = (Path(category) / "읽담" / filename).as_posix()
                        wanted[relative] = dict(category=category, relative_path=relative,
                                                sha256=base._digest(rendered),
                                                export_identity=_identity(chunk_id, category, relative))
        for relative, item in sorted(wanted.items()):
            path = _managed_path(root, item["category"], relative)
            old = old_entries.get(relative)
            if reserved.get(relative) not in (None, chunk_id):
                action, reason = "CONFLICT", "다른 Chunk의 소유 경로와 충돌"
            elif old:
                if path.exists() and item["sha256"] == old["sha256"]:
                    action, reason = "SKIP", "내용과 경로 동일"
                else:
                    action, reason = ("UPDATE", "정본 내용 변경") if path.exists() else ("CREATE", "소유 파일 재생성")
            elif path.exists():
                action, reason = "CONFLICT", "목록에 없는 기존 파일과 충돌"
            else:
                action, reason = "CREATE", "새 카테고리 파생본"
            actions.append(dict(action=action, chunkId=chunk_id, category=item["category"],
                                relativePath=relative, reason=reason))
            if action in ("CREATE", "UPDATE"):
                writes.append(dict(path=relative, before=old["sha256"] if old and path.exists() else None,
                                   text=rendered.decode("utf-8")))
                reserved[relative] = chunk_id
        for relative, item in sorted(old_entries.items()):
            if relative in wanted:
                continue
            actions.append(dict(action="DELETE", chunkId=chunk_id, category=item["category"],
                                relativePath=relative, reason="soft delete" if row["deleted_at"] else "태그/대상 변경"))
            cleanup.append(dict(path=relative, sha256=item["sha256"], category=item["category"]))
        if not any(action["action"] == "CONFLICT" and action["chunkId"] == chunk_id for action in actions):
            entries_by_chunk[chunk_id] = [wanted[key] for key in sorted(wanted)]
            if chunk_id in index:
                index[chunk_id]["예화창고 경로들"] = json.dumps(sorted(wanted), ensure_ascii=False)
    summary = {kind: sum(a["action"] == kind for a in actions) for kind in ACTIONS}
    summary.update(total=len(rows), tagged_chunks=sum(bool(r["illustration_tags"]) for r in rows),
                   multi_copy=multi_copy, dedupe=dedupe)
    return dict(version=1, owner_id=owner_id, chunk_ids=sorted(r["chunk_id"] for r in rows),
                index_before=base._file_hash(index_path), manifest_before=base._file_hash(manifest_path),
                index=index, manifest={"version": 1, "owner_id": owner_id, "entries": entries_by_chunk},
                writes=writes, cleanup=cleanup, actions=actions, summary=summary)


def _complete(root, plan):
    archive = root / "독서조각"
    index_path = base._safe_path(archive, "_index.csv")
    manifest_path = base._safe_path(archive, MANIFEST)
    pending_path = base._safe_path(archive, PENDING)
    index_bytes = base._index_bytes(plan["index"])
    manifest_bytes = base._json_bytes(plan["manifest"])
    for path, before, after in ((index_path, plan["index_before"], index_bytes),
                                (manifest_path, plan["manifest_before"], manifest_bytes)):
        if base._file_hash(path) not in (before, base._digest(after)):
            raise RuntimeError("내보내기 도중 목록이 변경되었습니다. 복구를 중단합니다.")
    for write in plan["writes"]:
        category = Path(write["path"]).parts[0]
        path = _managed_path(root, category, write["path"])
        if base._file_hash(path) not in (write["before"], base._digest(write["text"].encode("utf-8"))):
            raise RuntimeError("내보내기 도중 파생 파일이 변경되었습니다. 복구를 중단합니다.")
    for old in plan["cleanup"]:
        if base._file_hash(_managed_path(root, old["category"], old["path"])) not in (None, old["sha256"]):
            raise RuntimeError("이전 파생 파일이 변경되었습니다. 삭제하지 않습니다.")
    for write in plan["writes"]:
        category = Path(write["path"]).parts[0]
        path = _managed_path(root, category, write["path"])
        data = write["text"].encode("utf-8")
        if base._file_hash(path) != base._digest(data):
            base._atomic_write(path, data, replace=write["before"] is not None)
    base._atomic_write(manifest_path, manifest_bytes)
    base.write_index(index_path, plan["index"])
    for old in plan["cleanup"]:
        path = _managed_path(root, old["category"], old["path"])
        if path.exists():
            if base._file_hash(path) != old["sha256"]:
                raise RuntimeError("이전 파생 파일이 변경되었습니다. 삭제하지 않습니다.")
            path.unlink()
            base._sync_directory(path.parent)
            if path.parent.is_dir() and not any(path.parent.iterdir()):
                path.parent.rmdir()
                base._sync_directory(path.parent.parent)
    pending_path.unlink()
    base._sync_directory(archive)


def export(output_root: Path, *, owner_id: str, chunk_ids: list[str] | None = None, dry_run=False):
    """Select read-only DB rows; dry-run has no filesystem writes, export shares 1차-A lock."""
    rows = _read_rows(owner_id, chunk_ids)
    root = Path(output_root).resolve()
    archive = root / "독서조각"
    if dry_run:
        plan = _plan(root, rows, owner_id)
        return {"actions": plan["actions"], "summary": plan["summary"]}
    if not archive.is_dir():
        raise RuntimeError("1차-A 독서조각 export를 먼저 실행해야 합니다.")
    lock_path = base._safe_path(archive, ".export.lock")
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("다른 내보내기가 실행 중입니다.") from exc
        pending_path = base._safe_path(archive, PENDING)
        if pending_path.exists():
            try:
                previous = json.loads(pending_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("미완료 export 기록이 손상되었습니다.") from exc
            if (previous.get("version") != 1 or previous.get("owner_id") != owner_id
                    or previous.get("chunk_ids") != sorted(r["chunk_id"] for r in rows)):
                raise RuntimeError("미완료 export는 같은 사용자/조각 선택으로 복구해야 합니다.")
            _complete(root, previous)
        plan = _plan(root, rows, owner_id)
        if plan["summary"]["CONFLICT"]:
            raise RuntimeError("분류 export 대상에 충돌이 있어 쓰지 않습니다.")
        if (plan["writes"] or plan["cleanup"]
                or base._file_hash(base._safe_path(archive, MANIFEST)) != base._digest(base._json_bytes(plan["manifest"]))
                or base._file_hash(base._safe_path(archive, "_index.csv")) != base._digest(base._index_bytes(plan["index"]))):
            base._atomic_write(pending_path, base._json_bytes(plan), replace=False)
            _complete(root, plan)
        return {"actions": plan["actions"], "summary": plan["summary"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--chunk-id", action="append")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = export(args.output_root, owner_id=args.owner_id, chunk_ids=args.chunk_id, dry_run=args.dry_run)
    for action in result["actions"]:
        print(json.dumps(action, ensure_ascii=False, sort_keys=True))
    print(json.dumps({"summary": result["summary"]}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
