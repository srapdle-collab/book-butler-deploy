"""Owner-only Streamlit control for the Today Library pull."""
from __future__ import annotations

import time

import streamlit as st

from lib import db, readdam_sync


def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        return value.strip() if isinstance(value, str) else ""
    except Exception:
        return ""


@st.fragment(run_every="5m")
def render(owner_id: str) -> None:
    st.caption("오늘의 서재 · 읽은 조각")
    manual = st.button("지금 동기화", key="readdam_sync_now")
    now = time.monotonic()
    last = st.session_state.get("readdam_last_sync_monotonic", 0)
    if manual or now - last >= 300:
        st.session_state.readdam_last_sync_monotonic = now
        conn = None
        try:
            conn = db.get_connection()
            result = readdam_sync.sync_once(
                conn, owner_id=owner_id,
                url=_secret("TODAY_LIBRARY_URL"),
                token=_secret("TODAY_LIBRARY_READDAM_KEY"),
                sites_gate_key=_secret("TODAY_LIBRARY_SITES_GATE_KEY"),
            )
        except Exception:
            result = {"state": "db_retry", "received": 0}
        finally:
            if conn is not None:
                conn.close()
        st.session_state.readdam_sync_result = result
    result = st.session_state.get("readdam_sync_result", {"state": "not_configured", "received": 0})
    message = {
        "ok": f"동기화 완료 · {result['received']}건 확인",
        "not_configured": "읽담 연결 설정이 필요합니다.",
        "connection_key": "연결 열쇠 확인",
        "db_retry": "읽담 저장 연결을 확인해주세요. 다음에 다시 시도합니다.",
        "retry": "오늘의 서재 연결을 확인해주세요. 다음에 다시 시도합니다.",
    }.get(result["state"], "다음에 다시 시도합니다.")
    st.caption(message)
