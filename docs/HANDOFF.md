# 읽담 — 현재 인수인계 (HANDOFF)

이 파일은 **현재 상태와 다음 행동**만 적는다. 상세한 경과·진단·테스트 내역은 `docs/WORKLOG.md`에 둔다. 두 파일의 역할을 섞지 않는다.

## 작성 규칙

- 사용자(David)·ChatGPT 사령관·Codex·Claude Code·Work가 번갈아 작업하므로 모든 작업을 공동작업으로 간주한다.
- 다음 작업자는 작업 시작 전에 이 파일의 **최신 항목(맨 위)**부터 읽는다.
- 새 항목은 "항목" 구분선 바로 아래, 기존 항목들 위에 추가한다. 끝난 항목은 지우지 않는다. 다만 새 항목이 이전 상태를 대체하면 첫 줄에 그 사실을 적는다.
- 제목 형식: `## <다음 작업자>가 이어받을 작업 — <한 줄 요약> (<날짜>, <작성자>)`. 다음 작업자가 없으면 `## 최신 — <요약> (<날짜>, <작성자>)`.
- 각 항목에 반드시 아래 칸을 채운다. 해당 없음은 "없음"으로 쓴다.
  - **무엇을 했는지**
  - **어디까지 끝났는지**: 로컬 커밋만 / main 반영 / push / 배포 / 운영 확인을 구분한다. "커밋했다"와 "배포했다"를 섞지 않는다.
  - **확인해야 할 것**
  - **다음 작업자**
  - **브랜치** / **커밋** / **배포 상태**
  - **보류·실패·중단 이유**
- 프로젝트 간 연동(오늘의 서재 등)에 관한 결정은 `../CROSS_PROJECT_HANDOFF.md`에도 반영한다.

---

## 항목

## 사용자(David)/읽담 담당 Codex가 이어받을 작업 — 공동 상태 정합화 완료, 제품 main 반영·배포 승인 대기 (2026-09-27, Codex)

- **무엇을 했는지**: 공동 최신 `bf9ca9a`를 계승한 `codex/reading-chunks-current-state`의 **32cfc48**과 두 앱 문서를 대조·정합화했다. 공동 정본은 `/private/tmp/readdam-cross-current-gJs4x6/CROSS_PROJECT_HANDOFF.md`1.0절이며, 공동 저장소에서 `git show 32cfc48:CROSS_PROJECT_HANDOFF.md`로도 조회한다. 기본 공동 main의 상대경로 사본과 원본 읽담 `codex/reading-chunks-1a` 문서는 과거 스냅샷이다. 아래 `b23e316`의 문서 충돌에 의한 NO 판정을 이 최신 항목으로 대체한다.
- **어디까지 끝났는지**: **DB migration 완료 / 제품 main 반영·배포 전**. 운영 권한 프리플라이트(postgres/default ACL 위험)·보안설계·dry-run9DDL·백업·migration SUCCESS·후속 post-check 완료는 `bd04762`/`b23e316`의 확인 결과다. 구조·index3·PK/FK/UNIQUE/CHECK 정상, RLS on/policy0, PUBLIC/anon/authenticated/service_role CRUD=false, postgres=true. books705/activities5,667/owner NULL0, 기존 schema 예상 밖 변화 없음. 이번에는 운영 DB/테스트를 재실행하지 않고 문서만 로컬 커밋한다.
- **확인해야 할 것**: 이전 기술 검증157PASS/compile/syntax/diff PASS와 문서 정합화에 따라 **main 반영 준비 YES / 운영 배포 준비 YES(별도 실행 승인 필요)**. 1차-A는 M1 실검증 전이므로 완전 종료가 아니다. 실행 직전 ref·사용자 파일 해시·운영 상태를 다시 확인하고, 적용 완료된 migration은 재실행하지 않는다.
- **다음 작업자/순서**: David의 별도 승인 후 Codex가 깨끗한 worktree에서 최신 제품 main 반영 → origin/main 동기화 → deploy/main 반영 → Streamlit 배포 SHA 확인 → M1 Safari Reading Chunk CRUD/재접속/기존 기능 및 Data API anon 차단 재확인. txt는 별도 승인된 격리 로컬 경로 계획만 유지한다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunks-private-default`, 시작 `b23e316`; 제품 코드 `4362e8c` 불변, 이번에는 문서3개만 추가 커밋. main/origin=`4d97f4e`, deploy=`51e5b0c` 유지. 오늘의 서재 `9569cfd`의 2차 매핑 추천안은 기존 설계이며 이번에 구현 승인하지 않는다.
- **보류·금지**: 문서 충돌은 해소됐고 main/push/deploy/실제 CRUD는 별도 승인 대기다. **1차-B·Reading Chunk 2차 export·실제 iCloud export 금지**. 제품 코드·DB·사용자 기획문서 수정 없음, 과거 기록 삭제 없음.

## 사용자(David)/공동 문서 담당자가 이어받을 작업 — 배포 전 기술 검증 PASS, 공동 현재 상태 불일치로 준비 판정 보류 (2026-09-27, Codex)

- **무엇을 했는지**: main/origin `4d97f4e`, deploy `51e5b0c`, 제품 브랜치 `codex/reading-chunks-private-default`의 시작 HEAD `bd04762` 관계를 확인했다. 제품 브랜치는 main보다 13커밋, deploy보다 19커밋 앞선 단일 후손이다. main에는 `cbcf0b4`까지 초기 기능이 있고 `038ab2e`/`5148d6f`/`4362e8c` 수정은 없다. 이번 결과 기록은 후속 문서 커밋으로 추가한다.
- **어디까지 끝났는지**: 운영 REPEATABLE READ/READ ONLY 연결로 구조계약 OK, RLS on, policy0, 외부4주체 CRUD=false, postgres CRUD=true를 재확인했다. books705/activities5667/owner NULL0/chunk0, 기존 schema fingerprint 불변, maintenance 계획0문장. 전체157 PASS, Python63파일 compile·Node2파일 syntax·diff PASS. 제품 코드 변경 없음.
- **확인해야 할 것**: 공동 main `b2d9112`의 CROSS_PROJECT_HANDOFF는 운영 미적용/자동 init 잔존 상태이고, 더 최신 공동 브랜치 `codex/reading-chunks-preflight-docs`의 `bf9ca9a`도 운영 접속 전 중단 상태다. 읽담 최신 운영 적용 기록 `bd04762`와 현재 상태가 불일치한다. 사용자 지정 중단 기준에 따라 main 반영/운영 배포 준비 판정은 NO이며, 공동 문서를 임의 갱신하거나 main에 반영하지 않았다.
- **다음 작업자**: 공동 문서 담당자가 기존 미커밋 작업을 보존하며 최신 운영 적용·이번 검증 근거로 공동 현재 상태를 정합화한다. 이후 별도 승인 시 깨끗한 main worktree에서 제품 브랜치를 `git merge --ff-only codex/reading-chunks-private-default`로 반영하고 origin, deploy 순으로 동기화한다. 원본 사용자 작업트리는 사용하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: 제품 코드는 `4362e8c`와 동일; 이번 변경은 HANDOFF/WORKLOG 기록만 로컬 커밋. main/origin/deploy 유지, merge/push/deploy·실제 CRUD·iCloud 실행 없음. 사용자 기획문서2개 전후 SHA-256 동일, 두 문서의 미커밋 내용 및 임시 산출물은 merge diff에 없다.
- **보류·실패·중단 이유**: 기술 검사 실패가 아니라 공동 현재 상태의 Source of Truth 불일치다. 배포 후 smoke는 M1 Streamlit/Safari 책 목록·활동 → TEST chunk 생성/수정/검색 → 재접속 유지 → 선택 txt export(ISBN/읽은 시간/sourceApp) → 소프트 삭제 → 기존 기능 회귀 → Data API anon 차단 순서로 계획한다. txt는 승인된 격리 로컬 경로를 사용하며 iCloud 2차 export는 제외한다. 이번에는 실행하지 않았다.

## 사용자(David)가 이어받을 작업 — 운영 migration 성공, 앱 코드 main 반영·배포는 별도 승인 (2026-09-27, Codex)

- **무엇을 했는지**: 운영 `public` 전체를 custom-format으로 사전 백업하고 archive list/schema/data 추출을 검증했다. 직전 dry-run의 정확한9DDL·plan SHA `166d02b0…5961`을 재확인한 뒤 후보 `4362e8c`의 승인된 maintenance CLI로 단일 transaction 적용했다.
- **어디까지 끝났는지**: 운영 `reading_chunks` 표와 명명 index3개가 생성됐다. PK/FK/UNIQUE/CHECK 검증, RLS on, policy0, `PUBLIC`/`anon`/`authenticated`/`service_role` CRUD=false, `postgres` CRUD=true. chunk 행0. books705/activities5667/owner NULL0 및 기존 schema fingerprint `4f6b9306…1e6189` 불변. post-check PASS.
- **확인해야 할 것**: 사전 백업은 `/private/tmp/readdam-prod-backup-dag4jwb6/public-before-reading-chunks.dump`(SHA-256 `1e601cd1…ff0be`, mode0600)에 있다. archive 추출 검증은 했지만 별도 DB restore rehearsal과 장기 보존 위치 이동은 하지 않았다. 기존 public 표 ACL/RLS는 범위 밖으로 불변이다.
- **다음 작업자**: David가 제품 브랜치의 main 반영·Streamlit 배포를 별도로 승인한 뒤 읽담 담당자. 그 전에는 화면 CRUD/iCloud export를 하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: 제품 `4362e8c`, 작업 브랜치 `codex/reading-chunks-private-default`; 운영 DB migration만 적용. main/origin=`4d97f4e`, deploy=`51e5b0c` 불변. 미push·앱 미배포.
- **보류·실패·중단 이유**: migration blocker 없음. 앱 코드는 아직 운영 배포되지 않아 1차-A 화면 운영 검증은 미실행이다. 1차-B·2차 export 금지 유지.

## 사용자(David)/운영 담당자가 이어받을 작업 — 운영 dry-run 9DDL·plan SHA 확정, 실제 적용 별도 승인 대기 (2026-09-27, Codex)

- **무엇을 했는지**: 후보 `4362e8c`의 실제 maintenance CLI를 운영과 동일한 `SUPABASE_DB_*` 설정으로 `--apply` 없이 실행했다. 문서화된 운영 프로젝트, transaction pooler 6543, SSL, DB=`postgres`, schema=`public`, current/session user=`postgres`, PostgreSQL17.6, `transaction_read_only=on`을 비밀값 없이 확인했다.
- **어디까지 끝났는지**: 계획은 table1→index3→RLS→PUBLIC/anon/authenticated/service_role REVOKE의 정확한9DDL이며 예상 밖 SQL0. plan SHA=`166d02b0682da839a0caae3ad096fdf3b854974db3e4075c47fff6be846b5961`. 두 독립 read-only 연결과 실제 CLI 결과가 동일했다. 전후 reading_chunks/index/ACL/RLS 객체0, books705/activities5667/owner NULL0, public schema fingerprint `4f6b9306…1e6189`가 동일했다. 운영 DDL/DML0.
- **확인해야 할 것**: 이 SHA는 현재 운영 metadata와 후보 코드에 종속된다. 실제 적용 직전 다시 dry-run하여 동일하지 않으면 STOP한다. 백업/복원, maintenance 창, 실제 migration 실행은 별도 승인이 필요하다.
- **다음 작업자**: David가 백업과 실제 migration 적용 범위를 별도로 승인한 뒤 운영 담당자. 승인 전 `--apply` 금지.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunks-private-default`; 제품 `4362e8c`, 기존 문서 `117d8c8`, 이번 dry-run 기록은 후속 로컬 문서 커밋. main/origin=`4d97f4e`, deploy=`51e5b0c` 불변. 미push·미배포.
- **보류·실패·중단 이유**: dry-run blocker 없음. 다만 실제 migration·backup·배포 승인은 아직 없으므로 **운영 적용은 수행하지 않았고 1차-A 운영 미완료/1차-B 금지**다.

## 사용자(David)/운영 담당자가 이어받을 작업 — 비공개 기본 migration 후보 검토·운영 적용 별도 승인 (2026-09-27, Codex)

- **무엇을 했는지**: 운영 read-only 프리플라이트에서 앱 DB 주체 `postgres`, 신규 public relation의 외부 role 기본 GRANT 위험, 기존 Data API 노출을 확인한 결과를 반영했다. PostgreSQL 신규 표 계획을 표1+인덱스3+RLS+`PUBLIC`/`anon`/`authenticated`/`service_role` 각각 `REVOKE ALL`의 9문장으로 바꿨다. 같은 transaction 안에서 구조·ACL·RLS·policy0·`postgres` CRUD를 post-check하며 실패하면 전체 rollback한다.
- **어디까지 끝났는지**: 제품·테스트 로컬 커밋 `4362e8c`. 전체157 PASS, PostgreSQL17 WASM에서 위험한 default ACL 재현·REVOKE 누락 post-check rollback·정상9DDL·반복 no-op·기존14표 checksum 불변 PASS. 기존 PostgreSQL CRUD/export 회귀 PASS. 운영 DB DDL/DML·`--apply`·main 반영·push·deploy·iCloud 작업은 0건이다.
- **확인해야 할 것**: 실제 운영 적용 전 코드 검토, 백업/복원 확인, maintenance 창, 동일 앱 주체의 계획 SHA 재확인과 별도 적용 승인이 필요하다. PGlite는 실제 psycopg wire/PgBouncer/Supabase event trigger 환경을 대체하지 않는다. 기존 `books`/`activities`/`profiles`의 넓은 ACL/RLS는 이번 범위 밖으로 그대로다.
- **다음 작업자**: David가 운영 migration 검토·백업·적용 승인 범위를 결정한 뒤, 읽담 담당자가 운영에서 먼저 dry-run 계획만 재생성·대조한다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunks-private-default`, 제품·테스트 `4362e8c`; main/origin=`4d97f4e`, deploy=`51e5b0c` 불변. 미push·미배포.
- **보류·실패·중단 이유**: 로컬 migration 후보는 준비됐지만 운영 적용·백업·배포 승인은 아직 없다. **1차-A 운영 미완료, 1차-B 금지**. 원본 작업트리의 사용자 기획문서2개는 미변경이다.

## 사용자(David)/운영 담당자가 이어받을 작업 — 앱 DB role 미확정으로 서버 전용 접근정책 결정 중단 (2026-09-27, Codex)

- **무엇을 했는지**: 사용자 제공 read-only 권한 결과와 읽담 코드의 DB/Auth/Storage/export 경로를 대조했다. chunk CRUD/export는 PostgreSQL 설정 시 Streamlit 서버·CLI의 psycopg 직접 연결을 쓰고 Data API 직접 호출은 필요하지 않다. anon 키는 Auth, service-role 키는 사진 Storage에 쓰인다. [접근정책 감사·조건부 REVOKE 후보](READING_CHUNK_PRODUCTION_MIGRATION_PLAN.md)를 기록했다.
- **어디까지 끝났는지**: 운영 연결 role은 DSN 또는 `SUPABASE_DB_USER`로 런타임에서 결정되어 코드만으로 특정할 수 없다. 정책·RLS 필요 여부·REVOKE 안전성은 **미확정**. 읽담 문서 로컬 커밋만; 운영 DB 접속·DDL/DML·배포·환경변수 변경·main 반영·push 없음.
- **확인해야 할 것**: 비밀값을 공개하지 않는 승인된 운영 read-only 조회에서 실제 앱 `current_user`/`session_user`, 생성 role 기본 ACL, 서버 role의 새 표 권한, `anon`/`authenticated`의 상속·PUBLIC 포함 실효 권한과 Data API 노출을 확인한다. 현 maintenance CLI는 CREATE4문장만 원자 적용하므로 REVOKE를 포함한 실행 경로가 아니다.
- **다음 작업자**: 사용자/운영 담당자가 위 role/권한 metadata만 제공하거나 안전한 기존 조회 경로를 지정한다. 그 전에는 정책 확정·운영 DDL 승인을 요청하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunks-1a-fixes`, 이번 문서 전용 로컬 커밋. main/origin=`4d97f4e`, deploy=`51e5b0c`; 운영 미배포.
- **보류·실패·중단 이유**: 요청의 명시 중단 기준인 “실제 앱 연결 role을 코드만으로 확인할 수 없음”에 해당한다. **운영 NO-GO, 1차-A 미완료, 1차-B 금지**. 기존 public 표의 넓은 권한은 별도 위험이며 이번 범위에서 수정하지 않았다.

## 사용자(David)/운영 담당자가 이어받을 작업 — 1차-A 최소 migration SQL 확정, 권한 확인 전 적용 NO-GO (2026-09-27, Codex)

- **무엇을 했는지**: 사용자가 전달한 운영 읽기 전용 집계(books 705, activities 5,667, NULL-owner 각각 0, reading_chunks/관련 인덱스 부재, 기존 RLS 비활성/정책 0)를 코드·Runbook과 대조했다. [최소 표 1개+인덱스 3개 계획](READING_CHUNK_PRODUCTION_MIGRATION_PLAN.md), 백업·검증·rollback·배포 순서를 확정했다.
- **어디까지 끝났는지**: 문서 계획만 작성. 운영 DB 접속·DDL/DML·배포 없음. 운영 결과는 사용자 제공 자료이며 이번 세션 직접 재조회 아님. 제품 코드·사용자 파일 변경 없음.
- **확인해야 할 것**: 실제 migration role의 `current_user`/기본 ACL, `anon`·`authenticated` Data API 노출, `books.id` 타입/제약 및 FK 권한, 신규 객체명 전체 충돌, 앱 role 권한, 백업 복구 가능성을 읽기 전용 확인. 기본 GRANT로 RLS 없는 새 표가 노출된다면 정책 결정 전 STOP. 전달 activities 5,667은 이전 5,666 기록보다 1건 많으므로 사전 기준을 다시 잡고 원인을 확인한다.
- **다음 작업자**: 사용자/운영 담당자가 누락 metadata를 안전한 조회 결과로 제공하고, 보안·백업 범위를 확정한 뒤 별도 DDL/배포 승인을 결정한다.
- **브랜치 / 커밋 / 배포 상태**: 읽담 `codex/reading-chunks-1a-fixes`에서 문서만 기록. main/origin=`4d97f4e`, deploy=`51e5b0c` 유지. main 반영·push·운영 배포 없음.
- **보류·실패·중단 이유**: 신규 `public` 표의 기본 권한과 RLS 필요성을 현재 자료만으로 확정할 수 없다. **운영 적용 NO-GO, 1차-A 미완료, 1차-B 금지**.

## 사용자(David)/관리자가 이어받을 작업 — 운영 read-only 점검 연결 경로 미공급으로 중단 (2026-09-27, Codex)

- **무엇을 했는지**: 제품5148d6f/문서22f7b1f/공동f7fe19b와 최신 지침을 확인했다. 연결 설정은 값 없이 존재 여부만 확인했고 모두 미공급/빈 값이다. 활성 DB connector와 브라우저 연결도 없다. `.env`/Secrets를 읽거나 환경을 바꾸지 않고 접속 전에 중단했다.
- **어디까지 끝났는지**: 로컬 코드의 owner claim/profile DML 재확인과 [미실시·중단 기록](READING_CHUNK_PRODUCTION_PREFLIGHT.md)만 완료. 운영 연결/SQL0건. 실제 schema/index/constraint/RLS/ACL/role/version/count와 reading_chunks 존재 여부는 미확인이다.
- **확인해야 할 것**: books705/activities5,666은 비교 기준이지 이번 실측치가 아니다. 표1+index3 초안은 조건부 계획이며 운영 필요 DDL로 확정하지 않았다. 기존 NULL-owner 일괄claim과 profile UPSERT는 운영 무변경 확인 전 Blocker로 유지한다.
- **다음 작업자**: 사용자/관리자가 비밀값을 채팅에 노출하지 않는 승인된 기존 연결 경로를 제공하거나, 동일 앱 주체의 읽기 전용 조회 결과를 제공해야 한다. 환경변수·Secrets 변경을 에이전트가 임의 수행하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: 읽담 `codex/reading-chunks-1a-fixes`(시작22f7b1f), 공동 `codex/reading-chunks-preflight-docs`(시작f7fe19b)에 문서만 별도 기록. main/origin 로컬ref4d97f4e, deploy51e5b0c 유지. main/push/배포 없음.
- **보류·실패·중단 이유**: read-only 점검 승인은 있으나 실행 가능한 안전한 연결이 없다. 운영 오류·drift를 발견한 것은 아니다. **운영 NO-GO,1차-A 미완료/1차-B 금지** 유지. 원본 사용자2문서와 공동 미커밋 문서는 hash 동일·미변경이다.

## 사용자(David)/읽담 담당자가 이어받을 작업 — 자동 init 분리·read-only preflight 완료, 운영 NO-GO (2026-09-27, Codex)

아래 이전 수정 상태를 **수정 브랜치에 한해** 대체한다. 운영 Supabase 접속·쓰기·DDL·배포·실제 iCloud 접근·main 반영·push·1차-B는 실행하지 않았다.

- **무엇을 했는지**: 일반 연결의 schema-init/SQLite kind 자동변환 제거. connect→read-only 구조검사→OK/안전중단. 앱 오류 안내와 export 사전점검 추가. 명시 maintenance는 읽기 전용 계획을 기본값으로 하고, 승인hash·transaction·최종검사로 reading_chunks 신규표/누락index만 적용 가능하다. drift는 자동 교정하지 않는다.
- **어디까지 끝났는지**: 제품·테스트 `5148d6f` 로컬 커밋. 전체154 PASS/0 XFAIL, Python63파일·Node2개·diff PASS. 새 PostgreSQL WASM14시나리오 및 기존12시나리오/서비스 검증 완료. 합성705책/5,666기록/기존14표 checksum 불변. AUDIT-01은 감지·중단·교정금지 기준 PASS.
- **확인해야 할 것**: [새 구조·테스트 결과](READING_CHUNK_SCHEMA_PREFLIGHT.md), [최신 Runbook](READING_CHUNK_DEPLOY_RUNBOOK.md). contract는 구조 기반v1이며 DB version marker는 만들지 않는다. preflight는 ACL/RLS 검증을 대신하지 않는다. 기존 owner claim·소그룹 profile DML은 별개로 남아 있다.
- **다음 작업자**: 사용자에게 운영 read-only metadata/권한 점검만 별도 승인을 요청할 읽담 담당자. 운영 점검이 승인돼도 DDL/배포까지 승인된 것으로 해석하지 않는다.
- **브랜치 / 커밋**: `codex/reading-chunks-1a-fixes`, `/private/tmp/readdam-main-LIPAnD`, 시작952c3b3→5148d6f + 별도 문서 커밋. main/origin 로컬ref4d97f4e, deploy51e5b0c 유지. 공동 b2d9112는 별도 저장소 커밋이며 cherry-pick하지 않았다. 공동 상태 문서는 `codex/reading-chunks-preflight-docs` 별도 worktree에만 기록하고 공동 main도 유지한다.
- **배포 상태**: 미배포·미push·main 미반영. 원본 사용자2문서 및 공동 dirty PROJECT/WORKLOG hash 불변. 사용자/합성 iCloud 파일 미접근.
- **보류·실패·중단 이유**: 로컬 구현 GO이나 **운영 NO-GO /1차-A 미완료/1차-B 금지**. 운영 schema·권한·RLS/ACL·psycopg/PgBouncer·실제 화면·수정판 iCloud 검증과 승인이 남아 있다.

## 사용자(David)/읽담 담당자가 이어받을 작업 — 1차-A 차단 결함 로컬 수정, 운영 NO-GO 유지 (2026-09-27, Codex)

아래의 제품 무수정 감사 상태를 이 수정 브랜치에 한해 대체한다. **운영 접속·배포·DB 쓰기/DDL·사용자 예화창고 접근·1차-B는 실행하지 않았다.**

- **무엇을 했는지**: actor/owner/book 격리, PostgreSQL NULL 쪽수 타입, 선택·읽기 전용 export, 삭제 충돌 no-clobber, atomic index/journal 복구·txt SHA 영수증, 특수 태그 exact filter, 동일 세션 수정→재수정→soft delete를 수정했다. 스키마/기존 books·activities·통계 변경 없음.
- **어디까지 끝났는지**: 제품·테스트 `038ab2e` 로컬 커밋. 전체 **123 PASS / 1 strict XFAIL**, 감사 xfail **12→1**. Python53개/Node compile·diff PASS. PostgreSQL 시뮬레이션 및 실제 Python service→PG WASM 격리 검증 PASS; 기존14표 checksum 불변. /tmp에서32 TEST/CLI8회 export 검증, 실제 iCloud는 미접근.
- **확인해야 할 것**: [수정 결과·사용/복구 계약](READING_CHUNK_BLOCKER_FIXES.md). export CLI는 `--owner-id` 및 반복 가능한 `--chunk-id` 필수. `.export-state.json`/`.export-pending.json`/잠금을 사용하며, 실패 복구는 동일 owner/ID 선택으로만 한다. 구형 파일의 byte 일치가 확인되지 않으면 덮어쓰지 않고 중단한다.
- **다음 작업자**: 운영 접속 전 앱 일반 연결의 자동 init 분리·읽기 전용 schema preflight 범위를 확정할 읽담 담당자. 운영 권한·metadata·실제 psycopg/PgBouncer·실제 화면·수정판 iCloud 검증은 이후 별도 승인 필요.
- **브랜치 / 커밋**: `codex/reading-chunks-1a-fixes`, `/private/tmp/readdam-main-LIPAnD`, 제품 `038ab2e`(감사 `8843b56/6cdc7e7` 후속). main/origin ref=`4d97f4e`, deploy ref=`51e5b0c`. 이번 main 반영·push 없음. 원본 사용자2문서 및 공동 미커밋 문서 hash 불변.
- **배포 상태**: 미배포. 운영 Supabase 접속·쓰기·DDL0. 제품/테스트 커밋과 이 문서 기록 커밋을 분리한다. 공동 원격 미설정 유지.
- **보류·실패·중단 이유**: AUDIT-01의 잘못된 동일이름 index 감지/자동 교정은 미해결(스키마 변경 금지). 앱의31DDL 자동 init과 owner claim도 기존대로라 현 브랜치를 운영 GO로 볼 수 없다. 일반 동시 편집/의미중복 직렬화·다른 기기 iCloud 잠금은 보장하지 않는다. 1차-A 미완료·1차-B 금지 유지.

## 사용자(David)/읽담 담당자가 이어받을 작업 — 종합 감사 완료, 제품 수정·운영 전 NO-GO (2026-09-27, Codex)

아래의 단순 검증 진입 중단 상태를 확대 감사 결과로 대체한다. **운영 배포/쓰기/DDL/초기화 및 1차-B는 계속 금지다.**

- **무엇을 했는지**: deploy `51e5b0c` → 제품 main `4d97f4e` 전체 diff와31문장 init, 기존 owner/profile 쓰기 경로를 추적했다. SQLite 및 PostgreSQL17.5 WASM(PGlite0.4.6)에서705권/5,666기록·기존14표 보존, 반복/부분 실패/rollback/재시작을 시뮬레이션했다. 제품 코드는 수정하지 않았다.
- **어디까지 끝났는지**: 기존 기록 `4d97f4e`를 문서만임을 확인 후 origin/main에 push. 감사 테스트32개를 추가(`8843b56`), 전체85 PASS/12 strict XFAIL. `--runxfail`로12실패를 별도 재현했다. PG nullable-page 중복 쿼리42P18도 확인했다. iCloud 격리 TEST32개·CLI8회 정상 경로 PASS, 기존695항목 메타데이터 변경0.
- **확인해야 할 것**: [종합 감사](READING_CHUNK_PREDEPLOY_AUDIT.md)의 AUDIT-01~11 및 [배포/복구 runbook](READING_CHUNK_DEPLOY_RUNBOOK.md). 읽기 전용 CLI 분리, actor/book 경계, NULL 비교, export 원자성/삭제 대상 덮어쓰기, 태그 escaping/index 검증은 수정·재시험 필요. 연속 UI 오류는 실제 브라우저 판정 필요. Supabase role/RLS/ACL/실제metadata는 미확인이다.
- **다음 작업자**: 사용자 승인된 제품 수정 범위를 받은 읽담 담당자. 현 코드 그대로 배포하지 않는다. 운영 DB 직접 조회/배포는 별도 명시 승인·접근 경로 확보 후 runbook GO/STOP에 따른다.
- **브랜치 / 커밋**: main/origin=`4d97f4e`, 감사 `codex/reading-chunks-1a-audit` in `/private/tmp/readdam-main-LIPAnD`; 테스트 `8843b56`, 이번 감사 문서는 후속 별도 커밋. 감사 변경은 main 반영/push하지 않는다. 원본 기능 브랜치/사용자2파일은 그대로다.
- **배포 상태**: deploy/main=`51e5b0c`, 운영 접속·DB쓰기·DDL·배포0건. 설치 Chrome/Safari는 있으나 세션 제어 연결 없음. AppTest/WASM은 실제 운영 검증을 대체하지 않는다.
- **보류·실패·중단 이유**:12개 예상 실패를 운영 성공으로 간주하지 않는다. 사용자 소유 파일·이전 합성 txt/index 해시 불변. 신규 테스트 산출물 root는 `예화창고/_읽담_검증전용_20260927_16680d12`(활성31txt/삭제보관1txt/index32행)이며 삭제하지 않았다. 공동 원격 미설정 유지, 다른 작업자의2차 설계 `39ed52d` 보존. 1차-A DoD는 BLOCKED다.

## 사용자(David)/읽담 담당자가 이어받을 작업 — 기록 push 완료, 운영 검증 진입 중단 (2026-09-26, Codex)

아래의 기록 미push·운영 검증 미승인 상태를 대체한다. **제한된 운영 검증은 승인됐으나 배포·스키마 변경은 승인되지 않았다. 1차-A 완료 및 1차-B 진입은 불가하다.**

- **무엇을 했는지**: `431fe44`가 읽담 문서 3개만, 공동 `92e6d95`가 CROSS 문서만 변경했음을 검토했다. origin을 fetch해 fast-forward 가능함을 확인하고 `431fe44`를 origin/main에 push, 원격 SHA를 확인했다. 공동 저장소는 원격 미설정이라 push하지 않았고 임의로 원격을 추가하지 않았다.
- **어디까지 끝났는지**: 배포 원격은 `51e5b0c` 유지. 해당 소스에 reading chunk 서비스·화면·export CLI 및 스키마 정의가 없음을 확인했다. 실제 화면 조회는 브라우저 목록이 비어 있고 `Browser is not available: iab` 오류로 불가했다. 운영 DB에 접속하지 않아 표·필드·인덱스 존재 여부는 미확인이다. 운영 레코드 생성·수정·필터·삭제 및 운영 레코드 export·재export·index 검증은 모두 미실행이다.
- **확인해야 할 것**: 실제 화면을 열 수 있는 브라우저와 운영 DB의 읽기 전용 메타데이터 확인 경로가 필요하다. 배포 미러 기준으로 새 기능 배포가 필요하며 별도 승인을 받아야 한다. 새 코드의 앱/CLI는 `get_connection()`에서 `ensure_schema()`를 실행하므로 읽기 전용 점검용으로 실행하지 않는다. 운영에 없다면 필요한 additive 대상은 `reading_chunks` 22개 필드, chunk_id PK·source_ref UNIQUE·book_id FK·source_app CHECK와 `idx_reading_chunks_book/owner/duplicate` 3개 인덱스다. 실제 부재를 확인하기 전에는 적용 필요성을 확정하지 않는다.
- **다음 작업자**: 사용자(David)가 공동 저장소의 원격 목적지, 브라우저/읽기 전용 DB 확인 경로 및 배포·필요 시 additive 스키마 승인 범위를 결정한 뒤 읽담 담당자. 기존 전체 스키마 초기화는 기존 표 관련 DDL도 포함하므로 승인 전 실행 금지.
- **브랜치 / 커밋 / 배포 상태**: 별도 main worktree의 origin/main=`431fe44`, deploy/main=`51e5b0c`. 이번 중단 기록은 별도 로컬 문서 커밋으로 남기며 추가 push·배포하지 않는다. 공동 `92e6d95`는 미push다.
- **보존·남은 산출물**: 사용자 소유 기획문서 2개 SHA-256은 이전과 동일하다. 합성 테스트 txt `독서조각/2026/2026-09/2026-09-26_읽담_검증용_가상도서_p45-52_64894842.txt` 및 `_index.csv`도 이전 SHA-256과 동일하다. 운영 자료가 아닌 합성 테스트 산출물이며 삭제하지 않았다. 확인용 보존 또는 txt와 대응 index 행의 함께 정리는 사용자 결정이 필요하다.
- **보류·실패·중단 이유**: 미배포 기능, 브라우저 부재, 공동 원격 미설정. 운영 DB/데이터/스키마/인덱스 변경 작업은 0건이나 DB 전후 비교에 의한 무변경 검증은 수행하지 못했다. 코드 수정 없음.

## 사용자(David)/읽담 담당자가 이어받을 작업 — 실제 iCloud txt 검증 통과, 운영 검증 대기 (2026-09-26, Codex)

아래 항목의 txt 보관 루트 미확정·실제 export 미검증 상태를 대체한다. **1차-A 전체 완료와 1차-B 진입은 여전히 보류한다.**

- **무엇을 했는지**: 사용자가 지정한 `/Users/donghakim/Library/Mobile Documents/com~apple~CloudDocs/예화창고`를 보관 루트로 확정했다. `54c0d23`의 export CLI를 별도 합성 SQLite DB에 연결해 실제 iCloud 경로에서 네 번 실행했다. 제품 코드는 수정하지 않았다.
- **어디까지 끝났는지**: 최초 txt 1개 생성, 동일 데이터 재export 0개 작성, 동일 chunkId의 메모·시간 변경 후 같은 txt 1개 갱신, 다시 재export 0개 작성을 확인했다. `_index.csv`는 계속 1행이며 경로·chunkId·updatedAt·contentHash가 테스트 DB/파일과 일치한다. 실제 사용자 자료를 운영 DB에서 가져오는 흐름은 검증하지 않았다.
- **생성 파일**: 보관 루트 아래 `독서조각/2026/2026-09/2026-09-26_읽담_검증용_가상도서_p45-52_64894842.txt`, `독서조각/_index.csv`. 명확히 표시한 테스트 산출물로 남겨 두었다. 합성 DB와 검증 스크립트·보고서는 `/tmp/readdam-export-check-Hws0qK/`에 있다.
- **확인해야 할 것**: 별도 운영 적용 승인 후 Supabase 표·제약·인덱스·사용자 분리·기존 데이터 무변경, 실제 화면 생성·목록·수정·필터·soft delete·동일 ID 저장 및 운영 DB 기반 export를 확인해야 한다. 이번 확인은 이 Mac의 iCloud 로컬 경로 쓰기이며 다른 기기로의 iCloud 동기화까지 확인한 것은 아니다.
- **다음 작업자**: 사용자(David)가 운영 배포·Supabase 적용 및 운영 검증을 승인한 뒤 읽담 담당 작업자.
- **브랜치 / 커밋**: main worktree `/tmp/readdam-main-LIPAnD`, 검증 대상 `54c0d23`(기능 `cbcf0b4`까지). 이번 결과 문서는 별도 로컬 문서 커밋이며 origin push는 하지 않는다. 원본 작업트리의 사용자 소유 미커밋 기획문서 2개는 보존한다.
- **배포 상태**: origin/main은 `54c0d23`, deploy/main은 `51e5b0c`. 운영 배포·Supabase 접속/변경 없음.
- **보류·실패·중단 이유**: 이번 검증 범위에서 코드 결함·권한 오류 없음. 운영 적용은 사용자 미승인으로 보류. 예화 카테고리별 분류 export(2차) 및 1차-B는 미착수다.


## 사용자(David)/읽담 담당자가 이어받을 작업 — main·origin 반영 완료, 운영 검증 보류 (2026-09-26, Codex)

이 항목은 아래의 main 반영 중단·승인 대기 상태를 대체한다. **1차-A는 운영 검증 전이므로 완전 완료가 아니다. 1차-B에 진입하지 않는다.**

- **무엇을 했는지**: 사용자가 미커밋 기획문서 2개를 보존한 별도 worktree 사용을 명시적으로 승인했다. main 기준 변경 12개 경로에 사용자 파일이 없고 fast-forward 가능함을 확인한 뒤 `/tmp/readdam-main-LIPAnD`에서 main을 `51e5b0c` → `cbcf0b4`로 반영했다.
- **어디까지 끝났는지**: main 반영 후 전체 테스트 **65개 통과**, Python compileall·diff 검사 통과. 비공개 원본 `origin/main`에 `cbcf0b4` push와 원격 SHA 확인 완료. 이어서 이 상태 기록을 별도 문서 커밋으로 main·origin에 반영한다.
- **확인해야 할 것**: 운영 배포·Supabase 적용은 별도 승인 전까지 수행하지 않는다. 승인 후 reading_chunks 표·유일 제약·인덱스·사용자 분리와 books/activities 무변경을 확인하고, 운영 화면에서 생성·목록·수정·태그 필터·콘텐츠 타입·soft delete·동일 chunkId 재저장을 검증해야 한다. txt 보관 루트가 확정되면 실제 export·재export·파일 수·본문·`_index.csv`를 검증한다.
- **다음 작업자**: 사용자(David)가 운영 적용 승인과 txt 보관 루트를 결정한 뒤 읽담 담당 작업자.
- **브랜치 / 커밋**: 별도 worktree `main`에 기능 `aeecb7f`, 문서 `ae86be2`, 보완 `cbcf0b4`까지 포함. 원본 작업트리는 `codex/reading-chunks-1a` / `cbcf0b4`에 유지한다. 최신 상태 기록은 main 문서를 기준으로 읽는다.
- **배포 상태**: `deploy/main`은 `51e5b0c` 그대로. 배포 미러 push·운영 앱 실행·운영 DB 접속/변경 없음.
- **보류·실패·중단 이유**: 이번 사용자 승인 범위는 main 반영과 origin push까지다. 운영 배포·DB 적용, 보관 루트 확정 전 실제 export 검증은 명시적으로 보류했다. 테스트 실패·병합 충돌 없음.
- **사용자 파일 보존**: 원본 작업트리의 기획문서 2개는 이동·수정·stage·커밋하지 않았다. 두 파일의 작업 전후 SHA-256 일치를 확인했다.

## 사용자(David)가 이어받을 작업 — 1차-A 운영 적용 중단 조건 확인 (2026-09-26, Codex)

- **무엇을 했는지**: 운영 적용 전 원격·작업트리·txt 규격을 점검했다. txt에 빠져 있던 ISBN·읽은 시간과 `sourceApp` 원시 코드를 추가했다.
- **어디까지 끝났는지**: 보완 코드는 `codex/reading-chunks-1a`에 로컬 커밋했다. main 반영·push·배포·운영 DB 확인은 수행하지 않았다.
- **확인해야 할 것**: 사용자 소유 기획문서 2개가 남은 작업트리에서 main 반영을 허용할지, 또는 사용자가 먼저 이를 별도 커밋·이동할지 결정한다. 실제 txt 보관 루트 경로도 필요하다.
- **다음 작업자**: 사용자(David)가 반영 방법과 보관 루트를 결정한 뒤 읽담 담당 작업자.
- **브랜치**: `codex/reading-chunks-1a`.
- **커밋**: 기능 `aeecb7f`, 문서 정비 `ae86be2`, 이번 txt 보완 커밋은 Git 기록을 확인한다.
- **배포 상태**: 미배포. 점검 당시 `main`·`origin/main`·`deploy/main`은 모두 `51e5b0c`.
- **보류·실패·중단 이유**: 최상위 AGENTS.md의 main 반영 안전 조건은 다른 사람의 미커밋 변경이 없어야 한다. 현재 기획문서 수정 1개와 미추적 1개가 남아 있어 자동 반영을 중단했다. 실제 보관 루트도 확정되지 않았다.
- **보존 중인 사용자 소유 미커밋 변경**: `도서비서_기획문서.md`, `도서비서_기획문서 2.md` 모두 그대로 보존했다.


## 사용자(David)/ChatGPT 사령관이 결정할 작업 — Reading Chunk 1차-A 검토·main 반영 승인 (2026-09-26, Claude Code)

- **무엇을 했는지**: 공동작업 기록 체계를 정비했다. 이 HANDOFF를 새로 만들었고, WORKLOG에 기록 규칙을 추가했으며, `AGENTS.md`·`CLAUDE.md`를 새로 만들었다. 상위 공용 계약서 `../CROSS_PROJECT_HANDOFF.md`에 Reading Chunk 공동결정과 진행상태를 정식 기록했다. 기능 코드는 수정하지 않았다.
- **어디까지 끝났는지**
  1. Reading Chunk MVP 1차-A는 Codex가 구현해 **로컬 커밋만** 한 상태다 (`aeecb7f feat: add reading chunk mvp 1a`).
  2. **main 반영 안 함, push 안 함, 배포 안 함, 운영 Supabase 직접 적용 안 함.**
  3. 이번 문서 정비는 같은 브랜치에 문서 커밋으로 추가했다.
- **확인해야 할 것**
  1. 1차-A 동작 검토: 책 상세의 읽은 조각 입력·수정·삭제·태그 필터, `tools/export_chunks.py --output-root <보관루트>`.
  2. main 반영 여부. 이 앱은 Postgres 연결 시 `ensure_schema`가 `reading_chunks`를 추가하므로, **main 반영 후 배포하면 운영 Supabase에 표가 생긴다.** 승인 범위를 함께 정한다.
  3. txt 보관 루트 실제 경로.
  4. 1차-B(오늘의 서재 ↔ 읽담 API) 담당 지정. 미해결 결정 목록은 `../CROSS_PROJECT_HANDOFF.md` 1.9절에 있다.
- **다음 작업자**: 사용자(David)/ChatGPT 사령관이 결정한다. 승인되면 읽담 담당 작업자(Codex 또는 Claude Code)가 `AGENTS.md`의 main 반영 절차에 따라 반영·push·배포 미러 동기화·운영 확인을 하고, 이 파일과 공용 계약서를 갱신한다.
- **브랜치**: `codex/reading-chunks-1a` (main `51e5b0c`에서 fast-forward 가능한 상태로 확인됨)
- **커밋**: 기능 `aeecb7f`, 이후 이번 문서 정비 커밋
- **배포 상태**: 미배포. `origin/main`·`deploy/main` 모두 `51e5b0c`.
- **보류·실패·중단 이유**
  - main 반영·push·운영 적용은 사용자 검토 대기로 **보류**.
  - 예화창고 export는 실제 폴더 위치 미확인으로 2차에서 진행하기로 **보류**.
  - 기존 activities 5,666건 migration은 하지 않기로 결정됨 (보류가 아니라 범위 제외).
- **보존 중인 사용자 소유 미커밋 변경**: `도서비서_기획문서.md`(수정), `도서비서_기획문서 2.md`(미추적). 수정·커밋하지 않는다.
