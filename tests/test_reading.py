import pytest
from lib import db
from test_activity_inputs_app import isolated_app, open_detail, fetch_one


def test_timer_recovers_and_stop_freezes_and_save_is_exactly_once(isolated_app):
    from lib import reading
    conn=db.get_connection()
    session=reading.start(conn,'book-1',now=1000)
    conn.close()
    conn=db.get_connection()
    assert reading.active(conn)['id']==session['id']
    reading.stop(conn,session['id'],now=1090)
    reading.stop(conn,session['id'],now=1900)
    aid=reading.save(conn,session['id'],25)
    assert reading.save(conn,session['id'],25)==aid
    row=conn.execute('SELECT kind,base_page,page,pages_read,seconds_read,minutes_read FROM activities').fetchone()
    assert tuple(row)==(4,10,25,15,90,1.5)
    assert reading.active(conn) is None


def test_only_one_active_timer_and_cancel_has_no_activity(isolated_app):
    from lib import reading
    conn=db.get_connection()
    first=reading.start(conn,'book-1',now=1000)
    assert reading.start(conn,'book-1',now=1001)['id']==first['id']
    with pytest.raises(ValueError): db.add_progress(conn,'book-1',20,10)
    reading.cancel(conn,first['id'])
    assert conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]==0
    assert db.get_book(conn,'book-1')['current_page']==10


def test_timer_app_new_session_recovers_stopped_timer_and_saves(isolated_app):
    at=open_detail()
    at.button(key='open_progress').click().run()
    at.button(key='timer_start').click().run()
    assert not at.exception
    restarted=open_detail()
    assert restarted.button(key='timer_stop')
    restarted.button(key='timer_stop').click().run()
    assert not restarted.exception
    again=open_detail()
    again.number_input(key='timer_page').set_value(20)
    again.button(key='timer_save').click().run()
    assert not again.exception
    assert fetch_one(isolated_app[0],'SELECT kind,pages_read,page FROM activities')==(4,10,20)
    assert fetch_one(isolated_app[0],'SELECT state FROM reading_sessions')==('saved',)
