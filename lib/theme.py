"""북스윙의 따뜻한 서가/종이 느낌을 웹 화면에 적용한다."""
import streamlit as st


def apply():
    st.markdown('''<style>
    :root {
      --ink:#34281f; --ink-soft:#7c6c58;
      --paper:#fffdf8; --paper-line:#e4d4b8;
      --accent:#8b5a2f; --accent-strong:#6e4522; --accent-tint:#f1e3cd;
      --shadow:0 10px 26px -14px rgba(52,40,31,.35);
      --shadow-sm:0 4px 12px -6px rgba(52,40,31,.28);
    }
    .stApp {background:linear-gradient(175deg,#f9f4ea 0%,#f3e9d5 60%,#eee2c9 100%);color:var(--ink);}
    [data-testid="stSidebar"] {background:linear-gradient(165deg,#ecd9b8,#f4e8d2);border-right:1px solid var(--paper-line);}
    [data-testid="stMainBlockContainer"] {max-width:1140px;padding-top:2.25rem;}
    h1,h2,h3 {color:var(--accent-strong);letter-spacing:-.03em;font-weight:800;}
    h1 {font-size:2rem;}
    h2 {font-size:1.5rem;line-height:1.4;}
    .detail-title {font-family:inherit;font-size:1.4rem;font-weight:800;line-height:1.4;
      color:var(--accent-strong);letter-spacing:-.02em;margin:.1rem 0 .2rem;word-break:keep-all;}
    .detail-subtitle {font-size:.95rem;font-weight:500;color:var(--ink-soft);line-height:1.4;
      margin:0 0 .5rem;word-break:keep-all;}
    p,label,.stCaption,[data-testid="stCaptionContainer"] {color:var(--ink);}
    [data-testid="stCaptionContainer"] {color:var(--ink-soft)!important;}

    /* 카드 · 표면 (Streamlit 1.50: border=True 컨테이너는 key 클래스가 실제 카드 div에 바로 붙는다) */
    [data-testid="stMetric"] {background:var(--accent-tint);padding:16px;border-radius:14px;border:1px solid var(--paper-line);}
    [data-testid="stExpander"] {background:var(--paper);border-color:var(--paper-line);border-radius:14px;overflow:hidden;}

    /* 입력 필드 */
    .stTextInput input,.stNumberInput input,.stTextArea textarea,
    [data-baseweb="select"]>div,[data-baseweb="base-input"] {
      background:#fffaf0!important;border-radius:10px!important;border:1px solid var(--paper-line)!important;
    }
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus {
      border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-tint)!important;
    }

    /* 버튼 위계: primary=꽉 찬 강조, secondary=아웃라인 */
    .stButton>button,.stDownloadButton>button,.stLinkButton>a {
      border-radius:10px;border:1px solid var(--paper-line);background:#fffaf0;color:var(--ink);
      transition:all .15s ease;font-weight:600;
    }
    .stButton>button:hover,.stDownloadButton>button:hover {border-color:var(--accent);color:var(--accent-strong);background:var(--accent-tint);}
    .stButton>button[kind="primary"] {
      background:var(--accent);border-color:var(--accent);color:#fff9ee;box-shadow:var(--shadow-sm);
    }
    .stButton>button[kind="primary"]:hover {background:var(--accent-strong);border-color:var(--accent-strong);color:#fff9ee;transform:translateY(-1px);}

    [data-testid="stImage"] img {border-radius:6px;box-shadow:var(--shadow-sm);}

    /* 책 상세 표지: 원본 이미지 크기와 무관하게 항상 2:3 비율 유지, 깨지지 않게 */
    div.st-key-detail_cover {max-width:200px;margin:0 auto 1rem;}
    div.st-key-detail_cover [data-testid="stImage"] {aspect-ratio:2/3;overflow:hidden;border-radius:8px;}
    div.st-key-detail_cover [data-testid="stImage"] img {
      width:100%!important;height:100%!important;max-width:none!important;object-fit:cover;
    }
    @media(max-width:640px) {
      div.st-key-detail_cover {max-width:150px;}
    }

    /* 로그인/비밀번호 관문 카드 */
    div.st-key-auth_card {
      margin-top:min(9vh,4rem)!important;background:var(--paper)!important;
      padding:2.4rem 2.1rem 2.1rem!important;border-radius:16px!important;
      border:1px solid var(--paper-line)!important;box-shadow:var(--shadow)!important;
    }
    .st-key-auth_card h1 {text-align:center!important;margin-bottom:.15rem!important;}
    .st-key-auth_card [data-testid="stCaptionContainer"] {text-align:center!important;display:block!important;margin-bottom:1.4rem!important;}
    .auth-badge {font-size:2.3rem;text-align:center;margin-bottom:.35rem;filter:drop-shadow(0 3px 6px rgba(52,40,31,.25));}

    /* 독서 노트 카드 */
    [class*="st-key-note_card_"] {background:var(--paper);border-left:3px solid var(--accent);border-bottom:1px dashed var(--paper-line);border-radius:0 10px 10px 0;padding:.75rem .9rem .95rem;margin-bottom:.35rem;}
    [class*="st-key-note_card_"] [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;}
    [class*="st-key-note_card_"] [data-testid="stColumn"] {min-width:0!important;}
    .record-page {font-size:2.05rem;font-weight:800;line-height:1;color:var(--accent-strong);letter-spacing:-.08em;padding-top:.1rem;text-align:center;word-break:keep-all;}
    .st-key-reading_toolbar [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;}
    .st-key-reading_toolbar [data-testid="stColumn"] {min-width:0!important;flex:1!important;}
    .st-key-reading_toolbar button {padding:.35rem;font-size:.9rem;}

    /* 책장 표지 격자 */
    [class*="_cover_grid_"] [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;}
    [class*="_cover_grid_"] [data-testid="stColumn"] {min-width:0!important;flex:1!important;}
    [class*="_cover_card_"] {position:relative;}
    [class*="_cover_card_"]>[data-testid="stElementContainer"]:last-child {position:absolute;inset:0;z-index:2;height:100%;}
    [class*="_cover_card_"]>[data-testid="stElementContainer"]:last-child .stButton,
    [class*="_cover_card_"]>[data-testid="stElementContainer"]:last-child .stButton>div,
    [class*="_cover_card_"]>[data-testid="stElementContainer"]:last-child [data-testid="stTooltipIcon"],
    [class*="_cover_card_"]>[data-testid="stElementContainer"]:last-child [data-testid="stTooltipHoverTarget"] {height:100%!important;width:100%;align-items:stretch;}
    [class*="_cover_card_"] [data-testid="stButton"] button {height:100%!important;width:100%;opacity:0;padding:0;}
    [class*="_cover_card_"]>[data-testid="stElementContainer"]:first-child,
    [class*="_cover_card_"] [data-testid="stFullScreenFrame"],
    [class*="_cover_card_"] [data-testid="stFullScreenFrame"]>div {width:100%!important;}
    [class*="_cover_card_"] [data-testid="stImage"] {width:100%!important;aspect-ratio:2/3;overflow:hidden;}
    [class*="_cover_card_"] [data-testid="stImageContainer"] {width:100%!important;height:100%!important;}
    [class*="_cover_card_"] [data-testid="stImage"] img {width:100%!important;height:100%!important;max-width:none!important;object-fit:cover;border-radius:6px;transition:transform .2s ease;}
    [class*="_cover_card_"]:hover [data-testid="stImage"] img {transform:scale(1.02);}
    .shelf-cover-placeholder {aspect-ratio:2/3;background:linear-gradient(150deg,#ecdab9,#cfad7f);border:1px solid #b99065;border-radius:6px;box-shadow:var(--shadow-sm);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem;padding:.75rem;text-align:center;color:#5f422b;font-weight:700;line-height:1.3;}
    .shelf-cover-placeholder span {font-size:.88rem;word-break:keep-all;}

    @media(max-width:640px) {
      [data-testid="stMainBlockContainer"] {padding:1.25rem .85rem;}
      [data-testid="stMetric"] {padding:10px;}
      div.st-key-auth_card {padding:1.6rem 1.15rem 1.4rem!important;}
    }
    </style>''',unsafe_allow_html=True)
