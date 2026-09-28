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
