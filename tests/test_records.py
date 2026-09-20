import pytest
from lib import db
from test_activity_inputs_app import isolated_app, open_detail, fetch_one


def test_progress_edit_delete_restore_keeps_totals_and_page_consistent(isolated_app):
    from lib import records
    conn=db.get_connection()
    first=db.add_progress(conn,'book-1',20,10)
    last=db.add_progress(conn,'book-1',35,20)
    with pytest.raises(ValueError): records.update(conn,first,page=25,minutes=10)
    records.update(conn,last,page=40,minutes=15)
    assert db.get_book(conn,'book-1')['current_page']==40
    assert db.all_activities(conn)['pages_read'].sum()==30
    records.delete(conn,last)
    assert db.get_book(conn,'book-1')['current_page']==20
    assert db.all_activities(conn)['pages_read'].sum()==10
    records.restore(conn,last)
    assert db.get_book(conn,'book-1')['current_page']==40
    records.delete(conn,first)
    assert db.get_book(conn,'book-1')['current_page']==40
    assert db.all_activities(conn)['pages_read'].sum()==20


def test_quote_edit_stale_revision_rejected_and_soft_delete_reversible(isolated_app):
    from lib import records
    conn=db.get_connection()
    aid=db.add_quote(conn,'book-1',10,'old')
    records.update(conn,aid,page=12,quote='new',text='thought',expected_revision=None)
    with pytest.raises(ValueError): records.update(conn,aid,page=15,quote='stale',text='',expected_revision=None)
    records.delete(conn,aid)
    assert db.all_activities(conn).empty
    records.restore(conn,aid)
    row=db.all_activities(conn).iloc[0]
    assert (row['kind'],row['quote'],row['text'],row['page'])==(0,'new','thought',12)


def test_app_edit_delete_restore_and_timeline_book_link(isolated_app):
    conn=db.get_connection(); aid=db.add_note(conn,'book-1',10,'기존 메모'); conn.close()
    at=open_detail()
    at.button(key=f'edit_{aid}').click().run()
    at.text_area(key='record_text').set_value('고친 메모')
    at.button(key='record_save').click().run()
    assert not at.exception
    assert fetch_one(isolated_app[0], 'SELECT text FROM activities')==('고친 메모',)
    at.button(key=f'edit_{aid}').click().run()
    at.checkbox(key='record_delete_confirm').check()
    at.button(key='record_delete').click().run()
    assert not at.exception
    assert fetch_one(isolated_app[0], 'SELECT COUNT(*) FROM activities WHERE deleted_at IS NULL')==(0,)
    at.button(key=f'restore_{aid}').click().run()
    assert not at.exception
    at.session_state['view']='타임라인'; at.run()
    assert any(e.value=='고친 메모' for e in at.markdown)
    at.button(key=f'timeline_book_{aid}').click().run()
    assert not at.exception
    assert at.session_state['view']=='책 상세'
