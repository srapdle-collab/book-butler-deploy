"""북스윙의 따뜻한 서가/종이 느낌을 웹 화면에 적용한다."""
import streamlit as st


def apply():
    st.markdown('''<style>
    .stApp {background:#f6f0e6;color:#382c25;}
    [data-testid="stSidebar"] {background:linear-gradient(150deg,#ead8bb,#f3e7d4);}
    [data-testid="stMainBlockContainer"] {max-width:1140px;padding-top:2rem;}
    h1,h2,h3 {color:#654526;letter-spacing:-.035em;}
    [data-testid="stVerticalBlockBorderWrapper"]>div {background:#fffdf7;border-color:#d8c6ad;border-radius:12px;}
    [data-testid="stMetric"] {background:#ead8bb;padding:14px;border-radius:12px;}
    [data-testid="stExpander"] {background:#fdf8ef;border-color:#cbb69a;}
    .stButton>button,.stDownloadButton>button,.stLinkButton>a {border-color:#c6ae90;border-radius:9px;}
    .stButton>button:hover {border-color:#92663e;color:#79502c;}
    [data-testid="stImage"] img {border-radius:3px;box-shadow:0 4px 10px #382c2520;}
    [class*="st-key-note_card_"] {background:#fffdf7;border-left:3px solid #cfad92;border-bottom:1px dashed #d8c6ad;padding:.7rem .25rem .9rem;margin-bottom:.1rem;}
    [class*="st-key-note_card_"] [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;}
    [class*="st-key-note_card_"] [data-testid="stColumn"] {min-width:0!important;}
    .record-page {font-size:2.05rem;font-weight:800;line-height:1;color:#765033;letter-spacing:-.08em;padding-top:.1rem;text-align:center;word-break:keep-all;}
    .st-key-reading_toolbar [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;}
    .st-key-reading_toolbar [data-testid="stColumn"] {min-width:0!important;flex:1!important;}
    .st-key-reading_toolbar button {padding:.35rem;font-size:.9rem;}
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
    [class*="_cover_card_"] [data-testid="stImage"] img {width:100%!important;height:100%!important;max-width:none!important;object-fit:cover;}
    .shelf-cover-placeholder {aspect-ratio:2/3;background:linear-gradient(145deg,#e9d8ba,#c9ad87);border:1px solid #b99065;border-radius:4px;box-shadow:0 4px 10px #382c2520;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem;padding:.75rem;text-align:center;color:#5f422b;font-weight:700;line-height:1.3;}
    .shelf-cover-placeholder span {font-size:.88rem;word-break:keep-all;}
    @media(max-width:640px) {
      [data-testid="stMainBlockContainer"] {padding:1.25rem .85rem;}
      [data-testid="stMetric"] {padding:8px;}
    }
    </style>''',unsafe_allow_html=True)
