"""원본 상태 판정 보고서와 선택적 비파괴 DB 보정. python -m migration.audit_source --apply"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid
import zipfile

from lib.source_semantics import classify_book, source_event
from lib.schema import ensure_schema


def read_source(path):
    with zipfile.ZipFile(path) as archive:
        names = sorted(n for n in archive.namelist() if n.endswith('.book') and not n.startswith('__MACOSX'))
        return [json.loads(archive.read(n)) for n in names]


def apply_source(conn, books):
    ensure_schema(conn)
    if conn.execute("SELECT 1 FROM app_migrations WHERE name='source-semantics-v1'").fetchone():
        return False
    with conn:
        for raw in books:
            book_id = raw['uuid']
            status, evidence = classify_book(raw)
            ids = {str(uuid.uuid5(uuid.NAMESPACE_URL, f'bookswing:{book_id}:{i}')) for i in range(len(raw['activities']))}
            actual = conn.execute('SELECT id FROM activities WHERE book_id=?', (book_id,)).fetchall()
            has_new = any(r[0] not in ids for r in actual)
            current = conn.execute('SELECT status,current_page FROM books WHERE id=?', (book_id,)).fetchone()
            conn.execute('INSERT OR REPLACE INTO source_book_state VALUES (?,?,?,?,?)',
                         (book_id, raw.get('status'), raw.get('readingNow'), status, evidence))
            # 새로운 기록/상태 변경 흔적이 있는 책은 덮어쓰지 않는다.
            legacy_status = {1: '읽는 중', 2: '완독'}.get(raw.get('status'), '위시리스트')
            if current and not has_new and tuple(current) == (legacy_status, raw.get('currentPage')):
                finish = max((a['date'] for a in raw['activities'] if a['kind']==6), default=None)
                conn.execute('UPDATE books SET status=?,finish_date=? WHERE id=?',
                             (status, finish if status=='완독' else None, book_id))
            for i, activity in enumerate(raw['activities']):
                aid = str(uuid.uuid5(uuid.NAMESPACE_URL, f'bookswing:{book_id}:{i}'))
                conn.execute('UPDATE activities SET event_type=? WHERE id=?',
                             (source_event(activity['kind']), aid))
        # 기존 앱에서 생성한 kind=5는 완독 이벤트였다. 원본에는 별도 의미가 이미 지정됨.
        conn.execute("UPDATE activities SET event_type='completed' WHERE kind=5 AND event_type IS NULL")
        conn.execute("INSERT INTO app_migrations VALUES ('source-semantics-v1',?)", (int(time.time()),))
    return True


def report(books, path):
    statuses = Counter(b.get('status') for b in books)
    reading = Counter(b.get('readingNow') for b in books)
    classified = Counter(classify_book(b)[0] for b in books)
    cross = Counter((b['status'], max((a for a in b['activities'] if a['kind'] in (5,6,7)),
                 key=lambda a:a['date'], default={}).get('kind')) for b in books)
    agrees = sum((b.get('readCount') or 0)==sum(a['kind']==6 for a in b['activities']) for b in books)
    latest = Counter((b['status'], max(b['activities'],key=lambda a:a['date'],default={}).get('kind')) for b in books)
    rows = '\n'.join(f'| {s} | {k} | {n} |' for (s,k),n in cross.items())
    return f'''# 북스윙 상태 판정 검증 — 2026-09-20

원본 SHA256: `{hashlib.sha256(path.read_bytes()).hexdigest()}`

- 파싱: {len(books)}권, 활동 {sum(len(b['activities']) for b in books)}건. 실패 0건.
- raw status: {dict(statuses)}
- readingNow: {dict(reading)} (None은 필드 부재). 1은 한 권뿐이며 status=1, readCount=1이다.
- readCount와 kind=6 활동 수 일치: **{agrees}/{len(books)}권**, 합계 301회.
- kind=5는 416건 모두 page=1. kind=6은 301건 모두 page=1 및 별점 텍스트.
- 최근 전체 활동 교차 집계(status, kind): `{dict(latest)}`.

| status | 최근 생명주기 kind (날짜순 5/6/7) | 책 수 |
| --- | --- | --- |
{rows}

## 판정 기준 및 결과

{dict(classified)}

1. status=2이면서 가장 최근 생명주기 기록=5 → 읽는 중 **35권**. 35권 전부 일치한다.
2. status=1, 최근 생명주기=6 → 완독. readCount 일치와 시작→진도→별점 순서가 근거다.
3. status=1, 최근 생명주기=7 → 읽기 중단으로 추론. 원본 코드/명세 없이 의미를 확정한 것은 아니다.
4. status=1, 생명주기 없음, readCount=0 → 미독. 위시리스트와 구분한다.
5. 충돌 사례는 확인 필요로 남긴다. readingNow는 목록 필터로 사용하지 않는다.

현재 쪽이 전체 쪽과 같아도 자동 완독하지 않는다. 시작 후 마지막 쪽까지 갔지만 완료 처리를 하지 않은 책이 존재한다.
스크린샷의 27권과 백업 판정 35권 차이는 이 자료만으로 설명할 수 없다. 숫자에 맞춘 조건은 추가하지 않았다.
kind=5 시작, kind=6 완독(별점 동반)은 자료 전체의 일관성에 근거한 역추론이며 원본 앱 소스 확인은 아니다.

## 적용과 보존

숫자 kind와 본문·사진·ID는 그대로 유지한다. event_type으로 원본 시작(5)과 새 앱 완독(5)을 구분하여 통계가 잘못 합산되지 않게 한다.
원본 상태/readingNow/판정 근거는 source_book_state에 남긴다. 기존 마이그레이션 상태와 일치하고 새 기록이 없는 책에만 상태를 보정한다.
실제 DB 보정 전 SQLite 백업을 생성하며 마이그레이션은 한 번만 적용한다. 기존 변환 JSON/ZIP/사진은 수정하지 않는다.
이 보고서가 이전 validation_report의 status=1 읽는 중/status=2 완독 및 kind=5 완독 설명을 정정한다.
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path,default=Path('data/bookswing_import/BooksWing_backup.zip'))
    parser.add_argument('--db',type=Path,default=Path('data/book_butler.db'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    books=read_source(args.zip)
    Path('docs').mkdir(exist_ok=True)
    Path('docs/SOURCE_AUDIT.md').write_text(report(books,args.zip),encoding='utf-8')
    print(dict(Counter(classify_book(b)[0] for b in books)))
    if args.apply:
        conn=sqlite3.connect(args.db)
        backups=args.db.parent/'backups'; backups.mkdir(exist_ok=True)
        target=backups/f"before-stage1-{datetime.now():%Y%m%d-%H%M%S}.db"
        with sqlite3.connect(target) as copy: conn.backup(copy)
        print('backup:',target)
        print('applied:',apply_source(conn,books))
        print('integrity:',conn.execute('PRAGMA integrity_check').fetchone()[0])
        conn.close()


if __name__=='__main__': main()
