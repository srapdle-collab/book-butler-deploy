import re
from urllib.parse import urlsplit,parse_qs
from lib import db
from test_activity_inputs_app import isolated_app, open_detail


def test_export_has_citations_and_notes_are_opt_in(isolated_app):
    from lib import sharing
    conn=db.get_connection()
    db.add_quote(conn,'book-1',12,'가 & 나? #책','개인 생각')
    db.add_note(conn,'book-1',5,'단독 메모')
    book=db.get_book(conn,'book-1')
    body=sharing.export_book(conn,book)
    assert '테스트 책' in body and '저자' in body and 'p.12' in body
    assert '개인 생각' not in body and '단독 메모' not in body
    full=sharing.export_book(conn,book,include_notes=True)
    assert '개인 생각' in full and '단독 메모' in full
    assert parse_qs(urlsplit(sharing.mailto(book['title'],body)).query)['body']==[body]


def test_record_share_text_and_sms_include_content_and_source(isolated_app):
    from lib import sharing
    conn=db.get_connection()
    quote_id=db.add_quote(conn,'book-1',12,'기억할 문장','나의 생각')
    note_id=db.add_note(conn,'book-1',7,'단독 메모')
    book=db.get_book(conn,'book-1')
    rows={row['id']:row for row in conn.execute('SELECT * FROM activities')}

    quote_body=sharing.record_text(book,rows[quote_id])
    assert '기억할 문장' in quote_body and '나의 생각' in quote_body
    assert '테스트 책' in quote_body and '저자' in quote_body
    assert 'p.12' in quote_body
    assert re.search(r'\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}$',quote_body)

    note_body=sharing.record_text(book,rows[note_id])
    assert '단독 메모' in note_body and 'p.7' in note_body
    sms=sharing.sms(note_body)
    assert urlsplit(sms).scheme=='sms'
    assert parse_qs(urlsplit(sms).query)['body']==[note_body]


def test_memory_stays_until_refresh_and_links_to_book(isolated_app):
    from streamlit.testing.v1 import AppTest
    from test_activity_inputs_app import APP_PATH
    conn=db.get_connection(); aid=db.add_quote(conn,'book-1',12,'좋은 문장'); conn.close()
    at=AppTest.from_file(APP_PATH)
    at.session_state['view']='한 장의 추억'; at.run()
    assert not at.exception
    assert at.session_state['memory_id']==aid
    at.run()
    assert at.session_state['memory_id']==aid
    assert any('p.12' in e.value and '저자' in e.value for e in at.caption)
    assert at.button(key=f'memory_share_{aid}').label=='공유'
    assert any('카톡은 복사 후 붙여넣기' in e.value for e in at.caption)
    at.button(key=f'memory_share_{aid}').click().run()
    assert any(e.label=='메일로 보내기' for e in at.get('link_button'))
    assert any(e.label=='문자로 보내기' for e in at.get('link_button'))
    at.button(key='memory_book').click().run()
    assert at.session_state['selected_book_id']=='book-1'


def test_export_preview_changes_with_note_selection(isolated_app):
    conn=db.get_connection(); db.add_quote(conn,'book-1',10,'인용','비공개 생각'); conn.close()
    at=open_detail()
    assert '비공개 생각' not in at.text_area(key='export_preview').value
    at.checkbox(key='export_notes').check().run()
    assert '비공개 생각' in at.text_area(key='export_preview').value
    assert not at.exception


def test_share_actions_are_consistent_in_detail_timeline_and_shelf_detail(isolated_app):
    conn=db.get_connection()
    quote_id=db.add_quote(conn,'book-1',31,'공유할 인용문','공유할 생각')
    note_id=db.add_note(conn,'book-1',42,'공유할 메모')
    progress_id=db.add_progress(conn,'book-1',20,5)
    conn.close()

    at=open_detail()
    assert at.button(key=f'detail_share_{quote_id}').label=='공유'
    assert at.button(key=f'detail_share_{note_id}').label=='공유'
    assert not any(button.key==f'detail_share_{progress_id}' for button in at.button)
    at.button(key=f'detail_share_{note_id}').click().run()
    sms_link=next(e.url for e in at.get('link_button') if e.label=='문자로 보내기')
    body=parse_qs(urlsplit(sms_link).query)['body'][0]
    assert '공유할 메모' in body and '테스트 책' in body and 'p.42' in body
    assert any('복사하기' in e.proto.srcdoc for e in at.get('iframe'))

    at.session_state['view']='타임라인'; at.run()
    assert at.button(key=f'timeline_share_{quote_id}').label=='공유'
    at.button(key=f'timeline_share_{quote_id}').click().run()
    mail_link=next(e.url for e in at.get('link_button') if e.label=='메일로 보내기')
    mail_body=parse_qs(urlsplit(mail_link).query)['body'][0]
    assert '공유할 인용문' in mail_body and '공유할 생각' in mail_body

    at.session_state['view']='책장'; at.run()
    at.button(key='detail_book-1').click().run()
    assert at.session_state['view']=='책 상세'
    assert at.button(key=f'detail_share_{quote_id}').label=='공유'
