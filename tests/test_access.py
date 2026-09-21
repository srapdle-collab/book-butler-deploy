from streamlit.testing.v1 import AppTest

from test_activity_inputs_app import APP_PATH, isolated_app


def test_password_gate_hides_app_until_correct_password(isolated_app, monkeypatch):
    monkeypatch.setenv('BOOK_BUTLER_APP_PASSWORD', 'test-password')

    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not at.exception
    assert at.text_input(key='app_password').label == '비밀번호'
    assert not any(header.value == '📚 나의 책장' for header in at.header)

    at.text_input(key='app_password').set_value('wrong')
    at.button(key='unlock_app').click().run()
    assert any('비밀번호' in error.value for error in at.error)
    assert not any(header.value == '📚 나의 책장' for header in at.header)

    at.text_input(key='app_password').set_value('test-password')
    at.button(key='unlock_app').click().run()
    assert not at.exception
    assert any(header.value == '📚 나의 책장' for header in at.header)

    at.run()
    assert all(widget.key != 'app_password' for widget in at.text_input)


def test_auth_gate_hides_app_until_user_session(isolated_app, monkeypatch):
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'anon-key')
    monkeypatch.setenv('BOOK_BUTLER_APP_PASSWORD', 'legacy-password')

    at = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not at.exception
    assert at.text_input(key='login_email').label == '이메일'
    assert not any(button.label == '책장' for button in at.button)


def test_authenticated_owner_claims_library_and_sees_group_navigation(isolated_app, monkeypatch):
    from lib.auth import AuthUser

    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'anon-key')
    monkeypatch.setenv('READDAM_OWNER_EMAIL', 'owner@example.com')
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state['auth_user'] = AuthUser(id='owner-id', email='owner@example.com')
    at.run()

    assert not at.exception
    assert any(button.label == '책장' for button in at.button)
    assert any(button.label == '소그룹' for button in at.button)


def test_authenticated_user_can_create_group_and_save_daily_checkin(isolated_app, monkeypatch):
    from lib.auth import AuthUser

    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'anon-key')
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state['auth_user'] = AuthUser(id='member-id', email='member@example.com')
    at.run()
    next(button for button in at.button if button.label == '소그룹').click().run()
    assert not at.exception
    next(widget for widget in at.text_input if widget.label == '소그룹 이름').set_value('함께 읽기')
    next(button for button in at.button if button.label == '만들기').click().run()
    assert not at.exception
    note = next(widget for widget in at.text_area if widget.label == '한줄소감')
    note.set_value('오늘의 짧은 소감')
    next(button for button in at.button if button.label == '인증 저장').click().run()
    assert not at.exception
    assert any('오늘의 짧은 소감' in markdown.value for markdown in at.markdown)
