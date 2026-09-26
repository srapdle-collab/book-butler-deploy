# 읽담 작업 기록

이 파일은 **역사 기록**이다. 현재 상태와 다음 행동은 `docs/HANDOFF.md`, 프로젝트 간 공통 결정은 `../CROSS_PROJECT_HANDOFF.md`에 둔다.

기록 규칙 (2026-09-26부터):
- 최신 항목을 맨 위에 추가한다. 제목은 `## <날짜> — <작업자>: <작업명>` 형식이다.
- 최소 항목은 작업 목적, 실제 변경 내용, 테스트 결과, 커밋(브랜치), 배포 여부, 발견 문제, 남은 작업이다. 해당 없음은 "없음"으로 쓴다.
- 과거 항목은 수정하지 않는다. 사실을 보강할 때는 `- 보강(<날짜>, <작업자>):` 줄을 덧붙인다.
- 2026-09-26 이전 항목은 이 규칙 이전 형식이다.

## 2026-09-27 — Codex: Reading Chunk 운영 최소 additive migration 계획

- **목적**: 사용자 제공 운영 read-only 결과를 기준으로 실제 적용 없이 표1/index3의 정확한 SQL과 안전한 순서·중단 조건을 확정했다.
- **자료/판정**: books705/activities5,667 및 두 표 NULL-owner0, chunk 표/index 부재, 기존 RLS 비활성/정책0은 사용자 제공 결과이며 이번 세션 직접 조회하지 않았다. 이전 5,666 기록은 과거 기준으로 보존한다. `public` CREATE 가능만으로 FK REFERENCES·새 표 기본 ACL/anon/authenticated 접근을 증명할 수 없어 운영 NO-GO로 판정했다. 필요 시 새 RLS/GRANT 정책은 별도 결정/승인 대상이다.
- **실제 변경**: [실행 보류 계획](READING_CHUNK_PRODUCTION_MIGRATION_PLAN.md), HANDOFF/PROJECT/Runbook 문서만 갱신. 제품 코드, 기존 데이터·표, 운영 DB, 환경변수, iCloud 파일, 오늘의 서재는 변경하지 않았다. 공동 결정 변경이 없어 CROSS는 수정하지 않았다.
- **검증**: `lib/schema_maintenance`가 생성할 PostgreSQL 4문장과 Runbook SQL을 대조하고 `git diff --check` 및 명시 staged 경로 검사를 수행했다. 실제 운영 SQL/DDL/DML·실행 테스트는 0건; 기존 154 PASS는 앞선 로컬 결과이며 이번에 재실행하지 않았다.
- **커밋/배포**: `codex/reading-chunks-1a-fixes`의 문서 전용 로컬 커밋. main 반영·push·배포 없음. 원본 사용자 소유 기획문서 2개와 공동 dirty 문서의 전후 SHA-256 보존을 확인한다.
- **남은 일/위험**: 생성 role 기본 ACL/Data API 노출, FK 권한·books.id 제약, 전체 이름 충돌, 백업/복원, 운영 role 권한 및 별도 DDL/배포 승인. `public` 신규 표가 Data API에 노출될 가능성은 정책 확인 전 Blocker. 1차-A 미완료·1차-B 진입 금지.

## 2026-09-27 — Codex: 운영 read-only metadata/권한 점검 접속 전 중단

- **목적/승인**: 사용자 지정 Astra High 유지. 운영 metadata/권한/aggregate count 읽기 전용 점검만 승인. 운영 쓰기·DDL·환경변수 변경·main/push/배포는 금지.
- **실제 확인**: 읽담22f7b1f/제품5148d6f 및 별도 공동f7fe19b의 clean worktree 확인. 현재 process의 앱DB/표준PG 설정 존재 여부 boolean만 점검해 모두 미공급/빈 값 확인. 활성Supabase/Postgres connector 없음, psql은PATH에서 발견되지 않음, CUA apps/browsers 빈 목록. Cloud 실제설정 부재로 단정하지 않음.
- **중단**: 승인된 연결 경로가 없어 운영접속/SQL 실행0건. `.env`·Secrets·개인자료 읽기/출력/로드, 환경설정, 사용자 데이터·schema 변경 없음. 보안 경계를 우회해 자격증명을 찾지 않았다. 실제 버전·pool mode·schema·RLS/ACL/role/count 전부미확인,705/5,666은문서상비교기준.
- **분석/문서**: owner claim은 지정이메일 일치 시 두표의NULL-owner전체행 UPDATE, 소그룹화면은 user.id별profileUPSERT임을 코드에서 재확인. 운영대상행수 미확인으로Blocker유지. 최소DDL은Runbook의 표1/index3 조건부초안만 참조,실제필요량/승인hash생성없음. `READING_CHUNK_PRODUCTION_PREFLIGHT.md`/HANDOFF/PROJECT 및 공동별도branch에 중단상태 기록.
- **검증/보호**: 문서diff검사,제품코드변경없음. 테스트재실행없음(기존154PASS는이전로컬결과). 사용자2기획문서 및 공동dirty PROJECT/WORKLOG hash동일. iCloud미접근. 문서만명시stage·별도commit,main/push/배포없음.
- **다음단계**: 사용자/관리자가 기존앱주체의 안전한read-only연결 또는 비밀값을제외한metadata/count결과를 제공해야함. 비밀번호채팅전달 요청안함. 운영NO-GO/1차-A미완료/1차-B보류.

## 2026-09-27 — Codex: Reading Chunk 자동 schema-init 분리 및 read-only preflight

- **목적/범위**: 사용자 확인 Astra High 유지. 일반 앱/로그인/조회/export의 schema mutation 차단과 명시 maintenance 분리. 운영접속/DDL/배포/main/push/사용자 archive/오늘의 서재/1차-B는 금지 범위로 유지했다.
- **Git**: 읽담 시작952c3b3·제품기준038ab2e, 공동b2d9112의 실제 저장소와 ancestry 확인. 제품·테스트 **5148d6f**, 문서는 별도 커밋. `codex/reading-chunks-1a-fixes`에서만 작업, main/origin 로컬ref4d97f4e·deploy51e5b0c 불변, fetch/push 안 함. 공동 기록은 b2d9112 기반 별도 `codex/reading-chunks-preflight-docs` worktree에 작성하여 공동 main도 변경하지 않는다.
- **구현**: db.connect/require_schema 분리, schema.py는 기존DDL 상수만 유지, full initializer는 explicit maintenance 모듈로 이동. SQLite 연결 시 TEXT-kind 변환 삭제·drift STOP.15표/13named index/22chunk컬럼·제약·정의·validity·구조계약v1 검사. read-only CLI와 승인hash 계획/transaction/재검사 기반 좁은 additive CLI 추가. 기존 migration 도구는 import/명시 initializer 호출만 변경, 사용자 데이터 변환 실행 없음.
- **검증**: 전체154 PASS/0 XFAIL(24.17초), 신규preflight30테스트, 기존회귀 모두PASS. AUDIT-01은 같은이름 잘못된index 감지/자동수정금지 기준PASS로 xfail제거. Python63파일compile·Node2개syntax·diff PASS. SQLiteauthorizer의 Python3.9 None해제 차이는 harness수정으로 해결, 최종미해명실패0.
- **PostgreSQL/무결성**: 새Python→PG17.5WASM14시나리오 PASS, READ ONLY·9 drift·AUDIT01·중간DDL전체rollback·4DDL승인/no-op/누락index복구 검증.705책/5,666활동 및 다른12표 각1행의 전체행/컬럼/제약checksum 불변;14표 집계SHA256 `632df820c461f571ad2a4717e0ed8df2500a3d1e1d02e8e8a43f8130634605cd` 전후일치. 기존12시나리오 및 실제Pythonservice CRUD/export/소유권도재검증. 실제Supabase/psycopgwire/PgBouncer/RLS 검증아님.
- **증거/문서**: `READING_CHUNK_SCHEMA_PREFLIGHT.md`, 갱신Runbook/PROJECT/HANDOFF/AGENTS. `/tmp/readdam-preflight-validation-K5XgQm/{pytest.xml,pg-preflight.json,pg-service.json,pg-legacy.json}`. 기존legacy init시뮬레이션의 wrongindex한계는 역사대조로 유지하고 런타임detection PASS와구분했다.
- **보호**: 원본기획문서2개 SHA256 동일(`75fd87c2…1808e9`, `515a448b…86bc`), 공동dirty PROJECT/WORKLOG hash동일. 실제iCloud·기존합성파일 읽기/쓰기없음, 환경설정/의존성설치없음, 공동remote미설정 유지.
- **판정/남은일**: 로컬요구사항GO, 운영NO-GO. preflight는구조검사만이며 기존owner claim/profile DML과 RLS/ACL을 안전하다고 판정하지 않는다. 다음은별도승인된 운영read-only metadata/권한점검. 그뒤정확한DDL/backup·동등staging·main/push/배포·실제화면/export검증 각각승인필요.1차-A완료/1차-B진입보류.

## 2026-09-27 — Codex: Reading Chunk 운영 차단 결함 로컬 수정

- **목적·범위**: 사용자 확인 Astra High 설정 유지. 감사에서 선기록한 owner/book, PG NULL, export 안전성, 특수 태그, 연속 UI 차단 문제를 로컬/격리 환경에서 수정. 운영 배포·Supabase 접속/쓰기/DDL·기존 데이터·환경 설정·사용자 archive·오늘의 서재·1차-B 변경 없음.
- **Git 교차확인**: 읽담 aeecb7f/ae86be2는 main ancestry, 8843b56/6cdc7e7은 감사 브랜치에만 존재. 공동 f4bc698은 별도 저장소 main, cross-repo cherry-pick 없음. 깨끗한 감사 worktree에서 `codex/reading-chunks-1a-fixes` 분기했다. main/origin ref 4d97f4e, deploy ref 51e5b0c 유지, fetch/push 안 함.
- **제품 수정**: 인증 actor 명시 전달/owner 필수/book 관계 대조, UPDATE owner+book+active 조건과 삭제 부활 거절. NULL 비교 CAST, JSON exact 태그 비교. export의 schema-init 없는 read-only snapshot/명시 ID 선택, no-clobber 삭제 보관, 임시 파일·fsync·atomic index, SHA 영수증/journal/로컬 writer 잠금. UI는 callback 요청을 다음 render의 widget 생성 전에 처리한다.
- **테스트**: 27개 신규 pytest + 기존 감사 보강. 전체 **123 PASS/1 strict XFAIL**, 21.34초. xfail12→1, 해소된 감사31개는 runxfail로 PASS. Python53개 compile/Node syntax/diff PASS. 중간의 venv psycopg 미설치, Row 직렬화, 기존 UI 상태 오류는 원인 확인 후 해결했다. 별도 frontend build 없음.
- **PostgreSQL·무결성**: PGlite17.5/0.4.6 기존12시나리오 재실행, NULL4조합 PASS,705책/5,666활동/기존14표 checksum 불변. Python service를 실제 WASM 엔진에 연결하는 추가 harness에서 owner/book 거절·정상 CRUD·태그·read-only 거절·선택 export/삭제 및14표 행 checksum 불변 확인. 실제 psycopg wire/Supabase/PgBouncer/RLS 검증은 아님.
- **Export**: 생성/수정/이동/삭제 중 index 실패→fresh module 재실행, txt/state/index 교체 실패, index 완료 후 옛 파일 정리 실패, 충돌·변조·symlink·동시 writer 등을 임시 sentinel로 검증. /tmp root에서32 TEST/CLI8회, 최종txt32/index32행 유지. 실제 iCloud/기존 합성 산출물은 읽지도 쓰지도 않았다.
- **증거**: `docs/READING_CHUNK_BLOCKER_FIXES.md`, `/tmp/readdam-fix-validation-gkS7kq/{pytest.xml,pg-report.json}`, `/tmp/readdam-export-audit-SXWQN8/report.json`. psycopg 패키지는 이미 요구사항에 있으며 누락된 /tmp 테스트 venv에만 설치했다.
- **커밋/배포**: 제품·테스트 `038ab2e`, 인계/결과 문서는 별도 커밋. main 반영·push·운영 배포 없음. 원본 기획문서2개 및 공동 dirty PROJECT/WORKLOG hash 불변. 공동 CROSS는 깨끗함 확인 후 현 상태만 별도 기록한다.
- **남은 blocker/다음 단계**: AUDIT-01 drift1건은 strict xfail 유지(자동 schema repair 금지). 앱의 기존31DDL init/owner claim 경로는 미변경이므로 앱 init 분리·read-only preflight 범위를 먼저 확정해야 한다. 구형 export byte 검증 실패는 STOP. 이후 별도 승인된 운영 metadata/권한·backup·배포·1건 UI/DB/export/무결성 확인. **운영 NO-GO, 1차-A 완료/1차-B 진입 불가**.

## 2026-09-27 — Codex: 1차-A 운영 배포 전 종합 감사·합성 시뮬레이션
- **목적·안전 경계**: 사용자 후속 승인에 따라 읽기 전용 분석에서 격리 테스트/시뮬레이션/문서화를 확대했다. 운영 배포·Supabase 접속/쓰기/DDL·환경변수 변경·1차-B·기존 사용자 파일 변경은 수행하지 않았다.
- **Git**: `4d97f4e` 문서 3개/23행만 확인 후 origin push, main/origin 일치. 깨끗한 별도 worktree에서 `codex/reading-chunks-1a-audit` 분기. 원본 사용자 작업트리는 cbcf0b4 유지. 공동 저장소 remote는 여전히 없고 593b02c 보존; 감사 도중 추가된 타 작업자 39ed52d도 보존했다.
- **코드 감사**: 배포 diff 12파일(+1051/-1), 제품 5파일. DB wrapper 연결 시 autocommit 31DDL, 전체 rerun과 CLI도 호출. 기존 ownership의 NULL-owner books/activities UPDATE 및 그룹 profile UPSERT를 확인했다. init 신규 차이는 table 1개/index 3개뿐이나 기존 27문장도 재실행된다.
- **시뮬레이션**: 실제 데이터 없이 SQLite/PG17.5 WASM에 705권·5,666기록/기존 14표를 생성했다. 반복 init·재연결·구 init에서 전체 행/컬럼/PK/FK checksum 불변. PG 12시나리오로 빈 DB, 제약 5종, 중간 실패 부분 적용, 재실행, 잘못된 index, 부분 표, 명시 transaction rollback, READ ONLY 제어를 확인했다. 실제 Supabase/PgBouncer/psycopg/RLS/동시성 검증은 아니다.
- **추가 테스트**: `8843b56`은 테스트 3파일만. 전체 **85 passed, 12 xfailed**(기존 65+추가 32), 13.01초. strict xfail을 해제한 감사 테스트는 20 pass/12 fail로 실제 실패를 별도 확인했다. 신규 AppTest 연속 수정→삭제 KeyError는 별도 세션 성공과 구분해 실제 브라우저 판정 대기로 기록했다.
- **발견 문제**: NULL-page SQL 42P18, 사용자/book 경계 누락, 읽기 전용 export의 schema 호출, 특수 태그 3종, index 중복/손상 무검증, txt→index 중간 실패 복구 차단, index 중간 쓰기 truncation, 삭제 목적지 충돌 덮어쓰기, drift 미검증. 제품은 수정하지 않았고 감사 문서 AUDIT-01~11에 수정 필요성을 선기록했다.
- **iCloud 실파일**: 기존 공유 index를 쓰지 않는 `_읽담_검증전용_20260927_16680d12`의 32 합성 chunk로 별도 CLI 8회. 최초 32작성, 무변경 3회 0작성, 내용·분 1갱신, 날짜·페이지 1이동+1갱신, 삭제 1이동, 최종 0작성. txt 32개/index 32행·ISBN/시간/sourceApp/ID/hash 일치. 기존 695항목 lstat 변경·누락 0. 이전 합성 txt/index 및 사용자 2문서 SHA-256도 동일. 테스트 산출물은 모두 보존.
- **증거**: `/tmp/readdam-pg-audit-EnKMvd/report.json`, 추출 SQL 3개, pytest.xml; `/tmp/readdam-export-audit-e98hzG/report.json`·synthetic.sqlite. 테스트 스크립트는 Git에, 개인자료 없는 요약은 감사 문서에 보관한다. 의존성은 /tmp의 PGlite만 추가했고 프로젝트 requirements는 변경하지 않았다.
- **문서·검증**: `READING_CHUNK_PREDEPLOY_AUDIT.md`와 `READING_CHUNK_DEPLOY_RUNBOOK.md`에 전체 감사·DoD·DB 변경 계획·metadata-only SQL·실행 금지 rollback 명령·GO/STOP·수동 UI 체크·1차-B 준비를 기록했다. HANDOFF/PROJECT/CROSS도 상태 기록. compileall/diff 검사 수행. 테스트·문서 커밋 분리, 이번 새 커밋 main 반영/push 없음.
- **남은 일/위험**: 수정 승인 후 release blocker 해결→실제 PG/브라우저 확인→별도 운영 승인→runbook 순서. 현재 1차-A 미완료/1차-B 금지. 공동 PROJECT/WORKLOG의 오래된 내용은 사용자 미커밋이므로 수정하지 않았다.

## 2026-09-26 — Codex: 승인된 검증 기록 push 및 운영 검증 진입 중단
- **목적·승인 범위**: 기존 기록 커밋 검토/push 후, 스키마 변경 없이 가능한 경우에만 운영 검증용 chunk 1건으로 화면·DB·export를 검증한다. 일반 배포·스키마/인덱스 변경·기존 데이터 변경·1차-B는 금지됐다.
- **기록 검토·push**: `431fe44`는 HANDOFF/WORKLOG/PROJECT만 30행 추가·1행 삭제, `92e6d95`는 CROSS만 10행 추가·7행 삭제이며 합성 iCloud 검증 기록 외 변경이 없었다. 읽담 origin/main `54c0d23`에서 `431fe44`로 push하고 원격 SHA를 확인했다. 공동 저장소 `git remote -v` 결과가 비어 있어 `92e6d95`는 push 불가. 원격 추가/변경 없음.
- **운영 진입 점검**: fetch 및 ls-remote로 deploy/main=`51e5b0c` 확인. 배포 소스에 reading chunk 서비스/UI/CLI/스키마가 없다. 브라우저 도구의 앱·브라우저 목록 모두 비어 있으며 운영 URL을 열려는 요청은 `Browser is not available: iab`로 실패했다. 실제 운영 화면/실행 버전은 확인하지 못했다. Supabase 접속·메타데이터 조회는 하지 않았고 운영 표의 부재를 단정하지 않는다.
- **중단 근거·필요 범위**: 배포 소스 기준 실제 UI 검증에는 새 기능 배포가 필요하다. 제품 코드 차이는 `lib/notebook_ui.py`, `lib/reading_chunks.py`, `lib/reading_chunks_ui.py`, `lib/schema.py`, `tools/export_chunks.py`다(나머지는 문서·테스트). 새 앱과 CLI는 DB 연결 시 전체 `ensure_schema` DDL을 자동 실행하므로 제한된 검증 승인만으로 실행하지 않았다. 운영에 없는 경우 필요한 additive 정의는 reading_chunks 22필드, PK/UNIQUE/FK/CHECK와 chunk 전용 3인덱스다. 기존 표/인덱스 DDL도 포함된 초기화 전체 실행은 이번 승인 범위가 아니다.
- **미실행 검증**: 운영 레코드 생성/화면 표시/수정/DB 반영/검색·필터/export/메타데이터/index/재export/soft delete/DB 삭제 확인 모두 미실행. 신규 테스트 레코드와 운영 export 산출물은 없다. 운영 DB 쓰기·DDL·배포 0건; 운영 데이터/구조의 전후 대조 검증은 미실시다.
- **보존 확인**: 원본 기획문서 2개의 SHA-256은 이전 기록과 동일. 기존 합성 txt와 index 해시도 각각 `d5b596055dea2f33f3e736c0a06ae627751012d5affae109c55135c91ef6c915`, `83f927cee4e5148ddd8cf6fcc65557682566ca98d0f757f4af4164eee7fc7ce6`으로 동일. iCloud 파일 쓰기·이동·삭제 없음. 합성 chunk ID `64894842-88d0-48f4-8912-c9b2105b51ad`와 대응 index 행은 운영 테스트로 간주하지 않으며 사용자 정리 결정을 기다린다.
- **실제 변경·검증·커밋**: 제품 코드 변경 없음. 이번 중단 결과만 HANDOFF/WORKLOG/PROJECT 및 공동 CROSS에 기록하여 각 저장소의 로컬 문서 커밋으로 남긴다. diff 검사 수행, 제품 코드 무변경이므로 기존 65개 테스트는 재실행하지 않는다. 이번 새 기록의 push는 하지 않는다.
- **남은 작업**: 공동 원격 목적지 확인, 브라우저 및 안전한 운영 메타데이터 확인 경로 확보, 별도 배포·필요 시 additive 스키마 승인 후 제한된 1건 검증 재개. 1차-A 완료 불가, 1차-B 미진입.

## 2026-09-26 — Codex: iCloud 실경로 txt export·재export 검증
- **작업 목적**: 확정 보관 루트 `/Users/donghakim/Library/Mobile Documents/com~apple~CloudDocs/예화창고`에서 1차-A export의 실제 파일 동작을 검증한다. 기존 예화 카테고리 폴더로 분류하는 2차 export는 범위 밖이다.
- **검증 대상·격리**: main `54c0d23`의 `tools/export_chunks.py`를 수정 없이 CLI로 4회 실행했다. `/tmp/readdam-export-check-Hws0qK/synthetic.sqlite`만 `BOOK_BUTLER_DB_PATH`로 지정하고 dotenv 로딩을 비활성화했다. 운영 DB·사용자 SQLite·인증정보는 사용하지 않았다. 검증용 가상 책 1권과 chunk `64894842-88d0-48f4-8912-c9b2105b51ad` 1건을 만들었다.
- **최초 export**: `독서조각/2026/2026-09/2026-09-26_읽담_검증용_가상도서_p45-52_64894842.txt` 1개와 `독서조각/_index.csv` 1개 생성. 한글·공백이 포함된 iCloud 경로에서 정상 읽기/쓰기 확인. txt UTF-8(BOM 없음)·LF 확인.
- **실제 본문 대조**: 제목 `읽담_검증용_가상도서`, 저자 `검증용 가상 저자`, 합성 ISBN `9780000000002`, 날짜 `2026-09-26`, 범위 `45–52쪽`, 시간 최초 12분→갱신 후 15분, 원문·메모·태그·예화 태그·콘텐츠 타입·chunkId·`출처 앱: 읽담 (readdam)`이 모두 포함됨을 assert로 확인했다.
- **재export**: 1차 결과 `1개 작성`; 동일 데이터 2차 `0개 작성`(txt SHA-256·mtime 불변, index 바이트 동일); 동일 ID의 메모/시간을 수정한 3차 `1개 작성`(같은 경로 내용 갱신, 파일 수 1개 유지); 같은 수정 데이터 4차 `0개 작성`. 자동 번호 증가·중복 파일 생성 없음.
- **index**: 매회 데이터 1행 유지. 상대경로가 실제 txt를 가리키고 chunkId·updatedAt·contentHash가 합성 DB 값과 일치했다. 내용 수정 시 updatedAt/contentHash가 갱신됐으며 예화창고 경로들 필드는 비어 있다.
- **사용자 파일 보존**: 시작 전 `독서조각/`은 없었다. 기존 690개 파일·디렉터리 항목을 lstat로 비교해 누락 0, mode/size/mtime/ctime/inode 변경 0을 확인했다. 기존 파일 본문·해시는 읽지 않았다. 새 독서조각 폴더와 검증용 txt/index만 추가했다.
- **증거**: 일회성 스크립트 `verify_export.py`, `report.json`, 전후 메타데이터 목록은 `/tmp/readdam-export-check-Hws0qK/`에 있다. 최종 txt SHA-256 `d5b596055dea2f33f3e736c0a06ae627751012d5affae109c55135c91ef6c915`. 검증용 txt/index는 사용자 확인을 위해 보존한다.
- **실제 변경·커밋**: HANDOFF/WORKLOG/PROJECT 결과 기록만 변경해 main에서 로컬 문서 커밋한다. 제품 코드·테스트 코드 변경 없음. origin push·deploy push 없음.
- **발견 문제·한계**: 검증한 단일 chunk의 생성/무변경 재실행/내용 갱신에서 결함 없음. iCloud 원격 업로드 및 다른 기기의 동기화 완료는 미검증. 기존 65개 회귀 테스트는 제품 코드 변경이 없어 재실행하지 않았다.
- **남은 작업**: 별도 승인 후 운영 배포·Supabase 표/권한/사용자 분리·기존 데이터 보존·운영 화면 기능 및 운영 DB 기반 export 검증. 1차-A 전체 완료 및 1차-B 진입은 불가하다.


## 2026-09-26 — Codex: 별도 worktree에서 1차-A main 반영·origin push
- **작업 목적**: 사용자 소유 미커밋 기획문서 2개를 그대로 보존하면서, 명시적으로 승인된 main 반영과 origin push만 수행한다.
- **실제 변경 내용**: origin/deploy를 fetch해 양쪽 main과 로컬 main이 `51e5b0c`임을 확인했다. `main..cbcf0b4`의 12개 파일을 검토해 사용자 소유 파일·배포 자동화 변경이 없음을 확인했다. 깨끗한 `/tmp/readdam-main-LIPAnD` worktree에서 main을 `cbcf0b4`까지 fast-forward했다. 기능 수정은 없고 HANDOFF/PROJECT의 현재 상태와 이 기록을 갱신했다.
- **테스트 결과**: 반영 후 전체 pytest **65 passed in 10.04s**, `compileall app.py lib tools`, `git diff --check 51e5b0c HEAD` 통과. 테스트는 별도 임시 SQLite를 사용하며 운영 DB에는 접속하지 않았다.
- **커밋 / push**: 기능 `aeecb7f`, 문서 `ae86be2`, 보완 `cbcf0b4`가 main에 포함됐다. `origin/main`에 `cbcf0b4` push 및 원격 SHA 확인 완료. 이번 상태 문서는 별도 main 커밋으로 origin에도 push한다.
- **배포 여부**: 사용자 지시에 따라 deploy 미러 push와 운영 배포·Supabase 적용은 수행하지 않았다. 원격 `deploy/main=51e5b0c` 확인.
- **발견 문제**: 병합 충돌·테스트 실패 없음. 원본 작업트리는 기능 브랜치와 사용자 소유 미커밋 2개를 그대로 유지한다. 최신 인계 문서는 main worktree에 있다.
- **남은 작업**: 운영 적용 별도 승인 후 표·제약·인덱스·사용자 분리·기존 데이터 무변경 및 운영 화면 생성/수정/필터/soft delete/동일 ID 저장 확인. 보관 루트 확정 후 실제 txt export·재export·`_index.csv` 검증. 1차-A 완전 완료 및 1차-B 진입은 보류한다.

## 2026-09-26 — Codex: Reading Chunk 1차-A 운영 적용 사전 점검
- **작업 목적**: 1차-A 운영 반영 전 문서·구현·원격 상태를 확인한다.
- **실제 변경 내용**: txt export에 ISBN, 읽은 시간, `sourceApp` 코드 표기를 추가했다. 사용자 소유 기획문서 2개는 변경하지 않았다.
- **테스트 결과**: 전체 pytest 65개 통과, Python compileall 및 `git diff --check` 통과. 운영 화면·운영 Supabase·실제 txt 보관 루트는 검증하지 않았다.
- **커밋**: `codex/reading-chunks-1a`의 이번 보완 커밋. 정확한 SHA는 Git 기록을 확인한다.
- **배포 여부**: main 미반영, origin/deploy push 없음, 운영 배포 없음.
- **발견 문제**: `main`·`origin/main`·`deploy/main`은 `51e5b0c`로 일치하지만, 사용자 소유 미커밋 기획문서 2개가 있어 AGENTS.md의 자동 main 반영 안전 조건을 만족하지 않는다. txt 보관 루트도 아직 지정되지 않았다.
- **남은 작업**: 사용자 결정 후 안전한 main 반영, push, 배포, 운영 DB 및 실제 화면·txt export 검증.


## 2026-09-26 — Claude Code: 공동작업 기록 체계 정비 (문서만)
- **작업 목적**: 읽담 ↔ 오늘의 서재 공동작업과 여러 작업자(ChatGPT 사령관·Codex·Claude Code·Work) 간 인계를 추적할 수 있는 기록 체계를 만든다.
- **실제 변경 내용**: `docs/HANDOFF.md`를 신규 작성했다(작성 규칙과 현재 상태). 이 WORKLOG에 기록 규칙을 추가했고, `AGENTS.md`·`CLAUDE.md`를 신규 작성했다(작업 전 HANDOFF 필독, 연동 시 CROSS_PROJECT_HANDOFF 필독, 작업 후 기록 등 8개 원칙). `docs/PROJECT.md`에는 기록 체계와 Reading Chunk 진행상태를 추가했다. 상위 `../CROSS_PROJECT_HANDOFF.md`(동하비서 최상위 저장소)를 신규 작성하고, 오늘의 서재 AGENTS/CLAUDE/HANDOFF/WORKLOG에도 공용 참조를 추가했다(각 저장소에서 따로 커밋).
- **테스트 결과**: 문서 작업이라 테스트를 실행하지 않았다. 1차-A의 스키마 필드와 txt 파일명 규칙이 공통 설계와 일치하는지 코드를 읽어 대조했다.
- **커밋**: `codex/reading-chunks-1a`에 문서 커밋. 기능 코드·스키마·테스트는 변경하지 않았다.
- **배포 여부**: 없음. main 반영·push 없음.
- **발견 문제**: 없음(읽담 쪽). 최상위 저장소 관련 불일치는 공용 계약서가 아니라 최상위 문서 소관이며, 이번 보고에 따로 남겼다.
- **남은 작업**: 1차-A 사용자 검토와 main 반영·운영 적용 승인, 1차-B 담당 지정 (`docs/HANDOFF.md` 참고).

## 2026-09-26 — Codex: Reading Chunk MVP 1차-A
- SQLite·Postgres 초기화에 `reading_chunks`를 비파괴 추가했다. 기존 `books`·`activities`와 activity kind·통계는 변경하지 않았고, `chunk_id`·`source_ref` 유일성·`source_app`·콘텐츠 해시·소프트 삭제·검색 인덱스를 분리해 보관한다.
- 책 상세에 읽은 날짜·페이지 범위 또는 위치·시간·원문·메모·태그·예화 태그·콘텐츠 타입을 갖춘 읽은 조각 입력, 태그 필터 목록, 수정, 소프트 삭제를 추가했다. 읽담에서 새로 만드는 조각은 항상 `source_app=readdam`이다.
- 같은 owner·책·날짜·범위·내용 해시는 자동 병합하지 않고 경고 후 사용자가 `그래도 저장`을 선택할 때만 별도 UUID 조각으로 저장한다. 같은 `chunk_id` 재저장은 같은 행을 갱신한다.
- `tools/export_chunks.py --output-root <보관루트>`는 명시한 루트의 `독서조각/`만 UTF-8(BOM 없음)·LF txt와 `_index.csv`로 관리한다. 변경분만 다시 쓰고, 제목·날짜 변경은 index에 기록된 파일만 옮기며, 소프트 삭제된 조각은 `_삭제됨/`으로 이동한다. 예화창고는 위치·구조가 확인되지 않아 이번 범위에서 건드리지 않았다.
- 검증: 임시 x86_64 가상환경에서 전체 pytest **65개 통과**, py_compile 및 `git diff --check` 통과. 기존 `.venv`는 ARM NumPy와 현재 x86_64 Python의 아키텍처가 달라 사용하지 않았다.
- 운영 Supabase에는 비밀값을 읽지 않는 규칙상 이 세션에서 접속·적용하지 않았다. 배포/앱 시작 시 Postgres `ensure_schema`가 additive 표·인덱스만 생성한다. RLS·통계·기존 데이터·오늘의 서재 코드는 변경하지 않았다.
- 보강(2026-09-26, Claude Code): 커밋 `aeecb7f feat: add reading chunk mvp 1a`, 브랜치 `codex/reading-chunks-1a`. main 반영·push·배포·운영 Supabase 직접 적용은 하지 않았다. 사용자 소유 미커밋 기획문서 2개는 보존했다. 기존 activities 5,666건은 migration하지 않고 신규 chunk부터 공통 규격을 적용한다(`../CROSS_PROJECT_HANDOFF.md` 1.2절).

## 2026-09-20 — Codex: 인용구·메모 공유 통합
- 책 상세, 전체 타임라인, 한 장의 추억에 같은 `공유` 버튼을 적용했다. 책장에서 책을 열어도 같은 상세 진입 경로를 사용한다.
- 버튼을 누르면 복사하기, 메일로 보내기, 문자로 보내기가 펼쳐진다. 인용문/내 생각 또는 단독 메모와 책 제목·저자·페이지·기록일을 포함한다. 카톡은 복사 후 붙여넣기를 안내한다.
- 문자는 RFC 5724 `sms:?body=`를 사용하고 문자열 인코딩·본문 복원을 검증했다. Apple 공식 문서상 메시지 앱 실행은 지원되지만 본문 미리 채우기는 보장되지 않아 화면에 복사 대안을 표시했다. 실물 iPhone Safari 클릭은 현장 기기에서 추가 확인이 필요하다.
- TDD: 새 테스트가 공유 본문/문자 함수·세 화면 버튼 미구현으로 실패한 뒤 구현 후 통과. 전체 pytest/AppTest **35개 통과**.
- 타인 기획문서 수정과 미추적 사본은 그대로 보존했다. 전용 브랜치에 이 작업 파일만 커밋하며 main 병합·원격 push는 하지 않는다.

## 2026-09-20 — Codex: 1단계 통합 검증 완료
- 승인 10개 항목을 구현하고 `docs/STAGE1_REPORT.md`에 기능별 결과/대안/한계를 정리했다. 원본 의미를 향후 변환/적재에도 유지하도록 metadata 경로를 보완했다.
- 브라우저에서 화면을 옮긴 뒤 이전 매초 fragment 요청이 남는 현상을 확인해 초 표시를 브라우저 시계로 교체했다. 시간 계산/저장 기준은 서버 DB이며 새로고침 복구는 유지한다.
- warm theme와 좁은 화면의 4버튼 툴바, 화면 이동 시 맨 위 이동, 잘못된 사진 파일 거절을 보완했다. 타이머 실행 중 상태 변경 차단, 새 상태 이벤트 의미 명시.
- 검증: pytest/AppTest **33개 통과**. 실제 자료 복사본 6개 화면 예외0. 새 변환→임시 DB 적재 705권/5,666건 및 보정 상태/이벤트 집계 일치.
- 실데이터 보존: 기존 활동 11필드 대조 변경0/누락0, 705권/5,666건 및 kind별 개수 동일, 활동 사진 참조 누락0, integrity_check=ok.
- 브라우저: 데스크톱/390px, 타이머 초 표시·새로고침 복구·멈춤·자동 시간 저장 확인. 복사 성공 피드백 확인, 가상 클립보드 제약으로 붙여넣기 내용 대조는 미검증. 외부 메일 앱 발송 없음.
- 완료 코드는 `codex/bookswing-stage1`에 커밋. 타인 기획문서 수정과 미추적 사본은 보존. 공동작업 원칙에 따라 main 자동 병합·원격 push는 하지 않았다.
- 다음: 사용자 실사용 후 피드백. 네이티브 UI/푸시·SNS 확장은 별도 단계. 과거 진도 페이지 편집, 상태 이벤트 직접 삭제 제한은 보고서 참고.

## 2026-09-20 — Codex: 책장과 통계
- 책장/위시리스트/읽는 중 실시간 DB 집계, 읽는 책 6권 미리보기+전체보기, 카테고리 표지와 최근 기록순 정렬.
- 이번 달 일별/올해 월별 기본 통계 및 각각 달력 범위 선택. 한국 시간 기준 무기록일·월 포함, 미래 제외.
- 평균 일수는 양 끝 포함 일수, 월수는 걸쳐 있는 달 수. 초 단위 타이머를 분으로 환산, 소수 첫째 자리 표시. 원본 시작 이벤트를 완독 집계에서 제외.
- 검증: 기간/빈 데이터/한국 시간 경계/원본과 신규 완료/삭제 제외, 책장과 기간 선택 AppTest 4개 통과.

## 2026-09-20 — Codex: 추억과 내보내기
- 무작위 인용구는 새로 선택할 때까지 유지. 책 제목/저자/페이지/한국 시간 기록일을 표시하고 해당 책으로 이동.
- 메일 본문 미리보기/전체 복사/UTF-8 다운로드. 내 생각·단독 메모는 기본 제외하고 선택 시 포함.
- 긴 mailto(인코딩 후 2,000자 초과)는 제목만 열고 전체 복사/파일 첨부 대안 안내. 이 기준이 모든 메일 앱의 보장 한계는 아님.
- 검증: 공유/내보내기·독서 노트 AppTest 5개 통과. 클립보드/메일 앱 외부 동작은 AppTest 범위 밖.

## 2026-09-20 — Codex: 전체 타임라인과 기록 관리
- 책 제목/본문 검색과 유형 필터를 갖춘 전체 최신순 타임라인, 해당 책 이동 추가.
- 인용구/메모/사진 페이지·설명 수정, 진도 시간 수정. 현재 페이지와 일치하는 최신 진도에만 페이지 수정 허용.
- 소프트 삭제 및 복원: 통계 조회에서 삭제 기록 제외, 최신 진도 삭제 시 시작 페이지로 복귀. 사진 파일 보존.
- 수정 중 다른 화면의 변경은 revision으로 감지. 진행 중 타이머와 진도 변경 충돌 차단. 상태/완독 이벤트는 책 관리 전용.
- 검증: 기록 관리 3개 테스트 통과(최신/과거 통계, 현재 진도 복원, 동시 변경 방지, AppTest 수정/삭제/복원/이동).

## 2026-09-20 — Codex: DB 지속 타이머
- 타이머 시작/멈춤/저장/취소를 SQLite에 저장. 페이지 이동·새 Streamlit 세션에서 복구.
- 한 번에 한 세션만 허용. 멈춤 시 시간 고정, 저장 중복 호출은 동일 기록 반환. 수동 진도와 동시 사용 차단.
- 초 단위 원본 보존, 분은 초/60. 현재 진도는 저장할 때만 갱신하며 취소는 기록을 생성하지 않는다.
- 검증: 타이머 단위/AppTest 포함 10개 테스트 통과. 두 연결 간 복구 및 중복 저장 확인.

## 2026-09-20 — Codex: 독서 노트와 입력 폼
- 책 상세를 최신순 기록 카드, 페이지/기록일, 유형 필터로 재구성. 진도·인용구·사진·메모 툴바는 선택한 폼만 연다.
- 인용문+선택적 생각은 kind0, 인용문만 kind2, 메모 kind0, 사진 kind1. 현재 페이지 기본값과 취소, 사진 미리보기 추가.
- DB 확장 스키마는 기존 테이블/데이터를 삭제하지 않고 추가한다.
- 검증: AppTest 7개 통과. 진도/인용구/메모/사진 실제 임시 DB 반영, 카드 최신순, 취소, 책 관리 검증.
- 남은 일: DB 지속 타이머, 기록 관리/타임라인/공유/책장/통계.

## 2026-09-20 — Codex: 원본 의미 대조
- 사용자 승인 10항목 구현 시작. 브랜치 `codex/bookswing-stage1`. 기존 기획문서 수정/미추적 사본 보존.
- 705권/5,666건 원본 대조: 읽는 중35, 완독278, 미독320, 중단72. readingNow는 1권만1. readCount와 kind6 수 705권 모두 일치.
- 상태/생명주기 의미를 정정하되 숫자 kind·ID·본문·사진은 보존. 원본 의미와 새 앱 이벤트 의미 분리.
- SQLite 백업 `data/backups/before-stage1-20260920-151840.db` 후 원본에서 온 행만 보정. integrity_check=ok.
- 검증: 상태 판정과 멱등 보정 테스트. 근거/역추론 한계는 SOURCE_AUDIT.md.
- 남은 일: 독서 노트, 지속 타이머, 수정/삭제, 공유/책장/통계와 AppTest. 원격 push 없음.

## 2026-09-20 — Codex: 읽담 이름과 표지 격자 책장
- 사용자에게 보이는 앱 이름을 `읽담`으로 바꿨다. 저장소·폴더·DB 이름과 기존 기획문서 파일명은 유지했다.
- 책장을 4열 표지 격자로 바꾸고, 표지 전체를 누르면 책 상세로 이동하게 했다. 표지가 없으면 제목을 넣은 플레이스홀더를 보여 준다.
- 카테고리 구분을 유지하면서 각 카테고리 안에서는 최근 기록순으로 채워 격자가 듬성듬성해지지 않게 했다. 한 번에 24권(최대 4열×6행)만 SQLite에서 가져오며, 실제 705권은 30쪽으로 나뉜다.
- 검증: AppTest 집중 6개 통과. 실제 705권 DB의 브라우저에서 4열 표지 격자, 표지 클릭→책 상세 이동, 첫 화면 약 0.46초·다음 쪽 약 0.28초를 확인했다.
- 원격 push와 main 반영은 하지 않았다. 사용자 기획문서의 미커밋 변경과 미추적 사본은 보존했다.

## 2026-09-20 — Codex: 북스윙식 독서 노트와 좁은 화면 책장 보완
- 책 상세 기록을 종류별 구획 없이 최신순 단일 타임라인으로 다듬었다. 왼쪽에는 굵은 큰 페이지 번호, 오른쪽에는 인용·메모·진도 본문과 기록일을 배치했다.
- 인용문에는 화면용 따옴표를 추가하지 않고 원문 그대로 표시한다. 진도 문장 `OO쪽을 OO분 동안 읽었습니다`는 유지했다. 본문이 없는 시작·완독·중단 이벤트도 비어 보이지 않게 문장으로 표시한다.
- 좁은 화면에서 책장 4열이 한 줄씩 세로로 풀리던 문제를 해결했다. 이어 읽기와 책장 모두 표지가 4열로 유지된다.
- 검증: 독서 노트 AppTest 3개 통과, 실제 390px 모바일 화면에서 4열 책장 및 페이지-본문 카드 레이아웃을 확인했다.

## 2026-09-20 — Codex: 책장 표지 크기 통일
- 원본 표지 이미지의 제각각인 가로세로 비율 때문에 격자 행이 무너지던 문제를 수정했다. 모든 표지는 2:3 프레임을 채우며, 비율이 다른 이미지는 카드 안에서 잘려 보인다.
- 실제 4열 책장 화면에서 모든 카드가 같은 204×306px 프레임으로 표시되는 것을 확인했다.
- 검증: 관련 AppTest 6개 통과.

## 2026-09-20 — Codex: 공유 출처에서 기록일 제외
- 한 장의 추억과 복사·메일·문자 공유 본문에서 기록일을 제외했다. 인용문/메모, 책 제목·저자, 페이지 정보만 공유한다.
- 검증: 공유 AppTest 5개 통과.

## 2026-09-20 — Codex: 전체 카테고리 책장과 기록 검색
- 책장 기본값 `전체`는 페이지로 자르지 않고 705권을 카테고리별 표지 격자로 연속 표시한다. 카테고리·상태·제목/저자 필터는 그대로 유지한다.
- 타임라인 검색은 인용구·메모 본문과 책 제목·저자를 함께 찾는다. 결과에는 페이지와 책 제목·저자가 보이고, `해당 책으로 이동`으로 상세 독서 노트로 이동한다.
- 검증: 전체 39개 테스트 통과. 실제 DB에서 `로마서` 검색 90건, 결과의 페이지·출처 표시 및 첫 결과에서 해당 책 상세 이동 확인.
- 사용자 기획문서의 미커밋 변경과 미추적 사본은 보존했다. 원격 push는 요청 대기 상태다.

## 2026-09-20 — Claude: 클라우드 배포용 Supabase 인프라 준비 (인계)

**배경**: 사용자가 "컴퓨터를 꺼도 폰에서 기록할 수 있게" 클라우드 배포를 요청. Streamlit
Community Cloud는 디스크가 일시적이라 지금의 로컬 SQLite(`data/book_butler.db`)를 그대로
올리면 재배포·슬립 후 새 기록이 사라질 위험이 있음을 확인하고, 사용자와 상의해 Postgres
(Supabase)로 이전하기로 결정했다.

**완료한 일**:
- Supabase 프로젝트 `bookbutler-prod` 신규 생성 (ref `xsworhnixixaorjwiswx`, 서울 리전
  `ap-northeast-2`, 조직은 하루쑥과 동일한 `cpsxhaorakxyplkkhbih`, 무료 티어).
- `.env`(git 추적 제외)에 접속 정보 저장: `SUPABASE_URL`, `SUPABASE_ANON_KEY`,
  `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_PASSWORD`, `SUPABASE_DB_HOST`(커넥션 풀러,
  transaction 모드 6543 포트), `SUPABASE_DB_PORT`, `SUPABASE_DB_USER`, `SUPABASE_DB_NAME`.
  풀러 호스트로 접속 테스트(6543/5432 둘 다) 성공 확인. DB는 아직 빈 상태(스키마 없음).
- `.venv`에 `psycopg[binary]` 설치 확인(연결 테스트용). requirements.txt에는 아직 미반영.

**막힌 지점 (코덱스에게 인계)**: SQLite→Postgres 전환이 연결 문자열 교체 수준이 아니라
동시성·잠금 로직을 다시 설계해야 하는 작업임을 확인했다. 원 코드(특히 최근 작업물)에
SQLite 전용 패턴이 깊이 박혀 있음:
- `rowid` 암묵 컬럼 의존 (`lib/records.py`, `lib/record_ui.py`) — Postgres엔 없음, 명시적
  순번 컬럼(예: `id`가 UUID뿐이라 정렬용 시퀀스 필요) 설계 필요.
- `conn.execute('BEGIN IMMEDIATE')` 잠금 (`lib/records.py`, `lib/reading.py`) — 타이머
  동시 실행 차단, 기록 삭제 시 진도 페이지 되돌리기 로직이 이 잠금에 의존. Postgres
  트랜잭션/행 잠금(`SELECT ... FOR UPDATE`)으로 재설계 필요 — 원래 의도(동시 변경 충돌
  방지)를 정확히 이해하고 옮겨야 안전함.
- `INSERT OR REPLACE` (`lib/records.py`) → `INSERT ... ON CONFLICT DO UPDATE`.
- `PRAGMA table_info`, `sqlite_master` (`lib/schema.py`) → `information_schema.columns`/
  `information_schema.tables`.
- `?` 플레이스홀더 → `%s`. 직접 SQL을 쓰는 파일: `lib/db.py`, `lib/records.py`,
  `lib/record_ui.py`, `lib/reading.py`, `lib/shelf_ui.py`, `lib/sharing.py`,
  `lib/sharing_ui.py`, `lib/notebook_ui.py`(`pd.read_sql_query` 포함), `lib/schema.py`,
  `migration/load_db.py`, `migration/audit_source.py`.
- `pd.read_sql_query(query, conn)`가 여러 곳에서 쓰이는데, psycopg 연결에 그대로 넘기면
  파라미터 스타일 문제가 생길 수 있어 확인 필요.

**아직 안 한 일**:
- 사진(`migration/output/photos/`, `data/photos/`, 총 762장 이상)을 Supabase Storage로
  올리는 마이그레이션 스크립트.
- 기존 로컬 DB(705권/5,666건 + 최근 기록)를 새 Postgres로 옮기는 1회성 데이터 이관.
- Streamlit Community Cloud 앱 생성·시크릿 등록(기존 GitHub `srapdle-collab/book-butler`
  저장소는 이미 연결돼 있음, private 저장소 + 초대 전용 뷰어로 주식비서와 동일 패턴 권장).
- `requirements.txt`에 Postgres 클라이언트/Supabase Storage 클라이언트 추가.

사용자 승인 없이는 원격 push·main 반영을 하지 않았다(이번 세션은 로컬 작업만).

## 2026-09-20 — Codex: Supabase 지속 저장 전환
- SQLite와 Supabase Postgres를 함께 지원하는 DB 호환 계층을 추가했다. Postgres에서는 UUID와 별도 `position` 시퀀스로 SQLite `rowid` 정렬 의미를 보존한다.
- 기록 수정·삭제·복원과 단일 타이머는 Postgres 트랜잭션, 행 잠금, 트랜잭션 범위 advisory lock으로 이전했다. PgBouncer transaction pool에서 prepared statement 충돌이 나지 않도록 비활성화했다.
- private `book-photos` Storage 버킷을 쓰는 사진 어댑터를 추가했다. 배포 시에는 짧은 만료의 서명 URL로만 표지·기록 사진을 제공하며, 새 사진도 Storage에 저장한다.
- `migration/migrate_to_supabase.py --apply --verify`로 원본 SQLite를 이관했다. 검증 결과: books 705, activities 5,667, photo_manifest 762, source_book_state 705, app_migrations 1, reading_sessions 1이 원본과 일치했고 사진 762개를 업로드했다. 기록 사진 참조는 57개다.
- 실제 Supabase에서 목록→책 상세→활동 조회와 표지·기록 사진 서명 URL 발급을 확인했다. 자동화 테스트는 47개 통과했다.
- `main`에 이전 코드를 push했다. Streamlit Community Cloud 배포 화면은 공개 앱만 제공하므로, 요청한 초대 전용 조건을 지키기 위해 공개 배포와 Cloud secrets 등록은 보류했다. 비공개 앱을 지원하는 Streamlit Teams 또는 별도 인증 프록시가 필요하다.

## 2026-09-21 — Codex: 공개 배포용 앱 비밀번호 관문
- Community Cloud의 공개 앱 정책에 맞춰 앱 시작 직후 비밀번호 관문을 추가했다. `BOOK_BUTLER_APP_PASSWORD`는 로컬 `.env` 또는 Cloud Secrets에서만 읽으며 코드와 Git에는 저장하지 않는다.
- 비밀번호가 맞기 전에는 책장·기록·통계 등을 렌더링하지 않고 중단한다. 성공하면 세션 상태에만 인증 결과를 보관해 같은 세션에서는 다시 묻지 않는다.
- 검증: 비밀번호 미입력/오입력 시 앱 본문 비노출, 정답 입력 후 책장 노출 및 세션 유지 AppTest를 포함해 전체 48개 테스트 통과.
- `main`에 비밀번호 관문 코드를 push했다. Cloud Secrets에 넣을 실제 `BOOK_BUTLER_APP_PASSWORD` 값이 아직 로컬 `.env`에 없어 공개 배포와 실서비스 검증은 대기한다.

## 2026-09-21 — Codex: 공개 배포 미러와 비밀번호 보호 서비스
- 비공개 원본 `srapdle-collab/book-butler`는 그대로 보존하고, Streamlit 배포 전용 공개 미러 `srapdle-collab/book-butler-deploy`를 새로 만들었다. Cloud 앱은 이 공개 미러의 `main`과 `app.py`에 연결했다.
- 배포 주소: `https://read-dam-book-butler.streamlit.app/`. Supabase 접속 정보와 앱 비밀번호는 로컬 `.env` 및 Streamlit Cloud Secrets에만 등록했다.
- 실제 공개 브라우저에서 비밀번호 입력 전에는 잠금 화면만 보이고, 잘못된 입력은 차단되며, 올바른 입력 후에는 Supabase의 책장(705권)이 표시되는 것을 확인했다.
- `.env`, `data/`, `migration/output/`은 Git ignore 상태를 다시 확인했고, 공개 미러에도 비밀값·DB·사진이 추적되지 않는다.
- 이후 배포 갱신은 private `main`을 검증·push한 뒤 `git push deploy main`으로 수동 반영한다. 공개 미러에 비밀값이나 로컬 데이터 파일을 추가하지 않는다.

## 2026-09-21 — Codex: 계정별 개인 서재와 소그룹 1차 구현
- Supabase Auth 이메일 회원가입·로그인 관문을 추가했다. Auth 설정이 있으면 로그인 전에는 앱 본문을 렌더링하지 않으며, 로컬 비밀번호만 쓰는 기존 환경은 유지한다.
- `READDAM_OWNER_EMAIL`과 로그인 이메일이 일치할 때만 기존 705권 서재와 활동을 해당 계정의 `owner_id`로 한 번 연결한다. 다른 계정은 개인 서재 메뉴에 접근하지 못하고 소그룹 화면만 사용한다. 새로 추가하는 책과 그 책의 활동은 소유자 정보를 이어받는다.
- 소그룹 데이터 구조(프로필, 그룹·멤버, 1회용 초대, 일일 인증, 좋아요, 댓글)를 SQLite·Postgres 양쪽에 추가했다. 피드에는 명시적으로 선택한 인용구/사진의 스냅샷만 저장해, 개인 원본 기록이나 전체 책장은 그룹에 노출하지 않는다.
- 화면에서 소그룹 생성, 1회용 초대 링크 생성·참여, 오늘 읽기 체크와 한줄소감, 개인 인용구/사진 선택 첨부, 오늘의 시간순 피드, 좋아요와 댓글을 제공한다.
- 검증: AppTest로 인증 전 차단·소유자 서재 접근·소그룹 생성·오늘 인증 저장을 확인했고, 전체 테스트 56개를 통과했다.
- 남은 일: Supabase Auth의 이메일 확인/리디렉션과 `READDAM_OWNER_EMAIL`, `READDAM_APP_URL`을 Cloud Secrets에 설정한 뒤 실서비스에서 회원가입·두 계정 초대·피드 확인. 이 작업은 원격 push·배포 요청 전까지 로컬 브랜치에만 있다.

## 2026-09-22 — Codex: 회원가입 화면 전환 오류 수정
- 회원가입 버튼의 위젯 키 `show_sign_up`을 상태값으로 직접 바꾸면서 발생하던 Streamlit 예외를 수정했다. 버튼 콜백이 별도 상태 키 `signup_mode`를 설정하도록 분리했다.
- 검증: AppTest에서 로그인 화면 → 회원가입 버튼 → 표시 이름·가입 버튼 노출 전환을 재현했고 예외 없이 통과했다. 전체 테스트 57개 통과.

## 2026-09-22 — Codex: 소그룹 오늘 점검과 이모티콘 반응
- 소그룹 첫 화면에 구성원 전원의 오늘 인증 현황을 추가했다. 인증 완료 수와 구성원별 `읽었어요`·`소감 남김`·`아직` 상태를 표시한다.
- 날짜마다 동일하게 바뀌는 짧은 `오늘의 독서 문장`을 소그룹 상단에 표시한다.
- 기존 좋아요 하나를 ❤️·👏·🔥·💡 반응 선택으로 확장했다. 한 사람은 하나의 반응만 남길 수 있고, 같은 반응을 다시 누르면 취소되며 다른 반응을 누르면 교체된다.
- 기존 반응 테이블에는 `emoji` 열을 비파괴적으로 추가해 SQLite와 Supabase Postgres 모두에서 기존 좋아요를 ❤️로 보존한다.
- 검증: 소그룹 서비스·스키마·날짜 문장·AppTest를 포함한 전체 테스트 59개 통과.

## 2026-09-22 — Codex: 소그룹 기능 main 반영 및 공개 배포
- `codex/small-groups`를 `main`에 병합했다. 사용자의 기획문서 미커밋 변경과 미추적 사본은 그대로 보존했다.
- private 원본 `origin/main`과 공개 배포 미러 `deploy/main`에 같은 main 커밋을 반영해 Streamlit Community Cloud 재배포를 시작했다.
- 실제 `https://read-dam-book-butler.streamlit.app/`에서 임시 계정 로그인, 개인 서재 비노출, 소그룹 생성과 오늘 인증 저장을 확인했다. 화면에 오늘 점검, 오늘의 독서 문장, ❤️·👏·🔥·💡 반응 버튼이 표시됐다.
- 배포 점검용 Supabase 계정·그룹·인증·반응 데이터는 테스트 후 삭제했다. 전체 자동화 테스트 59개 통과.
