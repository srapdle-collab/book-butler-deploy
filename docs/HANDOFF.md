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
