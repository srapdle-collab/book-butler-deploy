"""Page-range reading: start at the current page, finish by entering the last page read."""
from datetime import datetime

import streamlit as st

from lib import db, reading


def _started(session) -> str:
    return datetime.fromtimestamp(session['started_at']).strftime('%m/%d %H:%M')


def render(conn,book,goto):
    session,expired=reading.active_fresh(conn)
    if expired:
        st.toast('24시간이 지난 읽기를 자동으로 취소했습니다.')
    if session:
        if session['book_id']!=book['id']:
            other=db.get_book(conn,session['book_id'])
            title=other['title'] if other else '다른 책'
            st.info(f"『{title}』을(를) {session['base_page']}쪽부터 읽는 중입니다 ({_started(session)} 시작). "
                    '그 읽기를 마치거나 취소해야 이 책을 기록할 수 있습니다.')
            go,drop=st.columns(2)
            if go.button('그 책으로 이동',key='timer_go',width='stretch'):
                goto('책 상세',session['book_id']); st.rerun()
            if drop.button('그 읽기 취소',key='timer_cancel_other',width='stretch'):
                reading.cancel(conn,session['id']); st.rerun()
            return
        st.markdown(f"**{session['base_page']}쪽부터 읽는 중** · {_started(session)} 시작")
        maximum=max(book['pages'] or 0,session['base_page']) or None
        with st.form('timer_finish'):
            page=st.number_input('끝난 쪽',min_value=session['base_page'],max_value=maximum,
                                 value=session['base_page'],step=1,key='timer_page')
            submitted=st.form_submit_button('읽기 끝 · 저장',key='timer_save',type='primary')
        if submitted:
            try: reading.finish(conn,session['id'],int(page))
            except ValueError as exc: st.error(str(exc))
            else:
                st.session_state.notice=f"{session['base_page']}~{int(page)}쪽을 기록했습니다."
                st.session_state.record_mode=None
                st.rerun()
        if st.button('이번 읽기 취소',key='timer_cancel'):
            reading.cancel(conn,session['id']); st.rerun()
    elif st.session_state.get('record_mode')=='progress':
        current=int(book['current_page'] or 0)
        if st.button(f'▶ 읽기 시작 ({current}쪽부터)',key='timer_start',type='primary'):
            try: reading.start(conn,book['id'])
            except ValueError as exc: st.error(str(exc))
            else:
                st.session_state.pop('timer_page',None)
                st.rerun()
