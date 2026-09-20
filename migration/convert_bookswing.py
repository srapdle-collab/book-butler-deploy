#!/usr/bin/env python3
"""BooksWing 백업 ZIP을 도서비서 JSON 구조로 변환하고 검증한다."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import uuid
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.source_semantics import classify_book, source_event


KIND_MAP = {
    0: "quote_with_note",
    1: "photo",
    2: "quote",
    3: "start",
    4: "progress_log",
    5: "finish",
    6: "rating",
    7: "other",
}

EXPECTED_BOOKS = 705
EXPECTED_ACTIVITIES = 5_666
EXPECTED_IMAGES = 768


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nullable(value: Any) -> Any:
    return value if value not in (None, "") else None


def progress_text(activity: dict[str, Any]) -> str | None:
    pages = nullable(activity.get("quote"))
    minutes = nullable(activity.get("text"))
    if pages is not None and minutes is not None:
        return f"{pages}쪽을 {minutes}분 동안 읽었습니다"
    if pages is not None:
        return f"{pages}쪽을 읽었습니다"
    if minutes is not None:
        return f"{minutes}분 동안 읽었습니다"
    return None


def convert_activity(
    raw: dict[str, Any], book_id: str, index: int
) -> dict[str, Any]:
    raw_kind = raw.get("kind")
    kind = KIND_MAP.get(raw_kind, "other")
    record_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"bookswing:{book_id}:{index}"))

    text = nullable(raw.get("text"))
    quote = nullable(raw.get("quote"))
    photo = nullable(raw.get("photo"))

    if raw_kind == 2:
        quote, text = text, None
    elif raw_kind == 4:
        text, quote = progress_text(raw), None

    return {
        "id": record_id,
        "book_id": book_id,
        "kind": kind,
        "eventType": source_event(raw_kind),
        "text": text,
        "quote": quote,
        "page": raw.get("page"),
        "date": raw.get("date"),
        "photo": f"photos/{photo}" if photo is not None else None,
        "visibility": "private",
    }


def convert_book(raw: dict[str, Any]) -> dict[str, Any]:
    raw_status = raw.get("status")
    status, evidence = classify_book(raw)
    return {
        "id": raw["uuid"],
        "title": nullable(raw.get("title")),
        "author": nullable(raw.get("author")),
        "publisher": nullable(raw.get("publisher")),
        "isbn": nullable(raw.get("isbn")),
        "subtitle": nullable(raw.get("subtitle")),
        "translator": nullable(raw.get("translator")),
        "category": nullable(raw.get("category")),
        "pages": raw.get("pages"),
        "currentPage": raw.get("currentPage"),
        "rating": raw.get("rating"),
        "status": status,
        "rawStatus": raw_status,
        "rawReadingNow": raw.get("readingNow"),
        "statusEvidence": evidence,
        "readCount": raw.get("readCount"),
        "startDate": raw.get("date"),
        "finishDate": max((a['date'] for a in raw.get('activities', []) if a['kind']==6), default=None) if status=='완독' else None,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def report_table(source_counts: Counter[int], target_counts: Counter[str]) -> str:
    rows = [
        "| 원본 kind | 의미 | 원본 개수 | 변환 개수 | 일치 |",
        "| ---: | --- | ---: | ---: | :---: |",
    ]
    for raw_kind, target_kind in KIND_MAP.items():
        source = source_counts[raw_kind]
        target = target_counts[target_kind]
        rows.append(
            f"| {raw_kind} | `{target_kind}` | {source:,} | {target:,} | "
            f"{'예' if source == target else '아니요'} |"
        )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="BooksWing_backup.zip 경로")
    parser.add_argument("output", type=Path, help="변환 결과 디렉터리")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    photos_dir = output / "photos"
    output.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)

    books: list[dict[str, Any]] = []
    activities: list[dict[str, Any]] = []
    parse_failures: list[dict[str, str]] = []
    source_kind_counts: Counter[int] = Counter()
    source_status_counts: Counter[int] = Counter()
    source_photo_count_total = 0
    book_ids: set[str] = set()
    book_filenames: set[str] = set()
    activity_photo_refs: defaultdict[str, list[str]] = defaultdict(list)

    with zipfile.ZipFile(source) as archive:
        file_infos = [info for info in archive.infolist() if not info.is_dir()]
        unsafe_names = [
            info.filename
            for info in file_infos
            if PurePosixPath(info.filename).name != info.filename
        ]
        if unsafe_names:
            raise ValueError(f"ZIP 루트 밖의 경로가 포함되어 있습니다: {unsafe_names[:5]}")

        book_infos = sorted(
            (info for info in file_infos if info.filename.endswith(".book")),
            key=lambda item: item.filename,
        )
        image_infos = sorted(
            (info for info in file_infos if info.filename.lower().endswith(".png")),
            key=lambda item: item.filename,
        )

        for info in book_infos:
            try:
                raw_book = json.loads(archive.read(info).decode("utf-8"))
                book_id = raw_book["uuid"]
                if book_id in book_ids:
                    raise ValueError(f"중복 책 UUID: {book_id}")
                if info.filename != f"{book_id}.book":
                    raise ValueError(
                        f"파일명과 책 UUID 불일치: {info.filename} / {book_id}"
                    )

                book_ids.add(book_id)
                book_filenames.add(info.filename)
                source_status_counts[raw_book.get("status")] += 1
                source_photo_count_total += raw_book.get("photoCount", 0) or 0
                books.append(convert_book(raw_book))

                raw_activities = raw_book.get("activities", [])
                if not isinstance(raw_activities, list):
                    raise ValueError("activities가 배열이 아닙니다")
                for index, raw_activity in enumerate(raw_activities):
                    raw_kind = raw_activity.get("kind")
                    source_kind_counts[raw_kind] += 1
                    converted = convert_activity(raw_activity, book_id, index)
                    activities.append(converted)
                    if converted["photo"]:
                        activity_photo_refs[PurePosixPath(converted["photo"]).name].append(
                            converted["id"]
                        )
            except Exception as exc:  # 파일 단위 실패를 리포트에 남긴다.
                parse_failures.append({"file": info.filename, "error": str(exc)})

        image_names = {info.filename for info in image_infos}
        for info in image_infos:
            destination = photos_dir / info.filename
            with archive.open(info) as source_image, destination.open("wb") as target_image:
                shutil.copyfileobj(source_image, target_image)

    target_kind_counts = Counter(activity["kind"] for activity in activities)
    target_photo_refs = {
        PurePosixPath(activity["photo"]).name
        for activity in activities
        if activity["photo"]
    }
    missing_photo_files = sorted(target_photo_refs - image_names)
    duplicate_photo_refs = sorted(
        name for name, record_ids in activity_photo_refs.items() if len(record_ids) > 1
    )
    expected_cover_names = {f"{book_id}_i.png" for book_id in book_ids}
    missing_covers = sorted(expected_cover_names - image_names)
    matched_covers = expected_cover_names & image_names
    unlinked_images = sorted(image_names - matched_covers - target_photo_refs)

    photo_manifest = []
    for name in sorted(image_names):
        if name in matched_covers:
            photo_manifest.append(
                {
                    "filename": name,
                    "type": "cover",
                    "book_id": name[: -len("_i.png")],
                    "record_ids": [],
                }
            )
        elif name in activity_photo_refs:
            photo_manifest.append(
                {
                    "filename": name,
                    "type": "activity",
                    "book_id": name.rsplit("_", 1)[0],
                    "record_ids": activity_photo_refs[name],
                }
            )
        else:
            photo_manifest.append(
                {
                    "filename": name,
                    "type": "unlinked",
                    "book_id": None,
                    "record_ids": [],
                }
            )

    write_json(output / "books.json", books)
    write_json(output / "activities.json", activities)
    write_json(output / "photo_manifest.json", photo_manifest)
    write_json(output / "parse_failures.json", parse_failures)

    all_expected_counts_match = (
        len(books) == EXPECTED_BOOKS
        and len(activities) == EXPECTED_ACTIVITIES
        and len(image_names) == EXPECTED_IMAGES
    )
    all_kind_counts_match = all(
        source_kind_counts[raw_kind] == target_kind_counts[target_kind]
        for raw_kind, target_kind in KIND_MAP.items()
    )
    report_status = (
        "통과"
        if all_expected_counts_match
        and all_kind_counts_match
        and not parse_failures
        and not missing_photo_files
        else "확인 필요"
    )

    failure_lines = (
        "없음"
        if not parse_failures
        else "\n".join(
            f"- `{failure['file']}`: {failure['error']}" for failure in parse_failures
        )
    )
    unlinked_lines = (
        "없음"
        if not unlinked_images
        else "\n".join(f"- `{name}`" for name in unlinked_images)
    )
    missing_photo_lines = (
        "없음"
        if not missing_photo_files
        else "\n".join(f"- `{name}`" for name in missing_photo_files)
    )
    missing_cover_lines = (
        "없음"
        if not missing_covers
        else "\n".join(f"- `{name}`" for name in missing_covers)
    )

    report = f"""# BooksWing 변환 검증 리포트

## 결과

- 종합 판정: **{report_status}**
- 원본 ZIP SHA-256: `{sha256(source)}`
- 원본 `.book`: {len(book_infos):,}개 / 파싱 성공: {len(books):,}개 / 실패: {len(parse_failures):,}개
- 원본 활동: {sum(source_kind_counts.values()):,}건 / 변환 활동: {len(activities):,}건
- 원본 PNG: {len(image_names):,}장 / 복사된 PNG: {len(list(photos_dir.glob('*.png'))):,}장
- 고유 책 UUID: {len(book_ids):,}개
- 고유 활동 UUID: {len({activity['id'] for activity in activities}):,}개

기획문서 기준값(책 {EXPECTED_BOOKS:,}권, 활동 {EXPECTED_ACTIVITIES:,}건, 사진 {EXPECTED_IMAGES:,}장)과 실제 백업 및 변환 결과가 {'모두 일치합니다' if all_expected_counts_match else '일치하지 않는 항목이 있습니다'}.

## activity kind 대조

{report_table(source_kind_counts, target_kind_counts)}

kind별 원본·변환 개수는 {'모두 일치합니다' if all_kind_counts_match else '일치하지 않는 항목이 있습니다'}.

## 책 상태 대조

- 원본 status 분포: {dict(source_status_counts)}
- status와 최근 생명주기 활동을 대조한 상태: {dict(Counter(b['status'] for b in books))}
- 판정 근거/한계는 docs/SOURCE_AUDIT.md 참고. readingNow만으로 읽는 중을 판정하지 않습니다.

## 사진 연결 검증

- 활동의 사진 참조: {sum(len(ids) for ids in activity_photo_refs.values()):,}건
- 고유 활동 사진 파일: {len(target_photo_refs):,}장
- 실제 파일이 없는 활동 사진 참조: {len(missing_photo_files):,}건
- 여러 활동이 함께 참조하는 사진: {len(duplicate_photo_refs):,}장
- 책 UUID와 일치하는 표지(`{{book_id}}_i.png`): {len(matched_covers):,}장
- 표지가 없는 책: {len(missing_covers):,}권
- 활동·표지와 연결되지 않은 보존 이미지: {len(unlinked_images):,}장
- 원본 책의 `photoCount` 합계: {source_photo_count_total:,}

활동의 `photo`에는 `photos/파일명`을 기록했고, `photo_manifest.json`에는 각 파일과 책·활동 ID의 연결을 기록했습니다. 연결되지 않은 이미지도 원본 보존을 위해 복사했습니다.

### 실제 파일이 없는 활동 사진 참조

{missing_photo_lines}

### 표지가 없는 책

{missing_cover_lines}

### 활동·표지와 연결되지 않은 이미지

{unlinked_lines}

## 파싱 실패 또는 누락

{failure_lines}

## 변환 규칙

- Book `id`는 원본 `uuid`를 그대로 사용했습니다.
- Book `status`는 원본 status와 최근 생명주기 활동을 대조했습니다. rawStatus/rawReadingNow/statusEvidence를 함께 보존합니다.
- Book `startDate`는 원본 `date`를 사용했습니다.
- Book `finishDate`는 현재 완독 상태인 책의 가장 최근 kind=6 기록일이며, 그 외에는 null입니다.
- Activity eventType은 원본 5=독서 시작, 6=완독(별점 동반), 7=중단 추정으로 구분합니다. kind의 기존 호환 이름/숫자는 변경하지 않습니다.
- Activity `id`는 `book_id`와 원본 배열 순서로 만든 결정적 UUID입니다. 같은 백업을 다시 변환하면 같은 ID가 생성됩니다.
- kind 2의 원본 인용문은 원본 `text`에서 새 `quote`로 이동했습니다.
- kind 4의 원본 `quote`(쪽수)와 `text`(분)를 사람이 읽을 수 있는 진행 로그 문장으로 합쳤습니다.
- kind 7은 매핑표의 “기타” 기록을 잃지 않도록 `other`로 보존했습니다.
- 모든 Activity `visibility`는 `private`으로 설정했습니다.
- 날짜는 원본 Unix timestamp(초)를 그대로 유지했습니다.

## 결과 파일

- `books.json`: Book 배열
- `activities.json`: Activity 배열
- `photos/`: 원본 PNG 전체
- `photo_manifest.json`: 사진과 책·활동 연결 관계
- `parse_failures.json`: 파일별 파싱 실패 목록
"""
    (output / "validation_report.md").write_text(report, encoding="utf-8")

    if report_status != "통과":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
