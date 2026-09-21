# 읽담 소그룹 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 계정별 개인 서재 보호와 소그룹 인증·피드·좋아요·댓글을 추가한다.

**Architecture:** Streamlit은 Supabase Auth 토큰을 세션에 저장하고, 새 `lib/auth.py`와 `lib/groups.py`가 인증된 사용자 ID를 검증한다. 개인 책과 활동에는 소유자를 추가하고, 그룹에는 별도 인증 스냅샷을 저장해 개인 원본 기록을 피드로 노출하지 않는다.

**Tech Stack:** Streamlit, Supabase Auth Python client, Supabase Postgres, psycopg, pytest, Streamlit AppTest.

**Spec:** `docs/superpowers/specs/2026-09-21-small-groups-design.md`

## Global Constraints

- 기존 705권·활동은 `READDAM_OWNER_EMAIL`의 첫 로그인 계정만 소유할 수 있다.
- 개인 서재/활동은 `owner_id = current_user_id`로 조회·수정한다.
- 그룹 피드에는 인증에 선택한 스냅샷만 저장하고 원본 개인 활동을 노출하지 않는다.
- Git에는 이메일·토큰·비밀번호·DB·사진을 넣지 않는다.
- 활동 kind 숫자 체계는 변경하지 않는다.

---

### Task 1: 인증 어댑터와 로그인 관문

**Files:**
- Create: `lib/auth.py`
- Modify: `app.py`, `requirements.txt`
- Test: `tests/test_auth.py`, `tests/test_access.py`

**Interfaces:**
- Produces `AuthUser(id: str, email: str, display_name: str | None)`, `is_configured()`, `sign_up(email, password)`, `sign_in(email, password)`, `current_user(access_token)`, `sign_out()`.
- `require_authenticated_user()` returns `AuthUser` or stops Streamlit rendering.

- [ ] **Step 1: Write failing tests**

```python
def test_auth_user_requires_configured_anon_key(monkeypatch):
    monkeypatch.delenv('SUPABASE_ANON_KEY', raising=False)
    assert auth.is_configured() is False


def test_auth_gate_hides_navigation_without_user(isolated_app, monkeypatch):
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'test-key')
    at = AppTest.from_file(APP_PATH).run()
    assert at.text_input(key='login_email').label == '이메일'
    assert not any(button.label == '책장' for button in at.button)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth.py tests/test_access.py::test_auth_gate_hides_navigation_without_user -v`

Expected: FAIL because `lib.auth` and login widgets do not exist.

- [ ] **Step 3: Implement the minimum adapter and gate**

```python
@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str
    display_name: str | None = None


def require_authenticated_user() -> AuthUser:
    user = st.session_state.get('auth_user')
    if user:
        return user
    render_auth_form()
    st.stop()
```

Use `supabase.create_client(url, anon_key)` only inside `lib/auth.py`. Store the access token in `st.session_state`, validate it with `auth.get_user(token)`, and provide sign-up, sign-in, sign-out UI with no secret values in messages.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_auth.py tests/test_access.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/auth.py app.py requirements.txt tests/test_auth.py tests/test_access.py
git commit -m "feat: add Supabase Auth gate"
```

### Task 2: 소유권 스키마와 기존 서재 일회성 귀속

**Files:**
- Modify: `lib/schema.py`, `lib/db.py`, `lib/database.py`
- Create: `lib/ownership.py`
- Test: `tests/test_ownership.py`, `tests/test_postgres_compat.py`

**Interfaces:**
- Produces `claim_legacy_library(conn, user: AuthUser, owner_email: str) -> bool` and `require_library_owner(conn, user_id: str) -> None`.
- `list_books`, `get_book`, `list_activities`, activity mutations accept `user_id` and filter on owner ID.

- [ ] **Step 1: Write failing tests**

```python
def test_claim_legacy_library_assigns_only_configured_email(conn):
    assert ownership.claim_legacy_library(conn, user('u1', 'owner@example.com'), 'owner@example.com')
    assert db.get_book(conn, BOOK_ID, user_id='u1') is not None
    assert db.get_book(conn, BOOK_ID, user_id='u2') is None


def test_non_owner_cannot_read_or_write_legacy_book(conn):
    with pytest.raises(PermissionError):
        db.update_book_status(conn, BOOK_ID, '완독', user_id='u2')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ownership.py -v`

Expected: FAIL because owner columns and functions do not exist.

- [ ] **Step 3: Implement the minimum schema and filters**

Add nullable `owner_id TEXT` to SQLite and `UUID` to Postgres books/activities. Backfill activity owners from their book owner during claim. Make every personal query filter by `books.owner_id` or `activities.owner_id`; use a permission exception for attempted cross-owner mutation.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ownership.py tests/test_postgres_compat.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/schema.py lib/db.py lib/database.py lib/ownership.py tests/test_ownership.py tests/test_postgres_compat.py
git commit -m "feat: scope library records to owners"
```

### Task 3: 그룹·초대·인증 도메인 서비스

**Files:**
- Create: `lib/groups.py`
- Modify: `lib/schema.py`
- Test: `tests/test_groups.py`

**Interfaces:**
- Produces `create_group(conn, user_id, name)`, `invite_url(group_id, token)`, `join_from_invite(conn, user_id, token)`, `save_checkin(conn, group_id, user_id, checked_on, note, attachment)`, `today_feed(conn, group_id, user_id, checked_on)`.
- `AttachmentSnapshot(kind, body, book_title, page, photo)` is the only attachment structure persisted in a check-in.

- [ ] **Step 1: Write failing tests**

```python
def test_invite_joins_once_and_cannot_be_reused(conn):
    group = groups.create_group(conn, 'owner', '새벽 독서')
    token = groups.create_invite(conn, group['id'], 'owner')['token']
    assert groups.join_from_invite(conn, 'member', token)['joined'] is True
    assert groups.join_from_invite(conn, 'other', token)['joined'] is False


def test_checkin_is_unique_per_member_group_and_korean_date(conn):
    groups.save_checkin(conn, GROUP_ID, 'member', date(2026, 9, 21), True, '읽었습니다', None)
    updated = groups.save_checkin(conn, GROUP_ID, 'member', date(2026, 9, 21), True, '다시 기록', None)
    assert groups.today_feed(conn, GROUP_ID, 'member', date(2026, 9, 21))[0]['note'] == '다시 기록'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_groups.py -v`

Expected: FAIL because group tables and service do not exist.

- [ ] **Step 3: Implement the minimum schema and service**

Create profiles, groups, members, one-time invites, daily check-ins with a `(group_id, user_id, checked_on)` unique index. Use `secrets.token_urlsafe(32)` for invite tokens, check membership before each read/write, and enforce the note length limits in the service.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_groups.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/groups.py lib/schema.py tests/test_groups.py
git commit -m "feat: add groups invites and daily checkins"
```

### Task 4: 선택 첨부·좋아요·댓글 도메인 서비스

**Files:**
- Modify: `lib/groups.py`, `lib/db.py`, `lib/storage.py`
- Test: `tests/test_groups.py`, `tests/test_storage.py`

**Interfaces:**
- Produces `attachment_candidates(conn, user_id)`, `toggle_reaction(conn, checkin_id, user_id)`, `add_comment(conn, checkin_id, user_id, body)`, `list_comments(conn, checkin_id, user_id)`.

- [ ] **Step 1: Write failing tests**

```python
def test_attachment_candidate_must_be_owned_quote_or_photo(conn):
    assert groups.attachment_candidates(conn, 'owner')
    assert groups.attachment_candidates(conn, 'member') == []


def test_like_toggles_and_comment_is_visible_only_to_members(conn):
    assert groups.toggle_reaction(conn, CHECKIN_ID, 'member')['liked'] is True
    assert groups.toggle_reaction(conn, CHECKIN_ID, 'member')['liked'] is False
    groups.add_comment(conn, CHECKIN_ID, 'member', '좋은 문장입니다')
    assert groups.list_comments(conn, CHECKIN_ID, 'owner')[0]['body'] == '좋은 문장입니다'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_groups.py::test_attachment_candidate_must_be_owned_quote_or_photo tests/test_groups.py::test_like_toggles_and_comment_is_visible_only_to_members -v`

Expected: FAIL because attachment, reaction, and comment functions do not exist.

- [ ] **Step 3: Implement the minimum protected sharing behavior**

Only return kind 1, 2, or 0 activities owned by the current user. Copy selected fields into `AttachmentSnapshot`; build signed photo URLs only when rendering that snapshot. Add a unique reaction index and comment membership checks.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_groups.py tests/test_storage.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/groups.py lib/db.py lib/storage.py tests/test_groups.py tests/test_storage.py
git commit -m "feat: add checkin attachments reactions and comments"
```

### Task 5: 소그룹 Streamlit 화면과 내비게이션

**Files:**
- Create: `lib/groups_ui.py`
- Modify: `app.py`, `lib/theme.py`
- Test: `tests/test_groups_app.py`

**Interfaces:**
- Consumes `AuthUser`, group service interfaces, and `goto`.
- Produces `render_groups(conn, user, goto)`.

- [ ] **Step 1: Write failing AppTest cases**

```python
def test_member_can_create_group_and_sees_invite_link(authenticated_app):
    at = authenticated_app.run()
    at.button('소그룹').click().run()
    at.text_input(key='group_name').set_value('새벽 독서')
    at.button(key='create_group').click().run()
    assert any('초대 링크' in value for value in at.markdown)


def test_member_checkin_appears_in_todays_feed_and_accepts_like_comment(authenticated_group_app):
    at = authenticated_group_app.run()
    at.checkbox(key='checked_today').check()
    at.text_area(key='checkin_note').set_value('오늘 읽었습니다')
    at.button(key='save_checkin').click().run()
    assert any('오늘 읽었습니다' in value for value in at.markdown)
```

- [ ] **Step 2: Run AppTest cases to verify they fail**

Run: `pytest tests/test_groups_app.py -v`

Expected: FAIL because the 소그룹 navigation and widgets do not exist.

- [ ] **Step 3: Implement the minimum UI**

Add `소그룹` to the authenticated navigation. Render group creation, join-pending invite, a group selector, an editable today check-in form, optional attachment selector, time-sorted feed cards, like toggle, and comment form. Hide personal navigation for users who do not own the legacy library.

- [ ] **Step 4: Run AppTest cases to verify they pass**

Run: `pytest tests/test_groups_app.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/groups_ui.py app.py lib/theme.py tests/test_groups_app.py
git commit -m "feat: add small group Streamlit experience"
```

### Task 6: 전체 회귀·Supabase 검증·문서화

**Files:**
- Modify: `docs/PROJECT.md`, `docs/WORKLOG.md`, `README.md`
- Test: all tests

- [ ] **Step 1: Add configuration documentation test or assertion**

```python
def test_owner_email_is_not_committed():
    assert 'READDAM_OWNER_EMAIL=' not in Path('.env.example').read_text()
```

- [ ] **Step 2: Run full automated suite**

Run: `pytest -q`

Expected: all existing and new tests pass.

- [ ] **Step 3: Verify actual Postgres schema and a test group without altering legacy records**

Run: `python -m migration.verify_small_groups --schema-only`

Expected: new tables and indexes exist; no legacy book/activity owner is claimed until configured owner signs in.

- [ ] **Step 4: Record deployment requirements**

Document that Cloud Secrets needs `READDAM_OWNER_EMAIL`, the public app uses Auth instead of a shared password, and a validated private `main` must be manually mirrored with `git push deploy main`.

- [ ] **Step 5: Commit**

```bash
git add docs/PROJECT.md docs/WORKLOG.md README.md tests/test_auth.py
git commit -m "docs: document small group deployment"
```
