import streamlit as st
from lib import db, records


def edit_controls(conn,row):
    if row['kind'] not in (0,1,2,4): return
    aid=row['id']
    if st.button('수정 · 삭제',key=f'edit_{aid}'):
        for key in list(st.session_state):
            if key.startswith('record_') and key not in ('record_mode',): st.session_state.pop(key,None)
        st.session_state.record_edit_id=aid
        st.session_state.record_revision=records.get(conn,aid)['updated_at']
        st.rerun()


def selected_editor(conn):
    area=st.empty()
    aid=st.session_state.get('record_edit_id')
    if not aid:
        area.empty()
        return
    row=records.get(conn,aid)
    if row['deleted_at'] is not None:
        area.empty()
        return
    with area.container():
        editor(conn,dict(row),aid)


def editor(conn,row,aid):
    original=records.get(conn,aid)
    book=db.get_book(conn,row['book_id'])
    is_progress=row['kind']==4
    allow_page=not is_progress or (records.is_latest(conn,original) and book['current_page']==row['page'] and book['status']=='읽는 중' and records.base_page(original) is not None)
    if is_progress:
        st.caption('시간 수정은 통계에 반영됩니다. 과거 진도 페이지는 다음 기록과 겹칠 수 있어 수정하지 않습니다.')
        if allow_page:
            st.info(f"최신 진도입니다. 삭제하면 현재 페이지를 {records.base_page(original)}쪽으로 되돌립니다.")
        else: st.caption('삭제 시 이 기록의 쪽수·시간을 통계에서 제외하며 현재 페이지는 유지합니다.')
    with st.form(f'edit_form_{aid}'):
        page=st.number_input('기록 페이지',min_value=0,value=int(row['page'] or 0),step=1,disabled=not allow_page,key='record_page')
        quote='';text='';minutes=None
        if is_progress:
            minutes=st.number_input('읽은 시간(분)',min_value=0.0,value=max(0.0,float(row.get('minutes_read') or 0)),step=0.5,key='record_minutes')
        else:
            if row['kind']!=1: quote=st.text_area('인용문 (선택)',value=row.get('quote') or '',key='record_quote')
            text=st.text_area('메모 / 내 생각',value=row.get('text') or '',key='record_text')
        save=st.form_submit_button('수정 저장',key='record_save')
    if save:
        try: records.update(conn,aid,page=int(page),quote=quote,text=text,minutes=minutes,expected_revision=st.session_state.record_revision)
        except ValueError as exc: st.error(str(exc))
        else: done('기록을 수정했습니다.')
    confirm=st.checkbox('이 기록을 삭제합니다 (휴지통에서 복원 가능)',key='record_delete_confirm')
    if st.button('기록 삭제',disabled=not confirm,key='record_delete'):
        try: records.delete(conn,aid,expected_revision=st.session_state.record_revision)
        except ValueError as exc: st.error(str(exc))
        else: done('기록을 휴지통으로 옮겼습니다.')
    if st.button('수정 닫기',key='record_close'): done()


def done(message=None):
    st.session_state.record_edit_id=None
    if message: st.session_state.notice=message
    st.rerun()


def trash(conn,book_id):
    rows=conn.execute('SELECT * FROM activities WHERE book_id=? AND deleted_at IS NOT NULL ORDER BY deleted_at DESC',(book_id,)).fetchall()
    if not rows: return
    with st.expander(f'휴지통 ({len(rows)})'):
        st.caption('사진 원본은 삭제하지 않습니다. 복원하면 통계에도 다시 반영됩니다.')
        for row in rows:
            st.write(f"{row['page']}쪽 · {(row['quote'] or row['text'] or '사진')[:100]}")
            if st.button('복원',key=f"restore_{row['id']}"):
                try: records.restore(conn,row['id'])
                except ValueError as exc: st.error(str(exc))
                else: done('기록을 복원했습니다.')
