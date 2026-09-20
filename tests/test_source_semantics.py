from lib import source_semantics as source


def test_status_2_is_reading_even_at_last_page():
    assert source.classify_book({'status': 2, 'readingNow': 0, 'readCount': 0,
        'currentPage': 200, 'pages': 200, 'activities': [{'kind': 5, 'date': 1}]})[0] == '읽는 중'


def test_latest_lifecycle_distinguishes_finished_stopped_and_unread():
    assert source.classify_book({'status': 1, 'readCount': 1,
        'activities': [{'kind': 6, 'date': 2}, {'kind': 5, 'date': 1}]})[0] == '완독'
    assert source.classify_book({'status': 1, 'readCount': 1,
        'activities': [{'kind': 6, 'date': 2}, {'kind': 7, 'date': 3}]})[0] == '읽기 중단'
    assert source.classify_book({'status': 1, 'readingNow': 1, 'activities': []})[0] == '미독'


def test_original_and_new_kind_five_have_distinct_meaning():
    assert source.source_event(5) == 'reading_started'
    assert source.source_event(6) == 'completed'


def test_correction_preserves_records_and_is_idempotent():
    import sqlite3
    import uuid
    from migration.load_db import SCHEMA
    from migration.audit_source import apply_source
    conn = sqlite3.connect(':memory:')
    conn.executescript(SCHEMA)
    raw = {'uuid':'b', 'status':2, 'readingNow':0, 'currentPage':10,
           'activities':[{'kind':5,'date':1}]}
    aid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'bookswing:b:0'))
    conn.execute("INSERT INTO books(id,title,status,current_page) VALUES ('b','book','완독',10)")
    conn.execute("INSERT INTO activities(id,book_id,kind,date) VALUES (?,'b',5,1)", (aid,))
    conn.commit()
    assert apply_source(conn,[raw])
    assert conn.execute('SELECT status FROM books').fetchone() == ('읽는 중',)
    assert conn.execute('SELECT id,kind,event_type FROM activities').fetchone() == (aid,5,'reading_started')
    assert not apply_source(conn,[raw])


def test_converter_carries_corrected_status_and_event_semantics():
    from migration.convert_bookswing import convert_book, convert_activity
    raw={'uuid':'b','status':2,'readingNow':0,'readCount':0,'activities':[{'kind':5,'date':1}]}
    book=convert_book(raw)
    assert book['status']=='읽는 중'
    assert book['rawStatus']==2
    assert convert_activity(raw['activities'][0],'b',0)['eventType']=='reading_started'
