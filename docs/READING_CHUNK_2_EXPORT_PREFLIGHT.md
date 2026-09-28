# Reading Chunk 2차 — 실제 export 전 읽기 전용 프리플라이트

## 최신 — 증거 보존형 실제 iCloud dry-run 재검증 PASS (2026-09-28, Codex)

- 비교 범위는 실제 예화창고 루트 이하 **736항목 전체**다. symlink를 따라가지 않고 각 항목의 상대경로·종류(file/directory/other)·size·mtime_ns를 핵심값으로 메모리에 보존하여 항목별 diff를 계산했다. ctime_ns·inode·birthtime은 진단값으로 분리했다. 개인 파일 본문을 읽거나 파일명 원본을 로그/문서에 기록하지 않았다. 임시 스냅샷 파일도 만들지 않았다.
- exporter 미실행 baseline A→8초→B: 핵심 차이 **0항목/0필드**, 진단값 차이 0. B→첫 PRE 역시 차이 0. 기존 승인 로컬 환경을 통해 owner 활성 Chunk 1건을 확인했고, 앱 `get_readonly_connection()`의 PostgreSQL `transaction_read_only=on`을 확인했다. owner/비밀값/본문은 출력하지 않았다.
- 첫 dry-run PRE→POST: 736항목, 핵심 차이 **0항목/0필드**, 진단값 차이 0. 계획은 CREATE 0 / UPDATE 0 / DELETE 0 / SKIP 1 / UNMAPPED 0 / CONFLICT 0, 다중 복사·dedupe 0. `읽담/` 경로·manifest·pending·lock 신규 생성 0. 첫 POST→두 번째 PRE도 차이 0.
- 둘째 dry-run PRE→POST: 736항목, 핵심 차이 **0항목/0필드**, 진단값 차이 0. 첫 실행과 action/summary가 동일하다. 새 관리 경로·manifest 0. 두 실행 모두 DB read-only, iCloud 파일 쓰기 경로 미실행. **실제 iCloud dry-run 안전성 PASS**. 이전 Boolean 불일치의 원인은 여전히 불명이며 이번 PASS가 그 원인을 소급해 설명하지는 않는다.
- **실제 export 실행 준비는 현재 NO.** 활성 Chunk의 `illustrationTags`가 비어 있어 생성할 카테고리 사본이 0건이고, 1차-A `.export-state.json`도 없다. 실제 export 분기는 사본이 없어도 빈 2차 manifest/pending과 index 기록을 쓸 수 있으므로, dry-run의 CREATE 0을 실제 실행의 무변경으로 해석하지 않는다. 이번에는 실제 export·백업·파일/DB write를 하지 않았다.

### 실제 export 실행계획 — 실행하지 않음

1. 별도 실제 쓰기 승인과 대상 Chunk/카테고리 생성 필요성을 확인한다. 실행 직전 DB read-only, 실제 루트/기존 카테고리, 활성 태그, 1차-A txt·`_index.csv`·`.export-state.json`의 소유/무결성, 2차 manifest·pending 상태를 재확인한다. 충돌·불일치·새 정책 필요 시 중단한다.
2. 기존 사람 파일 및 archive/index의 실행 전 상태를 iCloud 밖 안전한 위치에 백업하고 항목별 경로·종류·size·mtime 스냅샷을 보존한다. 백업/복구 권한과 위치는 실제 실행 전에 확정한다. 읽담 소유로 입증되지 않은 파일은 복구·정리 대상에서도 건드리지 않는다.
3. 동일 조건의 dry-run으로 CREATE/UPDATE/DELETE/CONFLICT와 상대경로를 재검토한다. 계획된 경로가 모두 기존 카테고리 `읽담/` 내부이고, 충돌·예상 밖 수정/삭제가 0일 때만 별도 승인된 실제 exporter를 한 번 실행한다. 최초 2차 manifest는 exporter의 소유 검증/원자적 기록 경로로만 생성한다.
4. 생성된 읽담 소유 파일 수·manifest와 index의 경로 일치·사람 파일 불변·새 최상위 카테고리 0을 확인한다. 그 뒤 같은 입력으로 두 번째 **실제** 실행을 하려면 별도 승인을 받고 중복 생성 0을 확인한다. 태그 변경·soft delete는 운영 Chunk를 변조하지 않고 합성 fixture 회귀 결과를 사용한다.
5. DB write, 소유권 불명, 사람 파일 변화, 새 카테고리, 예상 밖 UPDATE/DELETE, manifest/index 불일치, 잠금/복구 오류가 보이면 즉시 중단한다. 실제 쓰기 뒤 장애라면 보존한 백업과 exporter pending/manifest를 대조해 읽담 소유 파일만 복구하고 임의 재실행하지 않는다.

## 최신 — dry-run 전후 스냅샷 차이 진단: D, 원인 특정 불가 (2026-09-28, Codex)

- 당시 pre/post 스냅샷의 **원본과 항목별 diff는 보존되지 않았다**. 실행 기록에는 `before==after_first: False`만 있다. 비교 범위는 최상위·`독서조각/` 이름 목록, 기존 카테고리의 `읽담/` 존재 목록, `독서조각/` 추적 파일의 size·mtime_ns였다. 따라서 바뀐 항목 수·경로·필드 및 내용 hash 변화는 사후 특정할 수 없다. 본문을 읽지 않았고 pre/post 내용 hash도 없다.
- exporter `export(..., dry_run=True)`는 DB read-only 선택 뒤 `_plan()` 결과를 반환한다. 잠금 파일 `open(a+b)`, 디렉터리 생성, export/manifest/pending 쓰기·교체·삭제는 모두 그 반환 뒤의 실제 실행 분기다. `_plan()`의 경로 나열·stat·기존 index/상태 읽기는 read-only이며 당시 manifest와 매핑 태그가 없어 관리 파일 내용 읽기도 없었다. 코드상 dry-run의 파일 write 경로는 없다.
- exporter를 실행하지 않고 동일 범위를 순수 `iterdir`/`is_dir`/`exists`/`stat`으로 8초 간격 두 번 관찰한 결과 최상위 82개, archive 2개, 관리 폴더 0개, 추적 파일 1개의 비교값이 모두 동일했다. 원래 차이는 이 관찰에서 재현되지 않았다. 현재 `_index.csv` ctime은 당시 실행 시간대와 가깝지만 **원래 비교에는 ctime이 없었고 이전 ctime도 보존되지 않았다**. 이 사실만으로 iCloud/File Provider 또는 exporter를 원인으로 지목할 수 없다. 같은 시간대의 읽기 전용 통합 로그 조회에서도 해당 경로 이벤트 근거는 발견되지 않았다.
- **판정 D — 원인 특정 불가.** exporter 자체 write 가능성은 코드에서 배제되지만 외부 metadata 변화(A)나 스냅샷 방식의 오탐(B)을 입증할 원본 diff가 없다. 실제 export **NO-GO 유지**. 이번 진단에서 dry-run·DB 조회·파일 내용 조회·iCloud write·제품 코드 변경은 하지 않았다. 후속 재검증에는 항목별 상대경로·종류·size·mtime_ns를 개별 보존하고, ctime/inode/생성시각 등 변동성 metadata는 진단용으로 분리해 비교해야 한다. 재검증은 별도 승인된 실행에서만 한다.

## 최신 — 운영 Chunk 기반 실제 예화창고 dry-run, 안전성 NO-GO (2026-09-28, Codex)

- David가 기존 읽담 프로젝트 로컬 `.env`의 **운영 DB 읽기 전용 연결 용도**를 승인했다. 기존 앱 우선순위에 따라 PostgreSQL pooler 설정을 내부적으로 로드했다. 비밀값·DSN·이메일·DB role 이름은 출력·문서화하지 않았다. `db.get_readonly_connection()`에서 PostgreSQL `transaction_read_only=on`, 현재/세션 주체 동일, Reading Chunk·profiles 접근을 확인했다. 기존 owner 이메일 설정으로 profiles에서 **유일한 한 계정**을 내부 식별했고 해당 계정의 책 존재도 확인했다. DB DDL/DML 0건.
- 소유자의 Reading Chunk **총 2건 = 활성 1건 + soft deleted 1건**. 활성 1건의 `illustrationTags`는 비어 있다. 매핑 가능 0건, 미매핑 태그 보유 0건, 다중 카테고리 대상 0건이다. soft deleted 조각의 본문·태그는 보고하지 않았고 실제 dry-run 선택에서도 제외했다.
- 실제 예화창고를 대상으로 활성 1건만 exporter의 `dry_run=True`로 한 번 계산했다. 계획은 **CREATE 0 / UPDATE 0 / DELETE 0 / SKIP 1(예화 태그 없음) / UNMAPPED 0 / CONFLICT 0**, 다중 복사 0·동일 카테고리 dedupe 0이다. 기록·manifest가 없는 기존 파일을 소유로 추정하지 않았고 변경 대상 경로가 없다. exporter의 파일 쓰기 경로는 호출되지 않았으며 새 관리 폴더·manifest·pending 파일은 생기지 않았다.
- **안전성 감사 NO-GO:** 실행 전후 실제 iCloud 루트/`독서조각`의 이름·추적 파일 metadata 스냅샷이 같지 않았다. 별도 정적 metadata 조회 두 번은 안정적이었지만 첫 dry-run 때 차이가 난 원인은 특정하지 못했다. 파일 본문은 읽지 않고, 다운로드/외부 동기화/다른 요인을 추정해 무변경이라고 단정하지 않는다. 사용자 파일을 생성·수정·삭제하는 exporter 연산은 0건이나 **실제 파일시스템 무변경을 입증하지 못했다**. 따라서 두 번째 dry-run은 수행하지 않았고 실제 export 실행계획도 확정하지 않는다.
- 재개 조건은 메타데이터 차이의 원인을 읽기 전용으로 규명하고, 동일 범위의 dry-run 전후에 파일시스템 상태가 변하지 않음을 확인하는 것이다. 그 뒤에만 두 번째 결정론적 dry-run 및 실행계획 작성 여부를 판단한다. 실제 iCloud export는 계속 금지한다. 아래 Phase 3 미실행 기록은 이번 승인 전 상태다.

2026-09-28 · Codex · **Phase 1 완료, Phase 2 읽기 전용 완료, Phase 3 진입 차단. 실제 iCloud 변경 0건.**

## Phase 1 — 로컬 구현

격리 브랜치 `codex/reading-chunks-1b`의 `tools/export_chunk_illustrations.py`가 승인된 정확 일치·명시 매핑·모호 태그 미분류·카테고리별 파생 복사와 같은 카테고리 중복 제거를 구현한다. `독서조각/` 1차-A 소유 상태와 별도 manifest의 경로·digest·identity를 맞춘 뒤에만 생성/수정/정리한다. 미소유 파일은 이름이 같아도 `CONFLICT`다. dry-run은 DB/파일에 쓰지 않는다. 검증: 신규 17건, 읽담 전체 186건, compile, diff check; 임시 fixture CLI dry-run→실제 export→동일 재실행 PASS. 실제 DB/예화창고에 쓴 내용은 없다.

## Phase 2 — 실제 예화창고 구조, 읽기 전용

- 기존 주제 카테고리 **63개**. 별도 보존된 `_읽담_검증전용_…` 루트 1개는 카테고리가 아니며 exporter에서 제외했다. `독서조각/`은 별도 archive다.
- NFC 기준 동일 이름 충돌 0건, 카테고리 symlink 0건, 기존 카테고리의 `읽담/` 폴더 0건. 승인된 명시 매핑 대상 5개는 모두 실제 기존 폴더가 한 개씩 존재한다. 디스크의 실제 Unicode 이름은 그대로 경로에 사용한다. 모호 태그 중 `교회`·`사명`은 정확 일치 폴더가 있어도 미분류로 유지한다.
- 현 `독서조각/`에는 `_index.csv`가 있으나 `.export-state.json`, `_illustration_manifest.json`, `.illustration-pending.json`, `_예화창고_태그매핑.csv`는 없다. `_index.csv`의 존재만으로 실제 Chunk에 대한 1차-A 소유·무결성을 추정할 수 없다. 사람 파일의 본문은 읽지 않았다. 개별 Chunk 파일명 충돌 검사는 DB 행 접근 전이므로 미확인이다.

## Phase 3·4 — 실제 Chunk dry-run 및 안전성 감사

**미실행 / NO-GO.** 현재 실행 환경에 읽담 운영 DB용 `BOOK_BUTLER_DATABASE_URL` 또는 `SUPABASE_DB_*` 읽기 연결이 없고, 로컬 원본 SQLite에는 `reading_chunks` 표가 없다. 이 환경의 기존 도구에도 읽담 운영 DB 조회 경로가 없다. 따라서 실제 Chunk·소유자 ID를 확인할 수 없으며, 실제 예화창고를 대상으로 Chunk별 계획/집계를 계산하지 않았다. 실제 DB·iCloud 쓰기는 0건이다.

재개하려면 David가 **비밀값을 채팅/문서에 노출하지 않는 기존 승인된 읽기 전용 운영 DB 경로와 소유자 식별 방법**을 제공해야 한다. 그 뒤 실제 Chunk 전체를 read-only로 선택해 `--dry-run`을 실행한다. 첫 실제 manifest가 없으므로 기존 파일은 전부 미소유로 취급하고 이름 충돌은 `CONFLICT`다. `CONFLICT`, 예상 밖 대량 `UPDATE`/`DELETE`, 1차-A 소유 상태 누락이 있으면 실제 export 후보는 NO-GO다. dry-run 출력은 건수와 필요한 축약 식별자만 인계하고 본문은 기록하지 않는다. 같은 dry-run을 다시 수행해 계획이 안정적인지도 확인한다.

## Phase 5 — 실제 export 실행계획

Phase 3·4가 PASS하기 전에는 확정하지 않는다. 실제 export·백업·첫 manifest 생성·2회 실행·태그 변경·soft delete·rollback은 현재 실행하거나 승인된 상태가 아니다. 다음 한 작업은 읽담 운영 Chunk에 접근할 수 있는 **기존 읽기 전용 경로 확보**다.
