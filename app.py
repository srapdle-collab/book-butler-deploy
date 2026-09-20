# 도서비서 (Book Butler) - 1단계 Streamlit 앱

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from lib import db, library_api, streak

load_dotenv()

st.set_page_config(page_title="도서비서", page_icon="📚", layout="wide")

NAV_ITEMS = ["책장", "타임라인", "한 장의 추억", "통계", "스트릭 / 뱃지"]

if "view" not in st.session_state:
    st.session_state.view = "책장"
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "shelf_page" not in st.session_state:
    st.session_state.shelf_page = 1
if "add_book_candidates" not in st.session_state:
    st.session_state.add_book_candidates = []


def goto(view: str, book_id: str | None = None) -> None:
    st.session_state.record_edit_id = None
    st.session_state.record_mode = None
    st.session_state.view = view
    st.session_state.selected_book_id = book_id


def fmt_date(ts: int | None) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def status_badge(status: str) -> str:
    return {
        "읽는 중": "📖 읽는 중",
        "완독": "✅ 완독",
        "읽기 중단": "⏸️ 읽기 중단",
        "위시리스트": "🔖 위시리스트",
    }.get(status, status)


# ---------------------------------------------------------------- 책장 ----

def render_shelf(conn) -> None:
    st.header("📚 책장")

    categories = ["전체"] + db.list_categories(conn)
    statuses = ["전체", "읽는 중", "완독", "읽기 중단", "위시리스트"]

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        category = st.selectbox("카테고리", categories, key="shelf_category")
    with col2:
        status = st.selectbox("상태", statuses, key="shelf_status")
    with col3:
        search = st.text_input("제목/저자 검색", "", key="shelf_search")

    books = db.list_books(
        conn,
        category=None if category == "전체" else category,
        status=None if status == "전체" else status,
        search=search or None,
    )
    st.caption(f"{len(books)}권 (전체 705권)")

    page_size = 24
    total_pages = max(1, (len(books) - 1) // page_size + 1)
    st.session_state.shelf_page = min(st.session_state.shelf_page, total_pages)
    page = st.number_input(
        "페이지",
        min_value=1,
        max_value=total_pages,
        value=st.session_state.shelf_page,
        key="shelf_page_input",
    )
    st.session_state.shelf_page = page

    start = (page - 1) * page_size
    page_books = books.iloc[start : start + page_size]

    cols = st.columns(4)
    for i, (_, book) in enumerate(page_books.iterrows()):
        with cols[i % 4]:
            cover = db.cover_source(book)
            if cover:
                st.image(cover, width="stretch")
            else:
                st.markdown("*(표지 없음)*")
            st.markdown(f"**{book['title']}**")
            st.caption(f"{book['author'] or '-'} · {status_badge(book['status'])}")
            if st.button("상세보기", key=f"detail_{book['id']}", width="stretch"):
                goto("책 상세", book["id"])
                st.rerun()

    st.divider()
    with st.expander("➕ 새 책 추가"):
        render_add_book_form(conn)


def render_add_book_form(conn) -> None:
    auth_key = os.environ.get("DATA4LIBRARY_AUTH_KEY", "").strip()

    query = st.text_input("제목으로 검색 (도서관정보나루)", key="add_book_query")
    if st.button("검색", key="add_book_search_btn"):
        if not auth_key:
            st.session_state.add_book_candidates = []
            st.warning(
                "DATA4LIBRARY_AUTH_KEY가 설정되지 않았습니다 (.env 확인). "
                "아래 수동 입력 폼을 사용해주세요."
            )
        else:
            try:
                results = library_api.search_books(query, auth_key)
            except library_api.LibraryAPIError as exc:
                st.session_state.add_book_candidates = []
                st.warning(f"검색 실패: {exc}\n아래 수동 입력 폼을 사용해주세요.")
            else:
                st.session_state.add_book_candidates = results
                if not results:
                    st.info("검색 결과가 없습니다. 아래 수동 입력 폼을 사용해주세요.")

    candidates = st.session_state.get("add_book_candidates") or []
    selected: dict | None = None
    if candidates:
        st.caption(f"검색 결과 {len(candidates)}건 중 하나를 선택하세요")
        labels = [
            f"{c['title']} · {c['author'] or '저자 미상'} ({c['publisher'] or '출판사 미상'}, "
            f"ISBN {c['isbn'] or '-'})"
            for c in candidates
        ]
        pick = st.radio(
            "검색 후보", range(len(candidates)), format_func=lambda i: labels[i],
            key="add_book_pick",
        )
        selected = candidates[pick]
        cover_col, _ = st.columns([1, 4])
        with cover_col:
            if selected.get("cover_url"):
                st.image(selected["cover_url"], width="stretch")
            else:
                st.markdown("*(표지 없음 - 플레이스홀더)*")

    st.markdown("**세부 정보를 확인·수정한 뒤 저장하세요.**")
    categories = db.list_categories(conn)
    with st.form("add_book_form", clear_on_submit=True):
        title = st.text_input("제목", value=(selected or {}).get("title") or "")
        subtitle = st.text_input("부제", value=(selected or {}).get("subtitle") or "")
        author = st.text_input("저자", value=(selected or {}).get("author") or "")
        translator = st.text_input("역자", value=(selected or {}).get("translator") or "")
        publisher = st.text_input("출판사", value=(selected or {}).get("publisher") or "")
        isbn = st.text_input("ISBN", value=(selected or {}).get("isbn") or "")
        category_options = ["(미지정)"] + categories + ["직접 입력"]
        category_choice = st.selectbox("카테고리", category_options)
        custom_category = st.text_input("카테고리 직접 입력", key="add_book_custom_category")
        pages = st.number_input("전체 쪽수", min_value=0, value=0, step=1)
        status = st.selectbox("상태", ["위시리스트", "읽는 중", "완독"])
        submitted = st.form_submit_button("책장에 추가")

    if submitted:
        if not title.strip():
            st.error("제목을 입력해주세요.")
        else:
            if category_choice == "직접 입력":
                final_category = custom_category.strip() or None
            elif category_choice == "(미지정)":
                final_category = None
            else:
                final_category = category_choice
            db.insert_book(
                conn,
                {
                    "title": title.strip(),
                    "subtitle": subtitle.strip() or None,
                    "author": author.strip() or None,
                    "translator": translator.strip() or None,
                    "publisher": publisher.strip() or None,
                    "isbn": isbn.strip() or None,
                    "category": final_category,
                    "pages": int(pages) or None,
                    "status": status,
                    "cover_url": (selected or {}).get("cover_url"),
                },
            )
            st.success(f"'{title.strip()}'을(를) 책장에 추가했습니다.")
            st.session_state.add_book_candidates = []
            st.rerun()


# ------------------------------------------------------------ 책 상세 ----

def render_detail(conn, book_id):
    from lib.notebook_ui import detail
    detail(conn, book_id, goto, render_book_management)


def render_book_management(conn, book) -> None:
    with st.expander("⋯ 책 관리 · 내보내기"):
        from lib.sharing_ui import export_menu
        export_menu(conn, book)
        with st.form("status_form"):
            statuses = ["읽는 중", "완독", "읽기 중단"]
            current_index = statuses.index(book["status"]) if book["status"] in statuses else 0
            status = st.selectbox(
                "책 상태", statuses, index=current_index, key="manage_status"
            )
            change_status = st.form_submit_button("상태 저장", key="save_status")
        if change_status:
            db.update_book_status(conn, book["id"], status)
            st.success("책 상태를 변경했습니다.")
            st.rerun()

        st.markdown("**책 정보 수정**")
        with st.form("book_info_form"):
            title = st.text_input("제목", value=book["title"] or "", key="edit_title")
            subtitle = st.text_input("부제", value=book["subtitle"] or "", key="edit_subtitle")
            author = st.text_input("저자", value=book["author"] or "", key="edit_author")
            translator = st.text_input("역자", value=book["translator"] or "", key="edit_translator")
            publisher = st.text_input("출판사", value=book["publisher"] or "", key="edit_publisher")
            isbn = st.text_input("ISBN", value=book["isbn"] or "", key="edit_isbn")
            category = st.text_input("카테고리", value=book["category"] or "", key="edit_category")
            pages = st.number_input(
                "전체 쪽수", min_value=0, value=int(book["pages"] or 0),
                step=1, key="edit_pages",
            )
            save_info = st.form_submit_button("책 정보 저장", key="save_book_info")
        if save_info:
            try:
                db.update_book_info(
                    conn,
                    book["id"],
                    {
                        "title": title,
                        "subtitle": subtitle,
                        "author": author,
                        "translator": translator,
                        "publisher": publisher,
                        "isbn": isbn,
                        "category": category,
                        "pages": int(pages),
                    },
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("책 정보를 수정했습니다.")
                st.rerun()


# ------------------------------------------------------------- 통계 ----

def render_stats(conn) -> None:
    st.header("📊 통계")

    activities = db.all_activities(conn)
    activities["dt"] = pd.to_datetime(activities["date"], unit="s")

    granularity = st.radio("기준", ["일별", "월별"], horizontal=True, key="stats_granularity")
    freq = "D" if granularity == "일별" else "MS"

    progress = activities[activities["kind"] == 4].copy()
    progress["pages_read"] = progress["pages_read"].clip(lower=0)
    progress["minutes_read"] = progress["minutes_read"].clip(lower=0)

    pages_series = progress.set_index("dt")["pages_read"].resample(freq).sum()
    minutes_series = progress.set_index("dt")["minutes_read"].resample(freq).sum()

    finishes = activities[activities["kind"] == 5].copy()
    finish_series = finishes.set_index("dt")["id"].resample(freq).count()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("읽은 쪽수")
        st.bar_chart(pages_series)
    with col2:
        st.subheader("읽은 시간 (분)")
        st.bar_chart(minutes_series)

    st.subheader("완독 권수")
    st.bar_chart(finish_series)

    st.caption(
        "읽은 쪽수·시간은 진행 로그(progress_log)에 기록된 세션 값을 합산한 것이며, "
        "음수로 기록된 값은 0으로 처리했습니다. 완독 권수는 완독 처리(finish) 활동 건수입니다."
    )


# ------------------------------------------------------- 스트릭 / 뱃지 ----

def render_badges(conn) -> None:
    st.header("🔥 스트릭 / 뱃지")

    activities = db.all_activities(conn)
    days = streak.reading_days(activities["date"].tolist())
    runs = streak.compute_streak_runs(days)
    longest = streak.longest_streak(runs)
    current = streak.current_streak(days)
    badges = streak.earned_badges(runs)

    col1, col2, col3 = st.columns(3)
    col1.metric("현재 연속 기록", f"{current}일")
    col2.metric("역대 최장 기록", f"{longest.length if longest else 0}일")
    col3.metric("기록이 있는 날", f"{len(days)}일")

    if longest:
        st.caption(f"최장 기록 구간: {longest.start} ~ {longest.end}")

    st.subheader("뱃지")
    thresholds = streak.BADGE_THRESHOLDS
    cols = st.columns(len(thresholds))
    earned_map = {b["threshold"]: b for b in badges}
    for col, threshold in zip(cols, thresholds):
        label = streak.BADGE_LABELS[threshold]
        badge = earned_map.get(threshold)
        with col:
            if badge:
                st.success(f"🏅 {label}\n\n{badge['earned_date']}")
            else:
                st.caption(f"🔒 {label}\n\n미달성")


# --------------------------------------------------------------- main ----

with st.sidebar:
    st.title("📚 도서비서")
    for label in NAV_ITEMS:
        active = st.session_state.view == label or (
            label == "책장" and st.session_state.view == "책 상세"
        )
        if st.button(label, width="stretch", type="primary" if active else "secondary"):
            goto(label)
            st.rerun()

conn = db.get_connection()
if st.session_state.get("notice"):
    st.toast(st.session_state.pop("notice"))

if st.session_state.view == "책장":
    render_shelf(conn)
elif st.session_state.view == "책 상세":
    render_detail(conn, st.session_state.selected_book_id)
elif st.session_state.view == "타임라인":
    from lib.notebook_ui import timeline
    timeline(conn, goto)
elif st.session_state.view == "한 장의 추억":
    from lib.sharing_ui import memory
    memory(conn, goto)
elif st.session_state.view == "통계":
    render_stats(conn)
elif st.session_state.view == "스트릭 / 뱃지":
    render_badges(conn)
