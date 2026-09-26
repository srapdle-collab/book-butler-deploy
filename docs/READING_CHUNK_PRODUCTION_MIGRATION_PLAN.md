# Reading Chunk 1차-A — 운영 migration 최종 계획(실행 보류)

2026-09-27 / Codex. 이 문서는 **실행 승인서가 아니다**. 운영 DB 접속·DDL·DML·배포는 수행하지 않았다. 아래 운영 상태는 사용자가 전달한 읽기 전용 점검 결과이며 이 세션에서 독립 재조회하지 않았다.

## 확인된 상태와 미확인 게이트

- 전달된 운영 집계: books 705, activities 5,667, 두 표의 `owner_id IS NULL` 각각 0, profiles 1. `reading_chunks`와 관련 인덱스는 없음. 기존 표 RLS 비활성, 정책 0건, `public` USAGE/CREATE true.
- 이 결과로 새 표와 명명 인덱스 3개의 필요성은 확인된다. 기존 `reading_groups_pkey`, `one_active_reading`, `reading_sessions_pkey`와 세 명명 인덱스의 이름은 다르다. 단, `pg_class` 전체 네임스페이스에서 자동 생성될 PK/UNIQUE 인덱스명까지 충돌하지 않는지는 최종 확인해야 한다.
- 운영 `current_user`/`session_user`, DDL 실행 계정의 `REFERENCES public.books` 권한, `books.id` 실제 타입·PK/UNIQUE, 새 테이블 기본 ACL(`pg_default_acl`, 생성 계정별), `anon`·`authenticated`의 Data API 접근 가능 여부, 실제 앱 연결 계정의 SELECT/INSERT/UPDATE 권한, event trigger 및 PgBouncer 모드는 미확인이다. `public` CREATE=true만으로 이를 확정할 수 없다.
- Supabase의 [RLS 안내](https://supabase.com/docs/guides/database/postgres/row-level-security)와 [API 보안 안내](https://supabase.com/docs/guides/api/securing-your-api)에 따르면 노출된 `public` 표에 기본 GRANT가 생기는 구성에서는 RLS 없는 신규 표가 Data API로 노출될 수 있다. 기본 권한은 프로젝트·객체 생성 role의 설정에 따라 달라진다([PostgreSQL default privileges](https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html)). **실제 기본 ACL과 API 노출 범위가 확인되기 전에는 4문장 적용 NO-GO**. `anon`/`authenticated`에 접근권이 생긴다면 RLS/GRANT 정책 결정이 먼저 필요하며 이번 4문장만 실행하지 않는다.

## 정확한 신규 객체 DDL — 검토 전용, 실행 금지

`lib/schema_maintenance.plan_reading_chunks`의 PostgreSQL 계획과 같은 대상·정의다. `IF NOT EXISTS`를 쓰지 않아 예상 밖 동일 이름/정의 드리프트를 숨기지 않는다. 다른 기존 표·컬럼·데이터를 변경하지 않는다.

```sql
CREATE TABLE public.reading_chunks (
    chunk_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    book_id TEXT REFERENCES public.books(id),
    book_title TEXT NOT NULL,
    author TEXT,
    isbn TEXT,
    source_app TEXT NOT NULL CHECK(source_app IN ('readdam', 'today-library')),
    source_ref TEXT UNIQUE,
    read_date TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    position_note TEXT,
    minutes INTEGER,
    original_text TEXT,
    user_note TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    illustration_tags TEXT NOT NULL DEFAULT '[]',
    content_types TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE INDEX idx_reading_chunks_book
    ON public.reading_chunks(book_id, deleted_at, read_date DESC);
CREATE INDEX idx_reading_chunks_owner
    ON public.reading_chunks(owner_id, deleted_at, updated_at DESC);
CREATE INDEX idx_reading_chunks_duplicate
    ON public.reading_chunks(owner_id, book_id, read_date, page_start, page_end, content_hash);
```

`chunk_id` PK와 `source_ref` UNIQUE는 자동 유일 인덱스 2개를 만든다. `idx_reading_chunks_duplicate`는 **UNIQUE가 아니다**. 의미 중복은 서비스의 경고·사용자 선택으로 처리한다. FK는 책 존재만 보장하고 `owner_id`가 해당 책의 owner와 같은지는 보장하지 않는다. 읽담의 인증된 서버 서비스가 책 owner를 조회·대조하고, UPDATE/soft delete에서 `chunk_id + owner_id + book_id`를 함께 조건으로 사용한다. **DB 직접접근 경로에는 이 격리가 적용되지 않으므로**, 그런 role/API 접근이 있다면 별도 RLS/ACL 결정 없이 적용하지 않는다. 기존 책/활동의 ALTER·이관은 0건이다.

## 승인 전 읽기 전용 최종점검

승인된 운영 조회 경로에서 `BEGIN READ ONLY` 후 catalog/aggregate SELECT만 실행한다. 계정명·권한 결과만 기록하고 비밀값은 출력하지 않는다. 미확인/불일치가 있으면 STOP.

```sql
SELECT current_user, session_user, current_setting('server_version');
SELECT has_schema_privilege(current_user, 'public', 'USAGE') AS public_usage,
       has_schema_privilege(current_user, 'public', 'CREATE') AS public_create,
       has_table_privilege(current_user, 'public.books', 'REFERENCES') AS books_references;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='public' AND table_name='books' AND column_name IN ('id','owner_id');
SELECT c.relname, c.relkind, i.indisvalid, i.indisready, pg_get_indexdef(i.indexrelid) AS indexdef
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
LEFT JOIN pg_index i ON i.indexrelid=c.oid
WHERE n.nspname='public' AND c.relname IN
 ('reading_chunks','reading_chunks_pkey','reading_chunks_source_ref_key',
  'idx_reading_chunks_book','idx_reading_chunks_owner','idx_reading_chunks_duplicate')
ORDER BY c.relname;
SELECT pg_get_userbyid(d.defaclrole) AS creator_role, n.nspname AS schema_name,
       d.defaclobjtype, d.defaclacl::text AS default_acl
FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid=d.defaclnamespace
WHERE d.defaclobjtype='r' AND (n.nspname='public' OR d.defaclnamespace=0);
SELECT relname, relrowsecurity, relforcerowsecurity, relacl::text AS acl
FROM pg_class WHERE oid='public.books'::regclass;
SELECT tgname, tgenabled FROM pg_event_trigger;
SELECT count(*) FROM public.books;
SELECT count(*) FROM public.activities;
SELECT count(*) FROM public.books WHERE owner_id IS NULL;
SELECT count(*) FROM public.activities WHERE owner_id IS NULL;
```

`pg_default_acl`에 행이 없다는 것만으로 안전하다고 단정하지 않는다. 실제 migration 생성 role에 적용될 global/per-schema 기본 권한, built-in 기본권한, API의 exposed schema 및 `anon`/`authenticated` 역할 접근을 함께 판정한다. `books.id`가 `TEXT`이며 유일/PK인지 constraint metadata로도 확인한다. `SELECT`가 권한 부족으로 실패하면 권한을 올리지 말고 STOP. 기존 표 14개·필수 인덱스/컬럼은 별도의 `tools/schema_preflight.py` 기대 목록과 대조한다(신규 표 부재 때문에 전체 검사 결과는 MISSING_TABLE이 정상).

## 백업·적용·검증·배포 순서 — 향후 별도 승인 필요

1. **Preflight/STOP gate**: 위 권한·노출·FK·이름·기존 구조를 읽기 전용 확인한다. 사용자 전달 숫자 705/5,667과 재계수 결과가 다르면 원인 확인 전 STOP. 운영용 실제 psycopg/PgBouncer 경로와 migration role을 확정한다. RLS/GRANT가 필요하면 이 계획으로 진행하지 않는다.
2. **백업/복원 확인**: migration 직전 [Supabase 백업](https://supabase.com/docs/guides/platform/backups)의 실제 복구 지점/PITR 가용성을 확인한다. 승인된 비공개 위치에 `pg_dump` custom-format 전체 논리 백업을 만들고 `pg_restore --list`로 읽기 가능성을 확인하며, 가능하면 격리 DB에 복원 리허설한다([PostgreSQL pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html)). 백업 파일·접속정보는 Git/채팅에 남기지 않는다. 기존 14표의 schema/index·row count/체크섬 기준을 보관한다. 백업이 확인되지 않으면 STOP.
3. **배포 전 migration**: 기존 앱 트래픽과 다른 DDL을 통제하는 승인된 maintenance 창에서, 고정된 `5148d6f` 이상 수정판의 narrow `tools/schema_maintenance.py`가 실제로 만든 계획 4문장·SHA를 재확인한다. 명시 승인된 동일 SHA만 사용해 단일 transaction 내 표 → 인덱스 3개 → read-only 구조 preflight → COMMIT. 계획 변화·오류·잠금 초과·preflight 실패는 ROLLBACK/STOP. 구 버전 전체 initializer는 사용하지 않는다.
4. **사후 read-only 검증**: 아래 쿼리 및 `tools/schema_preflight.py --configured-postgres`가 `OK`/구조 계약 `reading-chunks-1a.v1`을 보고하는지 확인한다. 새 표 22컬럼, PK·UNIQUE·FK·CHECK, 명명 인덱스 3개와 정의/validity, RLS/ACL 노출, books/activities 기존 row count·NULL-owner·체크섬 불변을 확인한다. 불일치 시 앱 배포 STOP.
5. **앱 배포**: 별도 승인 후 수정 브랜치의 제품/테스트를 main에 안전하게 반영·전체 테스트하고, 승인된 정확한 SHA만 deploy/main으로 보낸다. 운영 앱이 read-only schema preflight를 통과하고 기존 책/기록/통계와 chunk 1건의 화면 CRUD·검색/필터·export/재export/index·삭제·기존 데이터 무변경을 검증한다. 실패 시 아래 rollback.

사후 구조 확인 예시(읽기 전용):

```sql
SELECT to_regclass('public.reading_chunks') AS reading_chunks;
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='public' AND table_name='reading_chunks'
ORDER BY ordinal_position;
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname='public' AND tablename='reading_chunks' ORDER BY indexname;
SELECT c.relname AS index_name, i.indisvalid, i.indisready, pg_get_indexdef(i.indexrelid) AS definition
FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid
WHERE i.indrelid='public.reading_chunks'::regclass ORDER BY c.relname;
SELECT conname, contype, convalidated, pg_get_constraintdef(oid) AS definition
FROM pg_constraint WHERE conrelid='public.reading_chunks'::regclass ORDER BY conname;
SELECT relrowsecurity, relforcerowsecurity, relacl::text
FROM pg_class WHERE oid='public.reading_chunks'::regclass;
SELECT has_table_privilege('anon','public.reading_chunks','SELECT') AS anon_select,
       has_table_privilege('anon','public.reading_chunks','INSERT') AS anon_insert,
       has_table_privilege('anon','public.reading_chunks','UPDATE') AS anon_update,
       has_table_privilege('authenticated','public.reading_chunks','SELECT') AS authenticated_select,
       has_table_privilege('authenticated','public.reading_chunks','INSERT') AS authenticated_insert,
       has_table_privilege('authenticated','public.reading_chunks','UPDATE') AS authenticated_update;
SELECT count(*) FROM public.books;
SELECT count(*) FROM public.activities;
SELECT count(*) FROM public.books WHERE owner_id IS NULL;
SELECT count(*) FROM public.activities WHERE owner_id IS NULL;
SELECT count(*) FROM public.reading_chunks;
```

## Rollback과 현재 판정

- COMMIT 전 오류: 단일 transaction을 ROLLBACK한다. 기존 표/행은 대상이 아니다.
- COMMIT 후 앱 배포 실패: 앱만 이전 배포 `deploy/main=51e5b0c`로 되돌리고, 신규 빈/검증용 표는 보존한다. `DROP TABLE`/인덱스 삭제나 전체 운영 DB restore를 자동 실행하지 않는다. 테스트 행·export 파일 정리는 별도 식별·승인을 거친다.
- 신규 표의 권한이 예상보다 넓거나 사용자 데이터 노출이 의심되면 즉시 STOP/앱 중지하고, 새 표만 대상으로 하는 RLS/REVOKE 조치는 별도 정책·승인으로 수립한다. 기존 표 정책을 임의 변경하지 않는다.
- **현재 판정: migration SQL 4개 확정, 운영 적용 NO-GO.** 실제 생성 role의 기본 ACL·Data API 노출·FK/실행권한·백업 확인이 남았다. 필요 시 RLS/GRANT 신규 정책은 사용자 결정 없이는 추가하지 않는다. 1차-A 미완료, 1차-B 금지.
