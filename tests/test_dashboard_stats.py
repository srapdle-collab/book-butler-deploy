from datetime import date,datetime
from zoneinfo import ZoneInfo
import pytest
from lib import db
from test_activity_inputs_app import isolated_app, APP_PATH
from streamlit.testing.v1 import AppTest


def ts(day,hour=12):
    return int(datetime(2026,9,day,hour,tzinfo=ZoneInfo('Asia/Seoul')).timestamp())


def test_stats_count_kst_days_and_completed_events_not_imported_start(isolated_app):
    from lib import statistics
    conn=db.get_connection()
    db.insert_activity(conn,book_id='book-1',kind=4,page=20,pages_read=10,minutes_read=2,timestamp=ts(1,0))
    db.insert_activity(conn,book_id='book-1',kind=5,page=1,timestamp=ts(1))
    conn.execute("UPDATE activities SET event_type='reading_started' WHERE kind=5")
    aid=db.insert_activity(conn,book_id='book-1',kind=6,page=1,timestamp=ts(2))
    conn.execute("UPDATE activities SET event_type='completed' WHERE id=?",(aid,));conn.commit()
    result=statistics.summarize(conn,date(2026,9,1),date(2026,9,10))
    assert result['pages']==10 and result['finishes']==1
    assert result['pages_per_day']==1 and result['books_per_month']==1
    assert len(result['daily'])==10
    assert result['daily'].iloc[0]['pages']==10
    conn.execute('UPDATE activities SET deleted_at=1 WHERE id=?',(aid,));conn.commit()
    assert statistics.summarize(conn,date(2026,9,1),date(2026,9,10))['finishes']==0


def test_empty_stats_and_calendar_month_denominator(isolated_app):
    from lib import statistics
    conn=db.get_connection()
    result=statistics.summarize(conn,date(2026,8,31),date(2026,9,1))
    assert result['days']==2 and result['months']==2
    assert result['pages_per_day']==0
    with pytest.raises(ValueError): statistics.summarize(conn,date(2026,9,2),date(2026,9,1))


def test_shelf_counts_are_dynamic_and_reading_all_links(isolated_app):
    conn=db.get_connection()
    db.insert_book(conn,{'id':'book-2','title':'새로 산 책','status':'위시리스트'})
    at=AppTest.from_file(APP_PATH).run()
    assert not at.exception
    assert [(x.label,x.value) for x in at.metric][:3]==[('책장','1'),('위시리스트','1'),('읽고 있는 책','1')]
    at.button(key='reading_all').click().run()
    assert at.selectbox(key='shelf_status').value=='읽는 중'
    at.button(key='detail_book-1').click().run()
    assert at.session_state['selected_book_id']=='book-1'


def test_stats_app_accepts_period_and_has_no_errors(isolated_app):
    at=AppTest.from_file(APP_PATH)
    at.session_state['view']='통계';at.run()
    assert not at.exception
    at.date_input(key='daily_period').set_value((date(2026,9,1),date(2026,9,10))).run()
    assert not at.exception
    assert any(x.label=='평균 쪽/일' and x.value=='0.0' for x in at.metric)
    assert any('10일' in x.value for x in at.caption)
