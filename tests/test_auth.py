from __future__ import annotations


def test_auth_configuration_requires_supabase_url_and_anon_key(monkeypatch):
    from lib import auth

    monkeypatch.delenv('SUPABASE_URL', raising=False)
    monkeypatch.delenv('SUPABASE_ANON_KEY', raising=False)
    assert auth.is_configured() is False

    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    assert auth.is_configured() is False

    monkeypatch.setenv('SUPABASE_ANON_KEY', 'anon-key')
    assert auth.is_configured() is True


def test_user_from_payload_requires_id_and_email():
    from lib import auth

    user = auth.user_from_payload({'id': 'user-1', 'email': 'reader@example.com', 'user_metadata': {'display_name': '독자'}})
    assert user.id == 'user-1'
    assert user.email == 'reader@example.com'
    assert user.display_name == '독자'
