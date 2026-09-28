# 읽담 작업 기록

이 파일은 **역사 기록**이다. 현재 상태와 다음 행동은 `docs/HANDOFF.md`, 프로젝트 간 공통 결정은 `../CROSS_PROJECT_HANDOFF.md`에 둔다.

기록 규칙 (2026-09-26부터):
- 최신 항목을 맨 위에 추가한다. 제목은 `## <날짜> — <작업자>: <작업명>` 형식이다.
- 최소 항목은 작업 목적, 실제 변경 내용, 테스트 결과, 커밋(브랜치), 배포 여부, 발견 문제, 남은 작업이다. 해당 없음은 "없음"으로 쓴다.
- 과거 항목은 수정하지 않는다. 사실을 보강할 때는 `- 보강(<날짜>, <작업자>):` 줄을 덧붙인다.
- 2026-09-26 이전 항목은 이 규칙 이전 형식이다.

## 2026-09-28 — Claude Code: i9 복귀 3층 정본 대조, 로그인 지속성 계획

- **작업 목적**: M1→i9 이동 뒤 읽담·오늘의 서재·통합 계약의 최신 기록을 실제 Git과 대조해 정본을 복원하고, 로그인 지속성 작업 계획을 세운다.
- **실행환경**: Intel i9 Mac / Claude Code, worktree `/private/tmp/readdam-login-persist`(`main` `3f42a52`).
- **실제 확인**: 읽담 origin/main = deploy/main = `3f42a52`(ls-remote), local main은 `0cbe841`→`3f42a52` ff다. 오늘의 서재 main은 `28cfe37`(remote 없음), 공동 main은 `4a610de`(remote 없음)이고, 공동 `188ac7b`는 미반영이다. D1 `0004` blocker는 세 층 기록이 일치한다.
- **로그인 조사**: `app.py:require_authenticated_user`는 `auth.sign_in`의 user·access token만 `st.session_state`에 저장한다. refresh token은 저장하지 않고 로그아웃 기능도 없다. Streamlit 1.50 `st.context.cookies`와 supabase-py 2.31 `refresh_session(refresh_token)`은 사용 가능함을 확인했다.
- **실제 변경 내용**: 문서만 바뀌었다(HANDOFF·WORKLOG). 코드 변경은 없다.
- **테스트 결과**: 해당 없음.
- **커밋/배포 여부**: 이 기록 커밋은 origin/main에만 push한다. deploy는 그대로다.
- **남은 작업**: 로그인 지속성 구현은 David 승인 뒤 진행한다.

## 2026-09-28 — Claude Code(Orca): 실사용 성능 감사 및 최소 고속화

- **작업 목적**: David가 실제 읽담 사용 중 "느려서 이렇게 쓰다가는 그냥 안 쓸 것 같다"고 판단. 기능 추가보다 우선하는 P0로 받아, 추측 없이 실측 기반으로 병목을 찾고 안전한 것만 고쳤다. 로그인 지속성·중복 방지 확장·새 API·새 Reading Chunk 기능·오늘의 서재·예화창고 자동화·UI 개편은 이번에 하지 않았다(요청대로 금지).
- **계측 방법**: (1) 운영과 같은 규모(705권/5,666건, `migration/output/{books,activities,photo_manifest}.json`을 이 워크트리에만 임시 복사해 `migration/load_db.py`로 재현, 커밋 안 함)의 로컬 SQLite에 AppTest로 주요 흐름을 태우면서 `sqlite3.Connection.set_trace_callback`으로 SQL 실행 횟수·순서를 정확히 셌다. (2) `lib.db.connect`를 임시로 감싸 `db.get_connection()` 호출 횟수(=스키마 검사 포함 전체 연결 설정 비용) 자체도 셌다. (3) 운영 Supabase Postgres에 `db.get_readonly_connection()`으로 읽기 전용 접속해 실제 네트워크 왕복 지연시간을 실측(`SELECT 1` 평균 17.6ms, `require_schema` 4쿼리 총 69~89ms, `list_books` 전체 707행 29~124ms 등).
- **발견 1(최대 병목, 수정함)**: 사이드바 네비게이션 버튼을 한 번 클릭하면 `db.get_connection()`이 **정확히 2번** 실행됨을 직접 계측으로 확인(1클릭 → connect 호출 1→2). 원인: 클릭이 이미 스크립트를 한 번 재실행시켰는데, 핸들러 안에서 `goto(label); st.rerun()`으로 또 한 번 강제로 재실행시켜 그 실행을 버리고 통째로(연결·스키마 검사 4쿼리·책장 조회 8쿼리 전부) 다시 돈다. 이 버튼들은 스크립트 뒤쪽의 최종 view 분기보다 먼저 실행되므로, `st.rerun()` 없이도 같은 실행 안에서 `goto()`가 바꾼 `session_state.view`를 분기가 그대로 읽는다 — 제거해도 정상 동작함을 AppTest로 확인. 제거 과정에서 버튼에 명시적 `key`가 없어 `type`(active 여부로 매 실행 바뀜)만으로 Streamlit이 위젯 식별자를 매기다, 연속 두 번째 클릭이 반영되지 않는 문제를 **직접 재현**했다(`_nav(_nav(at,"통계"),"책장")` 패턴의 기존 테스트 3개가 실패). `key=f"nav_{label}"`을 추가해 함께 고쳤고, key 추가만으로도(rerun 유무와 무관하게) 재현되던 실패가 사라짐을 별도로 검증했다.
- **발견 2(수정함)**: 책장 화면 한 번 그릴 때 `list_categories`가 필터 드롭다운·새 책 추가(위 바로가기/아래 펼침 두 자리)에서 각각 불려 화면당 2~3번 반복 실행됨을 확인. `st.cache_data(ttl=10)`로 캐싱했다. 밑줄 인자(`_conn`)만 쓰면 캐시 키에 DB 구분값이 하나도 안 남아, 서로 다른 임시 SQLite를 쓰는 테스트 사이에서 캐시가 섞이는 것을 직접 재현했고, `BOOK_BUTLER_DB_PATH`/`SUPABASE_DB_HOST` 기반 `db_identity`를 별도 인자로 추가해 서로 다른 두 SQLite를 번갈아 조회해도 각자 맞는 카테고리만 나오는 것을 확인했다.
- **발견 3(수정함)**: Reading Chunk 책 상세 목록에서 태그 필터 있는/없는 버전을 각각 `chunks.list_for_book`로 쿼리해 같은 조각 목록을 두 번 읽고 있었다(각 호출이 소유권 검사 1쿼리 + 목록 조회 1쿼리 = 2쿼리이므로 왕복이 사실상 2배). 태그 필터가 애초에 SQL이 아니라 파이썬에서 도는 구조임을 확인하고, 한 번만 조회한 뒤 태그 필터·중복 집계 모두 그 결과에서 계산하도록 합쳤다.
- **발견하고 보류한 것(회귀 위험/설계 판단 필요, 코드 변경 안 함)**:
  1. 책 상세 진입 등 **자식 함수 안의 `st.rerun()` 전반** — 원인은 발견 1과 동일하지만, 이 버튼들은 최종 view 분기가 **이미 결정된 뒤** 실행되므로 단순 제거가 아니라 dispatch를 반복 평가하는 구조(예: 루프)로 바꿔야 안전하다. 구조 변경이라 이번에는 보고만 한다.
  2. 책 상세 진입 시 `db.get_book`이 5번(app.py 사이드바, notebook_ui, record_ui, timer_ui, sharing_ui가 각자 재조회), `reading.active`가 3번 중복 조회됨(발견 1의 이중 실행 효과 제외하고도 실제 렌더 1회에 이 정도). 단순 TTL 캐시를 넣으면 책 정보를 수정한 직후 같은 렌더 안 다른 컴포넌트가 옛 값을 보여줄 위험이 있어(쓰기 직후 읽기 일관성) 이번엔 보류.
  3. `require_schema`(구조 무결성 검사)가 **모든 스크립트 실행마다** 재실행됨. 운영 Postgres 실측 4쿼리·69~89ms. 세션당 한 번만 검사하도록 캐싱하면 확실히 빨라지지만, "스키마가 실행 중 바뀔 수 있다"는 이 검사의 존재 이유(운영 안전장치, 최근 여러 커밋에서 신중하게 설계됨)와 상충할 수 있어 David/설계 판단이 필요하다고 보고 코드는 건드리지 않았다.
- **Reading Chunk 최종 UX 계약 감사(코드 변경 없음, 확인만)**: 목표 계약은 "작성 → 63개 카테고리 기준 자동 추천 → 강한 추천 기본 체크 → 확인/수정 → [저장하고 예화창고로 보내기] → 읽담 정본 저장 → 이후 Mac 자동 export → TXT 생성 → 해당 카테고리/읽담/에 자동 배치"이다. **자동 추천~읽담 정본 저장까지는 일치**한다: `_category_panel()`이 조각 저장 직후 `chunk_category_pending_id` 세션 상태로 자동 호출되고, `illustration_categories.recommend()`의 `defaultChecked` 항목이 미리 체크되며, `chunks.set_illustration_tags()`로 읽담 자체 DB(`reading_chunks.illustration_tags`)에 저장된다. **가장 큰 차이는 "이후 Mac 자동 export"다**: 현재 `tools/export_chunks.py --output-root <경로> --owner-id <id> --chunk-id <id>`는 사람이 터미널에서 직접 실행해야 하는 CLI이고, cron·launchd 등 자동 트리거는 코드 어디에도 없다(`grep`으로 확인). "David가 CLI 실행·폴더 복사를 해서는 안 된다"는 목표와 현재 상태 사이의 유일하지만 가장 큰 간극이다. 이번 작업에서 자동화를 새로 만들지 않았다(요청대로 감사만).
- **검증**: 위 세 가지 수정 적용 후 전체 pytest **256개 통과**(기존과 동일 개수 — 새 회귀 테스트는 추가하지 않았다, 아래 남은 일 참고), py_compile·git diff --check 통과. AppTest로 사이드바 연속 두 번 클릭 시나리오를 직접 재현·수정 확인(수정 전 실패 3개, 수정 후 통과). 계측용 SQLite(705권/5,666건)와 `_perf_probe.py`(감사용 스크립트, 커밋 안 함)로 수정 전/후 SQL 실행 횟수를 비교: 사이드바 재진입류 흐름이 80건→42건(약 47% 감소, 이중 실행 제거분), `list_categories` 중복 호출 제거(2~3회→1회), Reading Chunk 목록 조회가 함수 자체 기준 4쿼리→2쿼리로 절반.
- **한계**: 실제 운영 브라우저로 체감 속도를 확인하지 못했다(이 세션에 브라우저 연결 없음). SQLite 계측은 왕복 횟수·파이썬 처리시간만 정확하고 Postgres 네트워크 지연은 별도 실측치를 참고해 추정했을 뿐 두 수치를 합쳐 종단 시간으로 확정 측정하지는 않았다. 위 "발견하고 보류한 것" 3건에 대한 회귀 테스트도 이번에는 추가하지 않았다(수정하지 않았으므로).
- **배포**: `perf/audit-2026-09-28` 브랜치 커밋 `679cb6a`(`main` `021b00d`에서 분기, 중복 방지 기능 직후). `origin/main`·`deploy/main` 모두 `679cb6a`로 fast-forward push해 **운영 배포 완료**. Reading Chunk 로직·오늘의 서재·통합 계약(`CROSS_PROJECT_HANDOFF.md`)은 건드리지 않았다.
- **다음 작업**: 실제 운영 브라우저로 체감 속도 재확인. 위 "발견하고 보류한 것" 우선순위대로(특히 1번, 자식 함수 `st.rerun()` dispatch 구조 개선) 다음 성능 작업으로 진행할지 David 결정. Mac 자동 export는 별도 기능 작업으로 분리해 설계·승인 필요.

## 2026-09-28 — Claude Code(Orca): 새 책 추가 중복 검사 기능

- **작업 목적**: 사용자가 "이미 저장된 책이면 새 책 등록에서 검색해도 안 나오나?"라고 물어본 것을 계기로, 검색이 로컬 책장이 아니라 외부 API만 조회해 이미 등록한 책도 다시 후보로 나오고 중복 저장을 막는 장치가 없음을 확인했다. 사용자 승인 후 구체 UX 스펙을 받아 구현했다.
- **UX 요구사항**(사용자 제공): (1) 검색 결과는 숨기지 않는다. (2) 이미 책장에 있으면 "✓ 이미 내 책장에 있음" 표시. (3) 그 후보 선택 시 새 등록보다 "기존 책으로 이동"을 우선 제공. (4) ISBN 있으면 정규화 동일 여부로 저장 차단(최우선), ISBN 없을 때만 제목+저자 동일이면 경고(차단 아님), 제목만 같으면 무시, 다른 ISBN의 다른 판본은 같다고 단정하지 않음. (5) 저장 직전에도 재검사해 UI 우회를 막음. (6) 기존 중복 데이터는 삭제·병합하지 말고 존재 여부만 보고.
- **구현**: `lib/db.py`에 `normalize_isbn`(하이픈/공백 제거, 대문자 통일, ISBN-10/13 상호변환은 하지 않음), `isbn_lookup_map`, `find_book_by_isbn`, `find_books_by_title_author` 추가. `app.py`의 `render_add_book_form`: 검색 후보 라벨에 ISBN 매칭 표시 + "기존 책으로 이동" 버튼(검색 화면), 폼 제출 시 ISBN 매칭이면 `st.session_state`에 지속시켜 에러+이동 버튼을 다음 rerun에서도 보여주고(처음엔 `if submitted:` 블록 안에만 버튼을 뒀다가 클릭 시 사라지는 버그를 발견해 `pending_key`와 같은 지속 상태 패턴으로 고쳤다), 제목+저자만 일치하면 `pending_key`에 담아 "그래도 추가"/"취소"로 확인받는다(기존 reading_chunks의 "그래도 저장" 패턴 재사용).
- **운영 데이터 감사(읽기 전용 `get_readonly_connection`, 삭제·병합 없음)**: 707권 중 "희망을 짓는다는 것"(엘렌 데이비스)이 위시리스트/읽는 중 상태로 **2권 진짜 중복**. ISBN "2147483647"(2^31-1)을 서로 무관한 책 **12권**이 공유 — 정수 오버플로로 생긴 잘못된 값으로 보여 `normalize_isbn`에서 무효 처리하도록 제외(`_KNOWN_INVALID_ISBNS`). "역사지리로 보는 성경 세트" 1~3권은 세트 공용 ISBN 공유(정상, 중복 아님) — 다권 세트가 향후 ISBN만으로 오탐될 수 있는 한계로 남음. 제목+저자 기준 약한 중복 0건.
- **테스트**: `tests/test_add_book_dedup.py` 신규 18개(정규화 파라미터화 7개, 검색 결과 표시·이동 3개, ISBN 저장 차단·우회 방지 2개, 제목+저자 경고·확인·취소 3개, 제목만/ISBN 다름 비차단 2개, 무효 ISBN sentinel 비차단 1개). "기존 책으로 이동" 버튼이 다음 rerun에 사라지는 버그를 이 테스트들로 잡아 지속 상태로 고쳤다. 전체 pytest **256개 통과**(기존 238 + 신규 18), py_compile·git diff --check 통과.
- **배포**: `feature/add-book-dedup` 브랜치 커밋 `0fc97e2`(`main` `a3f44e2`에서 분기, P0 핫픽스 직후). `origin/main`·`deploy/main` 모두 `0fc97e2`로 fast-forward push해 **운영 배포 완료**. Reading Chunk, 통합 계약(`CROSS_PROJECT_HANDOFF.md`)은 건드리지 않았다.
- **남은 일**: 실제 운영 브라우저로 최종 시각 확인(이 세션엔 브라우저 연결 없음). "희망을 짓는다는 것" 기존 중복 2건 정리는 David 결정 필요(이번 작업에서 건드리지 않음). `docs/HANDOFF.md`에도 같은 내용을 기록했다.

## 2026-09-28 — Claude Code(Orca): P0 운영 책장 크래시 재현·원인 확정·핫픽스·배포

- **작업 목적**: David가 모바일 운영 앱에서 새 카테고리("분별력")를 직접 입력해 책을 저장한 뒤 책장으로 돌아오면 화면이 죽는 P0 장애를 복구한다. 새 기능 개발은 하지 않는다.
- **Phase 0**: `docs/HANDOFF.md`·`WORKLOG.md`·최상위 `AGENTS.md`·`CROSS_PROJECT_HANDOFF.md`를 먼저 읽었다. 원래 작업트리(`codex/reading-chunks-1a`, 사용자 미커밋 기획문서 2개 보유)는 건드리지 않고, `/private/tmp/readdam-p0-shelf-repro/readdam`에 `main`(당시 `0cbe841`) 워크트리를 새로 만들어 작업했다.
- **Phase 1 재현**: 실제 traceback 원문은 이번 세션에 전달되지 않아 스크린샷 기반 호출 흐름(`render_shelf → _cover_grid → _cover_card → db.cover_source(...)`)과 David가 추가로 확인한 재현 조건(새 카테고리 직접 생성 → 책 저장 → 책장 진입)만으로 시작했다.
- **Phase 2/3 원인 조사**: SQLite 기반 AppTest 재현은 실패했다(크래시 없음) — SQLite 경로는 문제가 없었다. Postgres dict-row 경로를 psycopg 없이 흉내 낸 `PostgresConnection`/`Cursor` 스텁으로 `lib.database.read_frame`과 `lib.shelf_ui._cover_card`를 직접 호출해 재현한 결과: **`pages` 같은 숫자 컬럼에 NULL이 한 행이라도 섞이면 pandas가 그 컬럼 전체를 float64로 승격시켜 NULL이 None이 아니라 NaN이 된다.** NaN은 파이썬에서 참으로 판정되므로 `shelf_ui._cover_card`의 `total = book['pages'] or 0`가 NaN을 그대로 넘기고, `st.progress(min(max(current/total,0),1) if total else 0, ...)`가 `st.progress(nan)`을 호출해 **`streamlit.errors.StreamlitAPIException: Progress Value has invalid value [0.0, 1.0]: nan`**을 던진다. 이건 `show_progress=True`(책장의 "이어서 읽기", `status='읽는 중'`)에서만 발생한다. `db.cover_source(...)`는 스크린샷에서 예외가 표시된 프레임이었을 뿐 그 함수 자체에서 예외가 나지는 않았다(직접 호출로 확인, `cover_photo`/`cover_url`이 None인 경우 정상적으로 `None`을 반환함).
- **부수 발견**: 2026-09-26에 같은 종류의 "nan 문자열" 버그를 고치며 `lib/database.py`의 `read_frame`에 `frame.where(pd.notna(frame), None)`을 추가했었는데(커밋 `51e5b0c` 계열), 이번 조사로 **이 수정이 숫자(float64) 컬럼에는 실제로 적용되지 않는다는 것을 확인했다.** `.where(cond, None)`은 float64 dtype 컬럼에 None을 넣어도 pandas가 조용히 NaN으로 되돌린다(`frame.astype(object).where(...)`처럼 dtype을 먼저 object로 바꿔야 실제로 None이 유지된다). 문자열 전용 컬럼(예: `quote`)에서는 우연히 잘 작동했을 뿐이었다.
- **수정 방법 검토**: `read_frame`을 `frame.astype(object).where(pd.notna(frame), None)`으로 바꾸는 안을 먼저 시도해 이 P0는 해결됨을 확인했다. 하지만 전체 테스트를 돌리자 `tests/test_notebook_app.py::test_cards_normalize_missing_values_from_new_pandas_string_dtype`가 회귀했다: 이 테스트는 pandas `future.infer_string` 모드에서 `read_frame`이 문자열 컬럼의 `'str'` dtype을 그대로 보존해야 한다고 요구하는데, `astype(object)`는 이를 깨버린다. 대신 `lib/notebook_ui.py`의 `cards()`가 이미 쓰고 있던 패턴 — DataFrame row를 쓰는 지점에서 `{k: None if pd.isna(v) else v for k, v in row.items()}`로 정규화 — 을 `lib/shelf_ui.py::_cover_card` 진입부에 그대로 적용하는 것으로 방향을 바꿨다. `read_frame`은 원래 상태로 되돌렸다(변경 없음).
- **Phase 4 최소 수정**: `lib/shelf_ui.py`의 `_cover_card` 맨 앞에 `book = {key: None if pd.isna(value) else value for key, value in book.items()}` 한 줄(및 import pandas) 추가. DB 데이터 변경 없음, schema 변경 없음, 새 API 없음, UI 재설계 없음.
- **테스트**: `tests/test_postgres_compat.py`에 `test_shelf_cover_card_does_not_crash_on_new_book_with_null_pages_from_postgres` 추가. 수정 전 상태(`git stash`로 되돌려 확인)로는 이 테스트가 실제로 실패함을 확인해 진짜 회귀 테스트임을 검증했다. 수정 후: 전체 pytest **238개 통과**(회귀 테스트 추가분 포함, 기존 `test_cards_normalize_missing_values_from_new_pandas_string_dtype`도 그대로 통과), `python -m py_compile` 통과, `git diff --check` 통과.
- **배포**: `hotfix/shelf-nan-progress-crash` 브랜치 커밋 `f4f3179`(`main` `0cbe841`에서 분기). `origin/main`·`deploy/main` 모두 `f4f3179`로 fast-forward push해 **운영 배포 완료**. Reading Chunk 1차-A/1차-B 코드는 건드리지 않았고 기존 NO-GO 상태는 그대로다.
- **남은 일**: 재배포 후 실제 운영 브라우저에서 "새 카테고리 생성 → 책 저장 → 책장 진입"이 실제로 안 죽는지 최종 시각 확인이 아직 없다(이 세션엔 브라우저 연결이 없었음). `docs/HANDOFF.md`에도 같은 내용을 기록했다.

## 2026-09-28 — Claude Code: i9→M1 이관 Checkpoint

- **작업 목적**: 새 기능 없이, M1 작업자가 HANDOFF·WORKLOG만 보고 이어받을 수 있게 전체 상태를 확정한다.
- **실행환경**: i9의 읽담전문, `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, `main`, 시작 HEAD `00f495c`.
- **실제 확인**: `git ls-remote`로 origin/main = deploy/main = local main = `00f495c`를 확인했다. worktree 4개 중 3개(/private/tmp)는 clean이다. 원본 작업트리는 사용자 기획문서 2건만 변경돼 있다. stash는 없다. 로컬 브랜치 9개 중 main에 없는 커밋(patch 기준)을 가진 것은 `codex/reading-chunks-1a`(1, 문서)·`codex/reading-chunks-1b`(23, main에 선별 재적용됨, 남은 차이는 문서 이력)·`codex/reading-chunks-private-default`(5, 문서)였고, origin에는 없었다.
- **실제 변경 내용**: 위 3개 브랜치를 origin에 같은 이름으로 새로 push했다(보존용, force 없음). HANDOFF에 이관 Checkpoint 항목을, WORKLOG에 이 항목을 추가했다. 코드·schema·Secrets·운영 DB·iCloud·오늘의 서재·공동 저장소 변경은 0이다.
- **테스트 결과**: 코드 변경이 없어 새 테스트는 없다. 직전 기능 커밋 기준 전체 237 passed(세션 임시 x86 venv).
- **커밋/배포 여부**: 이 기록 커밋을 main→origin/main→deploy/main에 일반 fast-forward로 올린다(문서만).
- **발견 문제/남은 작업**: i9 원본 `.venv`는 arm64 전용이라 i9에서 쓸 수 없다. Sites D1 `0004` blocker 유지, 2차 실제 export 대상 0건, 운영 UI는 David 확인이 필요하다. 다음 작업은 M1 환경 검증(fetch 후 전체 pytest)이다.

## 2026-09-28 — Claude Code: 새 책 등록 draft 유실(카테고리 조작·재검색) 수정

- **작업 목적**: 검색 결과를 선택한 뒤 카테고리 조작이나 화면 이동으로 자동입력 서지정보가 사라지고, 같은 책을 다시 검색해도 복원되지 않던 운영 버그를 고친다.
- **실행환경**: i9의 읽담전문, `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, `main`, 시작 HEAD `d0a6c54`. 시작 시 origin/main=deploy/main=`d0a6c54`(ls-remote)였다.
- **상태 흐름**: 검색어·폼 칸(제목·부제·저자·역자·출판사·ISBN·카테고리·직접입력·쪽수·상태)은 폼 위젯 key의 session state에 있고, Streamlit이 관리해 폼이 안 그려지면 사라진다. 검색 결과(`*_candidates`)·선택 표시(`*_autofill_source`)·draft(`*_autofill_values`)는 일반 session state라 계속 남는다. 선택한 후보는 radio 위젯 key다. 표지는 후보 dict에서 바로 그린다. 출간일은 DB에 칸이 없다. DB에는 저장 때만 쓴다.
- **재현(AppTest)**: 폼 안 카테고리 선택·직접 입력, 폼 밖 책장 필터 rerun에서는 유지됐다. 다른 메뉴에 다녀오면 폼 칸 key가 session state에서 사라졌지만 표지·후보·선택 표시는 남았고, 같은 책 재검색 뒤에도 전부 `''`였다(표시 일치로 조기 return). 저장 뒤에는 폼 칸에 이전 책 값이 남아 다음 선택에서 교체되지 않았다. `enter_to_submit` 기본값 True 때문에 '카테고리 직접 입력'에서 Enter를 누르면 저장이 제출된다.
- **실제 변경 내용**: `app.py`에서 같은 선택이면 지워진 칸만 draft에서 복원한다. 검색 버튼 성공 시 선택 표시를 지워 재선택하면 다시 적용한다. `_reset_add_book_draft`는 저장 뒤 draft와 폼 key 전체를 지운다. 폼은 `enter_to_submit=False`이고, 적은 새 카테고리를 우선 사용한다. 저장 로직·schema는 불변이다.
- **테스트 결과**: 신규 8건 중 6건 RED(화면 왕복 유지, 재검색 전체 복원, 상단 패널 왕복, 저장 뒤 오염, 새 카테고리 저장, Enter 제출) → GREEN. 유지 확인 2건(폼 안 카테고리 조작, rerun 중 사용자 수정값)은 수정 전에도 PASS였다. `tests/test_add_book_autofill.py` 28 passed, Reading Chunk 등 62 passed, 전체 **237 passed**, compile·diff PASS.
- **커밋/배포 여부**: 기능 `84b1604`와 이 기록 커밋. origin/main·deploy/main에 일반 fast-forward push한다. Streamlit 브라우저 smoke는 미확인이다.
- **발견 문제/남은 작업**: 이전 운영 시도에서 Enter로 책이 이미 저장됐을 수 있어 중복 여부를 David가 확인한다. 저장 성공 메시지가 곧바로 `st.rerun()` 때문에 보이지 않는 기존 동작은 범위 밖이라 두었다. 다른 화면에 다녀오기 전에 사용자가 직접 고친 미제출 값은 Streamlit 구조상 보존되지 않고 draft 값으로 돌아간다.

## 2026-09-28 — Claude Code: 새 책 검색 선택 시 서지정보 자동입력

- **작업 목적**: 검색 결과를 선택하면 도서관정보나루에서 알 수 있는 서지정보가 빈 칸에 자동으로 들어가게 한다. David는 없거나 잘못된 값만 고친다.
- **실행환경**: i9의 읽담전문(Intel i9 Mac 실제 Terminal / Claude Code), `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, `main`, 시작 HEAD `4dff9fe`. 실제 `git ls-remote` 결과 origin/main=deploy/main=`4dff9fe`였다. HANDOFF의 `5129d75`는 main 계보 안의 과거 커밋이다(불일치 아님).
- **감사 결과**: books에 있는 서지 칸은 title·subtitle·author·translator·publisher·isbn·category·pages·cover_url이다. 출간일 칸은 없고, 공저자는 author 문자열 안에서만 표현할 수 있다. upstream `srchBooks`/`srchDtlList`는 bookname(제목 :부제)·authors·publisher·publication_year·isbn13·class_no·class_nm·bookImageURL을 주고, 쪽수는 주지 않는다.
- **원인**: `render_add_book_form`의 text_input이 `key`를 쓰기 때문에, 첫 렌더 뒤에는 `value=`로 넘긴 후보 값이 무시됐다. 표지는 위젯이 아니어서 보였다. 또 `_parse_authors`는 `;`와 `:` 형식만 알아서 `엘렌 데이비스,윤상필 옮김`을 통째로 저자에 넣었다.
- **실제 변경 내용**: `app.py`에 `_autofill_add_book_fields`를 추가했다. 선택이 바뀌면 빈 칸이나 직전 자동입력 그대로인 칸만 session state로 채우고, 사용자가 입력·수정한 칸은 보존한다. 후보에 없는 값은 빈 칸으로 둔다. 출간년도·KDC 분류는 "참고용, 저장되지 않음" caption으로만 보인다. `lib/library_api.py`의 저자 파서는 명시 역할 표기가 있을 때만 저자/역자를 나눈다. 후보 dict에는 `publication_year`·`class_no`·`class_nm`을 추가했다. schema·insert_book·Reading Chunk 경로는 바꾸지 않았다.
- **테스트 결과**: RED(신규 16건 중 11건 실패, AppTest에서 선택 후 칸이 `''`) → GREEN. 신규 `tests/test_add_book_autofill.py`는 실제 upstream 응답 fixture로 선택 자동입력·후보 전환·사용자 입력 보호·저장 보존·category/pages 비추측·저자/역자 분리 14형식을 검증한다. 전체 **229 passed**, compile·`git diff --check` PASS. 원본 `.venv`는 i9에서 numpy/libpq arm64 문제로 쓸 수 없어 scratchpad 임시 venv(Streamlit 1.50)로 실행했다.
- **실제 upstream 확인**(키 비출력): 「희망을 짓는다는 것」 제목·ISBN 검색 모두 제목 `희망을 짓는다는 것`, 부제 `성경의 언어로 쌓아 올린 51편의 메시지`, 저자 `엘렌 데이비스`, 역자 `윤상필`, 출판사 `한국성서유니온선교회`, ISBN `9788932550817`, 표지 URL 있음, 2026, KDC 235.2였다. 역사란 무엇인가·데미안·사피엔스·순전한 기독교·채식주의자도 저자/역자가 올바르게 나뉘었다. `한상경 글·사진`처럼 모르는 표기는 원문 그대로 둔다.
- **커밋/배포 여부**: 기능 `b8ec52d`와 이 기록 커밋. 사전 원격 `4dff9fe`를 확인한 뒤 origin/main·deploy/main에 일반 fast-forward push한다. Streamlit 브라우저 smoke는 미확인이다.
- 보강(2026-09-28, Claude Code): David가 현재 수준으로 충분하다고 결정했다. 쪽수 추가 API와 카테고리 제안은 진행하지 않는다.
- **발견 문제/남은 작업**: 공저자(upstream 누락)와 쪽수는 추가 source가 필요하다. 출간년도 저장은 schema 변경 승인이 필요하다. 책 카테고리는 개인 분류와 KDC 매핑 방식을 David가 결정해야 한다. 사용자 기획문서 2건은 불변이다.

## 2026-09-28 — Claude Code: 도서관정보나루 title/isbn13 검색 수정 및 운영 반영

- **작업 목적**: 진단 판정 B에 따라 `srchBooks` 검색 파라미터를 최소 수정해 신간 제목·ISBN 검색 누락을 해소하고 운영에 반영한다.
- **실행환경**: Intel i9 Mac 실제 Terminal / Claude Code, `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`, `main`, 시작 HEAD `7f6bc6f`.
- **실제 변경 내용**: `lib/library_api.py`에 `_normalize_isbn13`을 추가했다(공백·하이픈 제거, 978/979로 시작하는 13자리). ISBN-13이면 `isbn13=`, 아니면 `title=`을 보낸다. 신규 `tests/test_library_api.py`는 title 사용·부분 제목·ISBN13·하이픈/공백 ISBN·숫자 제목(1984) 유지·파싱과 제목 없는 항목 제거 유지를 검증한다.
- **테스트 결과**: 먼저 RED 5 failed/1 passed를 확인했다. 수정 뒤 관련 13 passed(책 추가 AppTest 포함), 전체 **209 passed**, compile·`git diff --check` PASS.
- **실제 재현**(키 비출력): `희망을 짓는다는 것` 1건 중 1위, `9788932550817`·`978-89-325-5081-7` 1위, `희망을 짓는다` 10건 중 10위. 기존 도서 6권은 title 결과 상위 10건에 모두 있었다. 기존 keyword 결과는 `역사란 무엇인가`·`고요한 아침`·`순전한 기독교`에서 무관한 책이 상위에 나왔지만 title은 정확했다.
- **커밋/배포 여부**: 기능 `a5a7a51`, 이 기록 커밋. 이후 origin/main·deploy/main에 일반 fast-forward push(사전 원격 `542dbc8` 확인). Streamlit 화면 smoke는 브라우저 도구 부재로 미확인.
- **보류**: 저자/역자 파싱(`엘렌 데이비스,윤상필 옮김`), 공저자 누락, 국립중앙도서관 fallback, pageSize/pagination, UI 개편, schema 변경은 하지 않았다.
- **다음 작업**: David가 운영에서 제목·ISBN 검색을 직접 확인한다.

## 2026-09-28 — Claude Code: 도서관정보나루 신간 검색 누락 진단

- **작업 목적**: `희망을 짓는다는 것`(성서유니온, 2026-06-22, ISBN `9788932550817`)이 읽담 검색에서 나오지 않는 원인을 upstream과 읽담 처리 단계로 나눠 확인한다.
- **실행환경**: Intel i9 Mac 실제 Terminal / Claude Code, `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main` `main` `f836a89`. 스크립트는 세션 scratchpad에서만 실행했다. `.env`의 `DATA4LIBRARY_AUTH_KEY`만 읽었고 값은 출력하지 않았다.
- **현재 검색**: `lib/library_api.py` `http://data4library.kr/api/srchBooks`, `keyword=<입력>`, `pageNo=1`, `pageSize=10`, 페이지 이동 없음, cache 없음. 제목이 없는 항목만 제외하고 제목(` :` 부제 분리)·저자/역자(`;`·`역할:` 파싱)·출판사·isbn13·표지를 담는다. UI 문구는 “제목으로 검색”이다.
- **upstream 재현**: 제목을 `keyword`로 보내면 numFound 1이지만 다른 책(`대한민국에서 봉급쟁이로 산다는 것`)이 나오고 대상은 없다. 제목+저자를 `keyword`로 보내면 152건 중 상위 100건에 대상이 없다. 저자를 `keyword`로 보내면 151건 전체에 대상이 없다. ISBN을 `keyword`로 보내면 0건이다. 반면 `title=`·`title+author`·`author=엘렌 데이비스`(4건)·`author=오스틴 매키버 데니스`·`isbn13=`는 모두 **1위**, `srchDtlList`(isbn13)에서도 상세·표지 URL이 조회된다. 읽담 `search_books` 최종 결과는 네 입력 모두 대상 0건이다.
- **원인 근거**: 같은 출판사 최근 도서 12건을 제목으로 비교하니 `keyword` 결과에는 12/12 모두 대상이 없었고, `title`에서는 모두 1건 이상 나왔다. `keyword`는 제목 검색 파라미터가 아니다. 판정 **B**(query 파라미터). pagination(C)·후처리 filter(D)는 원인이 아니다. 부수로 E 성격의 이슈도 있다: upstream authors가 `엘렌 데이비스,윤상필 옮김`이라 현재 파서가 역자를 저자 칸에 넣고, 공저자 `오스틴 매키버 데니스`는 upstream authors에 없다(author 검색으로는 1위). upstream 출판사명은 `한국성서유니온선교회`.
- **fallback 평가**: 원인이 A가 아니므로 이번 건에는 필요 없다. 국립중앙도서관 ISBN 서지정보 API는 공개 문서 기준으로 제목·저자·출판사·ISBN·출판예정일/실제 출판일·쪽수(`PAGE`)·표지(`TITLE_URL`, 비어 있는 경우가 많음)를 준다. 별도 인증키(cert_key)가 필요하다. 실제 호출은 키가 없어 검증하지 않았다.
- **커밋/배포 여부**: 코드·설정·API key·배포 변경 0. 이 기록만 local main 문서 커밋·미push.
- **다음 작업**: David가 `keyword`→`title`(ISBN 입력 시 `isbn13`) 최소 수정 승인 여부를 결정한다.

## 2026-09-28 — Claude Code: 책장 상단 새 책 추가 origin/deploy 동기화

- **작업 목적**: local main `542dbc8`(새 책 추가 `dcf640c` 포함)을 origin/main·deploy/main에 반영하고 Streamlit 운영 갱신을 확인한다.
- **실행환경**: Intel i9 Mac 실제 Terminal / Claude Code, clean main worktree `/private/tmp/reading-chunk-1b-qfdk556c/readdam-main`.
- **실제 변경 내용**: 실제 원격 사전 조회 origin=deploy=`6a66872`(기록과 일치). ff 확인 후 `git push origin main:main`·`git push deploy main:main` 모두 `6a66872..542dbc8` 일반 push. force·merge·rebase 없음. 재조회 두 원격 모두 `542dbc8`.
- **테스트 결과**: 격리 pyenv에서 **203 passed**, compile·`git diff --check 6a66872 main` PASS. push 후 health 200 `ok`.
- **커밋/배포 여부**: 제품 원격 반영 완료. 운영 화면 smoke는 브라우저 도구 부재로 미수행. Secrets·Sites/D1·운영 DB·iCloud·launchd·오늘의 서재 변경 없음. 사용자 기획문서 2건 불변.
- **남은 일**: David가 운영 화면 smoke(새 책 추가 바로가기·추천 UI)를 확인한다.

## 2026-09-28 — Codex: 책장 상단 새 책 추가 바로가기

- **작업 목적**: 책장 맨 아래까지 이동하지 않고 새 책 등록을 시작할 수 있도록 `이어서 읽기` 바로 위에 상단 바로가기를 추가한다.
- **실제 변경 내용**: `lib/shelf_ui.py`에 `＋ 새 책 추가` 버튼과 상단 입력 surface를 추가했다. `app.py`의 기존 `render_add_book_form`은 key prefix를 받을 수 있게 하여 상단과 기존 하단이 같은 검색·입력 검증·`db.insert_book` 처리 함수를 사용한다. 하단 `➕ 새 책 추가` UI는 제거하지 않았다.
- **테스트 결과**: 먼저 상단 button이 없다는 AppTest RED를 확인했다. 구현 후 신규 AppTest는 상단 버튼 클릭, 상단·하단 입력 surface 동시 접근, 두 경로의 테스트 DB 저장을 검증한다. 관련 책장 테스트 **7 passed**, 전체 **203 passed in 35.11s**, Python compile PASS, `git diff --check` PASS.
- **커밋/배포 여부**: 기능·테스트 `dcf640c`을 local main에 커밋했다. 원격 push·deploy·운영 DB write·iCloud write·Sites/D1 변경은 없다.
- **범위/남은 일**: Reading Chunk·예화 추천·exporter·오늘의 서재·DB schema는 변경하지 않았다. 다음은 실제 Streamlit 화면에서 상단 바로가기 사용감을 확인하는 일 1건이다.

## 2026-09-28 — Claude Code: 추천·승인 기능 origin/deploy 동기화

- **작업 목적**: 검증된 local main `6a66872`를 origin/main·deploy/main에 반영하고 Streamlit 운영 smoke를 준비한다.
- **실제 변경 내용**: 실제 원격 사전 조회 origin=`0d1530d`, deploy=`74d3c9d`(기록과 일치). 두 SHA 모두 main의 조상임을 확인하고 `git push origin main:main`(`0d1530d..6a66872`), `git push deploy main:main`(`74d3c9d..6a66872`)을 일반 push했다. force·merge·rebase 없음. 재조회 결과 두 원격 모두 `6a66872`.
- **테스트 결과**: 기존 i9 `.venv`는 x86_64/numpy 불일치로 수집 오류가 나 사용하지 않았고, 기존 격리 test-venv 두 곳에서 각각 **202 passed**. compile·`git diff --check 74d3c9d main` PASS. 앱 health endpoint 200 `ok`.
- **커밋/배포 여부**: 제품 원격 반영 완료. Streamlit 로그·로그인·UI smoke는 브라우저 도구 부재로 미수행이며 David 수동 확인 대기. Secrets·Sites/D1·운영 DB·iCloud write 없음.
- **남은 일과 중단 이유**: 운영 UI 확인과 경로 A 실제 사용자 E2E는 David가 수행한다.

## 2026-09-28 — Codex: 추천·승인 기능 Streamlit 운영 배포 재개 전 휴면 sync 안전성 확인

- **작업 목적**: David가 유지하기로 한 1차-B 5분 fragment가 Secrets 없이 휴면 상태에서 외부 통신·DB write·chunk/receipt/book snapshot 부작용 없이 끝나는지 확인하고, PASS 시 origin·deploy·Streamlit 배포를 진행한다.
- **안전성 확인**: `sync_once`는 owner 형식 확인 뒤 URL·두 key가 하나라도 비어 있으면 `not_configured`로 즉시 반환한다. HTTP 접근을 예외로 만드는 격리 probe에서 결과는 `not_configured`였고 HTTP·Chunk DML·receipt·book snapshot 접근은 0건이었다. `db.get_connection()`은 `connect → read-only require_schema` 경로이며 schema mutation을 하지 않는다. fragment는 내부 session state 두 항목만 기록하고 오류를 출력하지 않는다.
- **검증 근거**: 기존 `test_missing_settings_make_no_http_request`와 main 전체 **202 passed in 29.92s**, Python compile PASS, `git diff --check` PASS를 유지한다. Secrets 등록·오늘의 서재 운영 연결·Sites/D1·운영 DB 직접 write·iCloud write는 0건이다.
- **배포 중단**: `git ls-remote origin refs/heads/main`을 두 차례 실행했으나 모두 `Could not resolve host: github.com`으로 실패했다. 원격 main 상태를 재확인할 수 없으므로 push·deploy를 시도하지 않았다.
- **커밋/남은 일**: 이번 결과 문서는 후속 커밋으로 남긴다. GitHub DNS/네트워크 복구 후 origin/main SHA 확인, 일반 fast-forward push, deploy/main 반영, Streamlit smoke 순으로 재개한다.

## 2026-09-28 — Codex: 예화 카테고리 추천·승인 기능 main 반영 및 배포 안전성 관문

- **작업 목적**: 검증된 예화 카테고리 추천·승인 기능을 읽담 main에 안전하게 반영하고 Streamlit 배포 전 1차-B·2차 exporter 자동 실행 여부를 확인한다.
- **실제 변경 내용**: 깨끗한 별도 main worktree에서 `codex/reading-chunk-category-approval`을 `0d1530d..59d0250`으로 ff-only 반영했다. 원본 작업트리의 사용자 소유 `도서비서_기획문서.md` 수정과 `도서비서_기획문서 2.md` 미추적 파일은 그대로 보존했다. 이 상태 기록만 추가한다.
- **테스트 결과**: 반영 main에서 전체 pytest **202 passed in 29.92s**, Python compile PASS, `git diff --check` PASS. deploy/main=`74d3c9d`부터 main까지의 변경은 Reading Chunk 1차-B·2차와 예화 카테고리 추천·승인 관련 파일임을 대조했다.
- **배포 안전성 감사**: 2차 exporter는 앱 시작·Streamlit 사용 흐름에서 호출되지 않는 명시적 CLI다. 1차-B `sync_once`는 URL·두 key가 비어 있으면 외부 HTTP 전에 `not_configured`로 반환한다. 다만 `lib/readdam_sync_ui.py`의 `@st.fragment(run_every="5m")`가 자동으로 동기화 경로를 호출하므로 “background sync 자동 시작 없음” 조건에는 맞지 않는다.
- **커밋/배포 여부**: 이번 상태 문서는 후속 커밋으로 남긴다. origin/main push, deploy/main 반영, Streamlit 배포, Secrets 등록, Sites/D1 변경, 운영 DB 직접 write, iCloud write는 모두 없다.
- **남은 일과 중단 이유**: 이번 범위는 오늘의 서재 코드를 바꿀 수 없으므로 자동 fragment를 제거·비활성화하는 별도 승인 없이 배포를 진행하지 않는다. 실제 David E2E도 운영 UI 반영 전에는 시작하지 않는다.

## 2026-09-28 — Codex: David 승인 예화 카테고리 사전 최소 수정

- **목적/변경**: 예화창고 카테고리를 배타적 분류가 아닌 다중 추천 가능한 주제 바구니로 확정했다. 유용한 중복 후보는 최대 3개·David 최종 선택 원칙을 유지했다. 승인된 세 keyword만 `d037be1`에서 반영했다: `그리스도인의 삶의 방식`, `시간`의 `세월` 삭제, `위선의 가면`.
- **불변 범위**: category 63개·canonical name·aliases·그 외 keywords는 이전 승인 사전과 동일하다. 새 카테고리·실제 폴더 이름·schema·오늘의 서재·1차-B·exporter 실행은 바꾸지 않았다.
- **검증**: 변경 전 승인 테스트는 RED, 반영 후 category 테스트 13 PASS와 공용 fixture PASS. 이전 snapshot과의 구조 비교로 category 63개·canonical 순서·aliases 불변, keyword 변경 category가 정확히 3개임을 확인했다. 전체 **202 passed**, Python compile PASS, `git diff --check` PASS.
- **실제 폴더/운영**: 실제 iCloud 최상위 디렉터리 이름과 metadata만 읽어 63/63 대응, 실제 물리 이름 63개 NFD, `교회`·`사명` NFC exact match, 검사 전후 metadata 동일을 확인했다. iCloud write·실제 export·운영 DB write 0건이다.
- **공동 기록/남은 일**: 읽담 HANDOFF/PROJECT/사전 문서는 갱신한다. 공동 CROSS 저장소에는 승인 철학을 기록하려 했으나 상위 Git worktree lock 쓰기 권한이 거부되어 커밋하지 못했고 깨끗하게 되돌렸다. 다음 작업은 David의 main 반영 여부 결정 1건이다.

## 2026-09-28 — Codex: Reading Chunk 경로 A 예화 카테고리 추천·승인 구현

- **목적/범위**: Reading Chunk를 먼저 빈 `illustrationTags`로 저장한 뒤, 실제 예화창고 기존 카테고리를 비AI 규칙으로 최대 3개 추천하고 David의 명시 승인 때만 canonical 값으로 저장한다. 오늘의 서재 코드·1차-B 운영 연결·운영 DB write·실제 iCloud export·main/push/deploy는 범위 밖으로 유지했다.
- **변경/커밋**: `276c958`은 `config/illustration_categories.json`(실제 63개 폴더의 NFC canonical snapshot), 안전한 갱신 CLI, aliases/keywords 초안, 공용 recommendation fixture, snapshot 검증·정규화·점수 엔진을 추가했다. UI에서 자유 예화 태그 입력을 제거하고 저장 직후 추천/검색 가능한 전체 다중 선택/승인/보내지 않음을 제공한다. 기존 legacy 자유 값은 일반 수정에서 보존하고 승인 패널에서만 canonical 또는 빈 목록으로 바뀐다. exporter는 canonical NFC exact folder match를 먼저 처리해 `교회`·`사명`을 정상 매핑하고 legacy ambiguous 규칙은 exact match가 없을 때만 적용한다.
- **검증**: 신규 snapshot·추천·저장·UI·legacy exporter 테스트를 포함한 전체 **201 passed**, Python `compileall` PASS, tracked 및 신규 파일 `diff --check` PASS. 공용 fixture는 명시 용서/관계/기도/믿음/사명/교회/복수/없음/alias/일반 tag 사례를 고정한다.
- **실제 예화창고 read-only preflight**: 최상위 이름/디렉터리 metadata만 읽었다. snapshot 63개와 실제 폴더 63개가 같은 순서로 일치하고, 물리 이름 63개 모두 NFD이며 `교회`·`사명`은 각각 단일 NFC exact match였다. 검사 전후 최상위 directory metadata도 동일했다. 파일 본문·실제 exporter는 실행하지 않았고 iCloud write 0건이다.
- **공동 계약/배포/남은 일**: exporter 우선순위 정책은 공동 로컬 문서 커밋 `188ac7b`에 기록했다. 읽담 main/origin/main=`0d1530d`, deploy/main=`74d3c9d`는 불변이며 운영 DB write 0건이다. 다음 작업 1개는 [63개 사전 초안](ILLUSTRATION_CATEGORY_DICTIONARY_DRAFT.md)의 David 검토다.
- **보강(2026-09-28, Codex)**: `298ef54`로 오늘의 서재 source Chunk도 읽담 승인 패널에서 카테고리를 비울 수 있는 UI 회귀를 명시했다. 전체 201 tests·compile·diff check를 다시 PASS했다.

## 2026-09-28 — Codex: 읽담 Reading Chunk local main을 origin/main에 동기화

- **목적/변경**: local main `8e15c1f`와 실제 원격 origin/main `74d3c9d`가 fast-forward 관계이고 별도 main worktree가 clean임을 확인했다. `git push origin main:main`으로 읽담의 Reading Chunk 1차-B·2차 코드/문서를 원격에 보존했다. 상태 인계를 HANDOFF/WORKLOG에 추가했다.
- **검증/보호**: push 뒤 main과 origin/main의 SHA 일치 및 작업트리 상태를 확인한다. 기존 원본 작업트리의 사용자 기획문서 2건과 deploy/main은 불변이다. 오늘의 서재·공동 저장소는 origin remote가 없어서 push하지 않았고 remote를 임의 설정하지 않았다.
- **상태/남은 일**: 읽담 측 1차-B·2차는 local/origin 보존 완료. 전체 1차-B origin 동기화는 오늘의 서재 원격 미설정으로 미완료이며 운영 연결도 Sites 관리형 D1 `0004` 공식 lifecycle 미확인으로 BLOCKED다. 2차 실제 export는 eligible illustration Chunk 0건으로 미실행이다. Streamlit/Sites 배포·Secrets·DB/iCloud write 0건. 다음은 오늘의 서재의 승인된 원격 동기화 경로 확인이다.


## 2026-09-28 — Codex: Reading Chunk 1차-B·2차 local main 정본화

- **목적/범위**: 기존 main `74d3c9d`와 깨끗한 후보 `90fe1c2`를 대조하고 Reading Chunk 변경만 별도 main worktree에서 반영했다. 후보의 기존 활동 nan 관련 문서 커밋 및 다른 작업은 가져오지 않았다. 원본 작업트리의 수정된 사용자 기획문서와 미추적 문서는 건드리지 않았다.
- **변경/커밋**: 1차-B ingest·payload 검증·책 매칭·chunkId 멱등성·pull/receipt/book snapshot·관련 테스트 `a0006a4`; 2차 manifest 소유권·태그 매핑·dry-run exporter·관련 테스트 `bf972a0`; 2차 로컬 계획·실제 iCloud 프리플라이트 기록 `b6a7c23`; HANDOFF/PROJECT/WORKLOG 최신 판정은 후속 문서 커밋. 기존 과거 NO-GO 기록은 보존했다.
- **검증**: 반영된 main 제품 기준 전체 **186 passed**, Python `compileall` PASS, `git diff --check` PASS. 2차 exporter는 명시적 CLI로만 실행되고 앱 시작 경로에서 import/호출하지 않는다. 1차-B는 URL/전용 토큰/Sites 게이트 설정이 없으면 HTTP 요청 없이 `not_configured`로 끝나는 것을 코드·테스트로 확인했다. 이번 작업에서는 실제 DB/iCloud를 조회하거나 변경하지 않았다.
- **현재 판정**: 1차-A COMPLETE. 1차-B LOCAL COMPLETE / 운영 연결 BLOCKED — Sites 관리형 D1 `0004` 공식 migration lifecycle 미확인. 2차 LOCAL COMPLETE, 앞선 운영 DB READ ONLY·실제 iCloud dry-run 2회 PASS, 현재 eligible illustration Chunk 0건으로 실제 export 미실행. 이번 작업의 운영 변경·DB write·iCloud write 0건. 기존 활동 nan 버그는 이전 운영 수정·확인으로 CLOSED.
- **남은 일/위험**: 1차-B는 공식 D1 적용 경로 확인 전 push·배포·운영 연결 금지. 2차 실제 export는 대상이 생긴 뒤 dry-run 재검증과 별도 승인 필요. 이번 세션 origin push·Streamlit 배포·Secrets 변경 없음.

## 2026-09-28 — Codex: 활동 카드 nan 표시 최소 수정

- **목적/변경**: 진단된 기존 활동 `NULL→pandas NaN→truthy` 표시 문제를 Reading Chunk와 분리해 수정. `lib/notebook_ui.py:cards()`에서 DataFrame 행을 표시용 dict로 만들 때 scalar `pd.isna(value)`만 `None`으로 바꾼다. DB reader, dtype 정책, schema/데이터, Reading Chunk 구현, 배포 코드는 변경하지 않았다.
- **RED/GREEN**: `tests/test_notebook_app.py` AppTest 3개 추가. None/float NaN/pd.NA인 quote, NaN text/photo, 정상 quote/text, 실제 문자열 `"nan"`, 0쪽, `future.infer_string=True`의 PostgreSQL DataFrame 경로를 화면 출력으로 검사한다. 수정 전 2실패(사진 NaN 경로 예외·문자 nan 출력)/1통과를 확인하고 최소 수정 후 카드6통과. 기존 카드 테스트도 유지된다.
- **검증**: 변경 전 기준157통과, 변경 후 전체 **160 passed in 13.09s**. `lib/notebook_ui.py`·`tests/test_notebook_app.py` Python compile PASS, `git diff --check` PASS. Node 파일 변경이 없어 별도 Node syntax 대상 없음. 테스트는 합성 데이터만 사용했으며 운영 DB 접속/DDL/DML0건. 실제 운영 앱은 미배포라 배포 후 화면 검증이 남는다.
- **커밋/배포/남은 일**: 제품·테스트 `c6951b4`를 `codex/reading-chunks-private-default`에 로컬 커밋, 결과 문서는 별도 커밋. main/origin/deploy push·Streamlit 재배포 없음, 원본 사용자 기획문서2개 불변. 다음은 David의 별도 승인 후 main 반영·운영 배포·기존 활동 카드 smoke 검증 1건. Reading Chunk 1차-A COMPLETE 유지, 1차-B/2차 export 미진입.

## 2026-09-28 — Codex: 기존 활동 nan 표시 재발 원인 진단

- **목적/변경**: 1차-A와 분리된 기존 활동 표시 결함만 진단. 제품 코드·운영 DB·migration·재배포·기존 데이터 변경 없음.
- **운영 원본**: 앱과 동일한 DB 설정을 안전하게 로딩하고 production target 확인 뒤 READ ONLY/REPEATABLE READ로 activities 전체5,667건을 조회했다. 활성5,667건, 활동 있는 책387권. `quote` NULL2,238, `text` NULL3,767, `photo` NULL5,610; 세 필드의 문자열 `nan`/숫자 NaN은 모두0. 이관 원본 SQLite의5,667 ID와 일치하고 NULL 여부 불일치0. 읽담의 2026-09-20 이관 기록도 5,667건 일치를 보고한다. 현재 운영에 원본에 없는 활동 행은 없다.
- **단계별 재현**: Safari 선택 책 3건은 `quote` NULL/문자열/NULL, `text` 문자열/NULL/NULL이나 카드에는 `nan`/잘못된 `내 생각`이 표시됐다. 로컬 pandas2.3.3의 `pd.options.future.infer_string=True`(pandas3 새 기본 dtype 호환 모드)를 켜 실제 운영 3건을 `db.list_activities()`로 읽으면 `quote`·`text`가 `str` dtype으로 추론되고 NULL이 float NaN이 된다. 기존 `frame.where(pd.notna(frame),None)`은 이 dtype에서 NaN을 None으로 바꾸지 못한다. `cards()`의 `row.get()`는 NaN을 참으로 취급해 문자 nan과 잘못된 라벨을 출력한다. 호환 모드 off에서는 같은 3건의 NULL이 None으로 남는다. pandas 공식 3.0 migration guide도 새 기본 `str` dtype의 결측값이 NaN이라고 명시한다. 운영의 정확한 pandas 버전은 직접 확인하지 못했다.
- **영향 추정/분포**: 동일 호환 모드로 운영 전체 행을 책별 DataFrame→iterrows 경로에 통과시키면 화면 quote/text NaN 후보 **5,050건/380권**(quote1,639, text3,743; 중복 가능), 3건 실제 화면 관찰. kind2=2,716, kind4=1,088, kind0=512 등이며 2013~2018년4,722건으로 원본 기록 분포와 함께 몰려 있다. 특정 이관 후 신생 데이터에 한정되지 않는다. 이 수치는 운영 화면 전수 계수가 아닌 재현 추정이다.
- **과거/판정**: `51e5b0c`는 Reading Chunk 전 동일 nan/라벨 증상을 기록하며 당시 all-NULL float64 추론을 원인으로 보았다. 현재도 NULL→DataFrame NaN→truthy 경로는 같지만 당시 운영 dtype 증거가 없어 세부 원인 동일 여부는 불명. 원본 NULL이 보존된 **표시 버그**이고 데이터 손상/스키마 변경/데이터 migration 근거는 없다. 최소 수정 후보는 두 화면이 공유하는 `lib/notebook_ui.py:cards()`의 row 결측 정규화 1곳이며 실제 수정/테스트는 별도 작업이다.
- **검증/커밋/배포/남은 일**: Safari 읽기 전용 관찰, Git 기록/코드·기존 테스트, 운영/SQLite read-only 집계 및 합성 dtype 재현. 문서만 이 브랜치에 로컬 커밋·미push. 다음은 승인된 별도 버그 수정/회귀 테스트 1건. 1차-B·2차 export 미착수.

## 2026-09-28 — Codex: 1차-A 실행 SHA·기존 활동 nan 최종 분류

- **목적/변경**: David가 지정한 두 종료 관문만 조사하고 HANDOFF/PROJECT/공동 인수인계에 판정을 기록했다. 제품 코드·운영 DB·배포 변경 없음.
- **SHA 검증**: deploy/main=`5129d75`, Streamlit 관리 로그 `Pulling code changes`→`Updated app!`, 실제 운영 Reading Chunk CRUD/export 동작. 관리 일반 설정·로그에는 commit SHA가 없고 GitHub commit status/check-runs/deployments에도 실행 SHA 증거가 없다. **실행 SHA 직접 확인 불가 / 강한 간접 증거 확보**로 남긴다.
- **nan 검증**: `51e5b0c`의 2026-09-26 커밋 메시지가 동일 `nan`/잘못된 `내 생각` 표시를 Reading Chunk 배포 전 운영 앱에서 사용자가 발견했다고 명시한다. `51e5b0c`→`5129d75`의 `lib/database.py` 및 `requirements.txt`는 동일, 활동 렌더링 본문도 변경되지 않았다. 기존 활동 데이터 해시는 배포 전후 동일했고 DB NULL은 문자 `nan`이 아니다. 현재 환경에서 옛 수정이 왜 충분하지 않은지는 미확정이며 별도 기존 표시 버그로 분리한다.
- **결론/남은 위험**: Reading Chunk 1차-A **COMPLETE**. 실행 SHA 직접 미확인 위험과 기존 활동 `nan` 잔여/재발 버그를 숨기지 않는다. 다음 작업 1개는 읽담의 기존 활동 `nan` 원인 진단. 1차-B·2차 export·iCloud 자동 export 미진입.
- **검증/커밋/배포**: Git diff·기존 문서·기존 배포 메타데이터와 읽기 전용 기존 활동 조회만 사용했다. 문서만 현재 브랜치에 로컬 커밋·미push; 새 배포/코드/DB 변경 없음.

## 2026-09-27 — Codex: Safari 재접속·txt export·테스트 삭제·보안 재확인

- **목적/승인**: David의 로그인 완료 및 진행 승인에 따라 남은 1차-A 운영 실검증을 수행했다. 실행 SHA 직접 확인은 완료로 간주하지 않았다.
- **Safari**: 재로그인 뒤 책장705권과 선택 책의 기존 활동3건을 확인했다. 동일 테스트 Chunk ID `48dad8d7-97f7-4ea7-a495-1f9d47ca1c37`이 Safari 재접속 후에도 수정된 메모·태그와 함께 유지됐다. 앞선 생성·조회·수정(7→11분)·일치/불일치 태그 검색과 연결해 실제 화면 CRUD 흐름을 검증했다.
- **Export/정리**: 승인된 기존 CLI로 이 테스트 ID 한 건만 격리 `/private/tmp`에 txt export했다. 출력1개에서 ISBN `9791130634500`, 읽은 시간11분, `출처 앱: 읽담 (readdam)`, 수정된 메모를 검사했다. 앱에서 정확한 테스트 Chunk만 소프트 삭제하고 목록의 빈 상태/삭제 알림 및 READ ONLY DB의 deleted_at 존재·전체1/활성0을 확인했다. 검증용 로컬 export 폴더의 txt·index·state·lock 파일4개를 삭제했다. 복구 가능한 DB 소프트 삭제 이력1건은 남는다.
- **보안/기존 데이터**: 최종 READ ONLY 비교에서 public 기존14표의 행 건수·내용 해시가 사전 기준과 같고 books705/activities5667/owner NULL0이었다. 기존 schema SHA `4f6b930680c82b0fc8d8cfd51e457d5dac7c997aa0c0f8be838184e92a1e6189` 불변. RLS enabled, policy0, PUBLIC/anon/authenticated/service_role CRUD=false, postgres=true. 실제 anon Data API GET HTTP401/42501 차단. 이전 post-check는 전체 chunk0을 기대하므로 이번 소프트 삭제 이력1건에서 `POSTCHECK_FAILED`로 표시되며, 이를 schema/보안 실패로 해석하지 않는다.
- **관찰/남은 위험**: 기존 활동 일부의 `nan` 표시가 다시 보였다. 관련 렌더링/DB reader는 이전 배포 코드와 동일하나, 원인은 이번 범위에서 확정하지 않았다. **실행 SHA 직접 확인: 미완료 / 간접 근거: deploy/main 5129d75 + Updated app 로그**. 따라서 Safari 검증은 완료, 1차-A는 INCOMPLETE. 다음 작업1개는 기존 운영 증거로 실행 SHA 직접 확인이다.
- **변경/검증/커밋/배포**: 제품 코드·DB schema/권한·오늘의 서재 앱·원격·Streamlit 배포 변경 없음. `docs/HANDOFF.md`, `docs/WORKLOG.md`, `docs/PROJECT.md`의 상태 기록만 제품 브랜치에 로컬 커밋·미push. 사용자 기획문서2개 해시 불변. 공동 정본 `1b5ff9a` 갱신. 1차-B/2차/iCloud 자동 export 금지 유지.

## 2026-09-27 — Codex: SHA 미확인 위험 승인 후 Safari CRUD 부분 검증

- David는 runtime SHA 직접 확인을 완료로 간주하지 않고, deploy/main 5129d75 + Updated app 로그 + 로그인/705권 표시를 근거로 실검증 진행을 승인했다.
- M1 Safari에서 부자의 그릇(큰글자도서)에 테스트 식별자 `[TEST-RC1A-20260927-M1-7429]` 1건을 생성했다. ID `48dad8d7-97f7-4ea7-a495-1f9d47ca1c37`, 페이지1–2, 시간7분→11분, 메모 수정. 저장 후 표시·수정 폼 기존 값·수정 후 표시·태그 일치 결과1/불일치 결과0/일치 복원 모두 확인했다.
- 독립 READ ONLY 조회로 같은 ID/수정 메모/11분/source_app=readdam/active1 확인. 기존 public14표 데이터 해시는 시작 전과 전부 동일. books705/activities5667/owner NULL0. RLS=true/policies0/외부4역할 CRUD=false/postgres=true. 실제 anon GET HTTP401/code42501 차단.
- 기존 책 목록과 활동3개는 표시되지만 일부 활동에 nan이 보였다. 관련 기존 렌더링/DB reader는 이전 deploy51e5b0c와 동일; 새 회귀로 확정하지 않았으며 전체 회귀 없음으로도 단정하지 않는다.
- Safari 새로고침 후 Auth 로그인 화면으로 돌아와 David에게 직접 재로그인을 요청했다. **테스트 행은 아직 활성1건이며 미삭제**. 재접속 유지·로컬 txt export·삭제·최종 post-check 미완료. 준비한 `/private/tmp/readdam_test_chunk_evidence.py`는 테스트 표시로 한 건만 READ ONLY 조회하고, 명시 --export 시 격리 /private/tmp에만 txt를 만드는 검증 보조이며 아직 export는 실행하지 않았다.
- 제품/main/원격은5129d75 불변. 결과 기록만 codex/reading-chunks-private-default에 로컬 커밋, 추가 push/배포/제품 수정/DDL/권한 변경 없음. 1차-A INCOMPLETE, 1차-B/2차/iCloud 금지. 다음은 재로그인 후 유지→export→정확한 테스트 Chunk 소프트 삭제→최종 무결성 확인.

## 2026-09-27 — Codex: 제품 main·운영 배포 및 Safari 실검증 관문 보류

- **승인/시작**: 제품5129d75 clean, 공동32cfc48, 오늘의서재2165808, 사용자기획문서2개기존SHA일치. fetch후main/origin4d97f4e·deploy51e5b0c로예상과동일. 운영READ ONLY post-check PASS, current/session postgres, reading_chunks0, schema/권한정상.
- **main/원격**: 별도main worktree `/private/tmp/readdam-release-main-jyMKCs`에서5129d75ff-only, 전체157 passed(12.53s)·diff PASS·사용자문서변경없음. 직전원격ref재확인후origin/main→deploy/main순서push, 양쪽실제원격SHA=`5129d75ed69081c51e5ad19ed23e48e5083259bd`확인. 예상밖커밋없음.
- **운영/Safari**: arm64 Safari로운영URL로그인화면및Manage app로그를확인.06:25:57 UTC Pulling code changes→06:25:58 Processed dependencies→06:26:00 Updated app. 대시보드연결소스book-butler-deploy/main/app.py. 실제runtimeSHA는로그/일반설정에없고GitHub커밋statuses빈목록(state pending), deployments빈목록, check-runs0이라직접확인미완료. 이값들을배포실패증거로단정하지도, 원격SHA를runtime확인으로대체하지도않았다.
- **보안/무결성**: `/private/tmp/readdam_release_readonly.py`가기존안전설정로딩후REPEATABLE READ/READ ONLY로public14표의전체행md5(to_jsonb)정렬집계해시와건수를배포전후대조, 모두동일. books705(해시c857683b6b4e9defe5c6f0156ba1fe67)/activities5667(507003c6cbdd8c5ad04bf107e111357d)/ownerNULL각각0/chunk0. 독립post-check에서도기존schema SHA4f6b930680c82b0fc8d8cfd51e457d5dac7c997aa0c0f8be838184e92a1e6189동일. RLS on/policy0/PUBLIC·anon·authenticated·service_role CRUD=false/postgres=true. 실제anonGET은배포전후HTTP401/code42501. API쓰기요청과DB DDL/DML은0건.
- **미실행/중단**: 사용자에게Safari기존계정직접로그인을요청했으나아직로그인화면이다. runtimeSHA확인관문도남아있어실제책/활동화면·Chunk생성/조회/수정/검색/재접속/export/삭제를실행하지않았다. 테스트Chunk0, txt0. 앱업데이트만으로완료하지않으며1차-A INCOMPLETE. 앱재부팅/Secrets변경/임시버전표시코드추가등우회없음.
- **인계/커밋**: 공동ca81d37과이저장소HANDOFF/PROJECT/WORKLOG에결과기록. 제품main/origin/deploy는5129d75고정, 결과문서만제품브랜치에로컬커밋·미push. 다음은Safari로그인/runtimeSHA근거확보후승인된실검증재개. 사용자문서2개불변,1차-B/2차/실제iCloud자동export금지.

## 2026-09-27 — Codex: 공동 Source of Truth 최신 운영 상태 정합화

- **목적/근거**: 사용자 승인으로 읽담 `bd04762`의 migration SUCCESS와 `b23e316`의 배포 전 기술검증157PASS를 공동 과거 상태와 대조했다. 제품 브랜치 시작 HEAD는 보고된 `b23e316`과 일치했고 코드/DB 추가 변경은 필요 없었다. 오늘의 서재 `9569cfd`는 2차 설계 보정 기록으로 운영 결과와 충돌하지 않는다.
- **변경**: 공동 `codex/reading-chunks-current-state`의 `32cfc48`이 프리플라이트·보안설계·dry-run9DDL·백업·migration 완료를 최신1.0절에 추가한다. 이 저장소 HANDOFF/PROJECT/WORKLOG는 해당 정본 위치와 현재 관문을 추가한다. 기존 항목은 삭제하지 않는다. 공동 main의 옛 상대경로 대신 `/private/tmp/readdam-cross-current-gJs4x6/CROSS_PROJECT_HANDOFF.md` 또는 공동 `git show 32cfc48:CROSS_PROJECT_HANDOFF.md`를 사용한다.
- **현재/판정**: **DB migration 완료 / 제품 main 반영·배포 전**, 1차-A 미완료. `b23e316`의 문서 충돌 blocker 해소. main 반영 준비 YES/운영 배포 준비 YES는 별도 승인 가능한 상태이지 실행 완료가 아니다. 최신157PASS·권한/구조/건수는 직전 검증 결과이며 이번 세션 DB 조회/테스트 실행은 없다.
- **검증/보호**: 문서 내용/근거 커밋·정본 참조·과거 줄 보존·문서만 변경·diff 검사, 사용자 기획문서2개 해시 불변을 확인한다. 제품/DB/migration 재실행/사용자 파일/공동 기본 dirty 문서 변경0. 커밋은 이 브랜치 문서3개만이며 main/origin/deploy는 기존 ref 그대로다.
- **다음/금지**: 별도 승인 후 최신 제품 main → origin/main → deploy/main → Streamlit 배포 → M1 Safari CRUD/재접속/기존 기능·Data API anon 차단 재확인. 1차-B·Reading Chunk 2차 export·실제 iCloud export 금지 유지. 이번 main merge/push/deploy/실제CRUD 실행0.

## 2026-09-27 — Codex: 제품 main 반영·배포 전 최종 검증

- **목적/범위**: 운영 migration 이후 제품 코드/DB 호환·Git 관계·사용자 파일 보호·배포 절차를 검증한다. merge/push/deploy/실제 CRUD/iCloud는 실행하지 않는다.
- **Git 실측**: 원격 fetch 후 main=origin/main=`4d97f4ecbaac6a0d95219469b79bde8df82bb9d6`, deploy/main=`51e5b0c72deb0afe69767da05028dea95dd688d1`, 검사 HEAD=`bd04762fd0975e4760e8760f608456a384b3cea5`. main...HEAD=0/13, deploy...HEAD=0/19. main에는 초기 구현 `aeecb7f`·출력 보완 `cbcf0b4`가 있고, 미반영은 `8843b56`, `6cdc7e7`, `038ab2e`, `952c3b3`, `5148d6f`, `22f7b1f`, `a1cac76`, `35bb2d5`, `f131eea`, `4362e8c`, `117d8c8`, `a9a71fa`, `bd04762`다. 이번 문서 기록 커밋은 이 목록 다음에 추가된다.
- **반영 파일**: main 대비39파일은 제품 안전성 수정·감사/회귀 테스트·운영 문서다. AGENTS 변경은 자동 init 제거 안내이며 migration/load_db·audit_source 변경은 offline initializer의 명시 승인 분리다. 사용자 기획문서 변경, `.env`, worktree/임시/백업 산출물은 main/deploy 대비 변경 목록에 없다. `4362e8c..HEAD`의 제품·테스트 diff는0이다.
- **운영 읽기 전용 결과**: 기존 안전한 로컬 설정 로딩 경로로 동일 운영 프로젝트·pooler6543·SSL, DB/schema=`postgres/public`, current/session=`postgres`, PostgreSQL17.6, transaction_read_only=on 확인. 구조계약 `reading-chunks-1a.v1` OK/issue0. PK/FK/UNIQUE/CHECK 정상, named index3+자동 index2 valid/ready. RLS=true/policy0, PUBLIC/anon/authenticated/service_role CRUD 각각 false, postgres CRUD 모두 true. books705/activities5667/owner NULL 각각0/chunk0. 기존 schema SHA `4f6b930680c82b0fc8d8cfd51e457d5dac7c997aa0c0f8be838184e92a1e6189` 불변. maintenance 계획0문장. 운영 DDL/DML0, 비밀값 출력0.
- **코드 연결/검증**: app→db.get_connection→psycopg→동일 conn의 chunk 서비스 SQL을 확인했다. chunk CRUD/export에 Data API 역할은 불필요하며 Auth/사진 Storage의 키 사용과 분리된다. 전체 pytest **157 passed in 13.15s**, 추적 Python63파일 compile PASS, Node audit2파일 syntax PASS, main 대비·작업 diff check PASS. Streamlit 앱으로 별도 Node 제품 build는 없다. 실제 사용자 CRUD는 미실행이다.
- **사용자 파일 보호**: 원본 `도서비서_기획문서.md` SHA-256=`75fd87c2c10ed9ce9a8dd9627ca2075cc16a5354fb57698b921ea801ca1808e9`, `도서비서_기획문서 2.md`=`515a448b3d245184697c1d69b6edf214757eb55e9d0f34fb7a3e9abaed6086bc`. 전후 동일이며 수정/stage/commit하지 않았다. 공동 기본 작업트리의 기존 변경도 보존한다.
- **배포 방법/계획**: blocker 해소와 별도 승인 뒤 깨끗한 main worktree에서 ref 재확인→`git merge --ff-only codex/reading-chunks-private-default`→검증→`git push origin main`→`git push deploy main` 순서다. 배포용 공개 미러 main을 Streamlit Cloud가 사용하므로 앱 로그/배포 SHA까지 확인한다. 소스 배포 후 기존 책·활동, TEST chunk 생성/수정/검색, 재접속 유지, 선택 txt export의 ISBN/읽은 시간/sourceApp, 소프트 삭제, 기존 기능 회귀, anon Data API 차단을 M1에서 검사한다. export는 승인된 격리 로컬 경로이며 iCloud 2차 export 제외. 현재는 계획만 확정했다.
- **판정/남은 일**: 기술 검증 PASS이나 main 반영 준비 NO/운영 배포 준비 NO. 공동 CROSS의 main `b2d9112`와 최신 별도 브랜치 `bf9ca9a` 모두 최신 상태가 운영 미적용/접속 전 중단으로 남아, 읽담 `bd04762` 및 운영 실측과 불일치한다. 사용자 지정 Source of Truth 충돌 기준에 따라 임의 해소하지 않고 기록한다. 다음 작업1개는 공동 현재 상태 정합화다. 이번 변경은 이 기록과 HANDOFF만 로컬 커밋하며 main/push/배포는 하지 않는다.

## 2026-09-27 — Codex: Reading Chunk 운영 migration 적용·즉시 보안 검증

- **목적/승인 범위**: 검증 후보 `4362e8c`와 승인 plan SHA `166d02b0682da839a0caae3ad096fdf3b854974db3e4075c47fff6be846b5961`의 신규 `reading_chunks` migration만 운영 Supabase에 적용한다. 실제 chunk CRUD·앱 배포·main/push·기존 표 권한·default ACL·iCloud·1차-B는 금지했다.
- **백업 관문**: libpq18.6 `pg_dump` custom-format으로 운영 `public` schema/data/ACL을 `/private/tmp/readdam-prod-backup-dag4jwb6/public-before-reading-chunks.dump`에 mode0600으로 저장했다(922,421 bytes, SHA-256 `1e601cd1acd4e6b394766e027cbafeae4f2b6659e8fa9bdf30898381e8dff0be`). `pg_restore --list` 94항목, schema 추출, data payload 전체 해제 및 books/activities/profile·chunk 부재를 확인했다. 별도 DB restore rehearsal은 미실행이다.
- **실행 직전**: 문서화된 운영 프로젝트·transaction pooler6543·SSL·DB postgres·schema public·current/session postgres·PG17.6 확인. chunk 객체 없음, books705, activities5667, owner NULL0, 기존 schema SHA `4f6b9306…1e6189`; 계획9DDL 및 승인 SHA가 재현됐다.
- **적용**: `tools/schema_maintenance.py --configured-postgres --apply --approve-plan <승인SHA>`만 사용했다. table1→index3→RLS→PUBLIC/anon/authenticated/service_role REVOKE의 9DDL과 구조·보안 post-check가 하나의 transaction에서 exit0으로 commit됐다.
- **독립 post-check**: 구조계약 `reading-chunks-1a.v1` OK, 표 owner postgres·행0, 명명 index3+PK/UNIQUE 자동 index2 모두 valid/ready. PK/FK/UNIQUE/CHECK 4제약 validated/nondeferrable. RLS=true, policy0. 외부4주체 SELECT/INSERT/UPDATE/DELETE=false, postgres 4권한=true. 적용 후 maintenance 계획은 statement0 no-op이다.
- **기존 상태 보존**: books705, activities5667, 양쪽 owner NULL0. chunk 객체를 제외한 기존 public relation/column/constraint/index/ACL fingerprint가 적용 전 `4f6b930680c82b0fc8d8cfd51e457d5dac7c997aa0c0f8be838184e92a1e6189`와 동일하다.
- **코드/배포/남은 일**: 전체157 PASS 재확인. migration 결과 문서만 작업 브랜치에 로컬 기록하며 main/push/deploy 없음. 다음은 별도 승인된 제품 main 반영·배포 준비이며, 그 전 실제 사용자 CRUD/Safari/iCloud/1차-B는 진행하지 않는다.

## 2026-09-27 — Codex: Reading Chunk 운영 migration 최종 dry-run

- **목적/범위**: 비공개 기본 migration 후보 `4362e8c`를 실제 운영 설정으로 읽기 전용 계획만 산출한다. `--apply`·DDL·DML·main/push/deploy·화면/iCloud 작업은 금지했다.
- **대상/연결**: 앱과 같은 `SUPABASE_DB_*` 단일 설정을 사용했다. 문서화된 운영 Supabase 프로젝트 일치, transaction pooler6543, sslmode=require, DB=`postgres`, schema=`public`, current/session user=`postgres`, PostgreSQL17.6, `transaction_read_only=on`을 확인했다. DSN·host·password·key는 출력/복사하지 않았다.
- **계획**: preflight=`MISSING_TABLE`, applicable=true. CREATE TABLE1, CREATE INDEX3, ENABLE RLS1, `PUBLIC`/`anon`/`authenticated`/`service_role` REVOKE4의 정확한9DDL·예상 밖 SQL0. 실행 순서는 table→book/owner/duplicate index→RLS→4role REVOKE. plan SHA=`166d02b0682da839a0caae3ad096fdf3b854974db3e4075c47fff6be846b5961`.
- **불변 검증**: 독립 read-only 연결2회와 실제 maintenance CLI 기본모드의 계획/SHA가 동일했다. 전후 chunk 관련 객체0, books705, activities5667, 두 표 owner NULL0, public 전체 relation/column/constraint/index metadata fingerprint `4f6b930680c82b0fc8d8cfd51e457d5dac7c997aa0c0f8be838184e92a1e6189` 동일. 운영 변경0건.
- **후보 일치/검증**: 현재 migration 파일과 `4362e8c` blob SHA-256이 모두 `5c059a3a…d622c`; 제품·테스트 diff0. 9DDL 순서 테스트 1 PASS. 기존 전체157 PASS는 후보 구현 시 결과이며 이번 dry-run에서 제품 코드는 변경하지 않았다.
- **커밋/배포/남은 일**: dry-run 결과는 HANDOFF/WORKLOG만 로컬 기록. main 반영·push·deploy 없음. 실제 적용 준비 판단은 YES이나, 백업/복원·maintenance 창·별도 실행 승인이 남았다. 다음은 David의 별도 승인 후 실제 적용 직전 plan SHA 재확인이다.

## 2026-09-27 — Codex: Reading Chunk 비공개 기본 migration 재설계

- **목적/범위**: 운영 read-only 프리플라이트로 확인한 `postgres` 앱 주체와 default ACL/Data API 노출 위험을 반영해 신규 `reading_chunks`만 생성 즉시 비공개로 만든다. 운영 DB 적용, 기존 표·default ACL·Supabase role 정책·배포·iCloud는 변경하지 않는다.
- **구현**: PostgreSQL 계획을 표1/index3 CREATE 뒤 RLS 활성화와 `PUBLIC`/`anon`/`authenticated`/`service_role`별 `REVOKE ALL PRIVILEGES`까지 총9문장으로 확장했다. 기존 `database.transaction()` 안에서 구조 post-check 후 ACL/RLS/policy/app-role post-check를 수행한다. 외부4주체의 SELECT/INSERT/UPDATE/DELETE가 모두 false, policy0, RLS on, owner/current/session=`postgres`, postgres CRUD 모두 true가 아니면 fail-closed로 rollback한다. SQLite의 기존4CREATE 경로와 전역 default ACL은 건드리지 않았다.
- **TDD/검증**: 신규 pytest3개를 먼저 실패 확인(4문장, post-check 부재) 후 구현했다. 전체 **157 passed**. PostgreSQL17 WASM에서 위험한 default ACL을 합성해 중간 DDL 실패 및 service_role REVOKE 누락의 전체 rollback, 정상9DDL 뒤 외부권한 false/RLS on/policy0/postgres CRUD true, 예상 밖 policy 감지, 반복 no-op, 기존14표 checksum 불변을 확인했다. 기존 PostgreSQL Reading Chunk CRUD/export 회귀도 PASS했다.
- **컴파일/품질**: Python compile, Node audit script syntax, `git diff --check` 최종 PASS. 비밀정보·운영 연결 사용 없음. `reading_chunks`에는 serial/identity가 없어 sequence 권한 정책이 필요하지 않다.
- **커밋/배포**: 제품·테스트 `4362e8c`, 브랜치 `codex/reading-chunks-private-default`. main/origin/deploy 반영·push·운영 migration 없음. 원본 dirty 작업트리의 사용자 문서2개는 수정하지 않았다.
- **남은 일/위험**: 실제 psycopg/PgBouncer/Supabase 환경과 backup/maintenance 창은 별도 승인 후 확인한다. 기존 public 표의 넓은 ACL/RLS는 이번 후보가 변경하지 않는다. 다음은 운영 적용이 아니라 동일 대상의 dry-run 9문장·plan SHA를 재검토하는 일이다. 1차-A 운영 미완료/1차-B 보류.

## 2026-09-27 — Codex: 1차-A 서버 전용 DB 접근정책 코드 감사·중단

- **목적**: 신규 `reading_chunks`를 Data API 직접 노출 없이 운영할 수 있는지, 특히 `anon`/`authenticated` REVOKE와 앱 CRUD의 양립 가능성을 판단한다.
- **제공된 운영 결과**: 사용자 read-only 조회상 books705/activities5,667, NULL-owner0, chunk 표/index 없음, `books.id text PK`, 기존 public RLS off/policy0, anon 기존 표 광범위 GRANT, `pg_default_acl` 신규 relation 기본 GRANT 가능. 이번 세션에서 운영 DB 재조회 없음.
- **코드 감사**: `app.py` → `lib/db.get_connection` → `lib/database.database_url_from_env` → psycopg; chunk UI/서비스는 이 SQL 연결을 받는다. export CLI도 동일 DSN의 read-only psycopg 연결. `lib/auth.py`의 anon 키는 Auth용이고 `lib/storage.py`의 service-role 키는 사진 Storage용이다. chunk Data API 호출은 검색되지 않았다. 실제 Postgres username은 환경의 URL 또는 `SUPABASE_DB_USER`로 결정되어 코드만으로 확인 불가. Secrets/.env 값은 읽지 않았다.
- **판정/발견 문제**: 요청의 중단 기준에 따라 서버 전용 ACL/RLS 정책을 확정하지 않았다. CREATE4문장만으로는 자동 기본 GRANT 노출 위험이 있다. 두 role만 REVOKE해도 PUBLIC/역할 상속 권한이 남을 수 있다. 현 maintenance CLI는 CREATE4문장만 단일 transaction에 넣으므로 REVOKE 포함 migration의 실행 수단이 아니다. 조건부 SQL은 기존 계획 문서에만 제시했다.
- **변경·검증**: 기존 migration 계획/HANDOFF/PROJECT와 이 WORKLOG만 갱신. 정적 코드 추적과 PostgreSQL/Supabase/Streamlit 공식 문서 대조, diff 검사. 제품 테스트는 코드 무변경이라 재실행하지 않음. 운영 SQL/DDL/DML·배포·환경변수·기존 표 권한 변경0.
- **브랜치/커밋/남은 일**: `codex/reading-chunks-1a-fixes` 문서 전용 로컬 커밋, main/push/deploy 없음. 실제 앱 `current_user`/`session_user`, migration role의 기본 ACL, 상속/PUBLIC 포함 effective privilege, Data API exposed schema, 서버 role의 새 표 CRUD 근거를 비밀값 없이 확인해야 한다. 승인 전 운영 NO-GO, 1차-A 미완료/1차-B 금지. 공동 결정 변경은 없어 상위 CROSS는 보존했다.

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
