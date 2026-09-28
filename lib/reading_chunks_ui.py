"""책 상세 안의 읽은 조각 입력·수정 화면."""
from __future__ import annotations

from datetime import date
from collections import Counter
import uuid

import streamlit as st

from lib import reading_chunks as chunks


def _clear_form_state():
    for key in list(st.session_state):
        if key.startswith("chunk_input_"):
            st.session_state.pop(key, None)
    st.session_state.pop("chunk_duplicate", None)
    st.session_state.pop("chunk_submit_pending", None)


def _close_form(message: str | None = None):
    _clear_form_state()
    st.session_state.pop("chunk_edit_id", None)
    st.session_state.pop("chunk_draft_id", None)
    if message:
        st.session_state.notice = message


def _open_new():
    _clear_form_state()
    # 저장을 다시 눌러도 같은 조각을 가리키도록 입력 화면을 열 때 ID를 만든다.
    st.session_state.chunk_draft_id = str(uuid.uuid4())
    st.session_state.chunk_edit_id = None


def _open_edit(chunk_id: str):
    _clear_form_state()
    st.session_state.chunk_edit_id = chunk_id
    st.session_state.pop("chunk_draft_id", None)


def _request_save():
    # The callback runs before the new render. Use that render's live DB connection,
    # not the previous render's already closed connection.
    st.session_state.chunk_submit_pending = True


def _range_label(chunk) -> str:
    start, end = chunk["page_start"], chunk["page_end"]
    if start is not None and end is not None:
        return f"{start}쪽" if start == end else f"{start}–{end}쪽"
    return chunk["position_note"] or "위치 미입력"


def _tag_text(values) -> str:
    return ", ".join(values or [])


def _optional_page(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("페이지는 정수로 입력해주세요.") from exc


def _save(conn, payload, *, owner_id, allow_duplicate=False):
    try:
        chunks.save(conn, owner_id=owner_id, allow_duplicate=allow_duplicate, **payload)
    except chunks.DuplicateChunk as exc:
        st.session_state.chunk_duplicate = payload
        st.warning(f"{exc} 자동 병합하거나 삭제하지 않았습니다.")
    except ValueError as exc:
        st.error(str(exc))
    else:
        _close_form("읽은 조각을 저장했습니다.")


def _form(book, existing):
    is_edit = existing is not None
    default_date = date.fromisoformat(existing["read_date"]) if is_edit else date.fromisoformat(chunks.today_kst())
    current_page = int(book["current_page"] or 0)

    st.subheader("읽은 조각 수정" if is_edit else "읽은 조각 남기기")
    st.caption("기존 독서 노트·진도·통계와 별도로 보관됩니다. 원문 또는 내 메모 중 하나는 필수입니다.")
    with st.form("reading_chunk_form"):
        st.date_input("읽은 날짜", value=default_date, key="chunk_input_date")
        left, right = st.columns(2)
        start_default = str(existing["page_start"]) if is_edit and existing["page_start"] is not None else ""
        end_default = str(existing["page_end"]) if is_edit and existing["page_end"] is not None else ""
        left.text_input("시작 페이지 (선택)", value=start_default, key="chunk_input_page_start", placeholder=str(current_page))
        right.text_input("끝 페이지 (선택)", value=end_default, key="chunk_input_page_end", placeholder=str(current_page))
        st.text_input(
            "위치 메모 (쪽수 없을 때)", value=(existing["position_note"] if is_edit else "") or "",
            key="chunk_input_position_note", placeholder="예: 3장, 전자책 42%",
        )
        st.number_input(
            "읽은 시간 (분, 선택)", min_value=0,
            value=int(existing["minutes"] if is_edit and existing["minutes"] is not None else 0),
            step=1, key="chunk_input_minutes",
        )
        st.text_area(
            "읽은 조각 원문", value=(existing["original_text"] if is_edit else "") or "",
            key="chunk_input_original_text",
        )
        st.text_area(
            "내 메모", value=(existing["user_note"] if is_edit else "") or "", key="chunk_input_user_note",
        )
        st.text_input("태그 (쉼표로 구분)", value=_tag_text(existing["tags"]) if is_edit else "", key="chunk_input_tags")
        st.text_input(
            "예화 태그 (쉼표로 구분)", value=_tag_text(existing["illustration_tags"]) if is_edit else "",
            key="chunk_input_illustration_tags",
        )
        st.multiselect(
            "콘텐츠 타입", options=list(chunks.CONTENT_TYPES),
            default=existing["content_types"] if is_edit else [],
            format_func=lambda value: chunks.CONTENT_TYPES[value], key="chunk_input_content_types",
        )
        st.form_submit_button(
            "수정 저장" if is_edit else "조각 저장", type="primary", key="save_reading_chunk", on_click=_request_save,
        )
    st.button("취소", key="chunk_cancel", on_click=_close_form)


def _submit_form(conn, book, existing, *, owner_id):
    values = st.session_state
    try:
        payload = {
            "book_id": book["id"],
            "chunk_id": existing["chunk_id"] if existing else values.chunk_draft_id,
            "read_date": values.chunk_input_date.isoformat(),
            "page_start": _optional_page(values.chunk_input_page_start),
            "page_end": _optional_page(values.chunk_input_page_end),
            "position_note": values.chunk_input_position_note,
            "minutes": int(values.chunk_input_minutes) or None,
            "original_text": values.chunk_input_original_text,
            "user_note": values.chunk_input_user_note,
            "tags": chunks.parse_tags(values.chunk_input_tags),
            "illustration_tags": chunks.parse_tags(values.chunk_input_illustration_tags),
            "content_types": values.chunk_input_content_types,
        }
    except ValueError as exc:
        st.error(str(exc))
        return
    _save(conn, payload, owner_id=owner_id)


def render(conn, book, *, owner_id):
    """책 상세에서 호출한다. 조각은 이 책에만 연결해 표시한다."""
    st.subheader("읽은 조각")
    try:
        chunks._book_snapshot(conn, book["id"], owner_id)
    except ValueError as exc:
        st.error(str(exc))
        return
    if st.session_state.get("chunk_duplicate"):
        st.warning("같은 범위·내용의 조각이 있습니다. 자동 병합하지 않았습니다.")
        if st.button("그래도 저장", key="save_chunk_anyway", type="primary"):
            _save(conn, st.session_state.chunk_duplicate, owner_id=owner_id, allow_duplicate=True)
        if st.button("중복 조각 저장 취소", key="cancel_duplicate_chunk"):
            st.session_state.pop("chunk_duplicate", None)
            st.rerun()

    edit_id = st.session_state.get("chunk_edit_id")
    if st.session_state.get("chunk_draft_id") or edit_id:
        existing = chunks.get(conn, edit_id, owner_id=owner_id) if edit_id else None
        if edit_id and (existing is None or existing["book_id"] != book["id"]):
            st.error("수정할 조각과 현재 책/사용자가 일치하지 않습니다.")
            return
        if st.session_state.pop("chunk_submit_pending", False):
            _submit_form(conn, book, existing, owner_id=owner_id)
        if st.session_state.get("chunk_draft_id") or st.session_state.get("chunk_edit_id"):
            _form(book, existing)
            return

    st.button("✦ 읽은 조각 남기기", key="open_reading_chunk", width="stretch", on_click=_open_new)

    tag = st.text_input("조각 태그 필터", key="chunk_tag_filter", placeholder="태그 하나를 입력하세요")
    rows = chunks.list_for_book(conn, book["id"], owner_id=owner_id, tag=tag or None)
    duplicate_counts = Counter((item["read_date"], item["page_start"], item["page_end"], item["content_hash"])
                               for item in chunks.list_for_book(conn, book["id"], owner_id=owner_id))
    if not rows:
        st.caption("아직 저장한 읽은 조각이 없습니다.")
        return
    for row in rows:
        with st.container(border=True, key=f"chunk_card_{row['chunk_id']}"):
            source = "오늘의 서재" if row["source_app"] == "today-library" else "읽담"
            st.caption(f"{row['read_date']} · {_range_label(row)} · {source}")
            if duplicate_counts[(row["read_date"], row["page_start"], row["page_end"], row["content_hash"])] > 1:
                st.warning("중복 의심 · 다른 조각으로 보관했습니다.")
            if row["original_text"]:
                st.markdown(row["original_text"])
            if row["user_note"]:
                st.caption("내 메모")
                st.write(row["user_note"])
            badges = [*row["tags"], *[f"예화: {item}" for item in row["illustration_tags"]],
                      *[chunks.CONTENT_TYPES[item] for item in row["content_types"]]]
            if badges:
                st.caption(" · ".join(badges))
            edit, delete = st.columns(2)
            edit.button("수정", key=f"chunk_edit_{row['chunk_id']}", width="stretch", on_click=_open_edit, args=(row["chunk_id"],))
            if delete.button("삭제", key=f"chunk_delete_{row['chunk_id']}", width="stretch"):
                st.session_state.chunk_delete_id = row["chunk_id"]
                st.rerun()
            if st.session_state.get("chunk_delete_id") == row["chunk_id"]:
                st.warning("삭제해도 복구 가능한 소프트 삭제입니다.")
                yes, no = st.columns(2)
                if yes.button("삭제 확인", key=f"chunk_delete_confirm_{row['chunk_id']}"):
                    chunks.soft_delete(conn, row["chunk_id"], owner_id=owner_id)
                    st.session_state.pop("chunk_delete_id", None)
                    st.session_state.notice = "읽은 조각을 삭제했습니다."
                    st.rerun()
                if no.button("삭제 취소", key=f"chunk_delete_cancel_{row['chunk_id']}"):
                    st.session_state.pop("chunk_delete_id", None)
                    st.rerun()
