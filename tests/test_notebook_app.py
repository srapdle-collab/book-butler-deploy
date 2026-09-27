from test_activity_inputs_app import isolated_app, open_detail, fetch_one
from streamlit.testing.v1 import AppTest


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


def test_cards_hide_only_missing_quote_text_and_photo():
    script = """
import math
import pandas as pd
from lib import notebook_ui

rows = pd.DataFrame([
    {'id': 'none', 'kind': 7, 'page': 0, 'date': 1700000000, 'quote': None, 'text': '메모 A', 'photo': None},
    {'id': 'nan-quote', 'kind': 7, 'page': 1, 'date': 1700000001, 'quote': math.nan, 'text': '메모 B', 'photo': None},
    {'id': 'na-quote', 'kind': 7, 'page': 2, 'date': 1700000002, 'quote': pd.NA, 'text': '메모 C', 'photo': None},
    {'id': 'nan-text', 'kind': 7, 'page': 3, 'date': 1700000003, 'quote': '정상 인용', 'text': math.nan, 'photo': None},
    {'id': 'nan-photo', 'kind': 7, 'page': 4, 'date': 1700000004, 'quote': None, 'text': None, 'photo': math.nan},
], dtype=object)
notebook_ui.cards(None, rows)
"""
    at = AppTest.from_string(script).run()
    assert not at.exception
    body = [element.value for element in at.markdown]
    captions = [element.value for element in at.caption]
    assert all(value in body for value in ('메모 A', '메모 B', '메모 C', '정상 인용', '기록'))
    assert 'nan' not in body
    assert '내 생각' not in captions
    assert not at.warning
    assert any('record-page' in value and '>0<' in value for value in body)


def test_cards_keep_normal_text_and_literal_nan_string():
    script = """
import pandas as pd
from lib import notebook_ui

rows = pd.DataFrame([
    {'id': 'normal', 'kind': 7, 'page': 1, 'date': 1700000000, 'quote': '정상 인용', 'text': '정상 메모', 'photo': None},
    {'id': 'literal', 'kind': 7, 'page': 2, 'date': 1700000001, 'quote': 'nan', 'text': '실제 문자열', 'photo': None},
])
notebook_ui.cards(None, rows)
"""
    at = AppTest.from_string(script).run()
    assert not at.exception
    body = [element.value for element in at.markdown]
    captions = [element.value for element in at.caption]
    assert all(value in body for value in ('정상 인용', '정상 메모', 'nan', '실제 문자열'))
    assert captions.count('내 생각') == 2


def test_cards_normalize_missing_values_from_new_pandas_string_dtype():
    script = """
import pandas as pd
from lib import database, notebook_ui

class Cursor:
    def fetchall(self):
        return [
            {'id': 'progress', 'kind': 7, 'page': 0, 'date': 1700000000, 'quote': None, 'text': '진도 메모', 'photo': None},
            {'id': 'quote', 'kind': 7, 'page': 1, 'date': 1700000001, 'quote': '원문', 'text': None, 'photo': None},
        ]

class PostgresConnection:
    backend = 'postgres'
    def execute(self, query, params=()):
        return Cursor()

with pd.option_context('future.infer_string', True):
    rows = database.read_frame(PostgresConnection(), 'SELECT * FROM activities')
    assert str(rows['quote'].dtype) == 'str'
    assert str(rows['text'].dtype) == 'str'
    notebook_ui.cards(None, rows)
"""
    at = AppTest.from_string(script).run()
    assert not at.exception
    body = [element.value for element in at.markdown]
    captions = [element.value for element in at.caption]
    assert '진도 메모' in body
    assert '원문' in body
    assert 'nan' not in body
    assert '내 생각' not in captions
