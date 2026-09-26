# Reading Chunk 1차-A 배포·복구 runbook (미승인/미실행)

2026-09-27 / Codex. 감사: [READING_CHUNK_PREDEPLOY_AUDIT.md](READING_CHUNK_PREDEPLOY_AUDIT.md).

후속 로컬 수정 `038ab2e`: [수정 결과·export 복구 계약](READING_CHUNK_BLOCKER_FIXES.md)을 먼저 읽는다. 수정 브랜치에서 export의 init/전체 조각 처리는 제거됐으며 owner/ID 선택, atomic index/journal 복구를 사용한다. 아래 감사 당시 CLI 위험/복구 항목은 구 코드에 대한 기록이다. **앱 일반 연결의31DDL과 schema drift/운영 권한 검증은 여전히 미해결**이므로 현재 NO-GO는 유지한다. 새 CLI 역시 이번에는 운영에 실행하지 않았다.

**현재 NO-GO. 이 문서의 운영 명령은 실행하지 않았다. 사용자 승인과 감사 blocker 해소 전에는 실행 금지다.**
현재 제품 main/origin=`4d97f4e`, rollback 기준=`51e5b0c72deb0afe69767da05028dea95dd688d1`.
신규 감사 브랜치는 테스트/문서만 포함하며 제품 수정은 없다.

## 1. 운영 metadata를 안전하게 읽는 방법

앱/CLI/get_connection을 사용하지 않는다. 이미 승인된 DB client에서 **raw PostgreSQL 연결 → BEGIN READ ONLY → catalog SELECT → ROLLBACK**만 수행한다. 접속정보는 화면/명령줄/로그에 출력하지 않는다. 새 role·GRANT·Secret 생성은 별도 승인 사항이다.
현재 세션에는 제어 가능한 브라우저/Supabase connector/psql이 없고, 비밀파일을 읽는 행위도 금지되어 있어 운영에서 실행하지 않았다. 방법 자체는 합성 PostgreSQL에서 metadata SELECT 성공 및 CREATE 거절(25006)을 확인했다.

아래는 실행 제안이다. 연결 대상 확인 후 DB role과 search_path를 먼저 확인하고, transaction_read_only가 on이 아니면 즉시 ROLLBACK/중단한다. pg_catalog 함수만 쓰고 사용자 정의 함수/뷰를 호출하지 않는다.

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '5s';
SET LOCAL lock_timeout = '1s';
SHOW transaction_read_only;
SELECT current_database(), current_user, current_schema(),
       current_setting('search_path'), current_setting('server_version');
SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user;

SELECT n.nspname, c.relname, c.relkind, c.relrowsecurity, c.relforcerowsecurity,
       c.relacl, pg_get_userbyid(c.relowner) AS owner
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
  AND c.relname IN ('books','activities','reading_chunks','reading_sessions','checkin_reactions');

SELECT table_schema,table_name,column_name,data_type,is_nullable,column_default,
       character_maximum_length,ordinal_position
FROM information_schema.columns
WHERE table_name IN ('books','activities','reading_chunks','reading_sessions','checkin_reactions')
ORDER BY table_schema,table_name,ordinal_position;

SELECT n.nspname,c.relname,k.conname,k.contype,k.convalidated,pg_get_constraintdef(k.oid)
FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE c.relname IN ('books','activities','reading_chunks','reading_sessions','checkin_reactions')
ORDER BY n.nspname,c.relname,k.conname;

SELECT n.nspname,t.relname AS table_name,i.relname AS index_name,
       x.indisvalid,x.indisready,x.indisunique,pg_get_indexdef(i.oid)
FROM pg_index x JOIN pg_class i ON i.oid=x.indexrelid
JOIN pg_class t ON t.oid=x.indrelid JOIN pg_namespace n ON n.oid=t.relnamespace
WHERE t.relname IN ('books','activities','reading_chunks','reading_sessions','checkin_reactions')
ORDER BY n.nspname,t.relname,i.relname;

SELECT schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check
FROM pg_policies WHERE tablename IN ('books','activities','reading_chunks');
SELECT defaclrole::regrole,defaclnamespace::regnamespace,defaclobjtype,defaclacl
FROM pg_default_acl;
SELECT n.nspname,c.relname,t.tgname,t.tgisinternal,pg_get_triggerdef(t.oid)
FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE c.relname IN ('books','activities','reading_chunks');
SELECT evtname,evtevent,evtenabled FROM pg_event_trigger;
ROLLBACK;
```

조회/출력 범위는 metadata뿐이다. information_schema의 빈 결과만으로 표 부재를 확정하지 않는다(권한에 따라 비노출). 실제 schema가 public인지, role이 소유자/우회 권한인지, Data API 노출/default grants/RLS 정책을 함께 대조한다. 필요한 권한이 없으면 확대하지 말고 중단한다. 운영 사용자 행의 count/checksum/NULL-owner 존재 조회는 별도 승인된 무결성 검증 단계에서 수행한다.

## 2. 필요한 DB 구조와 변경 계획

기존 books.id TEXT PK와 스냅샷용 title/author/isbn/owner_id가 필요하다. 신규 표는 아래22컬럼이다. UUID/date/ISO시간/JSON배열은 전용 DB 타입이 아니라 TEXT다. 날짜/쪽수/시간 범위·contentTypes 목록·본문 최소 조건은 앱 검증이며 DB CHECK로 모두 보장되지 않는다.

**운영 metadata를 읽지 않았으므로 변경 필요 여부는 아직 확정되지 않았다.** 표/제약/index가 이미 정확히 있으면 변경0. 부분/불일치라면 수정 SQL을 새로 승인받는다. IF NOT EXISTS로 덮고 진행하지 않는다.

### 변경 T: reading_chunks 신규 표 (없음이 확인된 경우에만)

- 목적: 기존 books/activities와 분리된 신규 조각 보관.
- 기존 데이터 영향: 행 복사/UPDATE/DELETE 없음. books FK 관계·catalog가 추가되고 잠금 가능. 기본 권한/노출 schema에 따라 보안 영향 가능.
- 위험: 중~높음(권한/RLS 미확정). 정책 없는 public 노출은 허용하지 않으며 현재 역할의 행 접근 경계가 검증되지 않으면 STOP.
- 사전 확인: 표 부재, schema/search_path, books.id 타입/유일성, 승인된 DB role/ACL/RLS·event trigger, backup/lock_timeout, 앱 DDL 비활성화/분리 대책.
- rollback: transaction commit 전 ROLLBACK. commit 후에는 표/데이터를 보존하고 앱만 rollback하는 것이 기본. 표 삭제는 별도 데이터 보존·의존성 검토와 명시 승인 필요.

다음은 현 코드와 동등한 **검토용 SQL**이다. public schema가 확인됐다고 가정한 표기이며 정책 미승인 상태에서는 실행 불가다. 런타임 현재 코드에는 schema 접두사가 없어 search_path 확인이 특히 중요하다.

```sql
CREATE TABLE public.reading_chunks (
    chunk_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    book_id TEXT REFERENCES public.books(id),
    book_title TEXT NOT NULL,
    author TEXT,
    isbn TEXT,
    source_app TEXT NOT NULL CHECK(source_app IN ('readdam','today-library')),
    source_ref TEXT UNIQUE,
    read_date TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    position_note TEXT,
    minutes INTEGER,
    original_text TEXT,
    user_note TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    illustration_tags TEXT NOT NULL DEFAULT '[]',
    content_types TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);
```

### 변경 I1~I3: 신규 표의 조회 인덱스 (정확히 없는 것만)

| 변경 | 목적/정확한 정의 | 데이터 영향/위험 | 사전 확인/rollback |
| --- | --- | --- | --- |
| I1 | `CREATE INDEX idx_reading_chunks_book ON public.reading_chunks(book_id,deleted_at,read_date DESC);` | 사용자 행 변경 없음. 표 쓰기 잠금·디스크/I/O, 빈 표에서는 낮음 | 같은 이름/정의/index validity 확인. transaction 내 실패 ROLLBACK; 확정 후 제거는 별도 승인 |
| I2 | `CREATE INDEX idx_reading_chunks_owner ON public.reading_chunks(owner_id,deleted_at,updated_at DESC);` | 동일. 이것만으로 사용자 분리 보장 안 됨 | 동일 + owner 필터 실제 쿼리 확인 |
| I3 | `CREATE INDEX idx_reading_chunks_duplicate ON public.reading_chunks(owner_id,book_id,read_date,page_start,page_end,content_hash);` | 동일. **unique 아님**, 의미 중복은 허용될 수 있음 | NULL 비교·동시 저장 검증. 동일 rollback |

PK와 source_ref UNIQUE의 자동 index2개까지 총5개가 필요하다. 별도 기존 컬럼/테이블 ALTER, RLS 변경, migration of activities는 이 변경 계획에 포함하지 않는다.

### 적용 방식의 필수 조건

1. 승인된 T/I1/I2/I3만 명시 transaction으로 실행하고 commit 전 metadata 확인. 각 명령은 사전에 선택된 대상이어야 한다.
2. 이미 전체 객체가 있으면 migration을 skip한다. 일부만 있거나 다르면 현 상태를 기록하고 STOP, 자동 repair 금지.
3. 현재 app/CLI의31문장 자동 init을 배포 migration으로 사용하지 않는다. 연결과 초기화를 분리하는 제품 수정/재테스트가 필요하다. 현 코드를 그대로 두면 사전 생성 후에도 기존 ALTER/CREATE를 다시 시도하므로 안전 문제가 해결되지 않는다.
4. RLS/ACL 정책을 임의 생성하지 않는다. 새 표의 노출·계정 분리 모델을 승인받고, 그 구현이 새 표에만 한정되는지 재감사한다.
5. PgBouncer·실제 psycopg NULL 바인딩·운영 버전 동등 staging에서 확인한다. PGlite는 이 검증을 대체하지 않는다.

## 3. Failure-mode 분석

| 상황 | 사용자 증상 | 데이터 위험 | 중단·복구/예방 |
| --- | --- | --- | --- |
| 앱 배포 성공, migration 실패 | 로그인 후 오류/책장 진입 불가 | 일부 새 객체 잔존, 이전 ALTER 적용 가능 | 즉시 새 배포 중지. committed 객체 inventory 확인, 앱 rollback. 자동 재시작 반복 금지 |
| migration 성공, 앱 배포 실패 | 구 화면 유지/앱 기동 오류 | 추가 표는 보존 가능 | 구 버전 유지·재배포, DB drop 불필요. 합성 구 init 호환 PASS |
| migration 중간 실패 | index/column 오류 | autocommit이면 앞선 명령 확정 | 명시 transaction이면 ROLLBACK. 현 init 경로는 수동 inventory부터 시작 |
| 앱 시작 직후 crash | 빈 화면/예외 | DDL 또는 owner claim은 이미 확정됐을 수 있음 | 로그/DB 상태 확인, 다시 시작 전 원인 규명. 읽기 화면도 무변경이라 추정 금지 |
| 새 코드 + 구 schema | 조각 조회/입력 실패, 기존 노트 렌더 중단 | 요청 실패·부분 초기화 | schema preflight/feature gate/명시 migration 필요 |
| 구 코드 + 새 schema | chunk가 보이지 않음, 기존 기능은 통상 유지 | 새 chunk 데이터 자체는 잔존 | additive 표 보존. 합성에서 구 init 후 checksum 확인 |
| 앱 rollback 후 DB만 새 schema | 이전과 동일 | 뒤에 들어온 chunk를 지우면 손실 | old app 유지, 새 표 보존, 재배포 때 재사용 |
| export 도중 종료 | 일부 txt 갱신/이동, index는 옛 상태 | 미등록 파일·덮어쓰기/재시도 차단 | exporter 중지, 파일/index 함께 snapshot. 원자성/journal 수정 전 자동 재시도 금지 |
| index 작성 중 실패 | header만 있는 index/오래된 경로 | index 소실, 이후 안전한 재export 어려움 | 검증된 일관된 세트로 복구하거나 새 격리 root로 재생성 후 비교. 기존 파일 삭제 금지 |
| 동시 export/iCloud 충돌 | 충돌 사본/뒤섞인 index | 마지막 write가 상대 세션 결과 덮음 | 단일 writer·잠금·원자 교체·기기간 동기화 확인 필요 |
| 잘못된 소유권/권한 | 타 사용자 조각 조회/수정 가능성 | 개인정보/무결성 위험 | release blocker. actor 검증+실제 role/정책 시험 후에만 GO |

## 4. Rollback runbook — 실행 금지, 승인 후 사용

### DB

- 스키마 생성 전 backup 시점 고정: 사용자 쓰기 정지/검증 창 확보 후 consistent DB dump와 schema/ACL, 기존14표의 PK 기준 행 비교/해시를 보호된 위치에 보관한다. 단순 row count만으로 무변경을 판정하지 않는다.
- example: `pg_dump --dbname=service=readdam_prod --format=custom --file=/APPROVED_PRIVATE_BACKUP/readam-pre-1a.dump`. service와 보호 경로는 사용자가 승인·설정해야 하며 현재 존재한다고 가정하지 않는다. 비밀번호 URL/명령줄 사용 금지. 실제 backup은 이번에 하지 않았다.
- `pg_restore --list /APPROVED_PRIVATE_BACKUP/readam-pre-1a.dump`로 구성 확인 후, **별도 빈 테스트 DB**에 복원 훈련한다. 운영 DB로 `--clean`/전체 덮어쓰기 restore 금지.
- 새4문장의 미commit transaction 실패는 ROLLBACK. autocommit 실패는 이미 확정된 객체를 metadata로 비교하고 app만 rollback한다.
- 기본은 **DB down migration 없음**. reading_chunks와 신규 index를 남겨 데이터 보존. 구 코드 호환을 검증했다. 누락된 기존 owner/emoji가 자동 추가된 경우 함부로 drop하지 않는다.
- 예상치 못한 기존 행 변경은 즉시 모든 검증 중단. 원인/변경 PK/backup/동시 사용자 작업을 비교한 별도 복구 계획 승인 전 DML 복구하지 않는다.

### 앱/배포 미러

강제 push/reset을 쓰지 않고 새 rollback commit으로 `51e5b0c`의 tracked tree를 복원한다. 다음은 **미실행 예시**이며 당시 deploy tip과 선형 이력을 다시 확인해야 한다. 다르면 STOP.

```bash
git fetch deploy
git log --graph --oneline 51e5b0c..deploy/main
git rev-list --merges 51e5b0c..deploy/main
# merge commit이 있으면 아래 자동 범위 revert를 쓰지 말고 별도 검토.
# 현재 deploy가 이미 51e5b0c면 rollback할 변경이 없으므로 종료.

# /tmp/readdam-rollback-approved 가 없는지 먼저 확인. 기존 worktree 재사용 금지.
git worktree add -b codex/rollback-reading-chunks /tmp/readdam-rollback-approved deploy/main
cd /tmp/readdam-rollback-approved
git status --porcelain
# 비어 있을 때만 진행
git revert --no-commit 51e5b0c..HEAD
# 충돌이면 STOP. 사용자 작업을 덮어쓰지 않음.
git diff --cached --check
git diff --cached --exit-code 51e5b0c -- .
# staged tree가 복구 대상과 완전히 같아야 함
git commit -m 'revert: restore pre-reading-chunk production tree'
# 격리된 기존 테스트/빌드·비밀정보 검사 후 별도 배포 승인 하에:
git push deploy HEAD:refs/heads/main
```

마지막 push는 Streamlit 배포를 일으킨다. 이번에는 금지다. remote가 움직였으면 non-fast-forward를 강제로 우회하지 않는다. 배포 완료 UI·로그·실제 실행 commit을 확인해야 하며 Git SHA만으로 복구 성공을 선언하지 않는다. rollback된 구 앱도 기존 DDL/owner claim이 있으므로 그 영향도 먼저 확인해야 한다.

### 파일/index

- exporter를 멈추고 불일치 상태를 그대로 보존한다. 기존 txt만 복원하거나 index만 과거로 덮지 않는다.
- 승인된 backup의 파일·index 일관된 세트를 대조하거나, read-only exporter가 수정된 뒤 별도 빈 복구 root에 재생성해 ID/경로/hash를 비교한다.
- 원래 폴더로 교체/이동/삭제는 사용자 승인 후 한 건씩 대상 확정. iCloud 전체 restore/동기화 재설정 금지.
- 이전 합성 txt/index와 신규 `_읽담_검증전용_20260927_16680d12`는 현재 보존한다. 운영 자료가 아니며 이번 감사에서 cleanup하지 않는다.

## 5. Production deployment checklist — 현재 첫 단계 STOP

| 순서 | 수행할 일 | GO | STOP |
| --- | --- | --- | --- |
| 0. 승인 | 코드 수정·DB migration·배포·1건 데이터·export·cleanup 권한을 각각 확정 | 범위/대상/시간 명확 | 포괄 승인 추정, 운영 변경 미승인 |
| 1. 코드 preflight | 감사11항목 해결/판정, 신규 테스트와 PG 통합·UI·diff 검사 | 안전 실패0, 원본 파일 보호, 배포 SHA 고정 | xfail를 성공으로 셈, NULL/owner/파일 덮어쓰기 문제 잔존 |
| 2. metadata | raw READ ONLY로 표/컬럼/제약/index/ACL/RLS/role/trigger 확인 | 정확한 기대 상태·최소 권한 | 드리프트, 새 권한 필요, 불명확한 RLS |
| 3. baseline/backup | 쓰기 검증 창·일관된14표 backup/hash·복원 훈련 | 복구 증거·보호 위치 확보 | backup 실패/운영 데이터 출력·무단 변경 |
| 4. migration | 승인된 T/I만 transaction·명시 timeout | 신규22컬럼/5index·제약 확인, 기존 구조/행 불변 | 기존 표 ALTER 필요·부분 적용·잠금·오류 |
| 5. deploy | clean source→정확한 SHA 테스트 후 origin/deploy | 명시 배포 승인·runtime init 분리 | 사용자 미커밋 포함·예상외 diff |
| 6. smoke | 앱 로딩/Auth·책장·기존 상세·기록/통계/타이머 표시 | 오류없음·기존 데이터 불변 | init 반복오류·owner claim 변화·소그룹 implicit write |
| 7. UI 생성 | 기존 책1권에 TEST chunk1개만 작성 | 원문/메모 TEST 표시·모든 필드 | 책 제목/기존 activity 수정, 2번째 chunk 생성 |
| 8. 수정/필터 | 같은 chunk 수정·태그 정상/없는 태그 비교 | 동일 ID·DB 반영·올바른 필터 | 다른 owner/book 변경·특수문자 실패 |
| 9. DB 확인 | read-only로 TEST ID·owner·book·ISBN·분·source 확인 | expected row1·user 데이터 불변 | NULL 소유자·예상 밖 행/권한 |
| 10. export | 읽기 전용/ID限定 exporter로 확정 루트에 작성 | TEST1파일만, ISBN/분/readdam·본문 정확 | current CLI 전체 export/DDL, 기존 파일 경로 충돌 |
| 11. 재export/index | 동일데이터·내용수정 재실행·index 대조 | 파일1개 유지·index1행/경로/hash 일치 | 새 중복·기존 행 삭제·부분 index |
| 12. delete | 화면 TEST 삭제 확인 후 deleted_at 검증 | active조회0·물리행1+tombstone | 물리 DELETE 필요·기존 자료 영향 |
| 13. 무결성/회귀 | baseline14표 PK/내용/시간/metadata/관계 대조 | 승인된 TEST 외 변경0, 기존 기능 정상 | 설명 안 되는 차이1건 이상 |
| 14. 정리·DoD | 승인된 테스트 산출물만 보존/정리 결정, 문서·commit·원격·runtime 기록 | 모든DoD PASS·사용자 최종 확인 | 운영미검증/미해결결함 남음 |
| 15. 다음 단계 | 1차-B 별도 승인 검토 | 1차-A 완료 후 별도 승인 | 지금은 항상 STOP |

## 6. 사용자 수동 화면 체크리스트 (미배포 상태에서 실행하지 않음)

Chrome/Safari가 설치돼 있으나 이 세션 CUA 연결은 없다. 자동화 우회·권한변경을 하지 않았다. 로컬 AppTest는 실제 브라우저/Cloud 검증을 대체하지 않는다.

| 순서/클릭 | 정상 | 즉시 중단 조건 |
| --- | --- | --- |
| 승인된 배포 후 운영 URL → 로그인 | 책장과 기존 권수·기록 표시 | 오류, 권한없는 서재 표시, DDL/owner 변경 감지 |
| 기존 책1권 → 상세 | 기존 표지/진도/독서노트 + 읽은 조각 섹션 | 기존 노트 사라짐, KeyError/SQL 오류 |
| `✦ 읽은 조각 남기기` | 날짜·쪽/위치·분·원문·메모·두 종류 태그·콘텐츠타입 | 필드/기존 책 변경 요청 |
| 원문/메모에 `[TEST 운영검증 전용]`, 한글 태그, 분 입력 → `조각 저장` | 카드1개, 새 ID1개 | 중복 카드/SQL 오류/책 진도·통계 변화 |
| `수정` → TEST 메모·시간·태그 변경 → `수정 저장` | 같은 카드·같은 ID 갱신 | 저장 후 조작 불가·에러/새 행 생성 |
| `조각 태그 필터` → 있는태그/없는태그/승인된 특수태그 | 해당 카드만/0개, 일치 기준 정확 | 관련없는 카드·타 사용자 자료 |
| 같은 세션에서 삭제 버튼 직전까지 이동 | 렌더/버튼 상태 정상 | AppTest와 같은 widget 오류 |
| 별도 승인된 Mac export 실행 후 파일 확인 | 지정 독서조각/YYYY/YYYY-MM 아래 txt, metadata·index 일치 | 화면에 export 버튼이 있다고 가정하지 말 것; 현재 CLI 수정 전 실행 금지 |
| 동일 ID 재export | 중복파일0·내용변경시 같은 대상 갱신 | 번호증가/다른 파일 덮어씀/index불일치 |
| 카드 `삭제` → `삭제 확인` | 카드 사라짐; DB deleted_at만 기록 | 기존 activity/책 소실·물리삭제 |
| 책장/기존 노트/통계/스트릭/타이머 표시 재확인 | 승인된 TEST 외 동일 | 값 변화·DB 기존행 차이 |

soft delete 후 DB 물리행은 남는 것이 정상이다. 사용자 수동 확인도 현재 운영 쓰기 금지를 우회하는 허가는 아니다. 운영 export·삭제분 파일정리·소그룹 표시로 인한 profile 쓰기는 각각 별도 안전범위 확인이 필요하다.
