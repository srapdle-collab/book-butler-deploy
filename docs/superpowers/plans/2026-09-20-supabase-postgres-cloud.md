# Supabase Postgres 및 클라우드 배포 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로컬 SQLite와 사진 파일에 있던 읽담 데이터를 Supabase Postgres·비공개 Storage로 옮기고 Streamlit Community Cloud에서 지속적으로 기록할 수 있게 한다.

**Architecture:** 앱은 `BOOK_BUTLER_DATABASE_URL`이 있으면 psycopg 기반 Postgres 연결을, 없으면 현재 SQLite 연결을 사용한다. 공통 SQL 실행·트랜잭션 도우미가 자리표시자와 행 잠금을 감추고, Postgres에는 UUID와 별도의 단조 증가 `position`을 저장해 SQLite `rowid` 정렬 의미를 보존한다. 사진은 비공개 `book-photos` 버킷에 원래 경로로 저장하고 서버에서 짧은 만료의 서명 URL을 발급한다.

**Tech Stack:** Python 3.9, Streamlit, psycopg 3, Supabase Storage REST API, SQLite (개발·기존 테스트), PostgreSQL 15+.

**Spec:** `docs/WORKLOG.md` 2026-09-20 “Claude: 클라우드 배포용 Supabase 인프라 준비 (인계)” 및 사용자 요청.

## Global Constraints

- activity kind 숫자(0~7), UUID, 기존 본문·사진 참조를 보존한다.
- 앱에는 개인 키를 넣지 않고 `.env`와 Streamlit Cloud secrets만 사용한다.
- SQLite 테스트와 로컬 사진 동작을 계속 지원한다.
- 현재 사용자 기획문서의 미커밋 변경·사본은 수정하거나 커밋하지 않는다.
- Postgres 이관은 `--apply`를 명시했을 때만 쓰기 작업을 한다.

---

### Task 1: DB 호환 계층과 Postgres 스키마

**Files:**
- Create: `lib/database.py`
- Modify: `lib/db.py`, `lib/schema.py`, `requirements.txt`
- Test: `tests/test_postgres_compat.py`

**Interfaces:**
- Produces `is_postgres(conn)`, `execute(conn, sql, params=())`, `read_frame(conn, sql, params=())`, `transaction(conn, lock_reading=False)`, `lock_rows(conn, query, params=())`.
- `get_connection()` selects Postgres when `BOOK_BUTLER_DATABASE_URL` exists, otherwise SQLite.

- [ ] **Step 1: Write failing tests** for qmark→`%s` conversion, Postgres selection from env, and schema DDL containing `activities.position` plus the partial active-session unique index.
- [ ] **Step 2: Run** `pytest tests/test_postgres_compat.py -v`; expect import/API failure.
- [ ] **Step 3: Implement** the minimum dialect helpers and idempotent Postgres schema creation. SQLite keeps its current schema and obtains `position` by `rowid` in query helpers.
- [ ] **Step 4: Run** the focused test and then `pytest -q`; expect all green.
- [ ] **Step 5: Commit** only compatibility files and tests.

### Task 2: Transactional reading and record operations

**Files:**
- Modify: `lib/db.py`, `lib/reading.py`, `lib/records.py`, `lib/record_ui.py`, `lib/notebook_ui.py`, `lib/sharing.py`, `lib/sharing_ui.py`
- Test: `tests/test_postgres_compat.py`, existing `tests/test_reading.py`, `tests/test_records.py`

**Interfaces:**
- `transaction(..., lock_reading=True)` takes a Postgres transaction-scoped advisory lock for the single active timer and uses SQLite immediate transactions locally.
- `lock_rows()` appends `FOR UPDATE` only for Postgres.

- [ ] **Step 1: Write failing tests** asserting Postgres query helpers use `position`, deletion effect uses `ON CONFLICT`, and timer/record mutations invoke the locking transaction helper.
- [ ] **Step 2: Run** focused tests; expect failure because SQLite-only statements remain.
- [ ] **Step 3: Implement** row locking for sessions, activity and book rows; preserve the partial unique active-session constraint; replace `rowid` ordering with `position`; replace `INSERT OR REPLACE` with portable upsert.
- [ ] **Step 4: Run** focused and all app tests; expect all green.
- [ ] **Step 5: Commit** only the transactional migration and tests.

### Task 3: Supabase Storage adapter and photo migration

**Files:**
- Create: `lib/storage.py`, `migration/migrate_to_supabase.py`
- Modify: `lib/db.py`, `lib/notebook_ui.py`, `requirements.txt`
- Test: `tests/test_storage.py`, `tests/test_supabase_migration.py`

**Interfaces:**
- `storage.upload_photo(key, content, content_type)`, `storage.signed_url(key)`, `storage.photo_source(value)`.
- `migrate_to_supabase.py --apply --verify` creates the schema, uploads files idempotently, imports SQLite rows with preserved `position`, and checks counts/references.

- [ ] **Step 1: Write failing tests** for path normalization, private signed URL request construction, and migration row mapping including `position`.
- [ ] **Step 2: Run** focused tests; expect missing adapter/script failures.
- [ ] **Step 3: Implement** Storage REST calls with service-role server credentials, SQLite export/Postgres upsert, `--apply` safety gate, and post-import count/photo-reference verification.
- [ ] **Step 4: Run** focused and full tests; expect all green.
- [ ] **Step 5: Commit** the adapter, script, dependencies, tests.

### Task 4: Live Supabase migration and Streamlit Cloud deployment

**Files:**
- Modify: `docs/WORKLOG.md`, `docs/PROJECT.md`

- [ ] **Step 1: Run** `python migration/migrate_to_supabase.py --apply --verify` with `.env` loaded; expect matching table counts and no missing photo object references.
- [ ] **Step 2: Set Streamlit Cloud secrets** from existing environment values without committing them; choose the existing private repository and main branch.
- [ ] **Step 3: Deploy**, wait for a healthy app, and create/read one non-destructive UI flow to confirm Postgres connectivity.
- [ ] **Step 4: Record** actual source/target counts, Storage upload results, deployment URL/state, and known limits in project documentation.
- [ ] **Step 5: Commit** documentation and push main to origin as required for deployment.
