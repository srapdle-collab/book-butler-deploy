# Reading Chunk 1차-A — schema-init 분리 및 읽기 전용 사전점검

2026-09-27 / Codex / 사용자 확인 Astra High 설정 유지. 제품·테스트 `5148d6f`.

**로컬 구현·격리 검증 PASS, 운영 NO-GO 유지.** 운영 Supabase 접속·쓰기·DDL·배포·환경 설정 변경·실제 iCloud 접근 없음. main 반영/push 및 1차-B 없음. 과거 감사와 수정 결과는 당시 기록이며 아래가 수정 브랜치의 최신 동작이다.

## 1. 연결과 변경 책임

- 이전 앱: 인증 → `db.get_connection()` → PG 전체31DDL `ensure_schema` / SQLite numeric-kind 자동 변환·schema 추가 → 화면. 재렌더·재연결 때 반복될 수 있었다.
- 현재 앱: 인증 → `db.get_connection()` → `db.connect()` → `require_schema()` → `inspect_schema_read_only()` → catalog SELECT/조회 PRAGMA → OK일 때만 화면. 실패 시 연결 close → `SchemaNotReady` 운영 안내 → `st.stop()`. 연결 자체의 SQLite `PRAGMA foreign_keys=ON`은 연결 설정이지 schema/data 변경이 아니다.
- SQLite는 기존 파일 `mode=rw`만 연다. 없는 DB는 생성하지 않는다. 구형 TEXT activity.kind는 변환하지 않고 UNSUPPORTED_SCHEMA로 차단한다. 과거 자동 데이터 변환 코드는 삭제했다.
- export: 명시 owner/ID → `get_readonly_connection()` → `require_schema()` → 선택 조회 → 파일 처리. PostgreSQL READ ONLY/REPEATABLE READ, SQLite mode=ro/query_only/snapshot 유지. schema 실패는 archive 파일 작업 전에 중단한다.
- 일반 앱/접속 모듈은 maintenance를 import/call하지 않는다. 인증 전 로그인 화면은 DB 연결도 하지 않는다. 인증 자체의 외부 Auth 요청은 이 schema 검사와 별개다.
- 기존 `claim_legacy_library`(NULL owner를 가진 books/activities UPDATE), 소그룹 profile upsert 및 사용자가 누르는 정상 CRUD는 **별개 DML로 그대로 존재**한다. 앱 전체가 read-only라는 뜻이 아니다. schema 실패는 이 경로들 전에 중단한다. 운영 무변경 확인/owner claim 검토가 여전히 필요하다.

## 2. Read-only structural contract

`lib/schema.py`는 기존 DDL 상수만 보유한다(DDL 내용 불변). `lib/schema_preflight.py`가 그 상수에서 기대 구조를 만들고 SQLite/PostgreSQL catalog와 비교한다.

- 필수15표/필수컬럼의 존재·타입,13개 명명 index의 대상 표·컬럼 순서·ASC/DESC·unique·조건·정의 및 PG valid/ready/live 비교.
- reading_chunks22컬럼의 타입·NULL/default/generated, PK(chunk_id), UNIQUE(source_ref), books FK의 삭제/수정 정책, sourceApp CHECK를 확인한다. PG 제약의 validated/deferrable도 비교한다.
- public의 일반 테이블만 허용하며 view/partitioned table/임시 객체나 search_path에 가려진 객체는 STOP. 예상 밖 reading_chunks 추가 컬럼도 지원하지 않는 구조로 STOP한다. 기존 다른 표의 추가 컬럼/비필수 index까지 제거·정규화하지 않는다.
- 계약 버전 `reading-chunks-1a.v1`과 기대 DDL SHA-256을 출력한다. **DB에 version row를 만들거나 DB에 저장된 버전 번호를 읽었다고 주장하지 않는다.** 현재는 구조 기반 버전 검사다.
- 상태: OK / MISSING_TABLE / MISSING_COLUMN / MISSING_INDEX / INDEX_DEFINITION_MISMATCH / UNSUPPORTED_SCHEMA / UNKNOWN_ERROR. JSON에는 복수 issue를 담고 최상위 status는 첫 issue다. 드라이버 오류의 DSN/비밀값은 출력하지 않는다.
- 정상 앱 검사도 SELECT/조회 PRAGMA만 호출한다. CLI/export는 DB 수준 read-only 연결도 강제한다. preflight는 구조 검사이며 RLS/ACL/실사용 권한·trigger·동시 schema 변경을 안전하다고 보증하지 않는다. 승인된 별도 보안 metadata 감사와 exclusive maintenance 창이 필요하다.

## 3. 명시적 maintenance

`tools/schema_maintenance.py`는 기본적으로 **읽기 전용 계획 출력**만 한다. 적용은 `--apply --approve-plan <검토한 SHA256>`를 둘 다 명시해야 한다. 이 옵션은 사용자의 승인을 대신하지 않는다.

- 기존14표가 정상이고 reading_chunks만 없으면 신규 표1 + index3 CREATE 계획. PG 대상은 `public.reading_chunks`와 `public.books`로 명시한다.
- 기존 chunk 표가 완전하고 일부 chunk index만 없으면 해당 CREATE INDEX만 계획한다. schema가 정상이면 변경0인 no-op 계획.
- 기존 표/컬럼 누락, 부분 chunk 표, 잘못된 같은 이름 index, 알 수 없는 구조는 `applicable=false`, 실행 SQL0. 기대 index 정의와 별도 검토 안내만 출력한다. 자동 DROP/ALTER/repair/데이터 migration 없음.
- 적용 transaction 안에서 계획/hash를 재검증 → 승인된 CREATE들 → preflight → commit. SQL 실패·마지막 검사 실패·stale plan이면 rollback/중단. 재적용은 최신 계획을 다시 읽어야 한다. 기존 계획을 blindly 재실행하지 않는다.
- 과거 전체 initializer는 `lib/schema_maintenance.initialize_schema(..., approved=True)`로 격리했다. 기존 offline 초기 적재/명시 source 보정 도구와 합성 fixture만 사용한다. **이 전체 initializer는 운영1A용이 아니며 과거 autocommit 부분 적용 특성이 남아 있다.** 좁은1A CLI는 이를 호출하지 않는다. `migration/load_db.py`는 기존 DB 재생성 도구이므로 운영 사용 금지다.

## 4. AUDIT-01과 검증 증거

- **AUDIT-01 PASS(감지·안전 중단·자동 교정 금지 범위)**. SQLite/PG에서 같은 이름의 다른 컬럼 index를 만든 뒤 mismatch를 확인했다. 기존 index가 그대로 남고 계획 적용이 거절된다. 운영 교정 자체는 수행/승인되지 않았다.
- 전체 **154 passed / 0 xfail**,24.17초. 신규 preflight 테스트30개: 정상/누락/타입·NULL·default·CHECK·FK drift, index 순서/정렬/조건/다른 표/이름 충돌, read-only authorizer·반복 파일 byte/checksum, 승인·stale plan·transaction rollback·CLI, 로그인→화면·책장/상세/통계/타임라인 DDL0, schema 실패 UI/export 중단. 기존 CRUD/export/복구/태그/연속수정/통계 테스트 모두 PASS.
- Python63파일 in-memory compile, Node2개 syntax, `git diff --check` PASS. 별도 frontend build 없는 Streamlit 앱이다.
- 신규 `tests/audit/pg_preflight_check.py`: 실제 Python preflight/maintenance → PG17.5 WASM.14시나리오 PASS. READ ONLY 반복,9구조 변형, AUDIT-01, 중간 DDL 실패 전체 rollback, 승인4DDL·3회 no-op, 누락index1개만 생성. 합성705책/5,666활동 및 다른12표 각1행을 포함한 기존14표의 전체 행·컬럼·제약/PK/FK checksum 전후 일치.
- 기존 `pg_service_check.py`도 재실행 PASS: 실제 서비스 CRUD/NULL/소유권/특수 태그/선택 export·재export·삭제 및14표 행 checksum `df45c2608b1e2b45770bee7d0049fd9c4ca973b507336350ea2609a4a529c991` 불변.
- 기존 `pg_simulation.mjs`12시나리오도 재실행: 정상9 PASS, 명시 legacy initializer의 wrong-index 한계1, 부분 표 STOP1, 기존 owner-claim 쓰기 경로1 확인. 이 스크립트는 **과거 full initializer 비교 실험**이며 현재 앱 자동 실행이 아니다. 새 detection PASS는 별도 Python harness로 확인했다. 결함을 숨기려고 legacy initializer를 자동 repair하도록 바꾸지 않았다.
- 결과 `/tmp/readdam-preflight-validation-K5XgQm/{pytest.xml,pg-preflight.json,pg-service.json,pg-legacy.json}`. 기존 /tmp venv/PGlite 재사용, 설치/환경 설정 변경 없음. 실제 psycopg wire/PgBouncer/Supabase/RLS 검증이 아니다.
- 테스트 과정 SQLite authorizer 해제(None)의 Python3.9 callback 차이로 테스트 harness 실패1건을 확인해 명시 허용 callback으로 수정했다. 최종 미해명 테스트 실패0. XML record_property 경고는 xunit1 출력으로 제거했다.

## 5. 상태/보호/다음 단계

- 읽담 `codex/reading-chunks-1a-fixes`, `/private/tmp/readdam-main-LIPAnD`; 시작952c3b3 → 제품5148d6f. main/origin 로컬 ref4d97f4e, deploy51e5b0c 불변. fetch/push/배포 안 함.
- 원본 기획문서2개 SHA-256 전후 동일: `75fd87c2…1808e9`, `515a448b…86bc`. 공동 기존 dirty PROJECT/WORKLOG도 hash 동일. 기존 사용자/합성 iCloud 산출물은 읽거나 수정하지 않았다.
- 공동 기록은 b2d9112 기반 별도 clean worktree `/private/tmp/readdam-cross-preflight-ec8ByH`, `codex/reading-chunks-preflight-docs`에만 기록한다. 공동 main과 dirty 문서, remote 미설정 상태를 보존한다.
- **구현 GO / 운영 NO-GO**. 다음 한 단계는 사용자에게 운영 **read-only metadata/권한 점검만** 승인을 받아 새 CLI 및 runbook의 ACL/RLS 확인을 수행하는 것이다. 실제 schema가 없거나 drift면 DDL을 실행하지 말고 정확한 계획/권한·backup 승인을 별도로 요청한다. main/push/배포도 별도 승인 필요.
- 이후 동등 staging psycopg/PgBouncer, 실제 화면 CRUD/통계, 수정판 iCloud export/재export/index·사용자 데이터 무변경을 확인해야1차-A 완료 판정 가능. 지금은1차-A 미완료,1차-B 금지.
