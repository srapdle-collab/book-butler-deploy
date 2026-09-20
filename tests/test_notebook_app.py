from test_activity_inputs_app import isolated_app, open_detail, fetch_one


def test_toolbar_opens_only_chosen_form_and_uses_current_page(isolated_app):
    at = open_detail()
    assert not [e for e in at.text_area if e.key != 'export_preview']
    at.button(key='open_quote').click().run()
    assert at.number_input(key='quote_page').value == 10
    at.text_area(key='quote_text').set_value('인용')
    at.text_area(key='quote_note').set_value('내 생각')
    at.button(key='save_quote').click().run()
    assert not at.exception
    assert fetch_one(isolated_app[0], 'SELECT kind,quote,text,page FROM activities') == (0,'인용','내 생각',10)
    assert fetch_one(isolated_app[0], 'SELECT current_page FROM books') == (10,)
    assert not [e for e in at.text_area if e.key != 'export_preview']


def test_cards_are_newest_first_and_cancel_does_not_save(isolated_app):
    import sqlite3
    with sqlite3.connect(isolated_app[0]) as conn:
        conn.executemany("INSERT INTO activities(id,book_id,kind,text,page,date) VALUES (?,'book-1',0,?,10,?)",
                         [('old','과거 기록',100),('new','최근 기록',200)])
    at = open_detail()
    body = [e.value for e in at.markdown]
    assert body.index('최근 기록') < body.index('과거 기록')
    assert not at.dataframe
    at.button(key='open_note').click().run()
    assert at.number_input(key='note_page').value == 10
    at.text_area(key='note_text').set_value('취소할 기록')
    at.button(key='cancel_input').click().run()
    assert fetch_one(isolated_app[0], 'SELECT COUNT(*) FROM activities') == (2,)


def test_cards_use_notebook_timeline_page_and_unlabeled_date(isolated_app):
    from lib import db
    conn = db.get_connection()
    db.add_progress(conn, 'book-1', 23, 12)
    db.add_quote(conn, 'book-1', 24, '따옴표 없이 보여 줄 인용문', '')
    conn.close()

    at = open_detail()
    markdown = [element.value for element in at.markdown]
    captions = [element.value for element in at.caption]
    assert any('record-page' in value and '>24<' in value for value in markdown)
    assert '따옴표 없이 보여 줄 인용문' in markdown
    assert '13쪽을 12분 동안 읽었습니다' in markdown
    assert not any(value.startswith('진도 ·') or value.startswith('인용구 ·') for value in captions)
