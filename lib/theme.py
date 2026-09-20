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
    [class*="st-key-note_card_"] {background:#fffdf7;border-left:3px solid #cfad92;}
    .st-key-reading_toolbar [data-testid="stHorizontalBlock"] {flex-wrap:nowrap!important;}
    .st-key-reading_toolbar [data-testid="stColumn"] {min-width:0!important;flex:1!important;}
    .st-key-reading_toolbar button {padding:.35rem;font-size:.9rem;}
    @media(max-width:640px) {
      [data-testid="stMainBlockContainer"] {padding:1.25rem .85rem;}
      [data-testid="stMetric"] {padding:8px;}
    }
    </style>''',unsafe_allow_html=True)
