import html
import random
import streamlit as st
import streamlit.components.v1 as components
from lib import db, sharing


def copy_button(text):
    # 사용자 텍스트를 JS에 보간하지 않고 HTML 텍스트 노드로 이스케이프한다.
    components.html('''<style>body{margin:0;font-family:system-ui}button{font:inherit;background:#fff8ed;border:1px solid #bfa78b;border-radius:8px;padding:9px 16px;cursor:pointer}textarea{position:absolute;left:-9999px}</style>
<textarea id="copy-source" readonly>'''+html.escape(text)+'''</textarea>
<button id="copy-button">전체 복사하기</button> <span id="copy-result" role="status"></span>
<script>document.getElementById('copy-button').onclick=async()=>{
 const source=document.getElementById('copy-source'); const result=document.getElementById('copy-result');
 try {await navigator.clipboard.writeText(source.value);result.textContent='복사했습니다.';}
 catch(error){source.focus();source.select();try {if(!document.execCommand('copy')) throw Error();result.textContent='복사했습니다.';}
 catch(error){result.textContent='아래 미리보기에서 직접 선택해 복사해주세요.';}}
};</script>''',height=55)


def share_actions(subject,body,filename):
    copy_button(body)
    url=sharing.mailto(subject,body)
    if len(url)>2000:
        st.caption('본문이 길어 메일 앱에는 제목만 전달합니다. 전체 복사 후 붙여넣거나 텍스트 파일을 첨부해주세요.')
        url=sharing.mailto(subject,'')
    st.link_button('메일 앱 열기',url)
    st.download_button('텍스트 다운로드',body.encode('utf-8'),file_name=filename,mime='text/plain')


def export_menu(conn,book):
    st.markdown('**메일로 내보내기**')
    include=st.checkbox('내 생각과 단독 메모도 포함',value=False,key='export_notes')
    body=sharing.export_book(conn,book,include)
    st.session_state.export_preview=body
    st.text_area('내보낼 내용 미리보기',key='export_preview',height=220,disabled=True)
    share_actions(f"{book['title']} — {book['author'] or ''}",body,'book-quotes.txt')


def memory(conn,goto):
    st.header('한 장의 추억')
    rows=conn.execute("SELECT * FROM activities WHERE kind IN (0,2) AND quote IS NOT NULL AND TRIM(quote)!='' AND deleted_at IS NULL ORDER BY id").fetchall()
    if not rows:
        st.info('아직 인용구가 없습니다. 책에서 마음에 남는 문장을 기록해보세요.'); return
    by_id={r['id']:r for r in rows}
    current=st.session_state.get('memory_id')
    if current not in by_id: current=random.choice(list(by_id))
    if st.button('↻ 다른 추억',key='memory_next'):
        choices=[key for key in by_id if key!=current]
        if choices: current=random.choice(choices)
    st.session_state.memory_id=current
    row=by_id[current]; book=db.get_book(conn,row['book_id'])
    with st.container(border=True):
        st.markdown(row['quote'])
        st.caption(sharing.citation(book,row))
    if st.button('해당 책으로 이동',key='memory_book'):
        goto('책 상세',book['id']); st.rerun()
    body=sharing.quote_text(book,row)
    share_actions(book['title'],body,'reading-memory.txt')
    with st.expander('공유할 내용 미리보기'):
        st.text(body)
