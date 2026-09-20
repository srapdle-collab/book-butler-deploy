import streamlit as st
from lib import db, reading


@st.fragment(run_every='1s')
def clock_face(session):
    seconds=reading.elapsed(session)
    st.metric('읽는 시간',f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}')


def render(conn,book,goto):
    session=reading.active(conn)
    if session:
        if session['book_id']!=book['id']:
            other=db.get_book(conn,session['book_id'])
            st.info(f"『{other['title']}』의 독서 타이머가 남아 있습니다.")
            if st.button('진행 중인 책으로 이동',key='timer_go'):
                goto('책 상세',session['book_id']); st.rerun()
            return
        st.caption(f"시작 페이지 {session['base_page']}쪽 · 새로고침 후에도 복구됩니다.")
        if session['state']=='running':
            clock_face(dict(session))
            if st.button('■ 멈춤',key='timer_stop',type='primary'):
                reading.stop(conn,session['id']); st.rerun()
        else:
            seconds=reading.elapsed(session)
            st.info(f'읽은 시간 {seconds//60}분 {seconds%60}초 · 멈춘 시점으로 고정됨')
            with st.form('timer_finish'):
                page=st.number_input('도달한 페이지',min_value=session['base_page'],max_value=max(book['pages'] or 0,session['base_page']) or None,
                                     value=session['base_page'],step=1,key='timer_page')
                submitted=st.form_submit_button('독서 기록 저장',key='timer_save',type='primary')
            if submitted:
                try: reading.save(conn,session['id'],int(page))
                except ValueError as exc: st.error(str(exc))
                else:
                    st.session_state.notice='독서 기록을 저장했습니다.'
                    st.session_state.record_mode=None
                    st.rerun()
        if st.button('이번 타이머 취소',key='timer_cancel'):
            reading.cancel(conn,session['id']); st.rerun()
    elif st.session_state.get('record_mode')=='progress':
        if st.button('▶ 읽기 시작',key='timer_start',type='primary'):
            try: reading.start(conn,book['id'])
            except ValueError as exc: st.error(str(exc))
            else:
                st.session_state.pop('timer_page',None)
                st.rerun()
