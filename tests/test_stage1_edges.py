import sqlite3
from lib import db
from test_activity_inputs_app import isolated_app, open_detail
import pytest


def test_status_change_during_timer_is_rejected_without_partial_write(isolated_app):
    from lib import reading
    conn=db.get_connection()
    reading.start(conn,'book-1',now=100)
    with pytest.raises(ValueError): db.update_book_status(conn,'book-1','완독')
    assert db.get_book(conn,'book-1')['status']=='읽는 중'
    assert db.all_activities(conn).empty


def test_new_status_events_explicitly_distinguish_completion(isolated_app):
    conn=db.get_connection()
    db.update_book_status(conn,'book-1','완독')
    row=conn.execute('SELECT kind,event_type FROM activities').fetchone()
    assert tuple(row)==(5,'completed')
    db.update_book_status(conn,'book-1','완독')
    assert conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]==1
    db.update_book_status(conn,'book-1','읽기 중단')
    assert conn.execute("SELECT COUNT(*) FROM activities WHERE event_type='stopped'").fetchone()[0]==1


def test_refresh_shelf_offers_active_timer_recovery(isolated_app):
    from lib import reading
    from streamlit.testing.v1 import AppTest
    from test_activity_inputs_app import APP_PATH
    conn=db.get_connection(); reading.start(conn,'book-1',now=100)
    at=AppTest.from_file(APP_PATH).run()
    at.button(key='resume_timer').click().run()
    assert not at.exception
    assert at.session_state['selected_book_id']=='book-1'
    assert at.button(key='timer_stop')


def test_reopening_quote_uses_latest_page_not_previous_form_value(isolated_app):
    at=open_detail()
    at.button(key='open_quote').click().run()
    at.number_input(key='quote_page').set_value(5)
    at.button(key='cancel_input').click().run()
    conn=db.get_connection();db.add_progress(conn,'book-1',25,10)
    at.button(key='open_quote').click().run()
    assert at.number_input(key='quote_page').value==25


def test_invalid_photo_does_not_create_record_or_file(isolated_app):
    conn=db.get_connection()
    with pytest.raises(ValueError): db.add_photo(conn,'book-1',1,'bad.png',b'not an image')
    assert db.all_activities(conn).empty
    assert not isolated_app[1].exists() or not list(isolated_app[1].iterdir())
