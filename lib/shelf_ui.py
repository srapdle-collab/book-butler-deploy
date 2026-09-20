import streamlit as st
from lib import db


def render(conn,goto,add_book):
    st.header('📚 나의 책장')
    counts={r['status']:r['n'] for r in conn.execute('SELECT status,COUNT(*) n FROM books GROUP BY status')}
    total=sum(counts.values()); wishes=counts.get('위시리스트',0)
    for col,label,value in zip(st.columns(3),['책장','위시리스트','읽고 있는 책'],[total-wishes,wishes,counts.get('읽는 중',0)]):
        col.metric(label,f'{value:,}')
    reading=db.list_books(conn,status='읽는 중')
    if not reading.empty:
        st.subheader('이어서 읽기')
        cols=st.columns(3)
        for i,(_,book) in enumerate(reading.head(6).iterrows()):
            with cols[i%3],st.container(border=True):
                source=db.cover_source(book)
                if source: st.image(source,width=85)
                if st.button(book['title'],key=f"resume_{book['id']}",width='stretch'):
                    goto('책 상세',book['id']);st.rerun()
                current=book['current_page'] or 0;total_pages=book['pages'] or 0
                st.progress(min(max(current/total_pages,0),1) if total_pages else 0,text=f'{current}/{total_pages or "미정"}쪽')
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
    books=db.list_books(conn,category=None if category=='전체' else category,status=None if status=='전체' else status,search=search or None)
    if status=='전체': books=books[books['status']!='위시리스트']
    st.caption(f'검색 결과 {len(books):,}권 · 전체 등록 {total:,}권 · 최근 기록순 (카테고리별 묶음)')
    page_count=max(1,(len(books)+23)//24)
    if st.session_state.get('shelf_page_input',1)>page_count: st.session_state.shelf_page_input=1
    page=st.number_input('책장 페이지',min_value=1,max_value=page_count,step=1,key='shelf_page_input')
    visible=books.iloc[(page-1)*24:page*24].copy()
    visible['category']=visible['category'].fillna('미분류')
    if visible.empty: st.info('조건에 맞는 책이 없습니다.')
    for category,group in visible.groupby('category',sort=False):
        st.subheader(category)
        columns=st.columns(3)
        for i,(_,book) in enumerate(group.iterrows()):
            with columns[i%3],st.container(border=True):
                source=db.cover_source(book)
                if source: st.image(source,width=150)
                else: st.caption('📖 표지 없음')
                st.markdown(f"**{book['title']}**")
                st.caption(f"{book['author'] or '저자 미상'} · {book['status']}")
                if st.button('상세보기',key=f"detail_{book['id']}",width='stretch'):
                    goto('책 상세',book['id']);st.rerun()
    with st.expander('➕ 새 책 추가'): add_book(conn)
