#!/usr/bin/env python3
"""읽담 reading_chunks를 사람이 보관하는 UTF-8 txt로 내보낸다.

예: python tools/export_chunks.py --output-root /Volumes/Archive

명시한 보관 루트의 ``독서조각/``만 만들고 관리한다. 예화창고는 실제 위치와
구조를 확인하는 다음 단계 전까지 전혀 건드리지 않는다.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from lib import db
from lib import reading_chunks as chunks

INDEX_HEADERS = ["chunkId", "상대경로", "updatedAt", "contentHash", "예화창고 경로들"]
INVALID_FILENAME = re.compile(r'[\\/:*?"<>|\r\n]+')


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
    candidate = (root / relative).resolve()
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
        return {row["chunkId"]: row for row in reader if row.get("chunkId")}


def write_index(path: Path, rows: dict[str, dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_HEADERS)
        writer.writeheader()
        for chunk_id in sorted(rows):
            writer.writerow(rows[chunk_id])


def _target_for(chunk, known_paths: dict[str, str]) -> Path:
    target = relative_path_for(chunk, 8)
    other = known_paths.get(target.as_posix())
    if other and other != chunk["chunk_id"]:
        target = relative_path_for(chunk, 12)
    return target


def export(output_root: Path) -> dict[str, int]:
    """명시 보관 루트 아래 독서조각과 그 index만 갱신하고 건수를 돌려준다."""
    archive = output_root.resolve() / "독서조각"
    archive.mkdir(parents=True, exist_ok=True)
    index_path = archive / "_index.csv"
    index = read_index(index_path)
    known_paths = {row["상대경로"]: chunk_id for chunk_id, row in index.items() if row.get("상대경로")}
    conn = db.get_connection()
    try:
        rows = chunks.all_chunks(conn, include_deleted=True)
    finally:
        conn.close()

    written = moved = deleted = 0
    for chunk in rows:
        old = index.get(chunk["chunk_id"])
        old_relative = old.get("상대경로") if old else ""
        old_path = _safe_path(archive, old_relative) if old_relative else None
        if chunk["deleted_at"]:
            if old_path and old_path.exists() and not old_relative.startswith("_삭제됨/"):
                destination = Path("_삭제됨") / old_path.name
                destination_path = _safe_path(archive, destination.as_posix())
                if destination_path.exists():
                    destination = Path("_삭제됨") / filename_for(chunk, 12)
                    destination_path = _safe_path(archive, destination.as_posix())
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_path), str(destination_path))
                moved += 1
                old_relative = destination.as_posix()
            if old:
                index[chunk["chunk_id"]] = {
                    "chunkId": chunk["chunk_id"], "상대경로": old_relative,
                    "updatedAt": chunk["updated_at"], "contentHash": chunk["content_hash"],
                    "예화창고 경로들": "",
                }
            deleted += 1
            continue

        target_relative = _target_for(chunk, known_paths)
        target_path = _safe_path(archive, target_relative.as_posix())
        if old_path and old_relative != target_relative.as_posix() and old_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                raise RuntimeError(f"내보낼 대상 파일이 이미 있습니다: {target_path}")
            shutil.move(str(old_path), str(target_path))
            moved += 1
        elif target_path.exists() and not old:
            # index에 없는 파일은 사용자가 만든 것으로 간주한다.
            raise RuntimeError(f"목록에 없는 기존 파일을 덮어쓰지 않습니다: {target_path}")

        changed = not old or old.get("updatedAt") != chunk["updated_at"] or old.get("contentHash") != chunk["content_hash"]
        if changed or not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(render_txt(chunk))
            written += 1
        index[chunk["chunk_id"]] = {
            "chunkId": chunk["chunk_id"], "상대경로": target_relative.as_posix(),
            "updatedAt": chunk["updated_at"], "contentHash": chunk["content_hash"],
            "예화창고 경로들": "",
        }
        known_paths[target_relative.as_posix()] = chunk["chunk_id"]
    write_index(index_path, index)
    return {"written": written, "moved": moved, "deleted": deleted, "total": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, type=Path, help="독서조각을 만들 명시적 보관 루트")
    args = parser.parse_args()
    load_dotenv()
    result = export(args.output_root)
    print(f"내보내기 완료: {result['written']}개 작성, {result['moved']}개 이동, {result['deleted']}개 삭제 처리 ({result['total']}개 조각)")


if __name__ == "__main__":
    main()
