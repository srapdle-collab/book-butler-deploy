from datetime import date,datetime
from zoneinfo import ZoneInfo
import pytest
import pandas as pd
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
    at.button(key='shelf_cover_book-1').click().run()
    assert at.session_state['selected_book_id']=='book-1'


def test_new_reading_book_enters_recent_preview_without_activity(isolated_app):
    """A newly registered reading book must not sort behind every dated book."""
    conn = db.get_connection()
    try:
        for number in range(2, 9):
            db.insert_book(conn, {
                'id': f'older-{number}', 'title': f'기존 독서 {number}',
                'status': '읽는 중', 'start_date': 1_000_000_000 + number,
            })
        db.insert_book(conn, {
            'id': 'new-reading', 'title': '희망을 짓는다는 것',
            'status': '읽는 중', 'category': '분별력',
        })
        new_book = db.get_book(conn, 'new-reading')
        preview_ids = db.list_books(conn, status='읽는 중').head(6)['id'].tolist()
        assert new_book['start_date'] is not None
        assert 'new-reading' in preview_ids
    finally:
        conn.close()


def test_shelf_top_add_book_uses_the_existing_add_book_flow(isolated_app):
    """상단 바로가기는 별도 로직 없이 같은 책 추가 함수를 연다."""
    at = AppTest.from_file(APP_PATH).run()
    assert at.text_input(key='add_book_query')  # 기존 하단 입력은 계속 제공한다.

    at.button(key='shelf_add_book_top').click().run()

    assert at.text_input(key='shelf_top_add_book_query')
    assert at.text_input(key='add_book_query')

    at.text_input(key='shelf_top_add_book_title').set_value('상단에서 추가한 책').run()
    at.button(key='shelf_top_add_book_submit').click().run()
    at.text_input(key='add_book_title').set_value('하단에서 추가한 책').run()
    at.button(key='add_book_submit').click().run()

    conn = db.get_connection()
    try:
        titles = {row['title'] for row in conn.execute('SELECT title FROM books').fetchall()}
    finally:
        conn.close()
    assert {'상단에서 추가한 책', '하단에서 추가한 책'} <= titles


def test_shelf_pages_large_grid_without_losing_books(isolated_app):
    """책장을 한 번에 모두 렌더링하지 않고 다음 페이지에서 나머지를 찾는다."""
    conn=db.get_connection()
    for number in range(2,27):
        db.insert_book(conn,{
            'id':f'book-{number}',
            'title':f'표지 책 {number}',
            'category':'신앙' if number%2 else '기도',
            'status':'미독',
        })
    conn.close()

    at=AppTest.from_file(APP_PATH).run()
    covers=[button for button in at.button if (button.key or '').startswith('shelf_cover_')]
    assert len(covers)==24
    assert at.number_input(key='shelf_page_input').value==1
    assert at.selectbox(key='shelf_category').value=='전체'
    at.number_input(key='shelf_page_input').set_value(2).run()
    assert len([button for button in at.button if (button.key or '').startswith('shelf_cover_')])==2
    assert any('표지 없음' in caption.value for caption in at.caption)

    at.text_input(key='shelf_search').set_value('테스트 책').run()
    assert at.number_input(key='shelf_page_input').value==1
    assert len([button for button in at.button if (button.key or '').startswith('shelf_cover_')])==1
    at.text_input(key='shelf_search').set_value('').run()
    at.number_input(key='shelf_page_input').set_value(1).run()
    at.button(key='shelf_cover_book-2').click().run()
    assert at.session_state['selected_book_id']=='book-2'


def test_shelf_search_with_no_matches_shows_empty_state(isolated_app, monkeypatch):
    original_list_books = db.list_books

    def postgres_empty_frame(conn, **kwargs):
        if kwargs.get('search'):
            return pd.DataFrame()  # psycopg dict rows preserve no columns when empty
        return original_list_books(conn, **kwargs)

    monkeypatch.setattr(db, 'list_books', postgres_empty_frame)
    at = AppTest.from_file(APP_PATH).run()
    at.text_input(key='shelf_search').set_value('TEST-READDAM-NO-MATCH').run()

    assert not at.exception
    assert any('검색 결과 0권' in item.value for item in at.caption)
    assert any('조건에 맞는 책이 없습니다.' in item.value for item in at.info)


def test_sidebar_uses_read_dam_name(isolated_app):
    at=AppTest.from_file(APP_PATH).run()
    assert any(title.value=='📚 읽담' for title in at.title)


def test_stats_app_accepts_period_and_has_no_errors(isolated_app):
    at=AppTest.from_file(APP_PATH)
    at.session_state['view']='통계';at.run()
    assert not at.exception
    at.date_input(key='daily_period').set_value((date(2026,9,1),date(2026,9,10))).run()
    assert not at.exception
    assert any(x.label=='평균 쪽/일' and x.value=='0.0' for x in at.metric)
    assert any('10일' in x.value for x in at.caption)
