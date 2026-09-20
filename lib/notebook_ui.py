"""책 상세와 전체 타임라인에서 공유하는 독서 노트 화면."""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from lib import db

KST = ZoneInfo('Asia/Seoul')


def date_label(timestamp):
    return datetime.fromtimestamp(int(timestamp), KST).strftime('%Y.%m.%d %H:%M')


def event_label(row):
    event = row.get('event_type')
    if event in {'reading_started','completed','stopped','timer_started'}:
        return {'reading_started':'독서 시작', 'completed':'완독', 'stopped':'읽기 중단', 'timer_started':'타이머 시작'}[event]
    return {0:'인용구 · 내 생각' if row.get('quote') else '메모',1:'사진',2:'인용구',3:'독서 시작',4:'진도',5:'완독',6:'별점',7:'기록'}.get(row['kind'],'기록')


def cards(conn, rows, goto=None, prefix='detail'):
    from lib.record_ui import selected_editor
    selected_editor(conn)
    if rows.empty:
        st.info('아직 기록이 없습니다. 위에서 오늘의 기록을 남겨보세요.')
        return
    size=20
    pages=max(1,(len(rows)+size-1)//size)
    key=f'{prefix}_records_page'
    if st.session_state.get(key,1)>pages: st.session_state[key]=1
    page=st.number_input('기록 페이지',min_value=1,max_value=pages,step=1,key=key)
    st.caption(f'총 {len(rows):,}개 기록 · 최신순')
    for _, series in rows.iloc[(page-1)*size:page*size].iterrows():
        row=series.to_dict()
        with st.container(key=f"note_card_{row['id']}"):
            page_col, content_col = st.columns([1, 6], vertical_alignment='top')
            page_col.markdown(
                f'<div class="record-page">{int(row["page"] or 0)}</div>',
                unsafe_allow_html=True,
            )
            with content_col:
                if row.get('title'):
                    st.caption(f"{row['title']} · {row.get('author') or '저자 미상'}")
                if row.get('quote'):
                    # 인용문은 원문 그대로 보인다. 화면용 따옴표를 덧붙이지 않는다.
                    st.markdown(row['quote'])
                if row.get('text'):
                    if row.get('quote'):
                        st.caption('내 생각')
                    st.markdown(row['text'])
                if row.get('photo'):
                    path=db.activity_photo_source(row['photo'])
                    if path:
                        st.image(path, width='stretch')
                    else:
                        st.warning('사진 파일을 찾을 수 없습니다.')
                if not any(row.get(field) for field in ('quote', 'text', 'photo')):
                    # 시작·완독·중단처럼 본문이 없는 기존 이벤트도 타임라인에서 비지 않는다.
                    st.markdown({
                        'reading_started': '책을 읽기 시작했습니다.',
                        'timer_started': '독서 타이머를 시작했습니다.',
                        'completed': '이 책을 완독했습니다.',
                        'stopped': '읽기를 중단했습니다.',
                    }.get(row.get('event_type'), event_label(row)))
                st.caption(date_label(row['date']))
                from lib.sharing_ui import record_share
                record_share(conn, row, prefix)
                from lib.record_ui import edit_controls
                edit_controls(conn, row)
                if goto and st.button('해당 책으로 이동', key=f"{prefix}_book_{row['id']}"):
                    goto('책 상세', row['book_id'])
                    st.rerun()


def close_input(message=None):
    st.session_state.record_mode=None
    if message: st.session_state.notice=message
    st.rerun()


def forms(conn,book,goto):
    with st.container(key='reading_toolbar'):
        for col,mode,label in zip(st.columns(4),['progress','quote','photo','note'],['📘 진도','💬 인용구','📷 사진','✏️ 메모']):
            if col.button(label,key=f'open_{mode}',width='stretch'):
                for key in ['quote_page','note_page','photo_page','progress_page','quote_text','quote_note','note_text','photo_upload']:
                    st.session_state.pop(key,None)
                st.session_state.record_mode=mode
                st.rerun()
    from lib.timer_ui import render as render_timer
    render_timer(conn,book,goto)
    mode=st.session_state.get('record_mode')
    if not mode: return
    current=int(book['current_page'] or 0)
    maximum=max(int(book['pages'] or 0),current) or None
    with st.container(border=True):
        if st.button('취소',key='cancel_input'): close_input()
        if mode=='progress':
            from lib.reading import active
            if active(conn):
                st.caption('위 타이머에서 멈춘 후 도달 페이지를 저장해주세요.')
                return
            st.caption('타이머를 사용하지 못한 경우 수동으로 기록할 수 있습니다.')
            with st.expander('시간 직접 입력'), st.form('progress_form'):
                page=st.number_input('도달한 페이지',min_value=0,max_value=maximum,value=current,step=1,key='progress_page')
                minutes=st.number_input('걸린 시간(분)',min_value=1,value=1,step=1,key='progress_minutes')
                saved=st.form_submit_button('진도 저장',key='save_progress')
            if saved:
                try: db.add_progress(conn,book['id'],int(page),int(minutes))
                except ValueError as exc: st.error(str(exc))
                else: close_input('진도를 기록했습니다.')
            return
        # 사진 선택 즉시 미리보기: 업로더를 form 밖에 둔다.
        uploaded=None
        if mode=='photo':
            uploaded=st.file_uploader('사진',type=['png','jpg','jpeg','gif','webp'],key='photo_upload')
            if uploaded:
                try: db.validate_photo(uploaded.getvalue())
                except ValueError as exc:
                    st.error(str(exc)); uploaded=None
                else: st.image(uploaded.getvalue(),width=220,caption='저장할 사진')
        with st.form(f'{mode}_form'):
            page=st.number_input('페이지',min_value=0,max_value=maximum,value=current,step=1,key=f'{mode}_page')
            quote=st.text_area('인용문',key='quote_text') if mode=='quote' else ''
            note=st.text_area('내 생각 (선택)',key='quote_note') if mode=='quote' else st.text_area('메모',key='note_text') if mode=='note' else ''
            submitted=st.form_submit_button({'quote':'인용구 저장','note':'메모 저장','photo':'사진 저장'}[mode],key=f'save_{mode}')
        if submitted:
            try:
                if mode=='quote': db.add_quote(conn,book['id'],int(page),quote,note)
                elif mode=='note': db.add_note(conn,book['id'],int(page),note)
                elif uploaded: db.add_photo(conn,book['id'],int(page),uploaded.name,uploaded.getvalue())
                else: raise ValueError('사진을 선택해주세요.')
            except ValueError as exc: st.error(str(exc))
            else: close_input('기록을 저장했습니다.')


def detail(conn,book_id,goto,management):
    book=db.get_book(conn,book_id) if book_id else None
    if book is None:
        st.info('책장에서 책을 선택해주세요.'); return
    if st.session_state.get('form_book')!=book_id:
        for key in list(st.session_state):
            if key.startswith(('edit_','manage_','quote_','note_','photo_','progress_')): st.session_state.pop(key,None)
        st.session_state.record_mode=None
        st.session_state.form_book=book_id
    if st.button('← 책장으로'):
        goto('책장'); st.rerun()
    cover,info=st.columns([1,4])
    source=db.cover_source(book)
    if source: cover.image(source,width='stretch')
    with info:
        st.header(book['title'])
        st.write(book['author'] or '저자 미상')
        st.caption(f"{book['category'] or '미분류'} · {book['status']} · 완독 {book['read_count'] or 0}회")
        current=book['current_page'] or 0; total=book['pages'] or 0
        st.progress(min(max(current/total,0),1) if total else 0,text=f'{current} / {total or "미정"}쪽')
    management(conn,book)
    forms(conn,book,goto)
    st.subheader('독서 노트')
    rows=db.list_activities(conn,book_id)
    choice=st.radio('기록 보기',['전체','인용구·메모','사진','진도'],horizontal=True,key='detail_filter')
    if choice!='전체': rows=rows[rows['kind'].isin({'인용구·메모':[0,2],'사진':[1],'진도':[4]}[choice])]
    cards(conn,rows)
    from lib.record_ui import trash
    trash(conn,book_id)


def timeline(conn,goto):
    st.header('타임라인')
    search=st.text_input('기록 검색 · 인용문, 메모, 책 제목, 저자',key='timeline_search')
    choice=st.radio('기록 종류',['전체','인용구·메모','사진','진도'],horizontal=True,key='timeline_kind')
    import pandas as pd
    rows=db.database.read_frame(conn, f"SELECT a.*,b.title,b.author FROM activities a JOIN books b ON b.id=a.book_id WHERE a.deleted_at IS NULL ORDER BY a.date DESC,a.{db.database.activity_position(conn)} DESC")
    if search:
        mask=rows[['title','author','quote','text']].fillna('').apply(lambda col:col.str.contains(search,case=False,regex=False)).any(axis=1)
        rows=rows[mask]
    if choice!='전체': rows=rows[rows['kind'].isin({'인용구·메모':[0,2],'사진':[1],'진도':[4]}[choice])]
    if search:
        st.caption(f'검색 결과 {len(rows):,}건 · 책 제목·저자·인용문·메모에서 찾았습니다.')
    cards(conn,rows,goto,prefix='timeline')
