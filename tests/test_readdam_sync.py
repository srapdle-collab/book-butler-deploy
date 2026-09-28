from __future__ import annotations

import requests

from lib import readdam_sync
from test_activity_inputs_app import isolated_app
from test_reading_chunks_ingest import owner_connection, payload


class Response:
    def __init__(self, status, body=None):
        self.status_code = status
        self.body = body

    def json(self):
        return self.body


class FakeHTTP:
    def __init__(self, chunks):
        self.chunks = chunks
        self.receipts = []
        self.books = None
        self.get_status = 200
        self.post_status = 200
        self.put_status = 200
        self.timeout_on_get = False
        self.lose_first_receipt = False

    def get(self, url, *, headers, timeout):
        assert url.endswith('/api/readdam/outbox') and timeout == 10
        assert headers['x-readdam-key'] == 'fake-key'
        assert headers['OAI-Sites-Authorization'] == 'Bearer fake-gate'
        if self.timeout_on_get:
            raise requests.Timeout()
        return Response(self.get_status, {"schemaVersion": 1, "chunks": self.chunks})

    def post(self, url, *, headers, json, timeout):
        assert url.endswith('/api/readdam/receipts') and timeout == 10
        if self.lose_first_receipt:
            self.lose_first_receipt = False
            raise requests.Timeout()
        self.receipts.append(json)
        return Response(self.post_status)

    def put(self, url, *, headers, json, timeout):
        assert url.endswith('/api/readdam/books') and timeout == 10
        self.books = json['books']
        return Response(self.put_status)


def run(conn, http):
    return readdam_sync.sync_once(conn, owner_id='user-1', url='https://library.example',
                                 token='fake-key', sites_gate_key='fake-gate', http=http)


def test_pull_receipt_and_minimal_book_snapshot(isolated_app):
    conn = owner_connection()
    http = FakeHTTP([payload()])
    assert run(conn, http) == {"state": "ok", "received": 1}
    assert http.receipts[0]['result'] == 'stored'
    assert len(http.books) == 1
    assert set(http.books[0]) == {'bookId', 'title', 'author', 'isbn', 'totalPages', 'status'}
    assert 'currentPage' not in http.books[0]
    assert conn.execute('SELECT count(*) FROM reading_chunks').fetchone()[0] == 1
    conn.close()


def test_lost_receipt_replays_same_chunk_as_already_stored(isolated_app):
    conn = owner_connection()
    http = FakeHTTP([payload()]); http.lose_first_receipt = True
    assert run(conn, http)['state'] == 'retry'
    assert not http.receipts
    assert run(conn, http)['state'] == 'ok'
    assert http.receipts[0]['result'] == 'already_stored'
    assert conn.execute('SELECT count(*) FROM reading_chunks').fetchone()[0] == 1
    conn.close()


def test_rejected_book_and_invalid_payload_send_receipts_without_rows(isolated_app):
    conn = owner_connection()
    missing = payload(bookId=None, bookTitle='없는 책', author=None, isbn=None)
    invalid = payload(pageStart=-1)
    http = FakeHTTP([missing, invalid])
    assert run(conn, http)['received'] == 2
    assert [item['errorCode'] for item in http.receipts] == ['book_not_matched', 'invalid_payload']
    assert http.receipts[1]['errorField'] == 'pageStart'
    assert conn.execute('SELECT count(*) FROM reading_chunks').fetchone()[0] == 0
    conn.close()


def test_401_timeout_and_5xx_leave_outbox_pending(isolated_app):
    conn = owner_connection()
    http = FakeHTTP([payload()]); http.get_status = 401
    assert run(conn, http)['state'] == 'connection_key'
    http.get_status = 503
    assert run(conn, http)['state'] == 'retry'
    http.get_status = 200; http.timeout_on_get = True
    assert run(conn, http)['state'] == 'retry'
    assert conn.execute('SELECT count(*) FROM reading_chunks').fetchone()[0] == 0
    conn.close()


def test_missing_settings_make_no_http_request(isolated_app):
    conn = owner_connection()
    http = FakeHTTP([])
    result = readdam_sync.sync_once(conn, owner_id='user-1', url='https://library.example',
                                    token='', sites_gate_key='fake-gate', http=http)
    assert result['state'] == 'not_configured'
    assert http.books is None
    conn.close()
