# Reading Chunk 1차-A 운영 배포 전 종합 감사

2026-09-27 / Codex. 제품 기준 `main=4d97f4e`, 배포 미러 `51e5b0c`.

후속 상태: `038ab2e`의 [차단결함 수정](READING_CHUNK_BLOCKER_FIXES.md), `5148d6f`의 [자동 init 분리/읽기 전용 preflight](READING_CHUNK_SCHEMA_PREFLIGHT.md)를 함께 읽는다. 현재 수정 브랜치는154 PASS/0 XFAIL이며 AUDIT-01은 감지·중단 PASS다. 아래는 당시main감사 원본으로 보존하며 운영NO-GO는 계속된다.

**판정: NO-GO. 운영 배포·운영 DB 쓰기/DDL/초기화·1차-B는 실행하지 않았다.**
이번 변경은 테스트·시뮬레이션·문서뿐이다. 제품 코드 수정은 하지 않았다. 아래 재현 결함을 해결하지 않고 배포 승인을 요청하지 않는다.
실행 절차와 정확한 additive SQL은 [배포/복구 runbook](READING_CHUNK_DEPLOY_RUNBOOK.md)을 따른다. 이 문서는 승인서가 아니다.

## 1. 실제 상태와 문서 교차검증

| 대상 | 확인한 상태 |
| --- | --- |
| 읽담 main / origin/main | `4d97f4e` 일치. 이번에 문서 3개/23행만인 커밋을 검토하고 `431fe44 → 4d97f4e` push·원격 SHA 확인 |
| deploy/main | `51e5b0c`, push/배포 없음 |
| 원본 읽담 worktree | `codex/reading-chunks-1a / cbcf0b4`, 사용자 기획문서 수정 1개·미추적 1개 유지 |
| 감사 worktree | `/private/tmp/readdam-main-LIPAnD`, `codex/reading-chunks-1a-audit`; main에서 감사 브랜치 분기. 이름과 달리 현재 main checkout이 아님 |
| 감사 테스트 | `8843b56`, main 반영/push 안 함 |
| 공동 저장소 | main, remote 없음. 기존 `593b02c` 보존. 감사 도중 다른 작업자의 `39ed52d`(2차 매핑 설계 문서)가 추가됨을 재확인하고 보존 |
| 오늘의 서재 | 독립 저장소, `codex/apple-reminder-roundtrip / 9569cfd`; 설계·인계 및 경로 목록만 읽음. 파일 수정 없음 |
| 이전 합성 산출물 | chunk `64894842-88d0-48f4-8912-c9b2105b51ad` txt와 대응 index 그대로 보존 |

읽담 관련 graph: `51e5b0c → aeecb7f → ae86be2 → cbcf0b4 → 54c0d23 → 431fe44 → 4d97f4e → (감사 브랜치)`.
과거 small-groups worktree는 Git 목록에서 prunable로 표시되나 삭제/정리하지 않았다.

확인한 불일치·주의:

1. 기존 HANDOFF/PROJECT/CROSS의 현재 origin `431fe44`, 추가 기록 미push 표기는 이번 `4d97f4e` push 이후 과거 상태다. 최신 항목으로 대체하며 역사 기록은 삭제하지 않는다.
2. 원본 읽담 폴더는 기능 브랜치에 남아 있어 그 안의 HANDOFF를 최신 main 문서로 오인하면 안 된다. 감사 문서는 별도 worktree에 있다.
3. 읽담 README는 SQLite/개인 단일 사용자·소그룹 향후 계획으로 설명하지만 현재 코드는 Supabase/Auth/소그룹을 포함한다. 운영 실행 지침으로 README의 초기 적재 명령을 사용하면 안 된다.
4. 공동 `docs/PROJECT.md`는 옛 사용자 경로와 "오늘의 서재 일반 폴더/미구현"을 기록하지만 실제로는 독립 저장소다. 해당 파일과 공동 WORKLOG는 다른 작업자의 미커밋 작업이라 수정하지 않았다.
5. 오늘의 서재 설계 머리·과거 HANDOFF의 "읽담 main 반영 전/로컬만"은 오래된 상태다. 최신 읽담 Git과 CROSS가 우선한다. 감사 도중 추가된 2차 구조 확인 `9569cfd/39ed52d`는 보존했고 1차-B/2차 구현 승인으로 해석하지 않았다.
6. 설계 5·6절은 export를 읽기 전용 조회로 규정하나 구현 CLI는 schema 초기화 연결을 사용한다(AUDIT-09). 설계의 더 최신 updatedAt만 upsert/저장 중 버튼 비활성화도 현 UI·save에서 일반적인 동시성 보장으로 구현되어 있지 않다. 공통 계약서의 순차 동일 ID 갱신은 동작하지만 동기화 계약 충족과 혼동하지 않는다.
7. "검색"은 현재 조각 태그 필터만 있다. 전문/제목 검색 UI, 화면 export 버튼은 없다. ISBN·시간·sourceApp은 DB/txt에 저장되지만 카드에는 시간/ISBN이 별도 표시되지 않는다.
8. 초기 기록의 `sourceApp=readam` 대신 확정 계약·구현은 **readdam**이다.
9. 과거 "브라우저 없음"은 설치 부재가 아니라 제어 연결 부재다. Chrome/Safari 설치 확인, CUA apps/browsers는 빈 목록, Chrome 연결은 `Browser is not available: chrome`. 네이티브 제어는 세션에서 비활성이다. 우회 자동화/설치/권한 변경 없음.

## 2. 실제 배포 diff와 커버리지

`51e5b0c..4d97f4e`: **12개 파일, +1,051/-1**. 제품 파일 5개, 테스트 2개, 문서·작업 규칙 5개.

| 기능 단위 | 파일·종류 | 영향/위험 | 검증 |
| --- | --- | --- | --- |
| 조각 CRUD/중복 | 신규 `lib/reading_chunks.py` | INSERT/UPDATE는 chunk 표만; owner 경계·동시성·NULL 쿼리 위험 | 기존 service 테스트 + 신규 경계/PG 재현 |
| 입력/수정/soft delete/태그 | 신규 `lib/reading_chunks_ui.py` | 기존 상세화면 안에서 실행; 예외 시 기존 노트까지 못 그림 | 기존 생성 AppTest + 수정/삭제 별도 세션 PASS, 연속 세션 실패 |
| 상세 통합 | 수정 `lib/notebook_ui.py` | chunk 상태 키 초기화 및 기존 노트 앞 render 추가; feature gate/장애 격리 없음 | 기존 65개 회귀 유지 |
| 스키마 | 수정 `lib/schema.py` +54행 | SQLite/Postgres에 신규 22컬럼 표·3일반 index. 기존 초기화 전체 재실행 | SQLite·PostgreSQL WASM 합성 데이터 보존/부분 실패 |
| txt/reexport/index | 신규 `tools/export_chunks.py` | DB 전체 chunk 조회; 파일 생성·덮어쓰기·이동·index 재작성; crash/충돌 위험 | 정상 경로 iCloud 32건·8회 PASS, 실패 경계 재현 |
| ISBN/시간/sourceApp | 위 service/CLI | 스냅샷 포함, 누락 ISBN/시간은 미입력; source 강제 readdam | 기존/추가 테스트·실제 격리 txt 대조 |
| API/환경/배포/의존성 | 변경 없음 | 신규 API·cron·환경변수 없음. 기존 DB 접속 설정 그대로 사용 | Git diff로 확인 |
| migration/통계/기존 기록 | 파일 변경 없음 | 자동 init·소유권 claim 등 기존 부수효과는 계속 존재 | 직접 diff·호출경로·보존 실험 |
| 테스트 | 기존 PG 문자열 검증 1개, 신규 chunk 테스트 4개 추가(기존 총65) | 원래 PG 서버 실행·장애/특수문자 커버리지 부족 | 이번 pytest32케이스 + PG12시나리오 + opt-in iCloud |
| 문서 | AGENTS/CLAUDE/HANDOFF 신규, PROJECT/WORKLOG 갱신 | 공개 배포 시 문서도 공개 미러에 포함될 수 있음 | 비밀값 없음; 로컬 경로·구조 공개 범위는 배포 검토 항목 |

`app.py`, `lib/db.py`, `lib/database.py`, `lib/ownership.py`, 통계/기존 기록, requirements, .streamlit, migration에는 배포 diff가 없다. "변경 없음"이 운영 영향 없음의 증거는 아니다.

## 3. DB init의 정확한 call chain

```text
app.py:14 load_dotenv
  → app.py:107 require_authenticated_user()
      미인증: st.stop → DB 연결에 도달하지 않음
      인증 성공 / 인증 미설정 로컬: 계속
  → app.py:349 db.get_connection()          # 캐시 없음, 전체 rerun마다
      → lib/database.py:11 database_url_from_env()
      → lib/db.py:100 psycopg.connect(autocommit=True, prepare_threshold=None)
      → PostgresConnection(raw)
      → lib/schema.py:105 ensure_schema()
          POSTGRES_SCHEMA를 세미콜론으로 분리 → 31문장을 순차 실행
  → app.py:357 claim_legacy_library()       # 지정 owner 로그인 시 기존 데이터 UPDATE
  → 화면 렌더링 / 소그룹 진입 시 ensure_profile() UPSERT
  → app.py:415 close()

tools/export_chunks.py:191 main()
  → load_dotenv → export(root)
  → mkdir 독서조각, read_index
  → db.get_connection() → 같은 전체 DDL
  → all_chunks(include_deleted=True) → 파일/목록 갱신
```

- DB URL이 있고 명시 db_path 및 BOOK_BUTLER_DB_PATH override가 없으면 Postgres 경로다. URL 우선, 없으면 SUPABASE_DB_HOST/PORT/USER/PASSWORD/NAME 모두로 구성한다. 값은 읽거나 출력하지 않았다.
- 접속 정보 누락 시 fail-closed가 아니라 SQLite 기본 경로로 fallback한다. 환경값 변경은 필요하지 않지만 배포 전 올바른 backend 확인이 필요하다.
- **앱 wrapper의 연결만으로 DDL이 실행**된다. raw psycopg 연결 자체에 init이 있는 것은 아니다. 화면에서 chunk 기능을 누르지 않아도 인증 후 시작/rerun에서 실행한다. 단순 모듈 import와 미인증 로그인 화면만으로는 이 연결을 호출하지 않는다.
- 스키마 호출에 production guard, opt-out, 버전 비교, lock, 전체 transaction, 자동 down migration이 없다. app_migrations 표가 있어도 이 초기화의 버전 관리에 쓰지 않는다.
- CLI는 전체 chunk를 owner/chunkId 필터 없이 읽는다. 운영 TEST 1건만 export하는 승인과 직접 맞지 않는다. 운영 초기화/전체 export를 우회 실행하지 않았다.
- SQLite는 numeric-kind 정규화 → ensure_schema → foreign_keys ON 순서다. 빈 DB에는 activities가 없어 ensure_schema가 바로 return한다. 구 text-kind DB면 rename/create/copy/DROP을 실행한다. 운영 Postgres 경로는 이 SQLite migration을 실행하지 않는다.
- 1차-A에는 앱 간 API가 없다. 도서 검색/Auth/Storage 외부 호출이 이 init을 직접 호출하지는 않지만 Streamlit 전체 rerun 과정에서는 다시 연결된다. 향후 API에서 get_connection을 재사용하면 DDL도 실행되므로 1차-B 설계 시 분리 필요.

## 4. SQL/DDL mutation inventory

전체 원문: `lib/schema.py:4`의 POSTGRES_SCHEMA. 독립 추출 증거:
`/tmp/readdam-pg-audit-EnKMvd/{baseline-init.sql,current-init.sql,additive-delta.sql}`.
추출기는 `tests/audit/pg_simulation.mjs`에 보관했다. 운영에 실행하지 않았다.

| 종류 | 현 Postgres 초기화 내용 | 기존 객체/데이터·실패 위험 |
| --- | --- | --- |
| CREATE TABLE | 15개: books, activities, photo_manifest, source_book_state, app_migrations, deletion_page_effect, reading_sessions, profiles, reading_groups, group_members, group_invites, daily_checkins, checkin_reactions, checkin_comments, **reading_chunks** | IF NOT EXISTS는 이름 존재 시 건너뛸 뿐 구조를 보정하지 않음. 부분 표는 그대로 남아 다음 index에서 실패 |
| ALTER TABLE | books.owner_id TEXT, activities.owner_id TEXT, checkin_reactions.emoji TEXT NOT NULL DEFAULT '❤️'를 ADD COLUMN IF NOT EXISTS | 기존 코드부터 존재. 누락됐다면 기존 표를 바꿈. emoji 누락 시 기존 행에도 기본값 의미가 생김. 잠금·권한 실패 가능 |
| CREATE INDEX | 일반12개 + unique1개 =13문장. 신규 chunk3개, 기존 활동3/책2/owner활동1/소그룹멤버1/일일인증1/댓글1/활성타이머 unique1 | 일반 CREATE INDEX, CONCURRENTLY 아님. 누락된 기존 index도 생성 시도. 같은 이름의 다른 정의/invalid 상태는 검증 안 함 |
| 제약·간접 객체 | 각 표 PK/UNIQUE/FK/CHECK/NOT NULL; activities identity sequence; FK 내부 trigger 등 PostgreSQL 자동 객체 | 새 chunk PK와 source_ref UNIQUE가 추가 index2개 생성 → chunk 실제 index5개. chunk FK는 책 삭제를 제한할 수 있고 CASCADE 없음 |
| DROP/DELETE/INSERT/UPDATE | **Postgres schema 문자열에는 없음** | 이것만으로 앱 전체가 읽기 전용이라는 뜻은 아님 |
| 권한/RLS/사용자 trigger | GRANT/REVOKE/CREATE POLICY/ENABLE RLS/CREATE TRIGGER 없음 | 기존 default ACL, 노출 schema, 접속 role에 따른 노출 가능성은 운영 metadata 확인 전 미확인 |
| 연결 후 기존 UPDATE | ownership.py:23,28의 NULL-owner books/activities 갱신 | READDAM_OWNER_EMAIL과 로그인 이메일 일치 시 transaction으로 실행. 실제 NULL 행이 있으면 변경됨 |
| 소그룹 UPSERT | groups.py:28 ensure_profile, groups_ui.py:163에서 호출 | 화면 진입만으로 profiles INSERT/ON CONFLICT UPDATE 가능. 1차-A 신규 변경 아님 |
| chunk DML | reading_chunks.py:204 INSERT, :220 UPDATE, :238 deleted_at/updated_at UPDATE | chunk만 변경. 실제 물리 DELETE는 하지 않음. save가 deleted_at=NULL로 바꾸므로 stale save가 삭제를 되살릴 수 있음 |
| 별도 migration 도구 | migration/load_db.py는 SQLite 파일 삭제 후 재작성, audit_source/migrate_to_supabase는 별도 명시 도구 | 시작 경로에서 자동 호출되지 않음. 이번 배포/감사에서 사용 금지 |

멱등성은 **동일한 완전한 구조 + 순차 실행**에서 제한적으로 확인했다. IF NOT EXISTS는 형상 일치·동시 실행 안전·권한·RLS·데이터 보존 전체를 보장하지 않는다.
각 문장이 autocommit으로 확정돼 뒤 문장 실패 시 앞선 DDL은 남는다. 연결을 닫거나 rollback을 나중에 호출해도 이미 확정된 문장은 되돌아가지 않는다. 자동 rollback 없음. 새 4문장을 명시 transaction으로 묶은 통제 실험에서는 rollback이 가능했다.

## 5. 발견한 문제와 필요한 수정 범위 (미수정)

| ID | 심각도/근거 | 문제 | 필요한 범위 |
| --- | --- | --- | --- |
| AUDIT-01 | 중, SQLite+PG 재현 | 동일 이름의 잘못된 index/부분 표를 init이 검증·교정하지 않음 | 배포 preflight 구조 비교·버전 migration. 임의 교정 금지 |
| AUDIT-02 | 중, 3케이스 재현 | 태그 LIKE가 `%`, `_`를 wildcard로 해석하고 `"` JSON escape를 처리하지 못함 | exact tag 비교/escaping 및 PG·SQLite 동일 테스트 |
| AUDIT-03 | 중, 재현 | 중복 chunkId index 행을 dict가 조용히 하나로 줄임 | index 중복/필드/경로 소유권 검증 후 변경 전 중단 |
| AUDIT-04 | 중, 재현 | DB updatedAt/hash 같으면 손상·수동 변경된 txt를 확인하지 않고 skip | 실제 파일 무결성 확인/충돌 보고 정책; 사용자 편집 무단 덮어쓰기 금지 |
| AUDIT-05 | 높음, fault injection | txt 생성 뒤 index 실패하면 미등록 파일이 남아 재실행이 차단됨 | 임시파일·원자 교체·복구 journal/검증 재개 절차 |
| AUDIT-06 | 높음, 재현 | `_삭제됨`의 8자·12자 대상이 모두 존재해도 마지막 대상에 shutil.move하여 기존 파일 덮어씀 | 모든 이동 목적지 no-clobber 검사/충돌 확장. 테스트 sentinel 내용 실제 교체됨 |
| AUDIT-07 | 중/미확정, AppTest | 같은 세션 수정 직후 삭제에서 제거된 widget 상태 KeyError | 실제 브라우저 재현으로 앱 결함/테스트 도구 한계 판별. 새 세션 수정·삭제는 PASS |
| AUDIT-08 | 높음, 재현+정적 | 다른 book/owner의 기존 chunkId를 save에 전달해도 거절 안 함. get/update/delete는 actor/owner 조건 없음 | actor 기반 owner/book 검증. RLS/권한 변경 필요 여부는 사용자 승인 후 결정 |
| AUDIT-09 | 높음, 재현+코드 | 읽기 전용이어야 할 CLI가 전체 schema 초기화 실행, 전체 owner/chunk 처리 | read-only 전용 연결, TEST/owner/chunk 범위 제한, init와 앱 연결 분리 |
| AUDIT-10 | 높음, fault injection | index를 'w'로 열어 중간 실패 시 기존 목록이 header만 남음 | 원자 index 교체·내구성/동시 exporter 잠금·검증된 백업 |
| AUDIT-11 | 높음, PostgreSQL WASM | NULL 페이지 중복 쿼리의 독립 `$5 IS NULL` 타입 추론 실패(42P18). 명시 타입 control은 PASS | nullable 비교 SQL 수정 및 실제 psycopg/Postgres 테스트 필요 |

추가 정적 위험: DDL RLS 미설정·owner_id는 TEXT NOT NULL일 뿐 사용자 분리 제약이 아님, fallback local-owner 허용, DB role/ACL 미확인. 실제 타 사용자 정보 노출을 운영에서 재현한 것은 아니다.
같은 ID 저장은 SELECT→INSERT/UPDATE이며 atomic upsert가 아니다. 순차 5회는 1행 유지하지만 동시 신규 저장은 PK 오류, 동시 편집은 마지막 쓰기 우선·삭제 부활 가능. 저장 버튼에 명시 disabled 상태 없음. full UUID 12자까지 충돌하는 경우의 자동 복구/동시 exporter/다른 기기 iCloud sync는 보장하지 않는다.

## 6. 시뮬레이션·데이터 보존 결과

운영 데이터는 읽거나 복제하지 않았다. 이름부터 TEST인 독립 합성 데이터다.

| 환경·시나리오 | 결과 |
| --- | --- |
| SQLite 705 books + 5,666 activities + 기타12표 각1행 | 기존14표의 전체 행/컬럼/PK/FK 포함 SHA-256 불변. init3회 + 연결 재개3회, foreign_key_check 빈 결과, integrity_check ok |
| SQLite 빈 DB | 표 생성 없음(기존 설계의 return). 초기 적재 없이 개발용 빈 SQLite에 앱 실행하면 준비되지 않음 |
| SQLite 부분 chunk 표 | 누락 컬럼으로 예상 중단, 기존 데이터 불변, 자동 repair 안 함 |
| 누락 index / 잘못된 동일이름 index | 누락 index는 재생성. 잘못된 정의는 그대로 남음 |
| PostgreSQL 17.5 / PGlite 0.4.6 | 임시 npm prefix에 설치, network DB 연결 없음. 운영 Postgres/PgBouncer/RLS 환경의 완전 복제는 아님 |
| PG 빈 DB | 31문장 성공, chunk22컬럼·index5개 확인 |
| PG 합성 baseline+기존 데이터 | 초기화4회·구 초기화 실행 후14표 checksum 동일 |
| PG 파일 저장 DB close/reopen | 재연결·초기화 후 기존 checksum 동일 |
| PG 중간 index 실패 | table+index3개가 남음, 기존 데이터 불변. 재실행 후5개 |
| PG 명시 transaction 통제 | 중간 실패 후 ROLLBACK하면 신규 표 부재로 복원 |
| PG chunk 제약 | PK, source_ref UNIQUE, FK, NOT NULL, sourceApp CHECK 5종 거절 확인; INSERT/UPDATE/soft delete·구 init 호환 PASS |
| PG NULL 페이지 중복 SELECT | 42P18 재현. 명시 타입 쿼리는 PASS. psycopg wire 바인딩은 미검증 |
| PG 읽기 전용 metadata 통제 | READ ONLY에서 metadata SELECT 성공, CREATE는25006으로 거절(합성 DB만) |
| 기존 owner claim SQL | 합성 NULL-owner book/activity 각각1행 변경 확인. 스키마 migration과 별도 위험 |

PG checksum 예: books `ebc124be4fa4691e18250c4e7019f3f0c8a8ed8b3f03120b47dfaf2f203566f0`, activities `7a43fb64805191a00ca847e1a7aa09ca8acbccfaf69c3f9316bc5c5ba92fa6ab`.
전체14표 증거는 `/tmp/readdam-pg-audit-EnKMvd/report.json`, SQLite fingerprints는 같은 폴더 `pytest.xml`에 있다.
lock/contention, 실제 권한/정책, 확장·event trigger, 운영 Postgres 버전, 백업 복구, 실사용 동시성은 미검증이다.

## 7. 전체 테스트와 실제 iCloud 추가 검증

- 테스트 커밋: `8843b56`, 제품 코드 변경 없음.
- 전체 pytest: **85 passed, 12 xfailed / 97 collected**, 13.01초. 기존65개 + 신규32개(20 PASS,12 엄격 xfail). 경고 없는 재실행 완료.
- `--runxfail` 감사32개: **20 passed, 12 failed**. 알려진 실패를 숨긴 전체 통과가 아니다. strict xfail은 수정 후 XPASS를 실패로 만들어 재검토하게 한다. PG NULL 결함은 별도 Node 시뮬레이션 결과다.
- 추가: 빈 값/NULL/잘못된 날짜·음수·범위/지원하지 않는 타입, 긴 한글·multiline, sourceApp NOT NULL, 같은 ID, 날짜/쪽수 경로 변경, index 없이 파일 존재, 파일 없이 index 존재, 8자 충돌→12자, index 중복/손상/crash, AppTest 수정/삭제.
- iCloud 격리 root: `/Users/donghakim/Library/Mobile Documents/com~apple~CloudDocs/예화창고/_읽담_검증전용_20260927_16680d12`.
- 하위 `독서조각/`에서 신규 TEST 32개로 CLI 별도 프로세스8회 실행. 최초32작성, 동일3회0작성(txt SHA/mtime 동일), 메모·시간변경1작성, 날짜/페이지변경1작성+1이동, soft delete1이동, 최종0작성. 활성 txt31 + `_삭제됨` txt1 + index32행 유지.
- 모든 txt의 chunkId, ISBN/누락 표기, 읽은 시간/누락 표기, sourceApp을 검사했고 index ID/경로/updatedAt/hash와 합성 DB가 일치했다. 한글·특수문자/긴 제목, 긴 multiline 메모, 8자 충돌도 포함했다.
- **기존695개 항목의 mode/size/mtime/ctime/inode 변경·누락0**. 기존 파일 본문은 읽지 않았다(지정된 이전 합성 txt/index만 별도로 해시 확인). 기존 공유 `독서조각/_index.csv`는 열어 쓰지 않았다.
- 증거 `/tmp/readdam-export-audit-e98hzG/report.json`, 합성 SQLite 같은 폴더. 현재 테스트 산출물은 모두 보존. 삭제 승인은 받지 않았다.
- 이 테스트 root는 충돌을 피한 하위 격리 root다. 지정 최상위 root의 운영 공유 index와 혼합, iCloud 원격 동기화, 다른 기기·동시 exporter는 검증한 것으로 간주하지 않는다.

## 8. Definition of Done

PASS는 표에 적힌 검증 범위에만 적용한다. PARTIAL/NOT TESTED/BLOCKED가 남아 전체 완료 불가다.

| 기준 | 상태 | 남은 검증/이유 |
| --- | --- | --- |
| 원본 미커밋2개·기존 산출물 보존 | PASS | 전후 해시 동일 |
| 기능 main/origin 반영 | PASS | 4d97f4e까지, 감사 브랜치는 별도 |
| additive SQL·합성 기존 데이터 보존 | PASS | SQLite/PG WASM; 운영 보증 아님 |
| 운영 schema/columns/index/ACL/RLS 확인 | NOT TESTED | 실제 metadata 미조회 |
| owner별 분리 | BLOCKED | AUDIT-08, 권한 모델 확인 필요 |
| 운영 배포 | BLOCKED | 미승인 + 미해결 결함 |
| 운영 기존 데이터 무변경 대조 | NOT TESTED | 운영 baseline/사후 snapshot 없음 |
| 생성/수정/목록/삭제 | PARTIAL | 합성 서비스·독립 UI 세션 PASS; 연속 UI/NULL PG/운영 미확인 |
| 태그·예화 태그 필터 | BLOCKED | 일반 한글 PASS, 특수문자3종 실패 |
| 콘텐츠 타입/책/ISBN/시간/sourceApp | PARTIAL | 합성 PASS, 운영 DB/txt 미검증 |
| 동일 ID·의미 중복 경고 | PARTIAL | 순차 PASS, PG NULL·동시성 미해결 |
| 실제 iCloud txt 정상 경로 | PASS | 합성 격리 root/이전 root 검증만 |
| export DB 읽기 전용·1건 범위 | BLOCKED | AUDIT-09 |
| 안전한 재export·index·삭제 충돌 | BLOCKED | AUDIT-03~06/10 |
| 운영1건 UI→DB→export→soft delete | NOT TESTED | 운영 작업0건 |
| 기존 회귀 전체/배포 smoke | PARTIAL | 기존65 PASS, 감사 실패12, 운영 회귀 미실시 |
| rollback·GO/STOP 절차 | PASS | 문서 작성·합성 old-code init 호환. 실제 복구 훈련 미실시 |
| 최신 인계·테스트 증거 | PASS | 감사 브랜치 문서·테스트, 운영 완료 기록 아님 |
| 1차-A 최종 완료 | BLOCKED | 위 미완료 전부 해결 필요 |
| 1차-B 진입 | BLOCKED | 명시 금지 유지 |

미완료만 추출: 운영 metadata/권한,11개 감사 이슈의 수정·판정, 동시 저장/동시 export, psycopg 기반 PG 통합, 실브라우저 연속 조작, 제한1건 export, 운영 baseline/사후 무결성, 운영 배포/화면/soft delete/export/index/회귀/복구 확인.

## 9. 1차-B 준비 감사 (구현 없음)

- 선행조건: 1차-A DoD 완료, 사용자 별도 착수 승인, D1 추가3표/workspace chunks/토큰/통계 반영 여부/담당자 확정. 통계에 반영하는 것은 아직 결정되지 않았다.
- 읽담 예상 경로: `lib/reading_chunks.py`의 안전한 수신 upsert/owner 검증, 새 sync 모듈(파일명 미확정), `app.py`의5분 제한·동기화 버튼, `lib/reading_chunks_ui.py`의 책 연결 대기 목록. 통계 반영 승인 시에만 reading/records 계층 검토.
- 오늘의 서재 예상 경로(계획): `db/schema.ts`와 additive migration, `app/api/workspace/route.ts`, `public/library/model.js`·`sync.js`, 책 상세 폼 파일(아직 미확정), 신규 `app/api/readdam/{chunks,receipts,books}/route.ts`. 현재 확인은 문서·파일 존재 목록만이다.
- DB 영향: D1 전용 토큰 지문·receipts·책 스냅샷3표, workspace chunks. Supabase에는 book_id NULL 허용된 조각 수신; 기존 DB/activities 이관 없음. token 원문은 읽담 Secret에만 두며 오늘의 서재는 Supabase 비밀값을 받지 않는다.
- UI 영향: 오늘의 서재 조각 입력/전송상태/수신 후 읽기 전용, 읽담 책 매칭(ISBN→제목+저자→대기). 현 save는 book 필수·source_app readdam 고정이라 그대로 수신용 재사용 불가.
- 테스트 전략: 양쪽 계약 스키마/Unicode/NULL, 같은 ID 재전송·오래된 updatedAt·삭제 재전송, batch부분 실패/receipt 누락 재시도, 토큰 폐기·사용자 분리·권한 거절, D1 revision409·오프라인 재동기화, 책매칭 실패, 통계 중복 방지(승인된 경우), 재export.
- 충돌 위험: 현 save의 무조건 updatedAt 갱신/삭제 부활, actor 없는 조회·수정, 전체 owner export, sourceApp 카드 하드코딩, nullable-page PG 오류, 의미중복 동시성. 먼저 1차-A에서 경계를 확정해야 한다. 1차-B 코드/API/D1/Secret 작업0건.

## 10. 근거와 재현

```bash
# 전부 합성 환경. 아래는 로컬 테스트 명령이며 운영 접속 명령이 아니다.
PYTHON_DOTENV_DISABLED=1 /tmp/readdam-chunk-test/bin/python -B -m pytest -q -p no:cacheprovider
PYTHON_DOTENV_DISABLED=1 /tmp/readdam-chunk-test/bin/python -B -m pytest tests/test_reading_chunks_audit.py --runxfail -q --tb=line -p no:cacheprovider
node tests/audit/pg_simulation.mjs /tmp/readdam-pg-audit-EnKMvd/node_modules/@electric-sql/pglite/dist/index.js /tmp/readdam-pg-audit-EnKMvd/report.json
```

iCloud 스크립트는 자동 pytest에서 실행되지 않으며 `--icloud-parent`, 새 `--scratch`를 명시해야 한다. 재실행은 새 합성 산출물을 추가하므로 필요할 때만 한다. 이번 산출물 삭제 명령은 제공/실행하지 않는다.

참조: [PGlite](https://pglite.dev/docs/), [psycopg transaction/autocommit](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [Postgres READ ONLY](https://www.postgresql.org/docs/current/sql-set-transaction.html), [CREATE INDEX의 IF NOT EXISTS 한계](https://www.postgresql.org/docs/current/sql-createindex.html), [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).
