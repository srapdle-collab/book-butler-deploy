from __future__ import annotations

from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from test_activity_inputs_app import APP_PATH, isolated_app


def _response(user_id="user-a", access="access-a", refresh="refresh-a", expires_at=9999999999):
    user = SimpleNamespace(id=user_id, email=f"{user_id}@example.invalid", user_metadata={})
    session = SimpleNamespace(access_token=access, refresh_token=refresh, expires_at=expires_at)
    return SimpleNamespace(user=user, session=session)


def test_sign_in_keeps_refresh_token_and_never_keeps_password(monkeypatch):
    from lib import auth

    calls = []
    fake = SimpleNamespace(auth=SimpleNamespace(sign_in_with_password=lambda body: calls.append(body) or _response()))
    monkeypatch.setattr(auth, "_client", lambda: fake)
    session = auth.sign_in(" user-a@example.invalid ", "secret-password")
    assert calls == [{"email": "user-a@example.invalid", "password": "secret-password"}]
    assert session.user.id == "user-a"
    assert session.access_token == "access-a"
    assert session.refresh_token == "refresh-a"
    assert "secret-password" not in repr(session)


def test_refresh_rotates_token_and_rejects_invalid_response(monkeypatch):
    from lib import auth

    received = []
    fake = SimpleNamespace(auth=SimpleNamespace(refresh_session=lambda value: received.append(value) or _response(refresh="rotated")))
    monkeypatch.setattr(auth, "_client", lambda: fake)
    session = auth.refresh_session("old-refresh")
    assert received == ["old-refresh"]
    assert session.refresh_token == "rotated"
    fake.auth.refresh_session = lambda value: _response(refresh="")
    with pytest.raises(auth.AuthError):
        auth.refresh_session("old-refresh")


def test_sign_out_revokes_only_current_session(monkeypatch):
    from lib import auth

    calls = []
    fake = SimpleNamespace(auth=SimpleNamespace(
        set_session=lambda access, refresh: calls.append(("set", access, refresh)),
        sign_out=lambda options: calls.append(("out", options)),
    ))
    monkeypatch.setattr(auth, "_client", lambda: fake)
    auth.sign_out("access-a", "refresh-a")
    assert calls == [("set", "access-a", "refresh-a"), ("out", {"scope": "local"})]


def test_cookie_script_has_security_attributes_and_escapes_script_text():
    from lib import auth_cookie

    script = auth_cookie.cookie_script('</script><img src=x onerror=alert(1)>')
    assert "Secure" in script
    assert "SameSite=Strict" in script
    assert "Path=/" in script
    assert "Max-Age=2592000" in script
    assert "</script><img" not in script
    assert "password" not in script
    clear = auth_cookie.cookie_script(None)
    assert "Max-Age=0" in clear


def _configured(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.delenv("READDAM_OWNER_EMAIL", raising=False)


def test_login_restores_new_session_and_updates_rotated_cookie(isolated_app, monkeypatch):
    from lib import auth, auth_cookie

    _configured(monkeypatch)
    browser = {"cookie": ""}
    writes = []
    monkeypatch.setattr(auth_cookie, "read_refresh_cookie", lambda: browser["cookie"])
    def write(value):
        writes.append(value)
        browser["cookie"] = value or ""
    monkeypatch.setattr(auth_cookie, "write_refresh_cookie", write)
    monkeypatch.setattr(auth, "sign_in", lambda email, password: auth.AuthSession(
        auth.AuthUser("user-a", "user-a@example.invalid"), "access-a", "refresh-a", 9999999999
    ))
    monkeypatch.setattr(auth, "refresh_session", lambda token: auth.AuthSession(
        auth.AuthUser("user-a", "user-a@example.invalid"), "access-b", "rotated", 9999999999
    ))

    first = AppTest.from_file(APP_PATH).run()
    first.text_input(key="login_email").set_value("user-a@example.invalid")
    first.text_input(key="login_password").set_value("secret-password")
    first.button(key="sign_in").click().run()
    assert not first.exception
    assert writes[-1] == "refresh-a"
    assert first.session_state["auth_user"].id == "user-a"
    assert "secret-password" not in repr(first.session_state)

    second = AppTest.from_file(APP_PATH).run()
    assert not second.exception
    assert second.session_state["auth_user"].id == "user-a"
    assert writes[-1] == "rotated"
    assert all(widget.key != "login_password" for widget in second.text_input)


def test_active_session_refreshes_and_updates_cookie(isolated_app, monkeypatch):
    from lib import auth, auth_cookie

    _configured(monkeypatch)
    writes = []
    received = []
    monkeypatch.setattr(auth_cookie, "write_refresh_cookie", writes.append)
    monkeypatch.setattr(auth, "refresh_session", lambda token: received.append(token) or auth.AuthSession(
        auth.AuthUser("user-a", "user-a@example.invalid"), "access-new", "refresh-new", 9999999999
    ))
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = auth.AuthUser("user-a", "user-a@example.invalid")
    at.session_state["auth_access_token"] = "access-old"
    at.session_state["auth_refresh_token"] = "refresh-old"
    at.session_state["auth_refresh_at"] = 0
    at.run()
    assert not at.exception
    assert received == ["refresh-old"]
    assert at.session_state["auth_access_token"] == "access-new"
    assert writes == ["refresh-new"]


def test_refresh_cannot_switch_authenticated_user(isolated_app, monkeypatch):
    from lib import auth, auth_cookie

    _configured(monkeypatch)
    writes = []
    monkeypatch.setattr(auth_cookie, "write_refresh_cookie", writes.append)
    monkeypatch.setattr(auth, "refresh_session", lambda token: auth.AuthSession(
        auth.AuthUser("user-b", "user-b@example.invalid"), "access-b", "refresh-b", 9999999999
    ))
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = auth.AuthUser("user-a", "user-a@example.invalid")
    at.session_state["auth_access_token"] = "access-a"
    at.session_state["auth_refresh_token"] = "refresh-a"
    at.session_state["auth_refresh_at"] = 0
    at.run()
    assert not at.exception
    assert "auth_user" not in at.session_state
    assert at.text_input(key="login_email")
    assert writes == [None]


@pytest.mark.parametrize("invalid", ["expired", "forged"])
def test_invalid_cookie_is_removed_and_login_screen_returns(isolated_app, monkeypatch, invalid):
    from lib import auth, auth_cookie

    _configured(monkeypatch)
    writes = []
    monkeypatch.setattr(auth_cookie, "read_refresh_cookie", lambda: invalid)
    monkeypatch.setattr(auth_cookie, "write_refresh_cookie", writes.append)
    monkeypatch.setattr(auth, "refresh_session", lambda token: (_ for _ in ()).throw(auth.AuthError("invalid")))
    at = AppTest.from_file(APP_PATH).run()
    assert not at.exception
    assert at.text_input(key="login_email")
    assert writes == [None]


def test_logout_clears_cookie_and_session_then_revisit_needs_login(isolated_app, monkeypatch):
    from lib import auth, auth_cookie

    _configured(monkeypatch)
    browser = {"cookie": "refresh-a"}
    logout_calls = []
    monkeypatch.setattr(auth_cookie, "read_refresh_cookie", lambda: browser["cookie"])
    monkeypatch.setattr(auth_cookie, "write_refresh_cookie", lambda value: browser.update(cookie=value or ""))
    monkeypatch.setattr(auth, "refresh_session", lambda token: auth.AuthSession(
        auth.AuthUser("user-a", "user-a@example.invalid"), "access-a", "refresh-a", 9999999999
    ))
    monkeypatch.setattr(auth, "sign_out", lambda access, refresh: logout_calls.append((access, refresh)))
    at = AppTest.from_file(APP_PATH).run()
    at.button(key="auth_logout").click().run()
    assert not at.exception
    assert logout_calls == [("access-a", "refresh-a")]
    assert browser["cookie"] == ""
    assert "auth_user" not in at.session_state
    assert "auth_access_token" not in at.session_state
    assert at.text_input(key="login_email")
    revisit = AppTest.from_file(APP_PATH).run()
    assert revisit.text_input(key="login_email")


def test_logout_clears_local_credentials_when_revocation_fails(isolated_app, monkeypatch):
    from lib import auth, auth_cookie

    _configured(monkeypatch)
    writes = []
    monkeypatch.setattr(auth_cookie, "write_refresh_cookie", writes.append)
    monkeypatch.setattr(auth, "sign_out", lambda access, refresh: (_ for _ in ()).throw(auth.AuthError("offline")))
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = auth.AuthUser("user-a", "user-a@example.invalid")
    at.session_state["auth_access_token"] = "access-a"
    at.session_state["auth_refresh_token"] = "refresh-a"
    at.session_state["auth_refresh_at"] = 9999999999
    at.run()
    at.button(key="auth_logout").click().run()
    assert not at.exception
    assert "auth_user" not in at.session_state
    assert "auth_refresh_token" not in at.session_state
    assert writes == [None]


def test_existing_user_is_not_replaced_by_another_cookie(isolated_app, monkeypatch):
    from lib import auth_cookie
    from lib.auth import AuthUser

    _configured(monkeypatch)
    monkeypatch.setattr(auth_cookie, "read_refresh_cookie", lambda: "user-a-token")
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = AuthUser("user-b", "user-b@example.invalid")
    at.session_state["auth_refresh_token"] = "user-b-token"
    at.session_state["auth_refresh_at"] = 9999999999
    at.run()
    assert not at.exception
    assert at.session_state["auth_user"].id == "user-b"


def test_shelf_book_title_is_escaped_in_html(isolated_app):
    from lib import db

    conn = db.get_connection()
    try:
        conn.execute("UPDATE books SET title=? WHERE id=?", ('<img src=x onerror=alert(1)>', 'book-1'))
        conn.commit()
    finally:
        conn.close()
    at = AppTest.from_file(APP_PATH).run()
    html_values = [item.value for item in at.markdown if '<div class="shelf-cover-placeholder">' in item.value]
    assert html_values
    assert "&lt;img" in html_values[0]
    assert "<img src=x onerror" not in html_values[0]
