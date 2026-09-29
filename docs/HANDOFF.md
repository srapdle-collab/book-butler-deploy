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

## 읽담 담당자가 이어받을 작업 — 희망 Chunk 승인 저장 불일치 확인 (2026-09-29, Codex)

- **무엇을 했는지**: David가 「희망을 짓는다는 것」 Chunk `b0135692…`의 카테고리 승인·「예화창고로 보내기」 완료를 알린 뒤, 운영 DB `get_readonly_connection()`으로 해당 행을 두 번 재조회하고 실제 예화창고에서 단일 pipeline dry-run을 각 두 번 실행했다. export 소유자와 Chunk 소유자가 일치한다.
- **어디까지 끝났는지**: 두 조회 모두 저장된 `illustration_tags=[]`, `updated_at=2026-09-28T22:36:31.831428+09:00`(최초 생성 시각과 동일)이다. 승인 카테고리는 **운영 DB에서 확인되지 않았다**. 운영 전체 Chunk 3건·활성 2건·활성 승인 태그 0건. 실제 예화 분류 계획은 CREATE 0/UPDATE 0/DELETE 0/SKIP 2/UNMAPPED 0/CONFLICT 0, 대상 카테고리·분류 파일 쓰기 0. 기본 TXT는 새 경로 2건, 기존 파일 수정·cleanup 0; deleted 집계 1은 soft delete DB 행이며 파일 삭제 계획 0. 실제 카테고리 63개와 snapshot 일치, 중복 Chunk+카테고리 계획 0, 계획 재실행 동일, 추적한 예화창고 메타데이터 전후 동일. 기존 사람 파일 영향 0, 운영 DB/iCloud write·실제 export·launchd 활성화 0. **첫 실제 카테고리 TXT export 실행 준비 NO**(승인 태그 저장 미확인).
- **확인해야 할 것**: 버튼 동작과 운영 DB 사이의 불일치 원인을 확인한다. 현재 조회만으로 앱 저장 실패인지, David가 사용한 앱의 DB 연결 대상이 다른지는 단정할 수 없다. 승인 카테고리를 추측해 채우거나 운영 데이터를 수정하지 않는다.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — 실제 앱의 「예화창고로 보내기」 저장 경로·연결 대상을 확인하고 같은 Chunk의 태그를 즉시 READ ONLY 재조회한다.
- **브랜치 / 커밋 / 배포 상태**: clean `main a81525a`에서 `codex/hope-approved-dryrun-20260929` 문서 기록. main/origin 반영값은 후속 Git 확인. `deploy/main=9f7aedf` 유지, 앱 재배포 없음.
- **보류·실패·중단 이유**: 실제 승인이 운영 DB의 해당 Chunk에 저장된 근거가 없어서 export GO 불가. 실제 iCloud export·launchd는 David 지시로 계속 보류.

## 최신 — 통합 운영 Runbook 대기 관문 (2026-09-29, Codex)

- **무엇을 했는지**: 통합팀이 공동 `docs/READING_CHUNK_1B_OPERATIONS_RUNBOOK.md`를 준비하고, 읽담 local `main f9b7af7`·서재 `d11113d`·공동 `53fb1db` 조합의 합성 fixture 3건을 재검증했다. 읽담 제품 코드 변경 없음.
- **어디까지 끝났는지**: 직접/서재 입력의 읽담 정본·export dry-run 연결은 local PASS. Sites D1 `0004` 운영 lifecycle은 COMPLETE / EXTERNAL BLOCKED이며 운영 TEST는 미실행.
- **확인해야 할 것**: 공식 답변 후 공동 Runbook 4·12번 슬롯과 TEST 잔존 데이터 수용을 먼저 확인한다. 읽담 전담팀의 희망 책·추천 UX 작업과 결정은 아래 항목 그대로 유지한다.
- **다음 작업자 / 다음 작업 1개**: 통합팀 — 공식 답변 도착 시 Runbook 슬롯을 채우고 운영 관문을 재판정한다. 읽담 단독 다음 작업은 아래 전담팀 항목을 따른다.
- **브랜치 / 커밋 / 배포 상태**: clean `main f9b7af7` 기준 검증, 이 기록은 문서 후속 commit. 읽담 deploy·운영 DB/iCloud·Sites·Secrets 변경 0.
- **보류·실패·중단 이유**: 공식 Sites 관리형 D1 절차 미회신. 제품 local fixture 실패 없음.

## 읽담 담당자가 이어받을 작업 — 희망 책 복원 계획·약한 예화 후보 준비 (2026-09-29, Codex)

- **무엇을 했는지**: David가 읽는 중 `94a4470c…` 보존·위시리스트 `b735496a…` 삭제 후보 지정을 확정했다. 운영 DB를 다시 READ ONLY로 조회해 세션 시작값 `1790602346`(2026-09-28 22:32:26 KST)과 22:36 생성 Chunk를 대조했다. 실제 63개 예화 폴더에서 승인 전 가상 카테고리별 pipeline 계획을 검증했다. 상세 조건·중단 기준은 [희망 책 정상화 계획](HOPE_BOOK_NORMALIZATION_PLAN.md).
- **어디까지 끝났는지**: start_date가 없는 읽는 중 행은 최근 활동도 없어 36위이며, 세션 시작값을 복원한다고 가정한 정렬에서는 앞서는 책 0권(예상 1위)이다. 위시리스트 행의 활동·세션·Chunk·사진 manifest·원본 상태 참조는 모두 0, 같은 제목의 checkin 0, 로컬 표지 사진 0. 삭제 계획만 수립했고 DB 행 변경·삭제 0이다.
- **추천/UX**: 활성 2건 중 하나는 추천 기능 이전 생성. 희망 책 Chunk는 기능 후 생성됐지만 기존 규칙 후보 0·승인 태그 0이며, 패널 열람 여부는 DB로 판별 불가하다. 본문과 기존 카테고리 이름의 독립 단어가 일치할 때만 약한 후보를 보여주는 보완을 코드 `c9d924b`에 구현했다. 현재 희망 Chunk 후보는 `성경, 말씀`, `성경,말씀묵상` 각각 점수 1·기본 체크 해제. 강한 추천의 기본 체크, 전체 63개 검색, 명시 승인 저장 흐름은 유지한다. 일반 자유 태그는 선택 사항임을 화면에 표시했다. 새 회귀 테스트 RED→GREEN, 전체 282 PASS, Python 38파일 구문·diff PASS.
- **첫 E2E 계획**: David가 한 카테고리를 고른다는 가정에서 각 실제 폴더 `읽담/`에 CREATE 1, 기존 사람 파일 UPDATE/DELETE 0. 현재 운영 illustrationTags는 여전히 0이며 실제 pipeline dry-run은 승인 후 재실행한다. 실제 export·launchd·운영 DB write·중복 삭제 0.
- **확인해야 할 것**: David가 실제 앱에서 희망 책 Chunk의 예화 카테고리를 확인·승인할 때까지 태그를 임의로 정하지 않는다. 운영 배포 상태는 `deploy/main`을 확인해야 하며 코드의 운영 UI smoke는 아직 미실행이다. 기존 Sites D1 `0004` 1차-B blocker와 공동 계약은 변경하지 않았다.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — David가 승인한 실제 illustrationTags가 저장되면 운영 DB+예화창고 pipeline dry-run을 재실행한다.
- **브랜치 / 커밋 / 배포 상태**: clean `codex/hope-ux-mainline-20260929`, 기능 `c9d924b`, 이 기록은 별도 문서 커밋. 시작 local main `4b43704`, origin/main `ef5742c`, deploy/main `9f7aedf`; 반영·push 최종값은 Git 확인. 앱 재배포 없음.
- **보류·실패·중단 이유**: 운영 DB write·삭제·실제 iCloud export·launchd는 David 지시로 금지. 실제 카테고리 승인이 없고 운영 앱의 새 추천 UI는 아직 배포되지 않았다.

## 최신 — 현 local main 양경로 fixture 재검증 (2026-09-29, Codex)

- **무엇을 했는지**: 통합팀이 격리 기록 `6b5803a`를 읽담 `main ef5742c` 위에 fast-forward해 전담팀의 후속 운영 조사 기록을 보존했다. 공동 fixture를 읽담 `6b5803a`·서재 `30d1f5e`·공동 `263810f` 조합에서 재실행했다. 제품 코드 변경 없음.
- **어디까지 끝났는지**: 두 입력 경로가 동일 `reading_chunks`와 exporter dry-run에 도달하고 receipt 유실·재전송/행 1건, 태그 보존·오래된 snapshot/invalid payload/not_configured까지 **3 PASS**. 기존 읽담 전체 281 PASS는 제품 코드가 같은 선행 검사다. 실제 운영 E2E는 미실행.
- **확인해야 할 것**: Sites 관리형 D1 `0004` 적용 주체·시점·실패 처리 공식 절차는 아직 확인되지 않아 1차-B 운영 연결 BLOCKED. 운영 책 중복 결정과 실제 exporter 보류 상태는 아래 전담팀 기록을 따른다.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — 아래 중복 책 보존 결정을 기다린다. 통합팀은 공동 계약서의 Sites D1 관문을 담당한다.
- **브랜치 / 커밋 / 배포 상태**: clean `main 6b5803a` 기준 fixture PASS. origin/deploy로 이번 기록 push/배포 없음. 원본 사용자 변경·운영 DB/iCloud/Sites/Secrets 변경 0.
- **보류·실패·중단 이유**: Sites D1 공식 절차 미확인. 로컬 통합 제품 실패 없음.

## 최신 — 통합 fixture의 읽담 경로 검증 (2026-09-29, Codex)

- **무엇을 했는지**: 공동 통합팀이 읽담 local `main 85c1e22`와 오늘의 서재 `main 28cfe37`을 격리해 두 입력 경로를 실제 읽담 계약 함수·합성 SQLite·임시 예화 폴더로 연결했다. 공동 `tests/test_reading_chunk_fixture_e2e.py` 3건 PASS. 제품 코드 변경 없음.
- **어디까지 끝났는지**: 직접 `save → 예화 태그 승인`, 서재 `pending → pull/ingest → ISBN 책 매칭 → receipt → synced`가 모두 읽담 `reading_chunks`에 도달하고 같은 `export_pipeline.run(dry_run=True)`에서 카테고리별 CREATE 대상으로 잡혔다. receipt 유실·재전송 멱등성·invalid payload·오래된 태그·설정 누락 검증. 읽담 기존 281 tests PASS. 브라우저·운영 E2E는 미실행.
- **확인해야 할 것**: 후속 읽담 전담팀의 운영 DB/예화창고 read-only dry-run은 아래 별도 항목이 최신이다. 1차-B 운영 연결은 Sites D1 `0004` 공식 적용 경로 확인 전 BLOCKED.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — 아래 운영 책 중복 건의 David 결정 대기 상태를 유지한다. 통합팀의 Sites D1 관문은 공동 계약서에서 별도로 관리한다.
- **브랜치 / 커밋 / 배포 상태**: `codex/integration-fixture-20260929`, 검증 기준 `85c1e22`; 이 문서는 읽담 전담팀의 `ef5742c` 문서 이력을 fast-forward로 계승한 별도 문서 커밋. 원본 사용자 변경, 운영 DB/iCloud/Sites/Secrets, 읽담 배포 변경 0.
- **보류·실패·중단 이유**: 운영 D1 관문 미확인. 이번 fixture에서 제품 실패 없음.

## 읽담 담당자가 이어받을 작업 — 운영 책 원인 확인·실제 예화창고 dry-run 완료 (2026-09-29, Codex)

- **무엇을 했는지**: M1 영구 저장소의 David 기획문서 미커밋 2건을 보존하고 clean 분리 worktree에서 local `main` `85c1e22`를 계승했다. 실제 `origin/main`·`deploy/main`은 모두 `9f7aedf`로 조회했다. 운영 DB 읽기 전용 연결로 「희망을 짓는다는 것」 두 행과 전체 Chunk를 조사하고 실제 예화창고에서 단일 파이프라인 dry-run을 두 번 실행했다.
- **어디까지 끝났는지**: 읽는 중 행 `94a4470c…`는 `분별력`, ISBN `9788932550817`, 567쪽, 현재 0쪽, `start_date=NULL`, 미삭제 활동 0건, 중단 세션 1건, 활성 Chunk 1건이다. 위시리스트 행 `b735496a…`는 같은 ISBN, 카테고리·쪽수 없음, 활동·세션·Chunk 0건이다. 책 표에는 created_at/updated_at가 없다. 이어서 읽기는 읽는 중 36권 중 정렬 상위 6권만 보이며, 읽는 중 행은 활동 날짜·start_date가 모두 없어 정렬값 0, 순위 36위다. `분별력`은 이 조회의 필터가 아니다. 중복으로 상태·메타데이터가 갈라졌으나 누락 직접 원인은 정렬 기준 날짜 부재다. 두 행은 변경하지 않았다.
- **dry-run 판정**: 운영 Chunk 3건(활성 2, soft deleted 1), 활성 예화 태그 0건. 1차-A 계획은 새 txt 2개, 기존 파일 UPDATE 0, 이동 0, soft delete 행 1건은 기존 소유 파일이 없어 실제 파일 삭제 0이다. 2차 분류 계획은 CREATE/UPDATE/DELETE/UNMAPPED/CONFLICT 0, SKIP 2, 대상 카테고리 0. 물리 카테고리와 snapshot은 NFC 63/63 일치. 기존 사람 파일 UPDATE/DELETE 0, 새 최상위 폴더 0, 중복 Chunk+카테고리 계획 0, 두 dry-run 결과 동일. `.export-state.json`과 분류 manifest는 현재 없으며 실제 쓰기 시 1차-A state 2행·index 총 3행(기존 소유 불명 검증 행 보존), 분류 manifest는 Chunk 3키/파생 파일 0개로 계획된다. DB/iCloud write 0. 주어진 사전 조건상 **실제 export 실행 준비 YES**, 실제 `--apply`와 launchd 활성화는 수행하지 않는다.
- **확인해야 할 것**: David가 중복 책 중 어느 행을 보존할지 결정한다. 독서 진행 이력이 붙은 읽는 중 행 보존이 합리적이나 DB 수정·병합·삭제는 별도 결정 전 금지다. 새 예화 태그가 생기면 dry-run을 다시 평가한다.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — David의 중복 책 보존 결정을 기다리고, 승인 범위가 정해지면 데이터 정리 계획을 제시한다.
- **검증**: 전체 281 tests PASS, Python 38파일 구문 검사 PASS, launchd plist lint PASS, `git diff --check` PASS. 실제 DB/iCloud write 0.
- **브랜치 / 커밋 / 배포 상태**: clean worktree `main`, 조사 기록 `6e175a6`을 local main에 fast-forward하고 `origin/main`에 일반 push했다. 이 상태 정리도 문서 커밋으로 origin에 보존한다. `deploy/main=9f7aedf` 유지, 앱 재배포 없음.
- **보류·실패·중단 이유**: 실제 export와 launchd는 David가 보류했다. 예화 분류 대상 태그는 현재 0건이다.

## 읽담 담당자가 이어받을 작업 — 원격·운영 DB DNS 차단, 실제 예화창고 무쓰기 사전점검 완료 (2026-09-29, Codex)

- **무엇을 했는지**: 세 층의 읽담 HANDOFF/WORKLOG/Git, 최상위 공동 계약·오늘의 서재 기록을 다시 대조했다. actual `origin/main`·`deploy/main`을 각 1회 `ls-remote`했으나 둘 다 이 Codex 실행환경에서 `github.com` DNS 실패로 조회·push하지 못했다. 공식 읽담 `.env`의 기존 PostgreSQL 연결 설정을 **값 출력 없이 프로세스에만** 로드해 Intel x86_64 psycopg의 READ ONLY 연결을 시도했지만 DB 호스트 DNS `gaierror`, 연결 `OperationalError`로 SQL 전 중단됐다. Secret·DB·원격 설정 변경 없음.
- **예화창고 결과**: 실제 iCloud 예화창고를 이름/관리 metadata만 READ ONLY 확인했다. snapshot 63개와 물리 63개 NFC 정확 일치, 물리 이름 63개 모두 NFD, `교회`·`사명` exact 매핑 PASS. `독서조각/_index.csv`는 1행이며 2026-09-26 문서화된 **합성 검증 Chunk** `64894842…`와 일치하고 해당 txt가 존재한다. 1차-A `.export-state.json`, 2차 manifest 및 두 pending은 없다. 소유가 확인되지 않은 이 기존 검증 파일을 파이프라인이 건드리지 않고 보존하도록 RED→GREEN 회귀 테스트·최소 수정을 local `main` `17c4e02`에 커밋했다. 사람 파일 내용 미열람·변경 0.
- **어디까지 끝났는지**: 전체 **281 tests PASS**, Python compile, diff check, plist lint PASS. 실제 운영 Chunk 연결에 실패했으므로 **운영 데이터 기반 전체 dry-run 미실행**이다. 따라서 CREATE/UPDATE/DELETE/SKIP/UNMAPPED/CONFLICT·대상 Chunk/카테고리·사람 파일 영향 계획은 **미산출(0으로 판정 금지)**. 실제 iCloud write/export 0, 운영 DB write 0, launchd 설치 0. 수동 로그인·진단 UI 유지/OIDC BACKLOG. 오늘의 서재 코드·통합 계약 변경 없음.
- **확인해야 할 것**: DNS 가능한 실행환경에서 기존 READ ONLY 경로로 「희망을 짓는다는 것」 두 행과 정렬 순위를 확인하고, 같은 연결로 실제 Chunk→실제 예화창고 `tools/export_pipeline.py` 기본 dry-run을 실행해 충돌·사람 파일 영향·manifest/state 계획을 산출한다. 이 결과 전에는 실제 export/launchd GO 불가.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — DNS 가능한 환경에서 **기존 운영 DB READ ONLY 연결을 복구**한다.
- **브랜치 / 커밋 / 배포 상태**: clean `/private/tmp/readdam-login-persist` `main`, 시작 `e91204d`, 기능 `17c4e02`와 이 기록 커밋이 로컬 정본이다. 로컬 추적 origin/main=deploy/main=`9f7aedf`는 **원격 현재값 미확인**. push·deploy 없음. 원본 `codex/reading-chunks-1a`의 David 기획문서 수정·미추적 2건 보존.
- **보류·실패·중단 이유**: 이 환경의 GitHub·Supabase DB DNS가 모두 실패. 이전 감사상 책 중복은 위시리스트/읽는 중 2건이나 이번 실제 row/rank 조회 불가; local SQLite 705권에는 해당 제목 0건, `reading_chunks` 표도 없어 운영 대체 데이터로 쓰지 않았다. 기존 `start_date` 코드 결함이 실제 누락의 직접 원인인지 미확정. 실제 export·launchd 활성화는 승인 전 금지.

## 읽담 담당자가 이어받을 작업 — 자동 export 격리 구현 완료, 운영 DB 감사 대기 (2026-09-29, Codex)

- **무엇을 했는지**: `tools/export_pipeline.py`로 해당 owner의 전체 Reading Chunk를 READ ONLY 조회해 1차-A txt와 예화 카테고리 `읽담/` 분류를 잇는 단일 명령을 만들었다. CLI는 기본 dry-run, 실제 파일 반영은 별도 승인 후 `--apply`다. 바뀐 Chunk 탐지, 수정·태그 이동·soft delete, pending 복구, 충돌/미매핑 선차단, 사람 파일 보호, 로컬 중복 실행 잠금을 임시 SQLite/폴더에서 검증했다. 설치되지 않은 launchd 템플릿과 [운영 준비 문서](READING_CHUNK_AUTO_EXPORT.md)를 추가했다.
- **어디까지 끝났는지**: clean `main` 기능 커밋 `3fe5d02`; 279 tests PASS, Python compile PASS, diff check PASS, plist lint PASS. 실제 iCloud write/export 0, launchd 설치 0, 운영 DB write 0. 운영 DB READ ONLY 접속은 이번 환경에서 앞 단계 `OperationalError`로 막혔으므로 실제 Chunk에 대한 dry-run과 두 중복 책 조사는 미실시다. 인증은 승인된 수동 로그인 유지·OIDC BACKLOG, 오늘의 서재/통합 계약 변경 없음.
- **확인해야 할 것**: 운영 DB 연결 가능한 Mac에서 먼저 「희망을 짓는다는 것」 두 행과 `start_date`/이어 읽기 정렬을 READ ONLY로 대조한다. 이후 별도 단계에서 실제 승인된 Chunk로 예화 파이프라인의 운영 dry-run 및 실제 기존 폴더/사람 파일 preflight를 검증하고, David 승인 전 iCloud `--apply`·launchd 설치는 하지 않는다.
- **다음 작업자 / 다음 작업 1개**: 읽담 담당자 — 운영 DB READ ONLY가 가능한 환경에서 「희망을 짓는다는 것」 두 중복 행과 이어서 읽기 순위를 대조해 누락 직접 원인을 확정한다.
- **브랜치 / 커밋 / 배포 상태**: `/private/tmp/readdam-login-persist` clean `main`, 기능 `3fe5d02`; 이 기록은 별도 로컬 커밋. 원격 tracking origin/main=deploy/main=`9f7aedf`, 실제 원격 재조회는 기존 GitHub DNS 제약으로 미확인. push·deploy 없음. 원본 `codex/reading-chunks-1a`의 David 기획문서 수정/미추적 2건 보존.
- **보류·실패·중단 이유**: 운영 DB 연결 실패로 P0-B 실제 원인 미확정; 실제 iCloud export 및 launchd 활성화는 David가 없는 동안 금지. 현재 파이프라인은 격리 검증 완료·운영 활성화 전이다.

## 읽담 담당자가 이어받을 작업 — 희망 책 운영 DB READ ONLY 연결 실패, 자동화 본선 진행 (2026-09-29, Codex)

- **무엇을 했는지**: P0-B의 두 중복 책을 운영 DB `get_readonly_connection()`으로 조회하려 했으나 연결 단계에서 `OperationalError`로 실패해 SQL은 실행되지 않았다. 비밀값과 오류 상세는 출력하지 않았다. 재시도나 우회 설치 없이 이 작업은 주차하고 Reading Chunk → 예화창고 격리 자동화로 이동한다.
- **어디까지 끝났는지**: 운영 DB 조회·write 모두 0, 두 책 삭제·병합·상태 변경 0. 이전 감사상 같은 제목/저자 2건의 상태는 위시리스트/읽는 중이지만 이번에 id·ISBN·start_date·현재 페이지·세션·Chunk·상단 6위 순위를 재확인하지 못했다. books schema에는 created_at/updated_at 컬럼이 없다. 기존 코드 수정 `6064b1b`은 새로 등록할 읽는 중 책에만 start_date를 채우므로 두 운영 행의 직접 원인이라고 확정할 수 없다.
- **확인해야 할 것**: READ ONLY 연결 가능한 환경에서 두 행과 책장 정렬 순위를 비교한다. David가 어느 중복을 보존할지 결정하기 전 데이터 변경 금지.
- **다음 작업자 / 다음 작업 1개**: 읽담 Codex — 격리 환경에서 Reading Chunk 변경분 자동 탐지와 안전한 export 단일 파이프라인을 구현한다.
- **브랜치 / 커밋 / 배포 상태**: clean local `main` `/private/tmp/readdam-login-persist`, 시작 `704cb16`; 문서 기록만 커밋, push·deploy 없음. 원격 tracking origin/main=deploy/main=`9f7aedf`, 실제 원격 조회는 GitHub DNS 제약으로 불가.
- **보류·실패·중단 이유**: 운영 DB 연결 실패로 실제 누락 원인 미확정. P0-A 인증은 수동 로그인 유지·OIDC BACKLOG.

## 읽담 담당자가 이어받을 작업 — 인증 수동 운영 유지, 자동 예화 export 본선 (2026-09-29, Codex)

- **무엇을 했는지**: David가 로그인 지속성 설계 감사의 판정을 승인했다. 운영에서 실패한 JS cookie → `st.context.cookies` 경로의 추가 패치는 **중단**한다. Streamlit + Supabase OIDC는 Beta·별도 승인 화면·서명 키·Secrets·user ID/RLS·철회 검증이 필요한 **BACKLOG**다. 오늘 밤 인증 코드·설정·배포 작업은 없다. 현재 수동 로그인과 비밀값 없는 진단 UI를 유지한다.
- **어디까지 끝났는지**: 이전 설계 감사 `6b86fd1` 뒤 이 결정은 local main의 기록 커밋으로 남긴다. 원격·deploy·운영 DB·iCloud 변경 0. P0-B 「희망을 짓는다는 것」과 Reading Chunk → 예화창고 자동화를 차례로 진행한다.
- **확인해야 할 것**: P0-B의 기존 두 행·정렬 순위는 운영 DB READ ONLY로만 확인한다. 연결이 막히면 blocker로 기록하고 예화 자동 파이프라인을 격리 환경에서 계속한다. 실제 iCloud 쓰기와 launchd 설치는 금지다.
- **다음 작업자 / 다음 작업 1개**: 읽담 Codex — 운영 DB READ ONLY로 「희망을 짓는다는 것」 두 레코드의 누락 직접 원인을 대조한다.
- **브랜치 / 커밋 / 배포 상태**: clean `main` `/private/tmp/readdam-login-persist`, 시작 `6b86fd1`; 로컬 tracking origin/main=deploy/main=`9f7aedf`(실제 원격은 DNS 제약으로 미확인). 이번 기록은 push·deploy하지 않는다.
- **보류·실패·중단 이유**: OIDC는 BACKLOG, 운영 데이터 변경은 David 결정 전 금지. 오늘의 서재·통합 계약 변경 없음.

## David가 결정할 작업 — persistent login 공식 인증 전환의 조건부 검토 (2026-09-29, Codex)

- **무엇을 했는지**: 읽담 인증만 설계 감사했다. David의 운영 증거는 JS 쿠키 write·재접속 persistence PASS, 같은 host WebSocket 101 PASS지만 Cookie 전달 FAIL, 앱 진단 `server_cookie_name_seen=NO`, `restore_attempted=YES`, `refresh_success=NO`, `session_restored=NO`, `failure_stage=cookie_missing`이다. 즉 Supabase refresh 전 서버 쿠키 경계에서 막힌다. [Streamlit `st.context.cookies` 문서](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.context)는 최초 요청의 쿠키만 읽는다고 명시한다. **현 JS cookie → `st.context.cookies` 방식의 추가 속성 패치는 중단 권고**다. 브라우저가 WebSocket에서 쿠키를 누락한 내부 이유까지 확정한 것은 아니다.
- **공식 대안 감사**: 설치·배포 요구 `streamlit>=1.50`이며 로컬 Streamlit 1.50에 `st.login/st.user/st.logout`은 있다. [1.50 `st.login` 문서](https://docs.streamlit.io/1.50.0/develop/api-reference/user/st.login)에 따르면 `Authlib>=1.3.2` 추가, `[auth]`의 정확한 `/oauth2callback` redirect URI·강한 `cookie_secret`·OIDC client ID/secret·discovery URL이 필요하다. 로컬 검증 venv에는 Authlib가 없다(운영 설치 여부 미확인). Streamlit 공식 identity cookie는 새 탭/새 세션을 복구하고 30일 뒤 만료되나 ID token 만료·Supabase 세션 폐기와 연동되지 않는다. `st.logout()`은 현재 세션의 identity cookie만 지우고 이미 열린 다른 세션·IdP 쿠키는 남는다. **1.50은 OIDC access token을 버리고 `st.user`에 ID token claim만 제공**한다. Community Cloud의 공식 OIDC 배포 튜토리얼은 있으나 이 Supabase 조합의 운영 호환은 검증 전이다.
- **Supabase OIDC·현재 사용자 계약**: [Supabase OAuth Server](https://supabase.com/docs/guides/auth/oauth-server)는 기존 이메일/비밀번호 사용자를 그대로 인증할 수 있고 OIDC ID token의 `sub`는 user ID다([OAuth flows](https://supabase.com/docs/guides/auth/oauth-server/oauth-flows)). 따라서 `st.user.sub`를 **검증된 동일 Supabase project의 `auth.users.id`와 대조**해 읽담의 `AuthUser.id`로 연결하면, 현재 `books/activities/reading_chunks.owner_id`, `profiles.id`, 그룹 membership의 ID 계약은 이론상 보존된다. 이메일만으로 소유권을 다시 연결하지 않는다. 단 실제 운영 사용자 ID와 claim의 일치·부재/재가입/이메일 변경 사례는 격리 검증 전이며 **자동 호환 완료 판정은 아니다**. 읽담은 서버 PostgreSQL·service-role Storage와 앱 내부 ID 검사로 접근하고, 1.50의 `st.login`은 Supabase access token을 노출하지 않으므로 Supabase user-token Data API/RLS 호출을 그대로 대체하지 못한다. OAuth access token 자체는 기존 RLS claim을 가진다([Supabase token security](https://supabase.com/docs/guides/auth/oauth-server/token-security)).
- **설정·위험**: OAuth Server 활성화, 별도 웹 authorization/consent UI, confidential OAuth client·secret, exact redirect URI, OIDC discovery, Streamlit Secrets가 필요하다. [Supabase 시작 문서](https://supabase.com/docs/guides/auth/oauth-server/getting-started)는 **Public Beta**이며 OIDC ID token 발급에는 RS256/ES256 비대칭 signing key가 필요하다고 명시한다. 현재 프로젝트 signing key 종류·OAuth Server 준비 상태는 Secrets/운영 설정에 접근하지 않아 미확인이다. [Streamlit `st.user` 문서](https://docs.streamlit.io/1.50.0/develop/api-reference/user/st.user)에 따르면 ID token 만료를 자동 검사하지 않는다. 30일 identity cookie를 기존 privileged DB 연결과 함께 쓰면 Supabase 사용자 폐기 후 권한이 오래 남을 위험이 있어 만료·재검증 정책이 선행돼야 한다.
- **비교·추천**: 공식 Streamlit+Supabase OIDC는 **조건부 장기 우선안**이나 현재 바로 전환할 작은 설정 변경은 아니다. Beta·서명 키·authorization UI·Authlib·1.50의 access-token 부재·재검증 정책을 격리 PoC에서 통과시켜야 한다. 대안 C인 Streamlit v1 양방향 component는 가능하나 refresh token을 JS에서 읽고 component 메시지로 Python에 보내므로 XSS·전달면·세션 보관 위험이 남고 iframe/Safari 운영 검증과 자체 유지보수가 필요하다. 현 단계의 최소 안전 상태는 기존 수동 로그인 유지, 기존 임시 진단 UI 유지, JS 쿠키 방식 추가 패치 중단이다.
- **어디까지 끝났는지**: 설계 감사와 이 HANDOFF·WORKLOG 기록만 완료; 인증 코드·requirements·Secrets·Supabase·DB·오늘의 서재·통합 계약·배포 변경 0. clean `main` `/private/tmp/readdam-login-persist` 시작 `9f7aedf`; 로컬 tracking origin/main=deploy/main=`9f7aedf`지만 이번 실제 `ls-remote`는 GitHub DNS 실패로 원격 현재 SHA 독립 확인 불가. David는 진단 UI가 운영에 있다고 보고했고 실행 SHA는 직접 확인하지 않았다. P0-B 「희망을 짓는다는 것」 기존 두 행 상태·직접 누락 원인 미확정, 별도 과제로 유지.
- **확인해야 할 것 / David 결정**: Public Beta·비대칭 서명 키 전환·별도 authorization UI와 인증 UX 변경을 감수해 **격리 OIDC 적합성 검증**을 승인할지 결정한다. 이후 production 설정 변경·코드 구현은 각각 별도 승인 범위다.
- **다음 작업자 / 다음 작업 1개**: David 결정 후, 운영 변경 없이 별도 환경에서 **Supabase OIDC `sub` ↔ 기존 user ID와 Streamlit 1.50 인증·만료 정책 적합성**을 검증하는 설계/PoC를 한다.
- **브랜치 / 커밋 / 배포 상태**: `main` / 이 기록 커밋 / 신규 push·deploy 없음.
- **보류·실패·중단 이유**: OIDC Beta 및 필수 설정·기존 owner ID 실제 대조·st.user 만료/폐기 정책 미검증. C는 보안·브라우저 운영 증거 부족. 추가 Safari 개발자도구 조작을 요청하지 않는다.

## 읽담 담당자가 이어받을 작업 — 로그인 복원 서버 경계 확인, 비밀값 없는 진단은 로컬 구현 (2026-09-29, Codex)

- **무엇을 했는지**: Work 브라우저 진단은 종료했다. David의 운영 증거는 `__Host-readdam-refresh` 쿠키 write·재접속 persistence PASS, 동일 host `wss /_stcore/stream` 101 PASS, **그 WebSocket Cookie 전달 FAIL**, 자동 복원 FAIL이다. 코드의 `components.html`은 iframe에서 `window.parent.document.cookie`로 앱 부모 문서에 쓰며 `__Host-` 요구조건인 `Secure; Path=/; Domain 미지정`을 충족한다. `SameSite=Strict; Max-Age=2592000`이다. Streamlit 1.50의 `st.context.cookies`는 최초 WebSocket request에서 읽으므로, 확인된 쿠키 미전달에서는 `refresh_session`·session_state 복원에 도달하지 못한다. Safari가 WebSocket Cookie를 제외한 **근본 이유**와 일반 HTTP Cookie 전달 여부는 미확정이다. `/api/v2/user/details` 404는 읽담의 직접 refresh 호출이 아니며 관련성은 미확정이다.
- **어디까지 끝났는지**: `lib/auth_cookie.py`에 서버 최초 요청의 쿠키 **이름 존재 여부만** 보는 함수를 추가했다. `app.py` 로그인 화면에 `server_cookie_name_seen`, `restore_attempted`, `refresh_success`, `session_restored`, `failure_stage`의 YES/NO/UNKNOWN 또는 단계명만 표시한다. token·cookie 값·비밀번호·Supabase credential·예외 본문은 진단 상태나 화면에 넣지 않는다. 로그인/로그아웃 동작과 인증 구조는 그대로다. 기능·테스트 local main 커밋 `804b512`; 전체 **273 PASS**, Python compile(허용된 `/private/tmp` pycache)·diff check PASS. 원격 push·deploy·운영 진단 화면 확인은 없다. 운영 DB/iCloud write 0.
- **확인해야 할 것**: 현재 JS cookie → 최초 WebSocket `st.context.cookies` 경로는 **이번 Safari 접속에서는 서버 복원에 실패**했다. `SameSite` 등을 추측으로 바꾸지 않는다. 더 작은 대체 구조 후보는 Streamlit v1 양방향 custom component로 브라우저 저장 쿠키를 Python 세션에 전달하는 방법이며 새 패키지는 필수 아님. 다만 refresh token이 컴포넌트 메시지와 세션으로 이동하는 보안 영향·구현/운영 검증이 있어 David 승인 전에 적용하지 않는다. 설치된 Streamlit 1.50에는 components v2가 없다. 진단 화면을 운영에 반영하려면 실제 원격을 다시 확인하고 별도 승인된 push·deploy가 필요하다. David에게 Safari 개발자도구 추가 조작을 요구하지 않는다.
- **P0-B**: 「희망을 짓는다는 것」 두 운영 행의 이번 READ ONLY 재조회는 `OperationalError`로 연결 단계에서 실패했다(비밀값 미출력). 이전 감사의 위시리스트/읽는 중 2건 외 현재 id·status·start_date·정렬순위·연결 데이터는 미확정이다. 미래 새 책용 `6064b1b`은 기존 운영 행을 수정하지 않는다. 두 행의 삭제·병합·상태 변경 없음.
- **다음 작업자 / 다음 작업 1개**: David가 진단 기능 운영 반영을 요청하면, 실제 원격 SHA를 대조해 안전하게 배포한 뒤 **일반 로그인 화면만**으로 `server_cookie_name_seen`과 실패 단계를 확인한다.
- **브랜치 / 커밋 / 배포 상태**: clean `main` worktree `/private/tmp/readdam-login-persist`; 시작 `95f7354`, 기능 `804b512` + 이 기록 커밋. 로컬 추적 origin/main=deploy/main=`06bc5e1`이고 이번 세션 실제 `ls-remote`는 github.com DNS 실패로 독립 확인 불가. 운영 실행 SHA 미확인. 사용자 원본 작업트리 기획문서 2건, 오늘의 서재, 통합 계약 불변.
- **보류·실패·중단 이유**: WebSocket 쿠키 미전달의 브라우저/Cloud 내부 이유 미확정; DB와 GitHub 원격 DNS/연결 실패. 인증 대체 구조·운영 데이터 변경은 승인 전 중단한다.

## 읽담 담당자가 이어받을 작업 — Safari 쿠키 지속 PASS, 서버 복원 경계 미확인 (2026-09-29, Codex)

- **무엇을 했는지**: David가 실제 Safari Console에서 `document.cookie.includes("__Host-readdam-refresh=")`를 정상 로그인 직후와 탭을 닫고 운영 URL을 다시 연 로그인 화면에서 모두 `true`로 확인했다. 따라서 **브라우저 cookie write·탭 종료 후 persistence는 PASS, 자동 로그인 복원은 FAIL**이다. refresh token 값은 보거나 기록하지 않았다.
- **코드 대조**: 새 Streamlit 세션에서 `require_authenticated_user`는 `st.context.cookies`를 한 번 읽고 값이 있으면 `auth.refresh_session(cookie)`를 호출한 뒤 `auth_user`·access/refresh token·만료시각을 session_state에 넣는다. 쿠키 읽기 오류는 `read_refresh_cookie`에서 None으로 숨겨지고 refresh 오류는 `AuthError`로 처리·쿠키 삭제 뒤 로그인 화면으로 돌아가므로 현재 화면만으로 cookie 미전달·read 실패·refresh 실패를 구분할 수 없다. 설치된 Streamlit 1.50 소스에서 `st.context.cookies`는 **WebSocket 최초 요청**의 쿠키를 읽는다. David의 `document.cookie=true`는 이 요청에 실제 쿠키가 실렸는지까지 입증하지 않는다. 기존 테스트는 쿠키 read/write와 Supabase refresh를 mock으로 대체했다.
- **404 대조**: David가 같은 재접속 상태에서 Safari 404 경로 `/api/v2/user/details`를 확인했다. 읽담 앱 코드·설치된 Streamlit 오픈소스 패키지에 해당 경로 호출은 없고, 읽담의 Supabase refresh는 서버에서 `POST token?grant_type=refresh_token`으로 실행된다. 따라서 이 404는 **읽담의 직접 refresh 요청이 아니다**. 호스트·Initiator 미확인이라 Streamlit Cloud/브라우저 확장 등 실제 호출 주체와 간접 영향은 미확정이며 root cause 또는 무관한 노이즈로 단정하지 않는다.
- **어디까지 끝났는지**: 코드·테스트·운영 DB·iCloud 변경 0. 이 HANDOFF·WORKLOG·PROJECT만 기록 커밋으로 갱신한다. 시작 local main=`a40368c`; 로컬 추적 origin/main=deploy/main=`06bc5e1`(David의 직접 push 근거), 실제 원격/Streamlit 실행 SHA는 이 세션에서 독립 확인하지 않았다. 앞선 책장 수정 `6064b1b`과 기록 `a40368c`는 여전히 local-only다. 기존 사용자 문서 2건 및 오늘의 서재·통합 계약은 불변이다.
- **확인해야 할 것**: Safari 재접속의 `/_stcore/stream` WebSocket 요청 Cookie 헤더에 **쿠키 이름만** 존재하는지, 404의 호스트·Initiator만 확인한다(값/쿼리/헤더 전문 공유 금지). WebSocket에 실렸는데 복원이 실패하면 token 비노출 상태로 서버의 `st.context.cookies` 존재 여부→refresh 호출/예외 종류→session_state 복원·rerun 유지 순서로 진단해야 한다. 토큰 값은 로그·문서·보고에 남기지 않는다.
- **다음 작업자 / 다음 작업 1개**: 운영 증거를 확인할 수 있는 읽담 담당자 — **새 WebSocket 요청의 쿠키 이름 전달 여부와 404 호출 주체를 확인해 서버 복원 실패 경계를 좁힌다**.
- **브랜치 / 커밋 / 배포 상태**: `main` / 기존 배포 `06bc5e1`, 로컬 `a40368c` + 이 기록 커밋 / 신규 push·배포 없음. Safari 로그인 지속성 FAIL 유지.
- **보류·실패·중단 이유**: 운영 브라우저 자동 접근 거부와 Codex 환경의 원격/DB DNS 제약으로 서버-side 쿠키·Supabase refresh 결과의 실제 값은 미확인이다. 추측에 따른 인증 코드 변경은 하지 않았다.

## 읽담 담당자가 이어받을 작업 — Safari 로그인 실패·읽는 중 누락 운영 증거 확보 (2026-09-28, Codex)

- **무엇을 했는지**: 아래의 “배포 대기” 기록은 David가 실제 Mac Terminal에서 origin/main과 deploy/main에 `06bc5e1`을 각각 정상 push한 사실로 대체한다. 이 세션의 local main·origin/main·deploy/main 추적 ref도 시작 시 모두 `06bc5e1`이었다. 다만 Codex 환경의 GitHub DNS 실패로 원격 현재 SHA를 독립 재조회하지 못했고 Streamlit 실행 SHA도 직접 확인하지 못했다. David의 실제 Safari 결과는 **로그인할 때마다 다시 로그인 화면: LOCAL TEST PASS / 사용자 push 후 REAL SAFARI FAIL**이다.
- **로그인 감사**: 로그인→refresh token 획득·session_state 저장→rerun 뒤 `components.html`에서 부모창 쿠키 write→새 Streamlit 세션의 `st.context.cookies` read→Supabase refresh→session_state 복원 경로를 추적했다. 기존 21개 테스트는 쿠키 read/write와 Supabase 호출을 mock으로 대체했으므로 Safari에서 쿠키가 실제 설정·전달되는지를 검증하지 않는다. 현재 cookie write/read/refresh 중 어느 단계가 실패했는지 **미확정**이다. 운영 브라우저 탭 자동 접근은 사용자가 거부했으며 우회하지 않는다. David에게 쿠키 **이름의 존재 여부만**(값 제외) 로그인 직후·재접속 뒤 확인해 달라고 요청했다. 인증 코드 변경은 없다.
- **책장 감사·수정**: 이전 읽기 전용 운영 감사에는 「희망을 짓는다는 것」 2권이 위시리스트/읽는 중으로 기록돼 있다(현재 각 행의 id·상태·카테고리는 재확인 불가). 이번 운영 DB read-only 연결은 Supabase pooler 호스트 DNS 실패로 SQL 실행 전 중단됐다. 코드에서 새 책을 `읽는 중`으로 저장해도 `start_date`가 NULL이고, ‘이어서 읽기’는 최근순 `head(6)`만 보이는 결함을 합성 DB RED로 재현했다. 기능 `6064b1b`은 **앞으로 새로 저장할 읽는 중 책의 시작일만 기록**한다(기존 운영 책 데이터·두 중복 행은 불변). 이 결함이 현재 2권 중 읽는 중 행의 실제 누락 원인인지는 start_date·정렬 순위 확인 전까지 미확정이다. 전체 읽는 중 목록은 별도 버튼으로 접근 가능하며, 중복 자체를 숨기는 쿼리는 없다.
- **어디까지 끝났는지**: 기능 `6064b1b` local main 반영, 신규 RED→GREEN, 전체 **270 PASS**, Python compile·diff check PASS. HANDOFF·WORKLOG·PROJECT는 후속 기록 커밋. 이번 작업의 origin push·deploy push·Streamlit 갱신·운영 DB/iCloud write는 0이다. 원본 사용자 기획문서 2건과 상위 공동 저장소는 보존했고 오늘의 서재·통합 계약은 변경하지 않았다.
- **확인해야 할 것**: Safari에서 쿠키 이름이 로그인 직후와 재접속 뒤 존재하는지(값은 절대 공유하지 않음) 확인한다. GitHub/DB DNS가 정상인 환경에서 두 원격 실제 SHA와 운영 책 2행의 상태·시작일·최근활동·상단 6위 내 순위를 읽기 전용으로 확인한다. 해당 책의 삭제·병합·상태·시작일 수정은 David 결정 전 금지한다.
- **다음 작업자 / 다음 작업 1개**: 운영 증거 확보 가능한 읽담 담당자 — **Safari 쿠키 존재 여부와 두 책의 read-only 상태·정렬 순위를 확보해 두 원인을 확정**한다.
- **브랜치 / 커밋 / 배포 상태**: clean `main` / 기존 배포 `06bc5e1`, 로컬 기능 `6064b1b` + 이 기록 커밋 / 신규 수정은 origin·deploy 미반영. 운영 로그인 지속성은 실패, 새 책 정렬 수정은 운영 미확인.
- **보류·실패·중단 이유**: 운영 브라우저 접근 거부 및 GitHub·Supabase DB 호스트 DNS 실패로 실제 cookie/DB 값 증거가 없다. 대규모 인증 변경·운영 데이터 정리는 착수하지 않았다.

## GitHub 연결 가능한 읽담 담당자가 이어받을 작업 — 로그인 지속성 배포 재개, 원격 DNS 재차 실패 (2026-09-28, Codex)

- **무엇을 했는지**: David의 배포 재개 요청에 따라 읽담 최신 HANDOFF/WORKLOG, 통합 Reading Chunk 계약, clean main과 원본 사용자 작업트리를 대조했다. 이번 인증 배포는 오늘의 서재·통합 계약 변경이 아니다. 실제 GitHub `git ls-remote`로 origin/main과 deploy/main을 각각 조회했으나 둘 다 `Could not resolve host: github.com`으로 실패했다.
- **어디까지 끝났는지**: 기존 기능 `70810d0`과 기록 `9b22c5d`가 local main에 있고 작업트리는 clean이다. 직전 21개 인증 테스트·전체 269개·compile·diff PASS 근거는 유지한다. 원격 SHA 확인·origin push·deploy push·Streamlit 갱신·Safari 실제 확인은 **이번 작업에서 진행되지 않았다**. 로컬 추적 ref origin/main=`93479a5`, deploy/main=`3f42a52`는 실제 원격 현재값으로 단정하지 않는다. 이 항목과 WORKLOG만 후속 기록 커밋으로 남긴다.
- **확인해야 할 것**: GitHub에 접속되는 환경에서 실제 origin/main·deploy/main SHA를 각각 조회한다. 예상 계보와 양쪽 fast-forward 가능 여부가 확인될 때만 local main을 일반 push하고 실제 원격을 재조회한다. 배포 후 Streamlit 갱신 확인 및 David Safari 로그인 지속성·로그아웃 검증이 남는다.
- **다음 작업자**: GitHub 연결 가능한 읽담 담당자. 다음 작업 1개는 **두 원격의 실제 SHA 조회 후 안전한 fast-forward 배포**다.
- **브랜치 / 커밋 / 배포 상태**: `main` / 기능 `70810d0`, 기존 기록 `9b22c5d` + 이 기록 커밋 / 원격·운영 미반영.
- **보류·실패·중단 이유**: 현재 Codex 실행환경의 GitHub DNS 해석 실패. 원본 `codex/reading-chunks-1a`의 David 소유 기획문서 수정 1건·미추적 1건과 상위 공동 저장소의 기존 미추적 항목은 그대로 보존했다. 제품 코드·오늘의 서재·통합 계약·운영 DB·iCloud 변경은 없다.

## GitHub 연결이 정상인 읽담 담당자가 이어받을 작업 — 로그인 지속성 로컬 구현 완료, 원격 반영 대기 (2026-09-28, Codex)

- **무엇을 했는지**: Intel i9 Mac의 clean main worktree `/private/tmp/readdam-login-persist`에서 David가 승인한 Supabase 로그인 지속성·사이드바 로그아웃·책장 HTML 제목 escape를 구현했다. 로그인 성공 또는 새 세션 복구 시 refresh token을 `__Host-readdam-refresh` 쿠키로 쓰고, 활성 세션의 토큰 만료 전에도 refresh/rotation을 처리한다. 실패하면 쿠키·로컬 인증 상태를 지우고 로그인 화면으로 돌아간다. 비밀번호는 지속 저장하지 않는다.
- **보안 경계**: 쿠키는 `Secure; SameSite=Strict; Path=/; Max-Age=2592000`(최대 약 30일 목표, Safari 실제 제한과 Supabase 세션 정책에 따름). Streamlit의 읽기 전용 `st.context.cookies`와 기존 `components.html` 부모창 JavaScript를 연결했으므로 **HttpOnly는 불가능**하고 XSS가 남은 위험이다. `unsafe_allow_html`에 삽입되던 책장 제목을 escape했다. 그 밖의 전체 앱 HTML 감사·재작성은 하지 않았다.
- **어디까지 끝났는지**: 기능 커밋 `70810d0`을 local main에 반영했다. 인증 관련 21 PASS, 전체 269 PASS, Python compile PASS, diff check PASS. 이 HANDOFF·WORKLOG·PROJECT 갱신은 후속 기록 커밋이다. **origin/main push·deploy/main 반영·Streamlit 운영 확인은 아직 없다.** 이번 세션의 실제 `git ls-remote origin`은 `Could not resolve host: github.com`으로 실패해 원격 상태를 확인하지 못했다. 로컬 추적 ref는 origin/main=`93479a5`, deploy/main=`3f42a52`이지만 실제 원격 SHA로 단정하지 않는다.
- **확인해야 할 것**: GitHub 연결이 정상인 환경에서 실제 origin/main·deploy/main SHA를 다시 조회하고 fast-forward 관계 및 diff를 대조한 뒤 local main→origin/main→deploy/main을 일반 push한다. Streamlit 갱신 뒤 David가 Safari에서 로그인→탭 닫기·재접속→자동 복구→로그아웃→재접속 시 로그인 화면을 실제 검증한다. 이 세션에는 운영 브라우저 검증이 없다.
- **다음 작업자**: GitHub 연결이 정상인 읽담 담당자. 다음 작업은 **원격 SHA 대조 후 안전한 fast-forward 배포 1건**이다.
- **브랜치 / 커밋 / 배포 상태**: `main` / 기능 `70810d0` + 이 기록 커밋 / 원격·운영 미반영. 오늘의 서재와 Reading Chunk 계약은 변경하지 않았다.
- **보류·실패·중단 이유**: 현재 Codex 실행환경의 github.com DNS 해석 실패로 원격 확인과 push를 진행할 수 없다. 원본 `codex/reading-chunks-1a` 작업트리의 David 소유 기획문서 수정·미추적 각 1건은 그대로 보존했다.

## David가 이어받을 작업 — i9 복귀 정본 대조 완료, 로그인 지속성 계획 승인 대기 (2026-09-28, Claude Code)

- **무엇을 했는지**: 실행환경은 Intel i9 Mac 실제 Terminal / Claude Code다. David가 M1에서 i9로 옮겨온 뒤 3층(읽담·오늘의 서재·통합 계약) 기록을 실제 Git과 대조했다. 코드 변경은 없다.
- **정본 대조 결과(일치)**
  - **읽담**: 실제 `git ls-remote` 결과 origin/main = deploy/main = `3f42a52`로, David 전달값과 같다. 성능 개선 `679cb6a`(사이드바 이중 rerun 제거·category 캐시·Chunk 중복 조회 제거, 256 tests)와 그 앞의 중복 책 방지 `0fc97e2`, 책장 NaN 핫픽스 `f4f3179`를 포함한다. i9 local main은 `0cbe841`에서 `3f42a52`로 fast-forward만 했다. 남은 dispatch/`st.rerun` 구조개편은 David 체감상 충분해 **보류**다.
  - **오늘의 서재**: 독립 저장소이고 remote가 없다. local `main` = `28cfe37`(v33 + Reading Chunk RC-only 통합, 141 tests). 운영 Sites는 v33 그대로다. 원본 작업트리는 `codex/apple-reminder-roundtrip`(`9430ce6`, 과거 상태)에 있고, 미추적 `.claude/`와 `.command` 2개가 있다.
  - **통합(동하비서 `CROSS_PROJECT_HANDOFF.md`)**: 공동 main은 `4a610de`(remote 없음)다. 최신 절은 "1차-B 운영 대기·2차 실제 dry-run PASS"다. `codex/reading-chunk-category-contract`의 `188ac7b`(카테고리 계약 +7줄)는 공동 main에 미반영이다.
  - **공통 blocker**: Sites 관리형 D1 `0004` 공식 migration lifecycle 미확인 → 1차-B 운영 연결 BLOCKED(두 저장소 기록 일치). 2차 실제 export는 대상 0건이라 미실행이다.
- **환경 주의**: 읽담 `.git`의 worktree 목록에 M1 경로(`/private/tmp/readdam-*`, 오늘의 서재의 `/Users/srapdlem1/...`)가 prunable로 보인다. 두 Mac이 같은 `.git`을 동기화(iCloud Documents 추정)해 공유하는 것으로 보인다. 두 Mac에서 동시에 git 작업을 하면 index/ref가 깨질 위험이 있으니 한 번에 한 Mac에서만 작업한다. prunable 항목은 정리하지 않았다. i9 원본 `.venv`는 arm64 전용이라 테스트는 세션 임시 venv로 돌린다.
- **다음 작업(승인 대기): 로그인 지속성**
  - **원인**: 로그인 결과를 `st.session_state`(브라우저 연결 1개 수명)에만 두고 Supabase refresh token은 버린다. 앱을 다시 열면 새 세션이 되어 로그인 화면이 다시 나온다. 로그아웃 기능도 없다.
  - **계획**: 로그인 성공 시 Supabase refresh token을 앱 도메인 1st-party cookie(Secure·SameSite=Strict·약 30일)로 저장한다(기존 `components.html` 부모 창 스크립트 방식 재사용, 새 의존성 없음). 새 세션에서는 `st.context.cookies`로 읽어 `auth.refresh_session`으로 복원하고, 회전된 새 refresh token으로 cookie를 갱신한다. 실패·만료 시 cookie를 지우고 기존 로그인 화면으로 돌아간다. 사이드바에 로그아웃(cookie 삭제 + Supabase sign_out)을 추가한다. schema·Secrets·오늘의 서재 변경은 없다.
- **브랜치 / 커밋 / 배포 상태**: `main`, 이 기록 커밋은 origin/main에만 push한다. deploy/main은 문서만 바뀌는 재배포로 운영 세션이 끊기지 않게 `3f42a52`로 둔다. worktree는 `/private/tmp/readdam-login-persist`다.
- **보류·실패·중단 이유**: 구현은 David 승인 대기다. 원본 작업트리(`codex/reading-chunks-1a`)의 사용자 기획문서 2건(`도서비서_기획문서.md` M, `도서비서_기획문서 2.md` ??)은 불변이다.

## 최신 — 실사용 성능 감사 및 최소 고속화 완료, 남은 병목 보고 (2026-09-28, Claude Code/Orca)

- **무엇을 했는지**: David가 "느려서 이렇게 쓰다가는 안 쓸 것 같다"고 한 것을 P0로 받아 실제 병목을 계측했다(추측 아님). 운영과 같은 규모(705권/5,666건)의 로컬 SQLite에서 `sqlite3.set_trace_callback`으로 SQL 실행 횟수를, 운영 Postgres에는 읽기 전용으로 접속해 실제 왕복 지연시간을 실측했다. 가장 큰 병목은 **버튼 클릭마다 `db.get_connection()`(스키마 검사 포함)이 정확히 2번씩 실행**되는 것이었다(직접 계측으로 확인: 클릭 1회당 connect 호출이 1→2로 늘어남). 원인은 이미 클릭이 스크립트를 한 번 재실행시켰는데 핸들러 안에서 다시 `st.rerun()`을 불러 그 실행을 버리고 통째로 한 번 더 도는 패턴. 사이드바 네비게이션처럼 최종 view 분기보다 먼저 실행되는 버튼은 `st.rerun()` 없이도 같은 실행 안에서 분기가 갱신된 `session_state.view`를 그대로 읽으므로 안전하게 제거했다. 제거 과정에서 버튼에 명시적 `key`가 없어 `type`(active 여부로 매번 바뀜)만으로 위젯을 식별하다 연속 두 번째 클릭이 반영 안 되는 문제를 발견해 `key=f"nav_{label}"`로 같이 고쳤다(AppTest로 재현·수정 확인). 추가로 책장의 `list_categories` 중복 호출(화면당 2~3회, DB 식별자 포함 `st.cache_data(ttl=10)`로 캐싱, DB 섞임 없음을 직접 검증)과 Reading Chunk의 `list_for_book` 중복 호출(태그 있는/없는 버전 각각 쿼리 → 한 번만 조회 후 파이썬에서 필터)도 고쳤다.
- **Reading Chunk 최종 UX 계약 감사(코드 변경 없음, 확인만)**: 자동 추천·기본 체크·확인/수정·읽담 정본 저장까지는 계약과 일치한다(`_category_panel`이 저장 직후 자동으로 뜨고, 강한 추천은 `defaultChecked`로 미리 체크되며, `set_illustration_tags`로 읽담 DB에 저장됨). **가장 큰 차이는 "이후 Mac 자동 export"다 — 현재는 자동화가 전혀 없고 `tools/export_chunks.py --output-root <경로> --owner-id <id> --chunk-id <id>`를 사람이 직접 실행해야 한다.** cron/launchd 등 자동 트리거도 없다. 이번 작업에서 새로 만들지 않았다(요청대로 감사만).
- **어디까지 끝났는지**: 전체 pytest 256개 통과, py_compile·git diff --check 통과. `perf/audit-2026-09-28` 브랜치 커밋 `679cb6a`(`main` `021b00d`=중복 방지 기능 직후에서 분기). `main`을 그 커밋으로 fast-forward해 **origin과 deploy 모두에 push·운영 배포 완료**(둘 다 `021b00d` → `679cb6a`). 실제 운영 브라우저 체감 확인은 하지 않았다(세션에 브라우저 연결 없음).
- **확인해야 할 것**: 실제 운영 브라우저로 체감 속도 확인. 아래 "다음 병목"은 이번에 고치지 않았다.
- **다음 작업자에게 남긴 병목(순서대로)**:
  1. **다른 화면 전환용 `st.rerun()` 전반**(책 상세 진입, Reading Chunk 폼/카테고리 패널 열고닫기, 필터 단축 버튼 등) — 클릭 1번이 스크립트 실행 2번(연결·스키마 검사·해당 화면 조회 전부 중복)이 되는 구조는 사이드바와 동일하다. 단 이 버튼들은 대부분 **최종 view 분기가 이미 결정된 뒤(자식 함수 안)**에서 실행되므로, 단순 제거가 아니라 dispatch를 반복 평가하는 구조(예: while 루프)로 바꿔야 안전하다 — 구조 변경이라 이번에는 보류.
  2. **책 상세 진입 시 `db.get_book` 5회, `reading.active` 3회** 중복 조회(app.py 사이드바, notebook_ui, timer_ui, record_ui, sharing_ui가 각자 다시 조회). 이미 상위에서 받은 `book`을 넘기거나 쓰기 후 무효화되는 캐시가 필요해서, list_categories처럼 단순 TTL 캐시만 넣으면 책 정보 수정 직후 다른 컴포넌트가 옛 값을 보여줄 위험이 있어 이번엔 보류.
  3. **require_schema(스키마 무결성 검사)가 매 스크립트 실행마다 재실행**됨(운영 Postgres 실측 4쿼리, 약 70~90ms). 세션당 한 번만 검사하도록 캐싱하면 확실히 빨라지지만, "스키마가 실행 중 바뀔 수 있다"는 이 검사의 존재 이유(운영 안전장치)와 상충할 수 있어 David/설계 판단이 필요해 보고만 한다.
- **브랜치**: `perf/audit-2026-09-28` (별도 워크트리 `/private/tmp/readdam-perf-audit/readdam`). 원본 `codex/reading-chunks-1a` 작업트리와 사용자 미커밋 기획문서 2개는 건드리지 않았다.
- **커밋**: 기능 `679cb6a`. 이 HANDOFF·WORKLOG 기록은 같은 브랜치의 후속 문서 커밋.
- **배포 상태**: **origin/main과 deploy/main 모두 `679cb6a`로 배포 완료.** Reading Chunk 로직·오늘의 서재·통합 계약(CROSS_PROJECT_HANDOFF.md)은 건드리지 않았다.
- **보류·실패·중단 이유**: 없음(중단 기준에 해당하는 큰 구조 변경·schema 변경·새 서비스 필요 없이 완료). 위 "다음 병목" 3건은 회귀 위험 또는 설계 판단이 필요해 의도적으로 보류했다.

## 최신 — 새 책 추가 중복 검사 기능 완료 (2026-09-28, Claude Code/Orca)

- **무엇을 했는지**: "새 책 추가"에서 이미 등록된 책을 실수로 중복 저장하는 문제를 막았다. ISBN이 있으면 정규화(하이픈/공백 제거) 동일 여부를 최우선 기준으로 저장을 막는다(폼 제출 시점에 다시 검사해 검색을 거치지 않은 수동 입력·재제출도 막는다). ISBN이 없을 때만 제목+저자가 모두 같으면 경고 후 "그래도 추가"로 확인받는다(reading_chunks의 기존 "그래도 저장" 패턴 재사용). 제목만 같은 동명이서는 막지도 경고하지도 않는다. 검색 결과는 숨기지 않고, 이미 있는 후보는 "✓ 이미 내 책장에 있음"으로 표시하며 "기존 책으로 이동" 버튼을 우선 제공한다.
- **운영 데이터 감사(읽기 전용, 삭제·병합 없음)**: "희망을 짓는다는 것"(엘렌 데이비스)이 상태만 다르게 **2권 진짜 중복** 등록돼 있었다(아직 정리 안 함, 다음 작업 참고). ISBN "2147483647"(2^31-1, 정수 오버플로 sentinel로 보임)을 서로 무관한 책 **12권**이 공유하고 있어 `normalize_isbn()`에서 이 값을 무효 처리하도록 제외했다. "역사지리로 보는 성경 세트" 1~3권은 세트 공용 ISBN을 공유하는 정상 케이스(중복 아님)였다 — 다권 세트가 향후 ISBN만으로 오탐될 수 있는 알려진 한계로 남겨뒀다. 제목+저자 기준 약한 중복은 0건이었다.
- **어디까지 끝났는지**: 전체 pytest 256개 통과(신규 회귀 테스트 18개 포함), py_compile·git diff --check 통과. `feature/add-book-dedup` 브랜치 커밋 `0fc97e2`(`main` `a3f44e2`=P0 핫픽스 직후에서 분기). `main`을 그 커밋으로 fast-forward해 **origin과 deploy 모두에 push·운영 배포 완료**(둘 다 `a3f44e2` → `0fc97e2`). 실제 운영 브라우저 시각 확인은 하지 않았다.
- **확인해야 할 것**: (1) 실제 운영 화면에서 검색 결과 표시·기존 책 이동·저장 차단·경고 흐름이 브라우저로 정상 동작하는지, (2) 기존 검색·서지정보 자동입력·카테고리·Reading Chunk에 회귀가 없는지, (3) "희망을 짓는다는 것" 기존 중복 2건을 병합/삭제할지 David 결정.
- **다음 작업자**: 운영 브라우저 검증 가능한 세션. 위 "희망을 짓는다는 것" 중복 2건 정리는 David 결정 후 별도 작업으로 진행한다(이번 커밋은 건드리지 않았다).
- **브랜치**: `feature/add-book-dedup` (별도 워크트리 `/private/tmp/readdam-dup-check/readdam`에서 작업). 원본 `codex/reading-chunks-1a` 작업트리와 그 안의 사용자 미커밋 기획문서 2개는 건드리지 않았다.
- **커밋**: 기능 `0fc97e2`. 이 HANDOFF·WORKLOG 기록은 같은 브랜치의 후속 문서 커밋.
- **배포 상태**: **origin/main과 deploy/main 모두 `0fc97e2`로 배포 완료.** Reading Chunk 1차-A/1차-B, 통합 계약(CROSS_PROJECT_HANDOFF.md)은 건드리지 않았고 기존 상태를 그대로 유지한다.
- **보류·실패·중단 이유**: 없음. 기존 중복 데이터 삭제·병합은 이번 작업 범위 밖(요청에 따라 존재 여부만 보고)이라 의도적으로 하지 않았다.

## 최신 — P0 운영 책장 TypeError/StreamlitAPIException 복구 완료 (2026-09-28, Claude Code/Orca)

- **무엇을 했는지**: David가 모바일에서 새 카테고리("분별력")를 직접 입력해 책을 저장한 뒤 책장으로 돌아오면 화면이 죽는 P0를 조사·재현·수정했다. Root cause: Postgres 경로에서 `pages` 같은 숫자 컬럼에 NULL이 한 행이라도 섞이면 pandas가 그 컬럼 전체를 float64로 승격시켜 NULL이 None이 아니라 NaN이 된다. NaN은 파이썬에서 참으로 판정돼 `shelf_ui._cover_card`의 `book['pages'] or 0`가 NaN을 그대로 넘기고 `st.progress(nan)`이 `StreamlitAPIException`을 던졌다. 스크린샷의 `db.cover_source(...)` 프레임은 예외가 표시된 위치였을 뿐 root cause는 아니었다. `notebook_ui.cards()`가 이미 쓰는 `pd.isna()` 정규화 패턴을 `_cover_card` 진입부에 그대로 적용해 고쳤다. `lib/database.py`의 `read_frame`을 고치는 방법도 검토했으나 pandas `future.infer_string` 'str' dtype을 깨서 기존 `test_cards_normalize_missing_values_from_new_pandas_string_dtype` 테스트를 회귀시켜 채택하지 않았다.
- **어디까지 끝났는지**: 실제 크래시를 재현하는 회귀 테스트 추가(수정 전 상태로는 진짜로 실패함을 확인) 후 전체 pytest 238개 통과, py_compile·git diff --check 통과. `hotfix/shelf-nan-progress-crash` 브랜치에서 커밋 `f4f3179` 생성 후, `main`을 그 커밋으로 **fast-forward하여 origin과 deploy 모두에 push·운영 배포 완료**했다(둘 다 `0cbe841` → `f4f3179`). Streamlit Community Cloud는 deploy/main 변경 시 자동 재배포되며, 재배포 후 실제 새 카테고리 등록→책장 진입 브라우저 검증은 아직 하지 않았다(아래 확인 항목).
- **확인해야 할 것**: 재배포 완료 후 실제 운영 앱에서 (1) 새 카테고리 직접 입력→책 저장→책장 진입이 죽지 않는지, (2) 기존 책·표지·검색이 정상인지, (3) Reading Chunk 관련 화면에 영향이 없는지(이번 수정은 `lib/shelf_ui.py`와 테스트 파일만 건드렸고 reading_chunks 코드는 만지지 않았다) 브라우저로 한 번 확인이 필요하다.
- **다음 작업자**: 운영 브라우저 검증을 할 수 있는 작업자(Safari/Chrome 연결 가능한 세션). 이상 없으면 이 항목의 "확인해야 할 것"에 결과만 추가하면 된다.
- **브랜치**: `hotfix/shelf-nan-progress-crash` (별도 워크트리 `/private/tmp/readdam-p0-shelf-repro/readdam`에서 작업, 원본 `codex/reading-chunks-1a` 작업트리와 그 안의 사용자 미커밋 기획문서 2개는 건드리지 않았다).
- **커밋**: 기능 `f4f3179`. 이 HANDOFF·WORKLOG 기록은 같은 브랜치의 후속 문서 커밋.
- **배포 상태**: **origin/main과 deploy/main 모두 `f4f3179`로 배포 완료.** Reading Chunk 1차-A/1차-B는 이번 작업과 무관하며 기존 NO-GO 상태를 그대로 유지한다(코드 변경 없음).
- **보류·실패·중단 이유**: 없음. 재현→원인 확정→최소 수정→테스트→배포까지 이번 세션에서 완료했다. 운영 브라우저를 통한 최종 시각 확인만 다음 작업자에게 남긴다.

## M1 읽담 담당자가 이어받을 작업 — i9→M1 이관 Checkpoint (2026-09-28, Claude Code)

이 항목은 이관 시점의 **전체 상태 요약**이다. 아래 이전 항목들의 "다음 작업"은 이 항목으로 대체한다.

- **실행환경**: i9의 읽담전문(Intel i9 Mac 실제 Terminal / Claude Code). 작업 worktree는 `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`(`main`)이다.
- **정본 SHA(이 기록 직전, 실제 ls-remote)**: local main = origin/main = deploy/main = `00f495c`. 이 기록 커밋도 main→origin→deploy에 일반 fast-forward로 올린다. M1에서는 `git fetch` 후 origin/main을 기준으로 삼는다.
- **완료(원격 보존)**
  1. Reading Chunk 1차-A: COMPLETE.
  2. 1차-B(오늘의 서재 pull/ingest/receipt/책 snapshot): 코드는 main·운영 배포에 있다. Secrets가 없어 5분 자동 sync는 `not_configured`로 끝나는 휴면 상태다. **운영 연결은 BLOCKED**: Sites 관리형 D1 `0004` 공식 migration lifecycle이 미확인이다.
  3. 2차 예화창고 exporter: 코드 COMPLETE(명시 CLI 전용). 실제 iCloud dry-run 2회 PASS. eligible illustration Chunk 0건이라 **실제 export 미실행**, iCloud write 0.
  4. 예화 카테고리 추천·승인(63개 snapshot, 승인 keyword 반영): main·운영 배포.
  5. 책장 상단 `＋ 새 책 추가` 바로가기: main·운영 배포.
  6. 도서 검색 title/isbn13 수정(`a5a7a51`): 운영 배포.
  7. 책 서지정보 자동입력(`b8ec52d`): 제목·부제·저자·역자(명시 표기만)·출판사·ISBN·표지. 출간년도·KDC는 참고 표시만 한다. 쪽수·카테고리 자동화는 David 결정으로 하지 않는다.
  8. 새 책 등록 state 유지 버그(`84b1604`): 화면 왕복·재검색·저장 뒤 오염·Enter 제출 수정, 운영 배포.
- **아직 local에만 있는 작업**: 없음. i9에만 있던 이력 브랜치 `codex/reading-chunks-1a`(`1f2d367`)·`codex/reading-chunks-1b`(`90fe1c2`)·`codex/reading-chunks-private-default`(`09c1603`)를 origin에 같은 이름으로 **보존용 push**했다. 이 브랜치들의 제품 내용은 main에 선별 반영돼 있고, 남은 차이는 과거 문서 기록뿐이다. **merge·rebase하지 말고 참고용으로만 쓴다.** 나머지 로컬 codex 브랜치는 모두 main에 포함돼 있다.
- **진행 중/미완료**: 진행 중인 코드 작업은 없다. 남은 것: David의 운영 화면 확인(새 책 등록 유지·자동입력·이전 Enter 시도로 생겼을 수 있는 중복 책), 1차-B 운영 연결(D1 blocker), 2차 실제 export(대상 0건). Streamlit 운영 UI는 i9에 브라우저 도구가 없어 에이전트가 확인하지 못했다(`_stcore/health`만 확인한 이력 있음).
- **blocker**: ① Sites D1 `0004` migration lifecycle 미확인(1차-B 운영 연결). ② i9에서는 원본 `.venv`가 arm64 전용이라 numpy/psycopg가 import되지 않는다. 테스트는 세션 임시 venv로 돌렸다. M1에서는 원본 `.venv`가 정상일 것으로 예상하지만, 첫 작업에서 확인한다.
- **사용자 기존 변경(건드리지 않음)**: 원본 작업트리 `/Users/donghakim/Documents/workspace/동하비서/도서비서`(브랜치 `codex/reading-chunks-1a`, HEAD `1f2d367`)에 `도서비서_기획문서.md` 수정(M)과 `도서비서_기획문서 2.md` 미추적(??)이 있다. commit·stash·reset·삭제 금지. 이 작업트리는 main이 아니므로, 여기서 main 작업을 하지 않는다.
- **임시 worktree(정본 아님, 재부팅 시 사라질 수 있음)**: `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`(main, clean), `/private/tmp/reading-chunk-1b-qfdk556c/readdam`(`codex/reading-chunks-1b`, clean), `/private/tmp/readdam-category-approval-jQMw6o/readdam`(`codex/reading-chunk-category-approval`, clean, main에 포함). 모두 커밋·원격에 보존됐다. M1에서는 이 경로를 쓰지 말고 origin에서 새로 받는다.
- **읽담 범위 밖 참고**: 상위 공동 저장소(동하비서)는 remote가 없고, `codex/reading-chunk-category-contract`의 1커밋(`188ac7b`, 카테고리 공동 계약)이 공동 main에 미반영이다. 이번 작업에서는 건드리지 않았다.
- **다음 작업(1개)**: M1 읽담 담당자가 `git fetch`로 origin/main=deploy/main을 확인하고 M1 `.venv`에서 전체 pytest(현재 기준 237 passed)를 돌려 환경을 검증한다. 그 뒤 David의 운영 새 책 등록 재검증 결과를 받는다.
- **브랜치 / 커밋 / 배포 상태**: `main`, 이 기록 커밋. 제품 코드 변경은 없다.
- **보류·실패·중단 이유**: 없음.

## David가 이어받을 작업 — 새 책 등록 draft 유실 수정, 운영 재검증 (2026-09-28, Claude Code)

- **무엇을 했는지**: 실행환경은 i9의 읽담전문(Intel i9 Mac 실제 Terminal / Claude Code)이다. worktree는 `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, 브랜치는 `main`, 시작 HEAD는 `d0a6c54`다. 운영 증상은 "카테고리 조작 뒤 자동입력 정보가 사라지고, 같은 책을 다시 검색해도 복원되지 않음"이었고, AppTest로 원인을 재현했다. ① 폼이 한 run이라도 그려지지 않으면(다른 화면에 다녀오기) Streamlit이 폼 칸 상태를 지운다. 하지만 `autofill_source` 표시는 남아 있어서, 같은 책을 다시 골라도 "이미 채움"으로 보고 건너뛰었다. ② 폼 안의 '카테고리 직접 입력'에서 Enter를 누르면 폼이 제출되어 책이 저장되고 폼이 비었다. ③ 저장 뒤 폼 칸에 이전 값이 남은 채 자동입력 기록만 지워져, 다음 검색 때 그 값을 사용자 입력으로 보고 교체하지 않았다. ④ 새 카테고리를 적어도 선택 상자가 '직접 입력'이 아니면 무시됐다.
- **수정**: 같은 선택이면 지워진 칸만 draft(`autofill_values`)에서 되살린다. 명시적 검색 뒤에는 같은 책이어도 draft를 다시 적용한다. 저장 뒤에는 draft와 폼 칸 전체를 비운다. 폼은 `enter_to_submit=False`로 바꿨다. 적은 새 카테고리는 선택 상자와 상관없이 저장한다. 폼 안의 카테고리 선택·입력만으로는 원래 rerun이 없어 유실 원인이 아니었다(테스트로 확인).
- **어디까지 끝났는지**: 기능 `84b1604`와 이 기록 커밋을 local main에 두었고, origin/main·deploy/main에 fast-forward push한다(결과는 git 기록으로 확인). schema·검색 API·예화 카테고리·오늘의 서재 변경은 0이다. 전체 237 passed, compile·diff PASS.
- **확인해야 할 것**: David가 운영에서 「희망을 짓는다는 것」을 검색·선택하고 카테고리 선택·새 카테고리 입력(Enter 포함)·다른 메뉴 왕복 뒤에도 정보가 유지되는지 확인한다. 또 이전 시도에서 Enter로 **책이 이미 저장됐을 수 있으니** 책장에 같은 책이 중복됐는지 확인한다. Streamlit 브라우저 smoke는 미확인이다.
- **다음 작업자**: David(운영 재검증 1건).
- **브랜치 / 커밋 / 배포 상태**: `main`, 기능 `84b1604`와 이 기록 커밋. origin/main·deploy/main fast-forward 대상이며, Streamlit 화면은 미확인이다.
- **보류·실패·중단 이유**: 없음. 사용자 기획문서 2건은 불변이다.

## David가 이어받을 작업 — 새 책 검색 선택 시 서지정보 자동입력, 운영 실제 등록 확인 (2026-09-28, Claude Code)

- **무엇을 했는지**: 실행환경은 i9의 읽담전문(Intel i9 Mac 실제 Terminal / Claude Code)이다. worktree는 `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, 브랜치는 `main`, 시작 HEAD는 `4dff9fe`다. 검색 결과를 골라도 표지만 나오고 칸이 비던 원인은 폼 위젯이 `key`로 상태를 유지해 `value=`가 무시된 것이었다. 이제 선택하면 제목·부제·저자·역자·출판사·ISBN의 **빈 칸(또는 직전 자동입력 그대로인 칸)**을 채우고, David가 직접 입력·수정한 값은 덮어쓰지 않는다. 저자 문자열은 명시 표기(`옮김`·`역`·`번역`·`공역`·`[공]옮김` / `지음`·`저`·`[지음]`·`엮음`·`글`)가 있을 때만 저자/역자로 나눈다. 출간년도와 도서관 분류(KDC)는 후보 옆에 **참고용 표시만** 하고 저장하지 않는다.
- **어디까지 끝났는지**: 기능 `b8ec52d`와 이 기록 커밋을 local main에 두었고, 사전 원격 `4dff9fe` 확인 뒤 origin/main·deploy/main에 fast-forward push한다(결과는 git 기록으로 확인). schema·외부 API·예화 카테고리·오늘의 서재 변경은 0이다.
- **확인해야 할 것**: David가 운영 읽담에서 「희망을 짓는다는 것」을 검색해 고르고, 제목·부제·저자 `엘렌 데이비스`·역자 `윤상필`·출판사·ISBN이 채워지는지, 저장 후 책 정보가 보존되는지 확인한다. Streamlit 브라우저 smoke는 브라우저 도구가 없어 **미확인**이다(AppTest로만 검증).
- **보류(추가 source 또는 결정 필요)**: ① 공저자 `오스틴 매키버 데니스`는 upstream에 없어 넣지 않았다(다른 source 필요). ② 전체 쪽수는 data4library가 주지 않아 수동 입력을 유지한다(국립중앙도서관 등 필요). ③ 출간년도는 books에 칸이 없어 저장하려면 schema 변경이 필요하다(승인 대기). ④ 책 카테고리는 David의 개인 분류(강해·신앙·설교학 등)와 KDC(`종교 > 기독교 > 포교, 교육, 교화활동, 목회학`)가 의미적으로 달라 자동입력하지 않았다. 매핑표를 만들지, 분류 칸을 따로 둘지 David가 결정해야 한다.
- **다음 작업자**: David(운영 실제 등록 확인 1건).
- **David 결정(2026-09-28)**: 현재 자동입력 수준으로 충분하다. 쪽수용 추가 API(알라딘·국립중앙도서관)와 KDC→개인 카테고리 제안은 하지 않는다. 다시 제안하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: `main`, 기능 `b8ec52d`와 이 기록 커밋. origin/main·deploy/main fast-forward 대상이며, Streamlit 화면은 미확인이다.
- **보류·실패·중단 이유**: 없음. 원본 작업트리(`codex/reading-chunks-1a`)의 사용자 기획문서 2건은 건드리지 않았다.

## David가 이어받을 작업 — 도서 검색 title/isbn13 수정 운영 반영, 실제 검색 확인 (2026-09-28, Claude Code)

- **무엇을 했는지**: Intel i9 Mac 실제 Terminal / Claude Code, worktree `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, `main`, 시작 HEAD `7f6bc6f`. David가 승인한 범위만 수정했다. `lib/library_api.py:search_books`가 `keyword=` 대신 `title=`을 보낸다. 공백·하이픈을 뺀 입력이 978/979로 시작하는 13자리 숫자면 `isbn13=`을 보낸다. 기존 ISBN 유틸이 없어 이 최소 정규화만 추가했다. pageSize·pagination·파싱·UI·schema는 불변이다.
- **어디까지 끝났는지**: RED 5건 → GREEN. `tests/test_library_api.py` 6건, 관련 책 추가 AppTest 포함 13 passed, 전체 **209 passed**, compile·diff check PASS. 실제 upstream에서 `희망을 짓는다는 것` 제목·`9788932550817`·`978-89-325-5081-7` 모두 **1위**였고, 부분 제목 `희망을 짓는다`는 10위였다. 기존 도서 6권(역사란 무엇인가·데미안·채식주의자·사피엔스·고요한 아침·순전한 기독교)은 title 결과 상위 10건에 모두 있었다. 기존 keyword보다 나빠진 사례는 없다. 기능 `a5a7a51`, origin/main·deploy/main에 fast-forward push 결과는 아래 WORKLOG와 git 기록으로 확인한다.
- **확인해야 할 것**: David가 운영 읽담 새 책 추가에서 `희망을 짓는다는 것`과 ISBN `9788932550817`을 검색해 책이 보이는지 확인한다. Streamlit 로그·화면 smoke는 브라우저 도구가 없어 **미확인**이다.
- **보류(별도 데이터 품질 이슈)**: upstream authors가 `엘렌 데이비스,윤상필 옮김` 형식이라 역자가 저자 칸에 들어간다. 공저자 `오스틴 매키버 데니스`는 upstream authors에 없다. 국립중앙도서관 fallback·새 API key·pageSize·UI 개편은 범위 밖이다.
- **다음 작업자**: David(운영 실제 검색 확인).
- **브랜치 / 커밋 / 배포 상태**: `main` 기능 `a5a7a51` + 이 기록 커밋. origin/main·deploy/main 반영, Streamlit 화면 미확인.
- **보류·실패·중단 이유**: 없음. 원본 작업트리의 사용자 기획문서 2건은 불변.

## David가 이어받을 작업 — 신간 검색 누락 원인은 query 파라미터(B), 수정 승인 판단 (2026-09-28, Claude Code)

- **무엇을 했는지**: Intel i9 Mac 실제 Terminal / Claude Code에서 `희망을 짓는다는 것`(ISBN `9788932550817`) 검색 누락을 진단했다. worktree `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, `main`, 시작 HEAD `f836a89`. 읽담과 같은 `srchBooks` endpoint와 같은 인증키로 upstream을 재현했다(키 비출력).
- **어디까지 끝났는지**: 원인 판정 **B**(upstream에는 있으나 읽담 query 방식 때문에 못 찾음). 읽담은 입력 문자열을 `keyword=`로만 보낸다. 이 파라미터로는 대상 책이 나오지 않지만 `title=`·`author=`·`isbn13=`·`srchDtlList`에서는 1위로 나온다. 코드·배포·API key 변경은 0이다.
- **확인해야 할 것**: 최소 수정 방향(`keyword` 대신 `title`, ISBN 형태 입력이면 `isbn13` 사용)을 David가 승인할지 결정한다. 부수 문제로, upstream `authors`가 `엘렌 데이비스,윤상필 옮김` 형식이라 현재 파서가 역자까지 저자 칸에 넣는다. upstream에는 공저자 `오스틴 매키버 데니스`도 없다. 쪽수는 data4library가 제공하지 않아 현재도 수동 입력이다.
- **다음 작업자**: David(검색 파라미터 최소 수정 승인 여부 결정).
- **브랜치 / 커밋 / 배포 상태**: `main`, 이번 기록은 local main 후속 문서 커밋·미push. origin/main=deploy/main=`542dbc8` 그대로.
- **보류·실패·중단 이유**: 진단 작업이라 수정하지 않았다. 원인이 A가 아니므로 국립중앙도서관 fallback은 이번 누락을 해결하는 데 필요하지 않다. 사용자 기획문서 2건은 불변.

## David가 이어받을 작업 — 542dbc8 origin/deploy 반영, 운영 화면 smoke 수동 확인 필요 (2026-09-28, Claude Code)

- **무엇을 했는지**: 실행환경은 Intel i9 Mac 실제 Terminal / Claude Code. worktree `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, branch `main`, 시작 HEAD `542dbc8`. 실제 원격 재조회 origin/main=deploy/main=`6a66872`(예상 일치)와 fast-forward 관계, 차이 5개 파일(`app.py`·`lib/shelf_ui.py`·책장 테스트·문서)을 확인하고 일반 push했다.
- **어디까지 끝났는지**: 실제 원격 재조회로 origin/main=deploy/main=`542dbc8`. push 전 203 passed·compile·diff check PASS. push 약 90초 뒤 앱 `_stcore/health` HTTP 200 `ok`. Streamlit `Updated app` 로그·실행 SHA·로그인·책장·상단 `＋ 새 책 추가`·Reading Chunk 추천 UI smoke는 브라우저 도구 부재로 **미확인**이다.
- **확인해야 할 것**: David가 Streamlit 관리 화면 `Updated app` 로그, 로그인·책장·기존 기능, 상단 `＋ 새 책 추가`가 `이어서 읽기` 바로 위에 있고 기존 책 추가 폼을 여는지, 하단 `➕ 새 책 추가` 유지, Reading Chunk 추천 패널·63개 검색·복수 선택·보내지 않음·수정 화면을 확인한다. 실제 책 추가·illustrationTags 승인은 David가 직접 한다.
- **다음 작업자**: David(운영 화면 smoke).
- **브랜치 / 커밋 / 배포 상태**: `main` 제품 `542dbc8`(origin·deploy push 완료), 이번 기록은 local main 후속 커밋·미push. Secrets·Sites/D1·운영 DB write·iCloud write·launchd·오늘의 서재 변경 없음.
- **보류·실패·중단 이유**: blocker는 브라우저 도구 부재로 운영 UI 자동 확인 불가뿐이다. 원본 `codex/reading-chunks-1a` 작업트리의 사용자 기획문서 2건은 불변.

## David가 이어받을 작업 — 책장 상단 새 책 추가 바로가기 검증·배포 판단 (2026-09-28, Codex)

- **무엇을 했는지**: 책장 지표 바로 아래, `이어서 읽기` 바로 위에 `＋ 새 책 추가` 버튼을 추가했다. 버튼을 누르면 상단 입력 surface가 열리며, 기존 하단 `➕ 새 책 추가`도 그대로 남는다. 두 surface는 하나의 `render_add_book_form` 함수와 동일한 검색·검증·`db.insert_book` 저장 경로를 공유하고, widget key scope만 분리한다.
- **어디까지 끝났는지**: 기능·회귀 테스트 커밋 `dcf640c`을 local main에 만들었다. AppTest에서 상단 버튼 클릭, 상단·하단 입력 surface의 동시 접근, 두 경로의 테스트 DB 책 저장을 확인했다. Reading Chunk·예화 추천·exporter·오늘의 서재·schema는 변경하지 않았다.
- **확인해야 할 것**: 실제 Streamlit 화면에서 상단 바로가기의 사용감만 확인하면 된다. 이번 작업은 원격 push·배포 요청이 아니므로 origin/main·deploy/main·운영 DB·iCloud는 변경하지 않았다.
- **다음 작업자**: David 또는 읽담 배포 담당자.
- **브랜치 / 커밋 / 배포 상태**: `main` / `dcf640c`; local main은 origin/main·deploy/main=`6a66872`보다 2커밋 앞섰다. 운영 배포 없음.
- **보류·실패·중단 이유**: 없음. 원본 `codex/reading-chunks-1a` 작업트리의 사용자 기획문서 2건은 그대로 보존했다.

## David가 이어받을 작업 — origin/deploy 6a66872 반영, Streamlit 운영 UI smoke 수동 확인 필요 (2026-09-28, Claude Code)

- **무엇을 했는지**: i9 실제 Terminal에서 `git ls-remote`로 origin/main=`0d1530d`, deploy/main=`74d3c9d`를 확인했다. 깨끗한 main worktree(`/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`)에서 두 원격 모두 fast-forward 관계와 deploy..main 22개 파일 차이(1차-B·2차 exporter·추천/승인, requirements·DDL 변경 없음)를 확인한 뒤 일반 push했다.
- **어디까지 끝났는지**: 실제 원격 재조회로 origin/main=deploy/main=`6a66872` 확인. push 전 202 passed·compile·diff check PASS. 앱 `_stcore/health` HTTP 200 `ok`. Streamlit `Updated app` 로그·로그인·책장·기존 기능·추천 UI는 브라우저 도구 부재로 **미확인**이다. 실행 SHA 직접 확인 없음.
- **확인해야 할 것**: David가 Streamlit 관리 화면에서 `Updated app` 로그, 로그인·책장·기존 활동·Reading Chunk 동작, 자유 입력 예화 태그 제거·추천 패널·63개 검색·복수 선택·보내지 않음·기존 Chunk 수정 화면 선택·snapshot 로드를 확인한다. 실제 illustrationTags 승인 저장은 David E2E에서 수행한다.
- **다음 작업자**: David(운영 smoke 및 경로 A 실제 사용자 E2E).
- **브랜치 / 커밋 / 배포 상태**: `main` 제품 `6a66872`(origin·deploy push 완료), 이번 상태 문서는 local main 후속 커밋·미push. Secrets·Sites/D1·운영 DB write·iCloud write 없음.
- **보류·실패·중단 이유**: Claude in Chrome 미연결로 운영 UI 자동 확인 불가. 코드·원격 반영 실패는 없다. 원본 작업트리의 사용자 기획문서 2건은 불변.

## 읽담 담당자가 이어받을 작업 — 자동 sync 휴면 안전성 확인, GitHub DNS 복구 후 배포 재개 (2026-09-28, Codex)

- **무엇을 했는지**: David 결정에 따라 1차-B의 5분 fragment는 유지했다. Secrets 없는 `sync_once`를 HTTP 접근을 실패시키는 격리 probe로 실행해 owner 형식 확인 뒤 `not_configured`로 반환함을 확인했다. HTTP·Chunk 생성/수정/삭제·receipt·book snapshot 호출은 0건이며, DB 연결의 schema inspection은 read-only다. fragment의 상태 변화는 `readdam_last_sync_monotonic`과 `readdam_sync_result` 두 session state뿐이다.
- **어디까지 끝났는지**: local main=`eff70b1` 기준으로 자동 sync 휴면 안전성은 PASS다. 전체 202 tests·compile·diff PASS 근거를 유지한다. 1차-B Secrets·오늘의 서재 운영 연결·Sites/D1·운영 DB/iCloud write는 모두 없다.
- **확인해야 할 것**: origin 사전 확인을 위해 `git ls-remote origin refs/heads/main`을 두 번 실행했지만 모두 `Could not resolve host: github.com`으로 실패했다. 원격 SHA를 확인하지 못했으므로 push·deploy를 시도하지 않았다.
- **다음 작업자**: GitHub DNS/네트워크가 정상인 읽담 담당자. origin/main SHA를 확인한 뒤 일반 fast-forward push → deploy/main 반영 → Streamlit smoke를 순서대로 재개한다.
- **브랜치 / 커밋 / 배포 상태**: `main` / `eff70b1` (이번 상태 문서는 후속 커밋); origin/main=`0d1530d`, deploy/main=`74d3c9d`. Streamlit 운영 배포 없음.
- **보류·실패·중단 이유**: 현재 실행 환경에서 GitHub DNS를 해석할 수 없다. 제품·테스트·자동 sync 휴면 경로의 실패가 아니라 원격 접속 제약이다.

## David가 이어받을 작업 — main 반영 완료, 1차-B 자동 동기화 관문으로 운영 배포 중단 (2026-09-28, Codex)

- **무엇을 했는지**: 깨끗한 별도 main worktree에서 `codex/reading-chunk-category-approval`을 `0d1530d..59d0250`으로 fast-forward했다. 원본 작업트리의 사용자 소유 기획문서 2건은 변경하지 않았다. main 기준 전체 테스트·compile·diff와 deploy/main 차이를 감사했다.
- **어디까지 끝났는지**: 추천·승인 기능은 local main에만 반영됐다. 전체 **202 passed**, Python compile, `git diff --check`는 PASS다. origin/main·deploy/main·Streamlit·Secrets·운영 DB·iCloud는 변경하지 않았다.
- **확인해야 할 것**: 1차-B UI `lib/readdam_sync_ui.py`는 Secrets가 비어 있으면 외부 HTTP 전에 `not_configured`로 끝나지만, `@st.fragment(run_every="5m")`가 자동으로 `sync_once`를 호출한다. 이번 배포 조건인 background sync 자동 시작 없음은 충족하지 않는다. 2차 exporter는 앱에서 호출되지 않는 명시적 CLI 진입점임을 확인했다.
- **다음 작업자**: David가 별도 1차-B 작업에서 자동 실행을 제거·비활성화할지 결정한 뒤 읽담 담당자.
- **브랜치 / 커밋 / 배포 상태**: `main` / 제품 `59d0250` (이번 상태 문서는 후속 커밋); origin/main=`0d1530d`, deploy/main=`74d3c9d`. 운영 배포 없음.
- **보류·실패·중단 이유**: 외부 HTTP 자동 실행 증거는 없지만 자동 scheduled fragment가 존재한다. 이번 작업은 오늘의 서재 코드를 수정할 수 없으므로 push·deploy·운영 UI smoke를 진행하지 않았다.

## David가 이어받을 작업 — 승인된 예화 카테고리 사전의 main 반영 판단 (2026-09-28, Codex)

- **무엇을 했는지**: David가 승인한 세 keyword만 반영했다. `그리스도인의 삶`은 `그리스도인의 삶의 방식`으로 구체화했고, `시간`의 `세월`은 삭제했으며, `위선`의 `가면`은 `위선의 가면`으로 구체화했다. 63개 카테고리는 배타적 분류가 아닌 주제 바구니이므로 유용한 다중 추천은 최대 3개까지 유지한다.
- **어디까지 끝났는지**: 읽담 로컬 기능 커밋 `d037be1` 완료. canonical names·aliases·나머지 keywords는 불변이며, 새 카테고리·실제 iCloud export·운영 DB write는 없다.
- **확인해야 할 것**: 공동 계약 저장소의 Git metadata 쓰기 권한이 현재 세션에서 막혀, 이번 승인 철학의 CROSS 기록 커밋은 만들지 못했다. 공동 worktree에는 미커밋 변경을 남기지 않았다.
- **다음 작업자/작업**: David가 승인된 로컬 사전 변경의 main 반영 여부를 결정한다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunk-category-approval` / `d037be1`; `main`·`origin/main`=`0d1530d`, `deploy/main`=`74d3c9d`. push·배포·Secrets·운영 DB·iCloud write 없음.
- **보류·실패·중단 이유**: fixture·관련 테스트·전체 202 tests·compile·diff·실제 폴더 read-only preflight는 PASS다. 공동 계약 신규 기록만 현재 상위 저장소 Git lock 권한 제약으로 보류했다.

## David가 이어받을 작업 — 예화 카테고리 63개 사전 초안 검토 (2026-09-28, Codex)

- **무엇을 했는지**: Reading Chunk 경로 A의 비AI 규칙 추천·명시 승인 UI·canonical 저장 검증·snapshot 갱신 도구를 구현했다. 실제 예화창고 최상위 폴더 이름만 읽어 63개 NFC canonical snapshot과 alias/keyword 초안을 만들었다. exporter는 실제 폴더 NFC exact match를 legacy alias/ambiguity보다 먼저 처리하도록 고쳤다. 공동 계약은 별도 로컬 브랜치 `codex/reading-chunk-category-contract`의 `188ac7b`에 반영했다.
- **어디까지 끝났는지**: 읽담 로컬 기능 커밋 `276c958`만 완료했다. 새 Chunk는 먼저 `illustrationTags=[]`로 저장되고, 승인 버튼을 눌렀을 때만 snapshot canonical 이름을 저장한다. 기존/오늘의 서재 Chunk도 읽담에서 카테고리를 고를 수 있다. main 반영·push·배포·운영 DB write·실제 iCloud export는 없다.
- **확인해야 할 것**: [63개 사전 초안](ILLUSTRATION_CATEGORY_DICTIONARY_DRAFT.md)을 David가 검토한다. 실제 폴더 추가·삭제·이름 변경은 snapshot 갱신 명령으로만 반영하며, alias/keyword는 이 초안에서만 조정한다.
- **다음 작업자/작업**: David가 63개 category/alias/keyword 초안 1건을 검토한다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunk-category-approval` / 기능 `276c958`, 오늘의 서재 Chunk UI 회귀 `298ef54`; `main`·`origin/main`=`0d1530d`, `deploy/main`=`74d3c9d`. 운영 배포·Secrets·DB 변경·iCloud write 없음.
- **보류·실패·중단 이유**: 구현·201개 테스트·compile·diff check·iCloud 이름/metadata read-only preflight는 PASS다. 사전 초안의 의미 적합성은 David 검토 전 확정하지 않는다. 1차-B 운영 연결 및 실제 2차 export는 기존 보류 상태로 유지한다.

## David가 이어받을 작업 — 읽담 Reading Chunk main을 origin에 보존 (2026-09-28, Codex)

- **무엇을 했는지**: 읽담 local main `8e15c1f`와 실제 원격 origin/main `74d3c9d`를 대조해 fast-forward 관계와 깨끗한 main worktree를 확인한 뒤 일반 push로 동기화했다. `deploy/main`은 건드리지 않았다.
- **어디까지 끝났는지**: 읽담 측 1차-B·2차는 local/origin 코드·문서 보존 완료. 1차-A COMPLETE. 1차-B 운영 연결은 Sites 관리형 D1 `0004` 공식 migration lifecycle 미확인으로 BLOCKED. 2차 실제 export는 eligible illustration Chunk 0건으로 미실행이다. 오늘의 서재와 공동 저장소에는 현재 `origin` remote가 없어 이번에 push하지 않았다.
- **확인해야 할 것**: 오늘의 서재 원격 Source of Truth를 동기화하려면 David가 기존 공식 원격 경로를 확인해야 한다. 임의로 remote를 추가하지 않는다. 1차-B 운영 blocker와 2차 export 별도 관문은 그대로다.
- **다음 작업자/작업**: David가 오늘의 서재의 승인된 원격 저장소/동기화 경로를 확인한다.
- **브랜치 / 커밋 / 배포 상태**: `main`·`origin/main`은 제품·문서 `8e15c1f`까지 동기화했고 이번 push 상태 기록은 후속 문서 커밋이다. deploy/main·Streamlit 운영 배포·Secrets·운영 DB·iCloud 변경 없음.
- **보류·실패·중단 이유**: 오늘의 서재/공동은 origin remote 미설정. 1차-B 운영 D1 blocker 유지. 원본 읽담 작업트리의 사용자 문서 변경은 보존했다.


## David가 이어받을 작업 — Reading Chunk 1차-B·2차 local main 정본화 완료 (2026-09-28, Codex)

- **무엇을 했는지**: 읽담 main `74d3c9d` 위에 Reading Chunk 1차-B ingest·pull·receipt·책 snapshot과 2차 예화창고 exporter·테스트·설계/운영 문서만 선별 반영했다. 후보 브랜치의 Reading Chunk 외 nan 버그 문서 커밋은 포함하지 않았다. 공동 정본은 공동 main `4a610de`의 `CROSS_PROJECT_HANDOFF.md`다.
- **어디까지 끝났는지**: 1차-A **COMPLETE**. 1차-B는 **LOCAL COMPLETE / 운영 연결 BLOCKED**(ChatGPT Sites 관리형 D1 `0004` 공식 migration lifecycle 미확인). 2차는 **LOCAL COMPLETE**. 실제 운영 DB READ ONLY와 실제 iCloud dry-run 2회 PASS, 현재 export 대상 illustration Chunk 0건, 실제 export 미실행, DB/iCloud write 0건. 기존 활동 nan 버그는 앞선 운영 수정·확인으로 CLOSED다. 이번 작업은 local main만 반영했고 push·배포는 하지 않았다.
- **확인해야 할 것**: 1차-B 운영 연결 전 Sites D1 `0004`의 공식 적용 경로를 외부에서 확인한다. 2차 실제 export는 대상 데이터가 생긴 뒤 다시 dry-run하고 별도 승인을 받는다. 과거 NO-GO와 미완료 항목은 당시 기록이며 이 최신 판정으로 대체한다.
- **다음 작업자/작업**: David가 Sites 관리형 D1 migration 공식 lifecycle 확인 경로를 결정한다.
- **브랜치 / 커밋 / 배포 상태**: `main` 제품 `a0006a4`·`bf972a0`, 2차 문서 `b6a7c23`, 이번 최신 상태 문서 후속 커밋. origin/main·deploy/main·Streamlit 운영은 변경하지 않았다.
- **보류·실패·중단 이유**: 로컬 검증 186 tests PASS, Python compile·diff check PASS. 운영 연결 blocker는 제품 코드 실패가 아니라 Sites D1 적용 절차 미확인이다. 원본 작업트리의 사용자 기획문서 변경은 보존했다.

## David가 이어받을 작업 — 활동 카드 nan 최소 수정 검증 완료, 운영 미배포 (2026-09-28, Codex)

- **무엇을 했는지**: 기존 활동 표시 버그만 `lib/notebook_ui.py:cards()`의 행 표시 경계에서 수정했다. 각 scalar에 `pd.isna`를 적용해 실제 결측만 `None`으로 정규화한다. DB 계층·전체 pandas dtype·Reading Chunk 코드·운영 DB는 그대로다.
- **어디까지 끝났는지**: 제품/테스트 로컬 커밋 `c6951b4`(`codex/reading-chunks-private-default`). 새 AppTest 3개가 None/NaN/pd.NA, 정상 문자열, 실제 문자열 `"nan"`, 0쪽, 새 pandas 문자열 dtype 경로를 검증한다. 변경 전 RED 2실패/1통과 → 변경 후 카드6통과, 전체160통과, 두 Python 파일 compile·diff check 통과. 운영 배포는 아직 없다.
- **확인해야 할 것**: 실제 운영 화면의 `nan` 소멸은 미배포라 미검증이다. main/origin/main/deploy/main은 기존 `5129d75` 기준이며 이 수정은 미반영·미push. 기존 사용자 기획문서2개는 불변이다.
- **다음 작업자/작업**: David가 수정 커밋의 main 반영·배포 및 배포 후 기존 활동 카드 smoke 검증을 별도 승인한다. 승인 전에는 push/배포하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunks-private-default` 제품 `c6951b4`, 이번 결과 문서는 별도 로컬 커밋. 앱 운영 배포는 이전 상태 유지.
- **보류·실패·중단 이유**: 로컬 테스트 실패 없음. 운영 화면 확인만 별도 배포 승인 관문이다. 1차-A COMPLETE 판정은 그대로이며 1차-B·2차 export에는 진입하지 않는다.

## 읽담 담당자가 이어받을 작업 — 기존 활동 nan 표시 원인 재현, 수정은 별도 (2026-09-28, Codex)

- **무엇을 했는지**: 코드·DB·배포를 바꾸지 않고 운영 activities 5,667건과 이관 원본 SQLite를 읽기 전용 대조하고, Safari의 기존 활동 3건 표시를 pandas 새 문자열 dtype 동작으로 재현했다. 아래 1차-A COMPLETE 판정은 유지한다.
- **어디까지 끝났는지**: Safari 책 상세 3/3건에서 `quote` 또는 `text`의 `nan`과 잘못된 `내 생각` 표시를 관찰했다. 운영 원본에는 해당 두 필드 및 `photo`의 문자열 `nan`/숫자 NaN 0건, NULL은 각각 2,238/3,767/5,610건. 원본 SQLite 5,667 ID와 모두 일치하며 세 필드의 NULL 여부 차이 0건이다.
- **확인해야 할 것**: 운영 pandas 버전은 직접 확인하지 못했다. 로컬 pandas 2.3.3의 3.x 문자열 dtype 호환 모드를 켜면 실제 3건과 동일한 NaN 위치가 재현되고 `read_frame().where(pd.notna(frame), None)` 후에도 남는다. 같은 모드로 운영 5,667건을 재현한 **추정 영향은 5,050건/380권**(quote 1,639건, text 3,743건; 중복 포함). 직접 운영 전체 화면 계수로 단정하지 않는다.
- **다음 작업자/작업**: 읽담 담당자가 별도 수정 승인 후 `lib/notebook_ui.py`의 `cards()`에서 표시용 row의 scalar 결측을 `None`으로 정규화하는 최소 수정과 회귀 테스트를 검토한다. 이번에는 진단만 했고 수정·migration·재배포는 없다.
- **브랜치 / 커밋 / 배포 상태**: `codex/reading-chunks-private-default` 문서 로컬 커밋·미push. 제품 main/origin/deploy=`5129d75`, 운영 배포 추가 없음.
- **보류·실패·중단 이유**: 현재 운영 pandas 정확한 버전과 2026-09-26 당시 실제 dtype은 미확인이다. 과거와 같은 NULL→DataFrame NaN→truthy 경로지만 당시와 현재의 세부 dtype 원인 동일 여부는 불명. 데이터 손상/활동 schema 변경/데이터 migration 필요 근거는 없다. 1차-B·2차 export 미진입.

## 읽담 담당자가 이어받을 작업 — 1차-A 완료, 기존 활동 nan 버그 분리 (2026-09-28, Codex)

- **무엇을 했는지**: 기존 Streamlit/GitHub 배포 기록과 Git·기존 활동 표시 경로를 읽기 전용 대조했다. 아래 2026-09-27의 1차-A INCOMPLETE 상태를 이번 종료 판정으로 대체한다. 제품 코드·DB·배포 변경 없음.
- **어디까지 끝났는지**: 1차-A Safari CRUD·검색·재접속·txt ISBN/시간/sourceApp·소프트 삭제·보안/기존 데이터 검증은 아래 기록대로 완료. **실행 SHA 직접 확인 불가 / 강한 간접 증거 확보**: deploy/main `5129d75`, Streamlit `Updated app!`, 신규 기능 실제 동작. 관리 로그·설정 및 GitHub 배포 메타데이터에 실행 SHA는 없다.
- **확인해야 할 것**: 기존 활동의 `nan`은 `51e5b0c`(2026-09-26)가 배포 전 실제 운영에서 보고한 동일 증상이다. 당시 수정 기록이 있지만 현재 재관찰된다. 활동 표시 본문·`lib/database.py`·의존성 선언 및 기존 활동 데이터는 이번 배포에서 불변. 정확한 현재 원인은 별도 버그로 진단한다.
- **다음 작업자/작업**: 읽담 담당자가 **기존 활동 `nan` 표시 원인 진단 1건**. 1차-B·2차 export·실제 iCloud 자동 export는 이번 작업에서 시작하지 않는다.
- **브랜치 / 커밋 / 배포 상태**: 제품 main/origin/main/deploy/main=`5129d75`. 이번 결과는 `codex/reading-chunks-private-default` 문서 로컬 커밋·미push, 운영 배포 추가 없음. 원본 사용자 기획문서2개 불변.
- **보류·실패·중단 이유**: Reading Chunk 1차-A **COMPLETE**. 실행 SHA 직접 증거 미확보는 명시적 잔여 위험이나 David 기준상 단독 차단 사유가 아니다. `nan` 현재 원인은 미확정이며 수정은 별도 작업이다.

## 읽담 운영 담당자가 이어받을 작업 — Safari 실검증 완료, 실행 SHA 직접 확인 남음 (2026-09-27, Codex)

- **무엇을 했는지**: David의 승인에 따라 실행 SHA 미확인 위험을 기록한 상태에서 M1 Safari 운영 검증을 마쳤다. 테스트 Chunk 1건의 생성·조회·수정·태그 검색을 이전 턴에, 재로그인 후 유지·txt export·삭제·보안 재확인을 이번 턴에 완료했다. 공동 최신 정본은 `codex/reading-chunks-current-state`의 `1b5ff9a`다.
- **어디까지 끝났는지**: 읽담 main/origin/main/deploy/main=`5129d75`, Streamlit `Updated app!` 로그 및 로그인·책장705권 확인. 격리 로컬 txt에는 ISBN `9791130634500`·읽은 시간11분·`sourceApp=readdam`이 있었다. 테스트 ID `48dad8d7-97f7-4ea7-a495-1f9d47ca1c37`은 앱에서 소프트 삭제했고 DB에서 deleted_at 존재·활성0을 확인했다. 임시 export 폴더도 제거했다.
- **확인해야 할 것**: **실행 SHA 직접 확인: 미완료 / 간접 근거: deploy/main 5129d75 + Updated app 로그**. 실행 SHA를 직접 증명할 기존 운영 증거를 확보한다. 테스트 소프트 삭제 이력은 복구 가능한 행1건으로 남는다. 기존 전체 행0을 가정한 이전 post-check의 실패 표시는 이 예상된 이력 때문이며, 기존 스키마 지문·보안은 별도로 정상 확인했다.
- **검증/관찰**: books705/activities5667/owner NULL0, 기존 public14표 데이터 해시와 기존 schema SHA `4f6b930680c82b0fc8d8cfd51e457d5dac7c997aa0c0f8be838184e92a1e6189` 불변. RLS on/policy0, PUBLIC·anon·authenticated·service_role CRUD=false, postgres CRUD=true, 실제 anon GET HTTP401/42501. 기존 활동3건은 표시됐으나 일부 `nan` 표시가 재관찰되어 전체 화면 회귀 없음으로 단정하지 않는다.
- **다음 작업자/작업**: 읽담 운영 담당 Codex가 **실행 SHA 직접 확인 근거 1개 확보**. 이를 확인하기 전 1차-A는 INCOMPLETE. 1차-B·2차 export·실제 iCloud 자동 export는 보류한다.
- **브랜치 / 커밋 / 배포 상태**: 결과는 `codex/reading-chunks-private-default`에서 문서만 로컬 커밋·미push. 제품 코드·DB schema/권한·main·원격·Streamlit 배포·사용자 기획문서 변경 없음. 아래 테스트 활성1건 기록은 과거 상태다.

## David/읽담 담당 Codex가 이어받을 작업 — Safari 재로그인 후 테스트 Chunk 검증·삭제 필수 (2026-09-27, Codex)

- **무엇을 했는지**: David는 실행 SHA 직접 확인을 미완료 위험으로 남긴 채 CRUD/export 진행을 명시 승인했다. 로그인 후 책장 705권·선택 책의 기존 활동 3개 표시를 확인하고, Safari에서 테스트 Chunk 생성·재조회·수정·태그 일치/불일치 검색을 통과했다.
- **어디까지 끝났는지**: 읽은 시간 7→11분, 메모 수정 저장을 DB 읽기 전용 조회로도 확인했다. 재접속 검증을 위해 Safari를 새로고침하자 로그인 화면으로 돌아왔다. 재로그인 후 화면 유지 확인·txt export·삭제는 아직 미완료다.
- **확인해야 할 것**: **활성 테스트 Chunk 1건이 남아 있다.** ID=`48dad8d7-97f7-4ea7-a495-1f9d47ca1c37`, 원문 식별자=`[TEST-RC1A-20260927-M1-7429]`, 태그=`TEST-RC1A-7429`, 책=부자의 그릇(큰글자도서), 1–2쪽. 검증 후 반드시 이 행만 앱의 소프트 삭제로 정리한다. 사용자 Chunk는 건드리지 않는다.
- **보안/관찰**: 기존 public 14표의 내용 해시·건수는 시작 전과 동일, books705/activities5667/owner NULL0. RLS on/policy0, 외부 4역할 CRUD=false, postgres=true, 실제 anon GET HTTP401/42501. 기존 활동 일부에 nan 표시가 관찰됐고 해당 표시 코드/DB reader는 이전 deploy 51e5b0c와 동일하나, 화면 회귀 전체 PASS로 단정하지 않는다.
- **다음 작업자/작업**: David가 Safari 읽담에 직접 재로그인 → Codex가 재접속 유지 확인 → 격리 로컬 txt(ISBN/11분/sourceApp) 확인 → 테스트 Chunk 소프트 삭제 및 재조회 → 최종 보안·무결성 점검. 비밀번호는 채팅에 보내지 않는다.
- **브랜치 / 커밋 / 배포 상태**: main/origin/deploy=`5129d75` 유지. 실행 SHA **직접 확인: 미완료 / 간접 근거: deploy/main 5129d75 + Updated app 로그**. 이번 기록만 제품 브랜치에 로컬 커밋·미push하며 제품 코드/DDL/권한은 수정하지 않았다.
- **보류·금지**: 재로그인 필요, 1차-A INCOMPLETE. 1차-B·2차 export·실제 iCloud 자동 export 금지 유지. 아래 로그인 전/테스트 행 0 기록은 과거 상태다.

## David/읽담 담당 Codex가 이어받을 작업 — main·원격 반영, runtime SHA·Safari 로그인 후 실검증 필요 (2026-09-27, Codex)

- **무엇을 했는지/완료 범위**: 승인 기준32cfc48/5129d75/2165808·제품 clean·사용자2문서 해시·운영post-check를 재확인했다. `/private/tmp/readdam-release-main-jyMKCs`의 깨끗한main에서4d97f4e→5129d75를ff-only 반영하고 **157 passed in 12.53s** 후 origin/main·deploy/main을동일SHA로push했다. Streamlit 관리로그06:26:00 UTC의Updated app 및M1 ARM64 Safari로그인화면을확인했다.
- **확인해야 할 것/보류**: 배포 원격SHA는 `5129d75ed69081c51e5ad19ed23e48e5083259bd`이나 runtime SHA를직접확인하지못했다. 로그/일반설정에는SHA가없고GitHub statuses/check-runs/deployments에도증거가없었다. Safari Auth로그인은사용자에게직접요청했으며아직미완료다. 기능검증을우회하지않고 **1차-A INCOMPLETE**로보류한다.
- **보안/보존**: 배포전후기존14표의행내용집계해시·건수동일, books705/activities5667/ownerNULL0/chunk0, 기존schema SHA4f6b9306…1e6189불변. RLS=true/policy0, PUBLIC/anon/authenticated/service_role CRUD=false, postgres=true. 실제anonGET HTTP401/42501차단. 테스트Chunk생성·CRUD·txt export는0건이라정리할테스트행도없다. 기존책/활동의화면회귀는아직미검증이다.
- **다음 작업자/작업**: David가Safari읽담계정로그인을완료하고, Codex가runtimeSHA근거확보후기존승인범위의생성→조회→수정→검색→재접속→로컬txt(ISBN/읽은시간/sourceApp)→소프트삭제→보안/무결성검증을재개한다. 비밀번호를채팅에보내지않는다.
- **브랜치/커밋/배포**: 제품main/origin/deploy는5129d75. 이번결과문서는`codex/reading-chunks-private-default`에만후속로컬커밋하며추가push/배포하지않는다. 공동최신정본은`codex/reading-chunks-current-state`의 **ca81d37**, `/private/tmp/readdam-cross-current-gJs4x6/CROSS_PROJECT_HANDOFF.md`다. 아래배포전기록을현재상태로해석하지않는다. 제품수정·DB DDL/DML·migration재실행없음,1차-B/2차/iCloud자동export금지유지.

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
