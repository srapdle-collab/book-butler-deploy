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
