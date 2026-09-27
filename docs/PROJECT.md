# 읽담

최신 배포 관문(2026-09-27, Codex): main/origin/main/deploy/main=`5129d75`, ff-only후157PASS·두원격push·Streamlit Updated app로그확인. **runtime SHA직접확인/Safari Auth로그인/실제CRUD·export는미완료,1차-A INCOMPLETE**. 기존14표행내용해시·건수/기존schema불변, RLS on/policy0/외부4주체CRUD=false/postgres=true/실제anonGET401·42501확인. 공동정본은`codex/reading-chunks-current-state`의`ca81d37` CROSS_PROJECT_HANDOFF 최신배포인계다. 다음은로그인/runtimeSHA근거확보후기존승인범위실검증재개. 제품코드·DB변경0, 결과문서는로컬브랜치에만기록한다. 아래배포전상태는역사기록이며1차-B/2차/iCloud자동export금지는유지한다.

공동 현재 상태 정합화(2026-09-27, Codex): **DB migration 완료 / 제품 main 반영·배포 전**. 공동 정본은 `codex/reading-chunks-current-state`의 `32cfc48`, `/private/tmp/readdam-cross-current-gJs4x6/CROSS_PROJECT_HANDOFF.md`1.0절이다(공동 저장소 `git show 32cfc48:CROSS_PROJECT_HANDOFF.md`로도 조회). 공동 main/원본 읽담 기능 브랜치의 옛 문서를 현재 정본으로 사용하지 않는다. 운영 권한 프리플라이트·보안설계·dry-run9DDL·백업·migration SUCCESS와 직전157PASS/운영 post-check는 완료된 근거다. `b23e316`의 문서 충돌은 이번 정합화로 해소해 main 반영 준비 YES/운영 배포 준비 YES이며, 실행 승인은 별도다. 다음은 제품 main → origin/main → deploy/main → Streamlit → M1 Safari CRUD 및 anon 차단 재확인이다. **1차-A 미완료, 1차-B·2차 export·실제 iCloud export 금지**. 제품 `4362e8c`, main/origin `4d97f4e`, deploy `51e5b0c`와 DB는 이번에 변경하지 않았다. 아래 상태 기록은 각 시점의 근거로 보존한다.

운영 점검 상태(2026-09-27): 사전 custom-format 백업과 승인 plan SHA 재확인 후 `4362e8c`의 신규 표1+index3+RLS+`PUBLIC`/`anon`/`authenticated`/`service_role` REVOKE 9DDL을 단일 transaction으로 적용했다. 운영 `reading_chunks`는 구조계약 OK·행0·RLS on·policy0·외부4role CRUD=false·postgres CRUD=true다. books705/activities5,667/owner NULL0 및 기존 public schema fingerprint는 불변이다. 기존 표/default ACL/Data API 구성은 변경하지 않았다. 앱 코드는 main/push/deploy 전이므로 1차-A 화면 운영 검증과 1차-B는 아직 금지다. [운영 migration 계획](READING_CHUNK_PRODUCTION_MIGRATION_PLAN.md)을 따른다.

최신 Reading Chunk 상태(2026-09-27): `codex/reading-chunks-private-default`의 `4362e8c`는 `5148d6f`의 자동 schema-init 제거/read-only 구조검사와 `038ab2e`의 CRUD/export 안전성 수정을 포함한다. 전체157 PASS이며 운영 schema migration/post-check도 성공했다. main/push/deploy와 실제 사용자 CRUD·iCloud 검증은 남아 **앱 운영 미완료/1차-B 금지 유지**. [새 구조/검증 결과](READING_CHUNK_SCHEMA_PREFLIGHT.md)와 HANDOFF/Runbook을 따른다. 아래 날짜별 상태는 해당 시점의 기록이다.

북스윙 개인 독서 기록을 보존하고 책장·독서 노트·타이머·공유·통계와 초대형 소그룹 인증을 제공하는 Streamlit 앱.
도서비서 폴더는 독립 Git 저장소이며 상위 동하비서에서 제외된다. 서브모듈 관계가 없다.

- 숫자 activity kind는 원본과 호환한다. 원본 생명주기 의미 정정은 `SOURCE_AUDIT.md` 참고.
- `reading_chunks`는 기존 `activities`와 별도인 additive 조각 보관 표다. 읽담 화면에서 만든 조각은 `source_app=readdam`이며, UUID·스냅샷 책 정보·태그·콘텐츠 타입·소프트 삭제를 가진다. 기존 책·기록·통계에는 연결하거나 변환하지 않는다.
- 실제 DB/사진/백업은 Git에서 제외한다. 테스트는 별도 임시 DB만 쓴다.
- DB 일반 연결은 `connect → read-only preflight → OK/안전중단`이다.15필수표/13named index/reading_chunks22컬럼·제약·구조계약v1을 검사하며 drift자동수정과 SQLite kind자동변환은 없다. `tools/schema_preflight.py`는read-only다. PostgreSQL의 `tools/schema_maintenance.py` 신규표 계획은 명시승인hash·단일transaction 안에서 표/index/RLS/외부4role REVOKE/구조·보안 post-check를 수행하며, 실패 시 rollback한다. 기존 full initializer는 offline bootstrap에만 남고 운영1A용이 아니다.
- Supabase Auth 계정이 개인 서재와 소그룹을 분리한다. 기존 705권 서재는 Cloud Secret `READDAM_OWNER_EMAIL`과 일치하는 계정만 소유자로 연결하며, 소그룹에는 사용자가 선택한 인용구·사진 스냅샷과 일일 인증·반응·댓글만 공유한다. 전체공개 피드·뱃지는 구현하지 않는다.
- `migration/load_db.py`는 초기 적재 전용이며 기존 DB를 재생성하므로 사용 중인 DB에 실행하지 않는다.
- 영속 데이터는 Supabase Postgres(`bookbutler-prod`, 서울 리전)에 저장한다. 로컬 개발/테스트는 SQLite를 유지하며, `BOOK_BUTLER_DATABASE_URL` 또는 Supabase DB 환경변수가 있으면 Postgres로 연결한다.
- 사진은 비공개 Supabase Storage `book-photos` 버킷에 저장하고 서버가 짧은 만료의 서명 URL을 발급한다. 서비스 키는 `.env` 또는 Streamlit secrets에만 둔다.
- 공개 Streamlit Community Cloud 앱은 배포 전용 공개 미러 `srapdle-collab/book-butler-deploy`에서 제공한다. 앱 시작 비밀번호와 Supabase 접속 정보는 Cloud Secrets에만 두며, 원본 저장소 `srapdle-collab/book-butler`는 비공개로 유지한다. 배포 미러는 검증된 `main` 변경을 `git push deploy main`으로 수동 동기화한다.

## 공동작업 기록 체계
- 작업자 규칙: `AGENTS.md`(정본), `CLAUDE.md`(Claude 진입점). 여러 작업자가 번갈아 작업하므로 항상 공동작업으로 간주한다.
- 현재 상태·다음 행동은 `docs/HANDOFF.md`(최신 항목 맨 위), 상세 역사는 `docs/WORKLOG.md`, 프로젝트 간 계약은 동하비서 최상위 `CROSS_PROJECT_HANDOFF.md`에 둔다.

## Reading Chunk 공동작업 (오늘의 서재 연동)
- 공통 결정·책임 범위·규격·진행상태의 정본은 `../CROSS_PROJECT_HANDOFF.md` 1절이다. 세부 설계는 `오늘의 서재/docs/READING_CHUNK_DESIGN.md`에 있다.
- 읽담이 reading chunk의 최종 Source of Truth다. txt·예화창고는 파생 사본이다. 기존 activities 5,666건은 migration하지 않는다.
- 1차-A(읽담 단독)는 `aeecb7f`에 구현됐고, txt 출력의 ISBN·읽은 시간·sourceApp 코드 보완 `cbcf0b4`까지 main·origin/main에 반영됐다(2026-09-26). 사용자 승인에 따라 별도 worktree에서 fast-forward했고 반영 후 전체 테스트 65개가 통과했다. 원본 작업트리의 사용자 소유 미커밋 기획문서 2개는 보존 중이다.
- 운영 배포와 Supabase 적용은 보류 상태이며 `deploy/main`은 `51e5b0c`다. origin push만으로 배포 미러를 동기화하지 않는다. **1차-A는 운영 검증 전으로 완전 완료가 아니며 1차-B(오늘의 서재 API 연동)와 2차(예화 카테고리별 분류 export)는 미착수**다.
- txt 보관 루트는 `/Users/donghakim/Library/Mobile Documents/com~apple~CloudDocs/예화창고`로 확정됐다. 1차-A는 그 아래 `독서조각/`만 관리한다. 합성 임시 SQLite의 검증용 chunk 1건으로 실제 txt 생성·동일 항목 재export·내용 갱신·index 일치를 2026-09-26 확인했다. 기존 690개 항목의 전후 메타데이터 변경·삭제는 없었다. 운영 DB 기반 export와 iCloud 기기간 동기화는 아직 검증하지 않았다.
- 2026-09-26 후속 제한 검증: 합성 검증 기록 `431fe44`는 검토 후 origin/main에 push했다. 공동 `92e6d95`는 공동 저장소 원격 미설정으로 미push다. deploy/main은 여전히 `51e5b0c`이며 해당 소스에는 chunk UI/서비스가 없다. 사용 가능한 브라우저도 없어 실제 운영 화면·DB 검증에 진입하지 못했다. 운영 표/필드/인덱스 존재 여부는 미확인이고 테스트 레코드 생성·운영 export·배포·DDL은 수행하지 않았다. 새 코드의 앱/CLI는 연결 시 전체 스키마 초기화를 실행하므로 읽기 전용 점검에 사용하면 안 된다. 별도 배포 및 필요 시 additive 스키마 승인이 필요하며 1차-A 완료·1차-B 진입은 보류한다. 이전 합성 txt/index는 변경 없이 보존한다.
- 최신(2026-09-27): `4d97f4e`도 origin/main push 완료. 감사 브랜치 `codex/reading-chunks-1a-audit`에서 제품 무수정으로 SQLite/PG-WASM의 705권·5,666기록/14표 보존, 31DDL·부분 실패·rollback을 검증했다. 전체 85 PASS/12 XFAIL이며 별도 PG NULL 쿼리 42P18 및 파일 충돌/원자성/owner 경계 등이 발견돼 **현 main 그대로 배포 NO-GO**다. 설치 Chrome/Safari는 있으나 세션 제어 연결은 없다. 격리 iCloud 32chunk/8회 export는 성공, 기존 695항목 불변. 상세/DoD는 [종합 감사](READING_CHUNK_PREDEPLOY_AUDIT.md), 승인 후 절차는 [runbook](READING_CHUNK_DEPLOY_RUNBOOK.md). 감사 테스트·문서는 main 반영/push하지 않고, 운영 변경·1차-B는 계속 금지한다.
