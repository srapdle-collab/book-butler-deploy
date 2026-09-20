from types import SimpleNamespace


def test_object_keys_keep_covers_and_record_photos_separate():
    from lib import storage

    assert storage.object_key('cover.jpg', kind='cover') == 'covers/cover.jpg'
    assert storage.object_key('photos/record.png', kind='photo') == 'photos/record.png'
    assert storage.object_key('../unsafe.jpeg', kind='photo') == 'photos/unsafe.jpeg'


def test_private_signed_url_uses_server_credentials(monkeypatch):
    from lib import storage
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return SimpleNamespace(status_code=200, json=lambda: {'signedURL': '/object/sign/book-photos/photos/a.jpg?token=x'}, raise_for_status=lambda: None)

    monkeypatch.setenv('SUPABASE_URL', 'https://project.supabase.co')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'service-secret')
    monkeypatch.setattr(storage.requests, 'request', fake_request)

    url = storage.signed_url('photos/a.jpg', expires_in=120)

    assert url == 'https://project.supabase.co/storage/v1/object/sign/book-photos/photos/a.jpg?token=x'
    method, endpoint, kwargs = calls[0]
    assert method == 'POST'
    assert endpoint.endswith('/storage/v1/object/sign/book-photos/photos/a.jpg')
    assert kwargs['json'] == {'expiresIn': 120}
    assert kwargs['headers']['Authorization'] == 'Bearer service-secret'
