# 1차-A 운영 Read-only Metadata / Permission Preflight — 접속 전 중단

2026-09-27 / Codex / 사용자 지정 Astra High 유지. 제품 기준 `5148d6f`, 시작 문서 `22f7b1f`, 공동 기록 `f7fe19b`.

**BLOCKED / 운영 NO-GO. 운영 SQL을 한 문장도 실행하지 않았다.** 읽기 전용 점검 승인은 받았지만, 현재 세션에 사용할 수 있는 승인된 운영 연결이 없다. 운영 서버 오류나 schema/권한 불일치를 발견한 것으로 해석하지 않는다.

## 확인한 사실과 미확인 항목

- 읽담 `codex/reading-chunks-1a-fixes`의 작업트리는 시작 시 clean, 제품/문서 커밋과 일치했다. 공동 `f7fe19b`는 별도 저장소의 `codex/reading-chunks-preflight-docs`에 있으며 읽담으로 cherry-pick하지 않았다.
- 현재 프로세스에서 `BOOK_BUTLER_DATABASE_URL`, `SUPABASE_DB_HOST/PORT/USER/PASSWORD/NAME`, `BOOK_BUTLER_DB_PATH`, `PGSERVICE/PGSERVICEFILE/PGHOST/PGPORT/PGUSER/PGDATABASE/PGPASSWORD`는 모두 비어 있거나 미공급이다. **값은 출력하지 않고 설정 여부 boolean만 확인**했다. Cloud 앱의 실제 설정 유무를 확인한 것은 아니다.
- 활성 도구에 Supabase/Postgres connector 없음. `psql`은 현재 PATH에서 발견되지 않았다. 브라우저 제어 inventory도 `apps=[]`, `browsers=[]`다. 브라우저가 컴퓨터에 설치되지 않았다는 뜻은 아니다.
- `.env`·Streamlit Secrets·인증 파일은 읽거나 로드하지 않았다. 환경변수 변경, 비밀값 출력, 임의 자격증명 탐색, DB role 생성/권한 변경, DB 연결 시도 없음. 새 preflight CLI 역시 실행하지 않았다(미설정 상태에서 반복해도 운영 증거를 얻지 못함).
- 따라서 실제 PostgreSQL 버전, endpoint/연결 방식, PgBouncer/Supavisor 여부·pool mode, current_user/session_user, schema/테이블/컬럼/index/constraint, RLS/ACL/GRANT/routine 권한 및 row count는 **전부 NOT TESTED**다.
- books705 / activities5,666은 과거 문서의 비교 기준이다. 현재 운영 count가 아니며, reading_chunks가 없다는 사실도 아직 확인하지 못했다.

## Schema diff 및 최소 DDL 초안: 조건부, 미실행

| 분류 | 로컬 기대 | 운영 대조 결과 |
| --- | --- | --- |
| 이미 존재/정의 일치 | 기존14표의 컬럼/제약, 기존10개 명명 index | 미확인 |
| 신규 추가 필요 | reading_chunks22컬럼, PK/UNIQUE/FK/CHECK, 신규3개 명명 index | 부재 여부 미확인 — 필요하다고 확정하지 않음 |
| 정의 불일치/이름 충돌 | preflight의 실제 index 정의·validity 비교 | 미확인 |
| 권한 확인 필요 | 연결 role, schema/table/routine ACL, 소유권·멤버십, RLS/policy/default ACL | 미확인 |
| 위험한 변경 필요 | 기존 표 ALTER, index 교정, RLS/GRANT 변경 여부 | 미확인 — 어떤 변경도 승인/생성하지 않음 |

기존14표가 정확하고 chunk 표가 없으며 이름 충돌/권한 문제가 없다는 **추후 검증을 전제로만** [Runbook 2절](READING_CHUNK_DEPLOY_RUNBOOK.md)의 표1개 + 일반index3개 CREATE 초안을 재사용한다. 정확한22컬럼/제약 SQL은 해당 절에 있다. 신규 index 대상은 다음과 같다.

- `idx_reading_chunks_book`: `(book_id, deleted_at, read_date DESC)`
- `idx_reading_chunks_owner`: `(owner_id, deleted_at, updated_at DESC)`
- `idx_reading_chunks_duplicate`: `(owner_id, book_id, read_date, page_start, page_end, content_hash)`

PK/UNIQUE의 자동index2개를 포함해 chunk index는5개가 된다. 이미 정확히 존재하면 해당 변경0. 누락index만 있으면 그 부분만 검토한다. 부분 표/다른 정의/기존 구조 변경이 필요하면 즉시 중단한다. **운영 근거가 없어 확정 migration이나 적용용 승인hash는 만들지 않았다.** 기존14표 ALTER·데이터 migration·GRANT/RLS 변경은 이 조건부 초안에 포함하지 않는다.

## Owner claim / profile DML: 코드에서 확인한 위험

- `app.py`는 인증 및 schema 검사 성공 후 `ownership.claim_legacy_library`를 호출한다. `READDAM_OWNER_EMAIL`이 있고 로그인 이메일과 case-insensitive 일치하면 books와 activities 각각의 **owner_id IS NULL 전체 행**을 로그인 ID로 UPDATE하는 transaction을 실행한다. TEST/책1권 범위 제한이나 chunk 전용 조건은 없다.
- `groups_ui.render`는 화면 진입 시 `groups.ensure_profile`을 호출한다. 로그인 user.id의 profiles 행을 INSERT하거나 같은id의 email/display_name을 UPDATE하고 commit한다. 내용이 같더라도 SQL 자체는 UPSERT이며 읽기 전용 화면이 아니다.
- 이번에는 앱을 실행하거나 이 함수를 호출하지 않았다. 운영 NULL-owner 개수, profile 존재/차이, 실제 실행 role 및 RLS 효과를 조회하지 못했다. 운영 영향 행 수를0이라고 추정하지 않는다.
- 두 경로 모두 Reading Chunk 신규 DDL과 독립적인 기존 동작이다. **기존 데이터 무변경을 요구하는 운영 화면 검증의 Blocker로 유지**한다. 먼저 aggregate SELECT로 NULL-owner/관계 위험과 profiles 대상 범위를 확인하고, 변경될 기존 행이 있다면 화면 검증 전에 해당 DML의 분리/명시승인 방식을 별도 결정해야 한다. 지금 코드 수정 필요성을 운영 사실로 확정하거나 임의 수정하지 않는다.

## 재개 조건

사용자에게 비밀번호/DSN을 채팅에 붙여 넣도록 요청하지 않는다. 다음 중 안전한 접근 경로를 사용자/관리자가 마련해야 한다.

1. 기존 승인된 관리 실행 환경에서 앱과 동일한 DB 접속 주체를 사용하고, 비밀값 노출 없이 read-only transaction을 보장하는 연결을 제공한다. 이번 에이전트는 환경변수나 Secrets를 임의로 설정하지 않는다.
2. 또는 사용자가 승인된 SQL client에서 metadata/권한·aggregate count 조회를 수행해 비밀값/원문/개인정보를 제외한 결과를 제공한다. 관리자 계정 결과를 앱 계정 권한으로 대체하지 않는다.

재개 시 첫 SELECT에서 read-only 상태·DB 버전·현재/session role·대상 일치를 확인한다. 구조 확인 뒤 SELECT 권한/RLS·불필요한 함수 호출이 없는 경로인지 확인하고 count/NULL-owner aggregate만 읽는다. 예상 밖 구조·권한·큰 count 차이는 그 시점에서 STOP한다. pool mode는 포트만으로 확정하지 않고 승인된 연결 설정/서비스 metadata 근거로 확인한다. 실제 DDL로 권한을 시험하지 않는다.

이번 승인은 읽기 전용 점검만이다. 연결 경로가 준비돼도 DDL/GRANT/쓰기/테스트 레코드/main merge/push/deploy는 금지다. 점검 완료 후 정확한 최소 DDL·권한·backup 계획을 다시 승인받아야 한다. 1차-A 완료/1차-B 진입도 보류한다.

문서 기록만 변경했다. 제품 코드·환경·운영·iCloud 파일 변경 없음. 읽담 사용자2문서와 공동 dirty PROJECT/WORKLOG SHA-256은 기존 기록과 동일하며 stage하지 않았다. 전체 테스트는 이번에 재실행하지 않았고 이전154 PASS를 현재 운영 검증 결과로 세지 않는다.
