#!/usr/bin/env python3
"""읽담의 모든 변경된 Reading Chunk를 1차-A와 기존 예화 카테고리에 순서대로 반영한다.

CLI 기본값은 읽기 전용 dry-run이다. 실제 실행은 별도 운영 승인 후 --apply가 필요하다.
한 Mac만 exporter로 사용하며, 운영 DB에는 읽기 전용으로만 연결한다.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from lib import database, db, ownership
from lib.schema_preflight import require_schema
from tools import export_chunk_illustrations as illustrations
from tools import export_chunks as base


def resolve_owner_id() -> str:
    """The configured library email must identify exactly one existing profile."""
    email = ownership.configured_owner_email()
    if not email:
        raise ValueError("READDAM_OWNER_EMAIL 설정이 필요합니다.")
    conn = db.get_readonly_connection()
    try:
        require_schema(conn)
        rows = database.execute(conn, "SELECT id FROM profiles WHERE lower(email)=?", (email,)).fetchall()
        if len(rows) != 1:
            raise ValueError("설정된 서재 소유자의 profile을 한 개로 확인할 수 없습니다.")
        return rows[0]["id"]
    finally:
        conn.close()


def _rows(owner_id):
    return illustrations._read_rows(owner_id, None)


def _fingerprint(rows):
    return [(r["chunk_id"], r["updated_at"], r["deleted_at"], base.render_txt(r)) for r in rows]


def _pending_ids(path, owner_id):
    try:
        pending = json.loads(path.read_text(encoding="utf-8"))
        ids = pending["chunk_ids"]
        if (pending["version"] != 1 or pending["owner_id"] != owner_id or not isinstance(ids, list)
                or not ids or any(not isinstance(item, str) or not item for item in ids)):
            raise ValueError("invalid pending")
        return ids
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("미완료 export 기록이 손상되었거나 소유자가 다릅니다.") from exc


def _run(root, owner_id, dry_run):
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("기존 예화창고 루트가 없거나 심볼릭 링크입니다.")
    archive = root / "독서조각"
    if archive.is_symlink():
        raise RuntimeError("독서조각 보관 폴더가 심볼릭 링크입니다.")
    pending_base = archive / ".export-pending.json"
    pending_illustrations = archive / illustrations.PENDING
    if dry_run and (pending_base.exists() or pending_illustrations.exists()):
        raise RuntimeError("미완료 export가 있어 dry-run 전에 복구가 필요합니다.")
    if not dry_run:
        # Resume each journal with its original selection before discovering new chunks.
        if pending_base.exists():
            base.export(root, owner_id=owner_id, chunk_ids=_pending_ids(pending_base, owner_id))
        if pending_illustrations.exists():
            illustrations.export(root, owner_id=owner_id,
                                 chunk_ids=_pending_ids(pending_illustrations, owner_id))
    rows = _rows(owner_id)
    ids = {r["chunk_id"] for r in rows}
    existing = base.read_index(archive / "_index.csv")
    orphans = set(existing) - ids
    if orphans:
        state_path = archive / ".export-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        manifest = illustrations._read_manifest(archive / illustrations.MANIFEST, root, owner_id)
        for chunk_id in orphans:
            legacy = existing[chunk_id]
            if (chunk_id in state or chunk_id in manifest["entries"] or legacy["예화창고 경로들"]
                    or not base._safe_path(archive, legacy["상대경로"]).is_file()):
                raise RuntimeError("DB에 없는 소유 조각이 기존 export 목록에 있습니다. 자동 삭제하지 않습니다.")
        # Receipt-less legacy verification rows are preserved byte-for-byte, never claimed.
    if not rows:
        if (archive / illustrations.MANIFEST).exists():
            raise RuntimeError("DB 조각은 없지만 기존 분류 manifest가 있습니다.")
        return {"base": {"written": 0, "moved": 0, "deleted": 0, "total": 0},
                "illustrations": {kind: 0 for kind in illustrations.ACTIONS}, "actions": []}
    base_plan = base._plan(archive, rows, owner_id)
    category_plan = illustrations._plan(root, rows, owner_id, base_preview=base_plan)
    if category_plan["summary"]["CONFLICT"] or category_plan["summary"]["UNMAPPED"]:
        if not dry_run:
            raise RuntimeError("분류 대상에 충돌 또는 미매핑이 있어 쓰지 않습니다.")
        return {"base": base_plan["result"], "illustrations": category_plan["summary"],
                "actions": category_plan["actions"]}
    if dry_run:
        return {"base": base_plan["result"], "illustrations": category_plan["summary"],
                "actions": category_plan["actions"]}
    base_result = base.export(root, owner_id=owner_id, chunk_ids=sorted(ids))
    if _fingerprint(_rows(owner_id)) != _fingerprint(rows):
        raise RuntimeError("export 중 DB 조각이 바뀌었습니다. 다음 실행에서 재검증합니다.")
    category_result = illustrations.export(root, owner_id=owner_id, chunk_ids=sorted(ids))
    return {"base": base_result, "illustrations": category_result["summary"],
            "actions": category_result["actions"]}


def run(output_root: Path, *, owner_id: str | None = None, dry_run=False):
    """Full scan includes soft deletes; receipts/manifest decide the changed files."""
    owner = owner_id or resolve_owner_id()
    requested_root = Path(output_root)
    if requested_root.is_symlink():
        raise RuntimeError("예화창고 루트 심볼릭 링크는 허용하지 않습니다.")
    root = requested_root.resolve()
    if dry_run:
        return _run(root, owner, True)
    # Local advisory lock spans both stages. Existing exporter locks protect each stage.
    lock_name = hashlib.sha256(f"{root}\0{owner}".encode("utf-8")).hexdigest()[:24]
    lock_path = Path(tempfile.gettempdir()) / f"readdam-pipeline-{lock_name}.lock"
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("다른 읽담 파이프라인이 실행 중입니다.") from exc
        return _run(root, owner, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path, help="이미 존재하는 예화창고 루트")
    parser.add_argument("--owner-id", help="합성/관리자 검증용; 일반 실행은 READDAM_OWNER_EMAIL 사용")
    parser.add_argument("--apply", action="store_true", help="파일 반영; 별도 운영 승인 전 사용 금지")
    args = parser.parse_args()
    load_dotenv()
    result = run(args.output_root, owner_id=args.owner_id, dry_run=not args.apply)
    print(json.dumps({"mode": "apply" if args.apply else "dry-run",
                      "base": result["base"], "illustrations": result["illustrations"]},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
