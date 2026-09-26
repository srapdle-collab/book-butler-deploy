# Reading Chunk 1차-A 운영 차단 결함 수정 결과

2026-09-27 / Codex / 사용자 확인 설정 Astra High. 제품·테스트 커밋 `038ab2e`.

후속 `5148d6f`: [schema-init 분리/preflight 결과](READING_CHUNK_SCHEMA_PREFLIGHT.md). 아래 당시 잔여 AUDIT-01은 **감지·안전중단 범위에서 PASS**, 자동 init은 수정 브랜치 일반 연결에서 제거됐다.154 PASS/0 XFAIL이며 운영권한/실사용 검증 대기로 NO-GO는 유지한다. 아래는038ab2e 시점의 기록이다.

**로컬 수정·격리 검증 완료. 운영 배포 판정은 NO-GO 유지.** 운영 Supabase 접속·쓰기·DDL, 배포, 환경 설정 변경, 실제 예화창고 접근, 오늘의 서재 수정, 1차-B 구현은 하지 않았다.
이 기록은 `6cdc7e7`의 [종합 감사](READING_CHUNK_PREDEPLOY_AUDIT.md)에 대한 후속이다. 과거 감사 결과를 삭제하거나 당시 통과로 바꾸지 않는다.

## 1. Git과 범위

- 읽담: `51e5b0c → aeecb7f → ae86be2 → cbcf0b4 → 54c0d23 → 431fe44 → 4d97f4e → 8843b56 → 6cdc7e7 → 038ab2e` ancestry 확인.
- main/origin/main은 로컬 ref 기준 `4d97f4e`, deploy/main은 `51e5b0c` 그대로다. 이번에는 fetch/push/배포하지 않았다. 원격 최신값을 재조회한 것으로 표현하지 않는다.
- 수정 브랜치 `codex/reading-chunks-1a-fixes`, worktree `/private/tmp/readdam-main-LIPAnD`. 감사 브랜치는 `6cdc7e7`에 보존. 원본 읽담 worktree `codex/reading-chunks-1a / cbcf0b4` 보존.
- 공동 기록 `f4bc698`은 동하비서 최상위 저장소 main의 커밋이다. 읽담 감사 커밋과 서로 다른 저장소임을 확인했고 cherry-pick하지 않았다. 공동 remote 미설정 유지.
- 제품 변경 6파일: `app.py`, `lib/db.py`, `lib/notebook_ui.py`, `lib/reading_chunks.py`, `lib/reading_chunks_ui.py`, `tools/export_chunks.py`.
- 테스트/시뮬레이션 8파일: `tests/test_reading_chunks.py`, `tests/test_reading_chunks_audit.py`, 신규 `tests/test_reading_chunks_security.py`, 신규 `tests/test_chunk_export_safety.py`, `tests/audit/icloud_stress.py`, `tests/audit/pg_simulation.mjs`, 신규 `tests/audit/pg_service_bridge.mjs`, 신규 `tests/audit/pg_service_check.py`.
- `lib/schema.py`, `lib/records.py`, `lib/reading.py`, `lib/ownership.py`, requirements 및 migration에는 변경이 없다. 기존 books/activities/통계 제품 동작을 변경하지 않았다.

## 2. 원인과 수정

| 항목 | 원인 | 수정·검증 |
| --- | --- | --- |
| AUDIT-08: 사용자/책 경계 | actor 없이 책에서 owner를 추론, ID만으로 조회·수정·삭제 | 인증된 actor를 app→상세→chunk로 전달. service의 owner 필수, book owner 대조, UPDATE의 ID+owner+book+active 조건. 다른 owner/book 및 삭제된 ID 재저장 거절. Postgres의 local-owner fallback 금지. SQLite의 owner NULL인 기존 로컬 책만 명시 local-owner 허용 |
| AUDIT-11: NULL 쪽수 | 독립 NULL 바인딩의 타입 추론 불가(42P18) | nullable 비교의 `CAST(? AS INTEGER)` 명시. NULL/NULL, NULL/값, 값/NULL, 값/값 모두 PostgreSQL 엔진에서 실제 쿼리 실행 |
| AUDIT-09: export 연결/범위 | 전체 init 연결과 전체 사용자·조각 조회를 재사용 | `get_readonly_connection` 신설. SQLite mode=ro/query_only/snapshot, PG read_only+REPEATABLE_READ/SHOW 확인. schema/init 호출 없음. owner/ID 선택 필수, 모든 ID 검증 후 파일 작업. 앱의 기존 일반 연결 init은 별도 잔여 위험 |
| AUDIT-06: 삭제 목적지 충돌 | 12자 fallback도 이미 존재하면 move가 덮어씀 | 존재 파일과 index 예약 경로를 모두 회피, 전체 ID+번호 확장. 신규 목적지는 atomic link의 no-clobber. 충돌 sentinel 불변 및 실제 이동 성공 검증 |
| AUDIT-05/10: 실패 복구/index | txt 먼저 직접 쓰고 index를 w로 truncate, 복구 근거 없음 | 동일 폴더 임시 파일→flush/fsync→atomic replace. 새 파일은 no-clobber link. durable journal→txt→integrity receipt→atomic index→옛 관리 경로 정리. 같은 owner/선택의 재호출만 복구 허용 |
| AUDIT-03/04: 목록/파일 무결성 | 중복 CSV를 dict로 축약, metadata만 보고 txt 손상 무시 | 헤더·행·ID/경로 중복 검증. txt byte SHA-256 영수증 비교, 수동 변경·미등록 파일·심볼릭 링크는 덮어쓰지 않고 중단 |
| AUDIT-02: 특수 태그 | JSON 문자열 LIKE의 wildcard/escape 의미가 태그 비교와 다름 | owner/book으로 제한한 결과의 JSON 배열에서 exact membership 비교. %, _, 인용부호, 역슬래시·한글 정상. 태그/예화 태그에 동일 기준 |
| AUDIT-07: 연속 화면 조작 | 저장 run에서 이미 그린 form 키 삭제·rerun으로 stale widget 잔존 | 버튼 callback은 저장 요청만 기록하고, 다음 render의 살아 있는 DB 연결로 widget 생성 전에 저장 처리. 새 세션 없이 수정→재수정→soft delete PASS |

actor 인자는 신뢰된 호출자가 넘겨야 한다. CLI `--owner-id`는 인증 토큰이 아니며 DB 자격증명 소유자에 대한 접근 통제가 아니다. 앱의 Auth 연결과 DB role/RLS/ACL 검증은 서로 다른 경계다. 이번에 RLS 정책을 만들거나 운영 정책이 안전하다고 판정하지 않았다.

## 3. Export 사용·복구 계약

승인된 환경에서만 사용하는 명령 형식(이번 운영 실행 없음):

```bash
python tools/export_chunks.py --output-root <승인된루트> --owner-id <검증된사용자ID> --chunk-id <선택한UUID>
# 여러 건은 --chunk-id 반복. 옵션 누락/빈 선택은 실패하며 전체 export로 대체하지 않는다.
```

- txt 경로와 `_index.csv`의 기존 5개 헤더는 유지한다. 선택하지 않은 index 행 및 `예화창고 경로들` 값을 보존한다.
- 관리 파일은 모두 `독서조각/` 안에만 둔다: `.export.lock`(같은 호스트 writer 배제), `.export-state.json`(owner/상대경로/실제 txt SHA-256), `.export-pending.json`(미완료 작업의 목표 내용/목록/복구 조건). 복구 journal에는 원문이 포함될 수 있으므로 txt와 같은 민감도로 보호한다. Git 추적/외부 업로드하지 않는다.
- 실패 시 기존 정상 index는 유지되거나 완성된 새 index로 교체된다. txt와 index를 하나의 OS transaction으로 교체하는 것은 아니다. 중간 불일치는 journal로 판별·roll-forward한다. **같은 owner와 정확히 같은 ID 집합, 같은 root로 재실행**한다. DB 최신 상태가 바뀌었으면 이전 작업 복구 후 새 snapshot을 반영한다.
- index/state/txt가 예상 SHA와 다르거나 잠금이 잡혀 있으면 중단한다. journal/index/state를 임의 삭제하거나 수동 편집해 우회하지 않는다. 다른 선택의 export는 기존 작업 복구 전 거절한다.
- 파일명 변경은 새 경로 작성과 index 교체가 성공한 뒤, hash가 확인된 옛 관리 파일만 정리한다. soft delete는 마지막 export 내용을 `_삭제됨/`으로 보존한다. DB 행은 물리 삭제하지 않는다.
- **구형 index만 있고 integrity receipt가 없는 기존 export**: txt가 현재 DB render와 byte 단위로 같을 때만 안전하게 등록한다. 이미 DB가 바뀌었거나 txt가 편집됐다면 소유/무결성을 추정해 덮어쓰지 않고 STOP한다. 별도 빈 검증 root로 생성해 비교하는 등 사용자 승인된 처리 계획이 필요하다. 실제 기존 iCloud 산출물에는 이 절차를 실행하지 않았다.
- filesystem은 macOS/POSIX의 동일 디렉터리 rename/link 및 fsync를 전제로 한다. 권한·link/fsync 미지원이면 우회 없이 실패한다. kill 시 임시 파일이 남을 수 있으나 index에 등록되거나 사용자 파일로 오인해 덮어쓰지 않는다. 재실행 복구 후 별도 확인 전 임시 산출물 정리를 하지 않는다.
- 로컬 flock은 다른 iCloud 기기의 exporter/동기화를 잠그지 못한다. 운영은 단일 export 기기/단일 writer 전제다. 수정판의 실제 iCloud 동작과 원격 동기화는 미검증이다.

구현 원리 확인: [psycopg 연결의 transaction 속성](https://www.psycopg.org/psycopg3/docs/api/connections.html), [Python 파일 교체 API](https://docs.python.org/3/library/os.html#os.replace). 이 문서상 보장과 실제 iCloud의 배포 검증을 혼동하지 않는다.

## 4. 검증 증거

- 전체 pytest **123 passed / 1 strict xfailed / 124 collected**, 21.34초. 기존 97개 대비 27개 추가. 감사 xfail 12개 중 11개 제거, 해소한 감사 31개는 `--runxfail -k 'not wrong_same_named_index'`로도 모두 통과했다.
- 남은 **AUDIT-01**: 같은 이름의 잘못된 index 정의를 `IF NOT EXISTS`가 감지/교정하지 않는다. 배포 preflight에서 정확한 columns/index/제약/validity 비교 전 STOP. 허용된 기대 실패이지 운영 GO 근거가 아니다. 자동 repair/schema 변경은 이번 범위 금지다.
- compile: app/lib/tools/tests의 Python 53개 구문 compile, Node 시뮬레이션/bridge syntax 검사 및 `git diff --check` PASS. 별도 프런트엔드 build 단계는 없는 Streamlit 앱이다.
- PostgreSQL17.5/PGlite0.4.6 기존 12시나리오 재실행. 정상 경로 9 PASS, 잘못된 index 재현 1, 부분 표 EXPECTED_STOP 1, 기존 owner claim 쓰기 경로 확인 1. NULL42P18은 더 이상 재현되지 않으며 오류를 삼키지 않고 assert한다. 기존14표(705책/5,666활동) checksum 불변.
- 신규 stdin bridge: 제품의 Python service를 그대로 PostgreSQL WASM에 연결해 NULL 중복, owner/book 거절, 정상 CRUD, 특수 태그, read-only DDL/DML 거절, 선택 export/재export/삭제 보관을 검증했다. 임시 14표의 행 checksum 전후 `df45c2608b1e2b45770bee7d0049fd9c4ca973b507336350ea2609a4a529c991` 일치. **실제 psycopg wire/PgBouncer/Supabase/RLS 통합 테스트는 아니다.** psycopg 연결 설정은 별도 mock으로 확인했다.
- SQLite 합성705/5,666 및 기존14표의 행·PK/FK·필드·시각·metadata checksum, init/재시작/구 init 호환 재검증 PASS. 추가 chunk CRUD/export도 기존 표 fingerprint 불변.
- export fault injection: 최초 생성·수정·경로 변경·삭제 중 index 실패 후 fresh module 복구, txt/state/index 각각 atomic replace 실패, index 성공 후 옛 경로 정리 실패, 같은 호스트 잠금, 신규 파일 race, 외부 txt 변경, 미완료 다른 선택 거절, 구형 index의 보수적 등록, 8/12자/전체ID 충돌과 symlink 거절 PASS. 사용자 파일 대신 임시 sentinel만 사용했다.
- 임시 로컬 root `/tmp/readdam-export-local-S5RtPY/_읽담_검증전용_20260927_9c12353d`에서 32 TEST/CLI8회. 최초32작성→동일3회0→내용1갱신→날짜/쪽수1이동+1작성→삭제1이동→최종0작성. 최종 txt32/index32행, ISBN/분/sourceApp/ID/hash 일치. **iCloud 실제 경로가 아니라 /tmp 테스트다.**
- 증거: `/tmp/readdam-fix-validation-gkS7kq/pytest.xml`, `pg-report.json`, 추출 SQL3개, `/tmp/readdam-export-audit-SXWQN8/report.json`. PGlite는 이전 /tmp 패키지 재사용, 누락된 psycopg Python 패키지는 /tmp 테스트 venv에만 설치했다. 제품 requirements/사용자 환경 설정은 변경하지 않았다.
- 중간 실패는 원인이 모두 확인됐다: 해소된 strict xfail의 XPASS→표식 제거, 테스트 venv의 psycopg 미설치→요구사항에 이미 있는 패키지 설치, fingerprint의 sqlite3.Row 직렬화→tuple 정규화, 기존 UI 키 오류→render 순서 수정. 미해명 실패 없음.

재현 명령(로컬 합성 환경만):

```bash
PYTHON_DOTENV_DISABLED=1 /tmp/readdam-chunk-test/bin/python -B -m pytest -q -p no:cacheprovider
node tests/audit/pg_simulation.mjs /tmp/readdam-pg-audit-EnKMvd/node_modules/@electric-sql/pglite/dist/index.js /tmp/NEW_APPROVED_SCRATCH/pg-report.json
PYTHON_DOTENV_DISABLED=1 /tmp/readdam-chunk-test/bin/python -B tests/audit/pg_service_check.py /tmp/readdam-pg-audit-EnKMvd/node_modules/@electric-sql/pglite/dist/index.js
```

## 5. 잔여 blocker와 다음 한 단계

1. **앱 runtime 자동 init은 그대로다.** `app.py → db.get_connection → ensure_schema`의31DDL, 기존 owner claim 경로를 export 수정으로 해결했다고 간주하지 않는다. 일반 연결의 init 분리/읽기 전용 schema preflight 방식을 별도 확정해야 한다. 기존 데이터·스키마를 임의로 수정하는 자동 우회는 불가하다.
2. 운영 metadata·RLS/ACL·role·backup/복구·실제 psycopg/PgBouncer·운영 화면·수정판 iCloud·운영1건 end-to-end 검증이 남았다. 현재 사용자의 운영 접근/배포 금지는 유지된다.
3. 구형 export에 receipt가 없고 DB/txt가 이미 다르면 자동 갱신 금지. 실제 archive 확인과 처리 계획에 별도 승인이 필요하다.
4. 동시 편집의 일반적인 version 충돌 정책이나 분산 iCloud 잠금은 구현하지 않았다. 삭제 부활은 막았지만 동시 동일 ID 신규 INSERT는 PK로 거절될 수 있으며, 서로 다른 ID의 의미 중복 동시 저장까지 직렬화하지 않는다. 로컬 단일 writer 검증과 구분한다.

**다음 한 단계:** 운영에 접속하기 전에, 앱의 기존 자동 init을 분리하고 schema drift를 읽기 전용으로 차단하는 로컬 수정 범위를 확정한다. 그 뒤 실제 DB metadata/권한 확인·배포는 각각 별도 승인과 runbook을 따른다. main 반영/push도 이번에는 하지 않았다. 1차-A 완료 처리와 1차-B 진입은 불가하다.

## 6. 보호한 사용자 작업

원본 읽담의 아래 두 파일은 수정·이동·stage·commit하지 않았고 작업 전후 SHA-256이 동일하다.

- `도서비서_기획문서.md`: `75fd87c2c10ed9ce9a8dd9627ca2075cc16a5354fb57698b921ea801ca1808e9`
- `도서비서_기획문서 2.md`: `515a448b3d245184697c1d69b6edf214757eb55e9d0f34fb7a3e9abaed6086bc`

공동 docs/PROJECT.md·WORKLOG.md는 다른 작업자의 미커밋 상태 그대로이며 전후 hash도 동일하다. 공동 CROSS만 별도 상태 기록 가능함을 확인했다. 실제 예화창고의 이전 합성 txt/index와 32건 테스트 폴더는 이번에는 읽거나 수정하지 않았으며 현재 해시를 재검증했다고 주장하지 않는다.
