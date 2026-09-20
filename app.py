# 도서비서 (Book Butler) - 1단계 Streamlit 앱

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from lib import db, streak

st.set_page_config(page_title="도서비서", page_icon="📚", layout="wide")

NAV_ITEMS = ["책장", "통계", "스트릭 / 뱃지"]

if "view" not in st.session_state:
    st.session_state.view = "책장"
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "shelf_page" not in st.session_state:
    st.session_state.shelf_page = 1


def goto(view: str, book_id: str | None = None) -> None:
    st.session_state.view = view
    st.session_state.selected_book_id = book_id


def fmt_date(ts: int | None) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def status_badge(status: str) -> str:
    return {"읽는 중": "📖 읽는 중", "완독": "✅ 완독", "위시리스트": "🔖 위시리스트"}.get(status, status)


# ---------------------------------------------------------------- 책장 ----

def render_shelf(conn) -> None:
    st.header("📚 책장")

    categories = ["전체"] + db.list_categories(conn)
    statuses = ["전체", "읽는 중", "완독", "위시리스트"]

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
            cover = db.photo_path(book["cover_photo"])
            if cover:
                st.image(str(cover), width="stretch")
            else:
                st.markdown("*(표지 없음)*")
            st.markdown(f"**{book['title']}**")
            st.caption(f"{book['author'] or '-'} · {status_badge(book['status'])}")
            if st.button("상세보기", key=f"detail_{book['id']}", width="stretch"):
                goto("책 상세", book["id"])
                st.rerun()


# ------------------------------------------------------------ 책 상세 ----

def render_detail(conn, book_id: str | None) -> None:
    if not book_id:
        st.info("책장에서 책을 선택해주세요.")
        return

    book = db.get_book(conn, book_id)
    if book is None:
        st.error("책 정보를 찾을 수 없습니다.")
        return

    if st.button("← 책장으로"):
        goto("책장")
        st.rerun()

    col_cover, col_info = st.columns([1, 3])
    with col_cover:
        cover = db.photo_path(book["cover_photo"])
        if cover:
            st.image(str(cover), width="stretch")
    with col_info:
        st.header(book["title"])
        if book["subtitle"]:
            st.caption(book["subtitle"])
        st.write(
            f"**저자** {book['author'] or '-'}  ·  **역자** {book['translator'] or '-'}  ·  "
            f"**출판사** {book['publisher'] or '-'}"
        )
        st.write(f"**카테고리** {book['category'] or '-'}  ·  **ISBN** {book['isbn'] or '-'}")
        st.write(f"**상태** {status_badge(book['status'])}  ·  **완독 횟수** {book['read_count']}회")
        st.write(f"**별점** {'★' * (book['rating'] or 0)}{'☆' * (5 - (book['rating'] or 0))}")

        pages = book["pages"] or 0
        current = book["current_page"] or 0
        ratio = min(current / pages, 1.0) if pages else 0.0
        st.progress(ratio, text=f"{current} / {pages}쪽 ({ratio * 100:.0f}%)")
        st.caption(f"시작일 {fmt_date(book['start_date'])} · 완독일 {fmt_date(book['finish_date'])}")

    activities = db.list_activities(conn, book_id)

    tab_quotes, tab_photos, tab_timeline = st.tabs(
        [f"인용구·메모 ({len(activities[activities['kind'].isin(['quote', 'quote_with_note'])])})",
         f"사진 ({len(activities[activities['kind'] == 'photo'])})",
         f"전체 기록 ({len(activities)})"]
    )

    with tab_quotes:
        quotes = activities[activities["kind"].isin(["quote", "quote_with_note"])]
        if quotes.empty:
            st.caption("인용구·메모가 없습니다.")
        for _, row in quotes.sort_values("date").iterrows():
            page_label = f" (p.{row['page']})" if row["page"] else ""
            st.markdown(f"> {row['quote'] or ''}{page_label}")
            if row["text"]:
                st.write(row["text"])
            st.caption(fmt_date(row["date"]))
            st.divider()

    with tab_photos:
        photos = activities[activities["kind"] == "photo"]
        if photos.empty:
            st.caption("사진 기록이 없습니다.")
        photo_cols = st.columns(3)
        for i, (_, row) in enumerate(photos.sort_values("date").iterrows()):
            path = db.photo_path(row["photo"].replace("photos/", "") if row["photo"] else None)
            with photo_cols[i % 3]:
                if path:
                    st.image(str(path), width="stretch", caption=fmt_date(row["date"]))

    with tab_timeline:
        if activities.empty:
            st.caption("기록이 없습니다.")
        else:
            view = activities.sort_values("date", ascending=False)[
                ["date", "kind", "page", "text", "quote"]
            ].copy()
            view["date"] = view["date"].apply(fmt_date)
            st.dataframe(view, width="stretch", hide_index=True)


# ------------------------------------------------------------- 통계 ----

def render_stats(conn) -> None:
    st.header("📊 통계")

    activities = db.all_activities(conn)
    activities["dt"] = pd.to_datetime(activities["date"], unit="s")

    granularity = st.radio("기준", ["일별", "월별"], horizontal=True, key="stats_granularity")
    freq = "D" if granularity == "일별" else "MS"

    progress = activities[activities["kind"] == "progress_log"].copy()
    progress["pages_read"] = progress["pages_read"].clip(lower=0)
    progress["minutes_read"] = progress["minutes_read"].clip(lower=0)

    pages_series = progress.set_index("dt")["pages_read"].resample(freq).sum()
    minutes_series = progress.set_index("dt")["minutes_read"].resample(freq).sum()

    finishes = activities[activities["kind"] == "finish"].copy()
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

if st.session_state.view == "책장":
    render_shelf(conn)
elif st.session_state.view == "책 상세":
    render_detail(conn, st.session_state.selected_book_id)
elif st.session_state.view == "통계":
    render_stats(conn)
elif st.session_state.view == "스트릭 / 뱃지":
    render_badges(conn)
