"""단일 사용자 독서 세션. 트랜잭션으로 중복 저장을 방지한다."""
from __future__ import annotations
import time
import uuid
from lib import db


def active(conn):
    return conn.execute("SELECT * FROM reading_sessions WHERE state IN ('running','stopped')").fetchone()


def start(conn,book_id,now=None):
    now=int(time.time()) if now is None else now
    with conn:
        conn.execute('BEGIN IMMEDIATE')
        existing=active(conn)
        if existing:
            if existing['book_id']==book_id: return existing
            raise ValueError('다른 책의 타이머를 먼저 저장하거나 취소해주세요.')
        book=db.get_book(conn,book_id)
        if book is None: raise ValueError('책을 찾을 수 없습니다.')
        sid=str(uuid.uuid4())
        conn.execute("INSERT INTO reading_sessions(id,book_id,started_at,base_page,state) VALUES (?,?,?,?,'running')",
                     (sid,book_id,now,book['current_page'] or 0))
    return active(conn)


def stop(conn,session_id,now=None):
    now=int(time.time()) if now is None else now
    with conn:
        conn.execute("UPDATE reading_sessions SET stopped_at=MAX(started_at,?),state='stopped' WHERE id=? AND state='running'",(now,session_id))


def cancel(conn,session_id):
    with conn:
        conn.execute("UPDATE reading_sessions SET state='cancelled' WHERE id=? AND state IN ('running','stopped')",(session_id,))


def elapsed(session,now=None):
    end=session['stopped_at'] if session['stopped_at'] is not None else int(time.time()) if now is None else now
    return max(0,end-session['started_at'])


def _write_progress(conn,book_id,base,page,seconds,timestamp=None):
    db.validate_page(conn,book_id,page)
    if page<base: raise ValueError('도달 페이지는 시작 페이지 이상이어야 합니다.')
    if seconds<0: raise ValueError('시간은 0 이상이어야 합니다.')
    minutes=seconds/60
    amount=page-base
    text=f'{amount}쪽을 {minutes:g}분 동안 읽었습니다'
    aid=db.insert_activity(conn,book_id=book_id,kind=4,page=page,text=text,pages_read=amount,
                           minutes_read=minutes,timestamp=timestamp,commit=False)
    conn.execute('UPDATE activities SET base_page=?,seconds_read=? WHERE id=?',(base,seconds,aid))
    conn.execute("UPDATE books SET current_page=?,status='읽는 중' WHERE id=?",(page,book_id))
    return aid


def save(conn,session_id,page):
    with conn:
        conn.execute('BEGIN IMMEDIATE')
        session=conn.execute('SELECT * FROM reading_sessions WHERE id=?',(session_id,)).fetchone()
        if session is None: raise ValueError('독서 세션을 찾을 수 없습니다.')
        if session['state']=='saved': return session['activity_id']
        if session['state']!='stopped': raise ValueError('먼저 타이머를 멈춰주세요.')
        book=db.get_book(conn,session['book_id'])
        if (book['current_page'] or 0)!=session['base_page']:
            raise ValueError('독서 중 진도가 변경됐습니다. 현재 진도를 확인한 후 수동 기록해주세요.')
        aid=_write_progress(conn,session['book_id'],session['base_page'],page,elapsed(session),session['stopped_at'])
        conn.execute("UPDATE reading_sessions SET state='saved',activity_id=? WHERE id=?",(aid,session_id))
    return aid


def manual(conn,book_id,page,minutes):
    with conn:
        conn.execute('BEGIN IMMEDIATE')
        if active(conn): raise ValueError('진행 중인 타이머를 먼저 저장하거나 취소해주세요.')
        book=db.get_book(conn,book_id)
        if book is None: raise ValueError('책을 찾을 수 없습니다.')
        if minutes<=0: raise ValueError('읽은 시간은 1분 이상이어야 합니다.')
        return _write_progress(conn,book_id,book['current_page'] or 0,page,round(minutes*60))
