"""소그룹 화면. 개인 원본 기록은 명시적으로 고른 스냅샷만 피드에 남긴다."""
from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from lib import database, groups
from lib.auth import AuthUser

KST = ZoneInfo("Asia/Seoul")


def _today() -> str:
    return datetime.now(KST).date().isoformat()


def _attachment_choices(conn, user_id: str):
    rows = database.execute(
        conn,
        """SELECT a.id, a.kind, a.quote, a.text, a.photo, a.page, b.title
           FROM activities a JOIN books b ON b.id = a.book_id
           WHERE a.owner_id = ? AND a.deleted_at IS NULL AND a.kind IN (1, 2)
           ORDER BY a.date DESC LIMIT 80""",
        (user_id,),
    ).fetchall()
    choices = {"첨부하지 않기": None}
    for row in rows:
        item = dict(row)
        if item["kind"] == 1:
            label = f"사진 · {item['title']} {item['page'] or 0}쪽"
        else:
            snippet = (item["quote"] or "").replace("\n", " ")[:42]
            label = f"인용 · {item['title']} {item['page'] or 0}쪽 · {snippet}"
        choices[label] = item
    return choices


def _snapshot(item):
    if not item:
        return None
    return {
        "kind": item["kind"],
        "body": item["quote"] or item["text"],
        "book_title": item["title"],
        "page": item["page"],
        "photo": item["photo"],
    }


def _invite_url(token: str) -> str:
    base = os.environ.get("READDAM_APP_URL", "").strip().rstrip("/")
    return f"{base}/?invite={token}" if base else f"?invite={token}"


def _render_create(conn, user: AuthUser):
    with st.expander("소그룹 만들기"):
        with st.form("create_group"):
            name = st.text_input("소그룹 이름", placeholder="예: 월요 읽담")
            submitted = st.form_submit_button("만들기")
        if submitted:
            try:
                group = groups.create_group(conn, user, name)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.selected_group_id = group["id"]
                st.success(f"'{group['name']}' 소그룹을 만들었습니다.")
                st.rerun()


def _render_join(conn, user: AuthUser):
    token = str(st.query_params.get("invite", "")).strip()
    if not token:
        return
    if st.session_state.get("handled_invite") == token:
        return
    st.info("소그룹 초대 링크입니다.")
    if st.button("이 소그룹 참여하기", key="join_group_invite", type="primary"):
        try:
            group_id = groups.join_invite(conn, token, user.id)
        except groups.GroupAccessError as exc:
            st.warning(str(exc))
        else:
            st.session_state.handled_invite = token
            st.session_state.selected_group_id = group_id
            st.query_params.clear()
            st.success("소그룹에 참여했습니다.")
            st.rerun()


def _render_checkin(conn, group_id: str, user_id: str):
    with st.expander("오늘 인증 남기기", expanded=True):
        options = _attachment_choices(conn, user_id)
        labels = list(options)
        with st.form(f"checkin_{group_id}"):
            is_read = st.checkbox("오늘 읽었어요", value=True)
            note = st.text_area("한줄소감", max_chars=300, placeholder="오늘 읽은 것 또는 마음에 남은 한 문장을 적어보세요.")
            picked = st.selectbox("내 인용구/사진 첨부 (선택)", labels)
            submitted = st.form_submit_button("인증 저장", type="primary")
        if submitted:
            try:
                groups.save_checkin(
                    conn, group_id, user_id, is_read=is_read, note=note,
                    attachment=_snapshot(options[picked]), checked_on=_today(),
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("오늘의 인증을 저장했습니다.")
                st.rerun()


def _render_feed(conn, group_id: str, user_id: str):
    st.subheader("오늘의 인증")
    feed = groups.group_feed(conn, group_id, user_id, checked_on=_today())
    if not feed:
        st.info("아직 오늘의 인증이 없습니다. 첫 기록을 남겨보세요.")
        return
    for item in feed:
        with st.container(border=True):
            st.markdown(f"**{item['display_name']}** · {'📖 읽었어요' if item['is_read'] else '✍️ 소감'}")
            if item["note"]:
                st.write(item["note"])
            if item["attachment_body"]:
                st.caption(
                    f"{item['attachment_book_title'] or '책'} · {item['attachment_page'] or 0}쪽"
                )
                st.markdown(item["attachment_body"])
            if item["attachment_photo"]:
                from lib import db
                source = db.activity_photo_source(item["attachment_photo"])
                if source:
                    st.image(source, width=280)
            reacted = bool(item["reacted"])
            if st.button(
                f"{'♥' if reacted else '♡'} 좋아요 {item['reaction_count']}",
                key=f"reaction_{item['id']}",
            ):
                groups.toggle_reaction(conn, item["id"], user_id)
                st.rerun()
            comments = groups.list_comments(conn, item["id"], user_id)
            for comment in comments:
                st.caption(f"{comment['display_name']}: {comment['body']}")
            with st.form(f"comment_{item['id']}", clear_on_submit=True):
                body = st.text_input("댓글", key=f"comment_body_{item['id']}")
                if st.form_submit_button("댓글 남기기"):
                    try:
                        groups.add_comment(conn, item["id"], user_id, body)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.rerun()


def render(conn, user: AuthUser):
    """현재 계정이 속한 그룹만 보여준다."""
    groups.ensure_profile(conn, user)
    st.header("👥 소그룹")
    _render_join(conn, user)
    _render_create(conn, user)
    my_groups = groups.list_groups(conn, user.id)
    if not my_groups:
        st.info("아직 소그룹이 없습니다. 새 그룹을 만들거나 초대 링크로 참여하세요.")
        return
    ids = [group["id"] for group in my_groups]
    selected = st.session_state.get("selected_group_id")
    if selected not in ids:
        selected = ids[0]
        st.session_state.selected_group_id = selected
    selected_index = ids.index(selected)
    group_id = st.selectbox(
        "내 소그룹", ids, index=selected_index,
        format_func=lambda value: next(group["name"] for group in my_groups if group["id"] == value),
    )
    st.session_state.selected_group_id = group_id
    current = next(group for group in my_groups if group["id"] == group_id)
    if current["role"] == "owner":
        invite_key = f"group_invite_{group_id}"
        if st.button("새 초대 링크 만들기", key=f"create_invite_{group_id}"):
            st.session_state[invite_key] = groups.create_invite(conn, group_id, user.id)
        token = st.session_state.get(invite_key)
        if token:
            st.caption("초대 링크는 한 번만 사용할 수 있습니다.")
            st.code(_invite_url(token), language=None)
    _render_checkin(conn, group_id, user.id)
    _render_feed(conn, group_id, user.id)
