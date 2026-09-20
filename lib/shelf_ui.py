import streamlit as st
from lib import db


PAGE_SIZE = 24


def _cover_card(book, goto, prefix='shelf', show_progress=False):
    """표지 영역 전체를 누르면 책 상세로 이동하는 초밀평 카드."""
    with st.container(key=f"{prefix}_cover_card_{book['id']}"):
        source = db.cover_source(book)
        if source:
            st.image(source, width='stretch')
        else:
            st.markdown(
                f'<div class="shelf-cover-placeholder">📖<span>{book["title"]}</span></div>',
                unsafe_allow_html=True,
            )
            st.caption('표지 없음')
        if show_progress:
            current=book['current_page'] or 0
            total=book['pages'] or 0
            st.progress(min(max(current/total,0),1) if total else 0,text=f'{current}/{total or "미정"}쪽')
        if st.button(
            f"{book['title']} 상세 보기",
            key=f"{prefix}_cover_{book['id']}",
            help=f"{book['title']} 상세 보기",
            width='stretch',
        ):
            goto('책 상세', book['id'])
            st.rerun()


def _cover_grid(books, goto, prefix='shelf', show_progress=False):
    if books.empty:
        return
    # 좁은 화면에서도 4열을 유지해 한 줄씩 길게 늘어지는 일을 막는다.
    with st.container(key=f"{prefix}_cover_grid_{books.iloc[0]['id']}"):
        columns = st.columns(4, gap='small')
        for index, (_, book) in enumerate(books.iterrows()):
            with columns[index % 4]:
                _cover_card(book, goto, prefix=prefix, show_progress=show_progress)


def render(conn,goto,add_book):
    st.header('📚 나의 책장')
    counts={r['status']:r['n'] for r in conn.execute('SELECT status,COUNT(*) n FROM books GROUP BY status')}
    total=sum(counts.values()); wishes=counts.get('위시리스트',0)
    for col,label,value in zip(st.columns(3),['책장','위시리스트','읽고 있는 책'],[total-wishes,wishes,counts.get('읽는 중',0)]):
        col.metric(label,f'{value:,}')
    reading=db.list_books(conn,status='읽는 중')
    if not reading.empty:
        st.subheader('이어서 읽기')
        _cover_grid(reading.head(6), goto, prefix='resume', show_progress=True)
        if st.button(f'읽고 있는 책 전체보기 ({len(reading)}권)',key='reading_all'):
            st.session_state.shelf_status='읽는 중'
            st.session_state.shelf_category='전체'
            st.session_state.shelf_search=''
            st.session_state.shelf_page_input=1
            st.rerun()
    if st.button('책장 전체보기',key='shelf_all'):
        st.session_state.shelf_status='전체'; st.session_state.shelf_category='전체'
        st.session_state.shelf_search='';st.session_state.shelf_page_input=1;st.rerun()
    category_col,status_col,search_col=st.columns([2,2,3])
    categories=['전체']+db.list_categories(conn)
    if st.session_state.get('shelf_category','전체') not in categories: st.session_state.shelf_category='전체'
    category=category_col.selectbox('카테고리',categories,key='shelf_category')
    status=status_col.selectbox('상태',['전체','읽는 중','완독','미독','읽기 중단','위시리스트','확인 필요'],key='shelf_status')
    search=search_col.text_input('제목/저자 검색',key='shelf_search')
    selected_category=None if category=='전체' else category
    selected_status=None if status=='전체' else status
    exclude_status='위시리스트' if status=='전체' else None
    matched=db.count_books(conn,category=selected_category,status=selected_status,search=search or None,exclude_status=exclude_status)
    st.caption(f'검색 결과 {matched:,}권 · 전체 등록 {total:,}권 · 카테고리별 · 각 카테고리 최근 기록순')
    page_count=max(1,(matched+PAGE_SIZE-1)//PAGE_SIZE)
    if st.session_state.get('shelf_page_input',1)>page_count: st.session_state.shelf_page_input=1
    page=st.number_input('책장 페이지',min_value=1,max_value=page_count,step=1,key='shelf_page_input')
    visible=db.list_books(
        conn,
        category=selected_category,
        status=selected_status,
        search=search or None,
        exclude_status=exclude_status,
        limit=PAGE_SIZE,
        offset=(page-1)*PAGE_SIZE,
        group_by_category=selected_category is None,
    ).copy()
    visible['category']=visible['category'].fillna('미분류')
    if visible.empty: st.info('조건에 맞는 책이 없습니다.')
    for category,group in visible.groupby('category',sort=False):
        st.subheader(category)
        _cover_grid(group, goto)
    with st.expander('➕ 새 책 추가'): add_book(conn)
