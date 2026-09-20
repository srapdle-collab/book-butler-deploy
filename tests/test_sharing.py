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
    at.button(key='memory_book').click().run()
    assert at.session_state['selected_book_id']=='book-1'


def test_export_preview_changes_with_note_selection(isolated_app):
    conn=db.get_connection(); db.add_quote(conn,'book-1',10,'인용','비공개 생각'); conn.close()
    at=open_detail()
    assert '비공개 생각' not in at.text_area(key='export_preview').value
    at.checkbox(key='export_notes').check().run()
    assert '비공개 생각' in at.text_area(key='export_preview').value
    assert not at.exception
