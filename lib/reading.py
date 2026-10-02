"""단일 사용자 독서 세션. 트랜잭션으로 중복 저장을 방지한다."""
from __future__ import annotations
import time
import uuid
from lib import db, database


def active(conn, *, lock=False):
    query="SELECT * FROM reading_sessions WHERE state IN ('running','stopped')"
    cursor=database.lock_rows(conn,query) if lock else conn.execute(query)
    return cursor.fetchone()


STALE_SECONDS=24*60*60


def is_stale(session,now=None):
    """A reading left open for a day was forgotten, not read."""
    now=int(time.time()) if now is None else now
    return now-session['started_at']>=STALE_SECONDS


def active_fresh(conn,now=None):
    """Return (open session or None, whether a forgotten one was just cancelled)."""
    session=active(conn)
    if session and is_stale(session,now):
        cancel(conn,session['id'])
        return None,True
    return session,False


def start(conn,book_id,now=None):
    now=int(time.time()) if now is None else now
    with database.transaction(conn,lock_reading=True):
        existing=active(conn,lock=True)
        if existing and is_stale(existing,now):
            conn.execute("UPDATE reading_sessions SET state='cancelled' WHERE id=? AND state IN ('running','stopped')",(existing['id'],))
            existing=None
        if existing:
            if existing['book_id']==book_id: return existing
            raise ValueError('다른 책의 타이머를 먼저 저장하거나 취소해주세요.')
        book=database.lock_rows(conn,'SELECT * FROM books WHERE id=?',(book_id,)).fetchone()
        if book is None: raise ValueError('책을 찾을 수 없습니다.')
        sid=str(uuid.uuid4())
        conn.execute("INSERT INTO reading_sessions(id,book_id,started_at,base_page,state) VALUES (?,?,?,?,'running')",
                     (sid,book_id,now,book['current_page'] or 0))
    return active(conn)


def stop(conn,session_id,now=None):
    now=int(time.time()) if now is None else now
    with database.transaction(conn,lock_reading=True):
        conn.execute("UPDATE reading_sessions SET stopped_at=CASE WHEN started_at>%s THEN started_at ELSE %s END,state='stopped' WHERE id=%s AND state='running'" if database.is_postgres(conn) else "UPDATE reading_sessions SET stopped_at=MAX(started_at,?),state='stopped' WHERE id=? AND state='running'", (now,now,session_id) if database.is_postgres(conn) else (now,session_id))


def cancel(conn,session_id):
    with database.transaction(conn,lock_reading=True):
        conn.execute("UPDATE reading_sessions SET state='cancelled' WHERE id=? AND state IN ('running','stopped')",(session_id,))


def elapsed(session,now=None):
    end=session['stopped_at'] if session['stopped_at'] is not None else int(time.time()) if now is None else now
    return max(0,end-session['started_at'])


def _write_progress(conn,book_id,base,page,seconds,timestamp=None):
    db.validate_page(conn,book_id,page)
    if page<base: raise ValueError('도달 페이지는 시작 페이지 이상이어야 합니다.')
    amount=page-base
    if seconds is None:
        minutes=None
        text=f'{base}~{page}쪽, {amount}쪽을 읽었습니다'
    else:
        if seconds<0: raise ValueError('시간은 0 이상이어야 합니다.')
        minutes=seconds/60
        text=f'{amount}쪽을 {minutes:g}분 동안 읽었습니다'
    aid=db.insert_activity(conn,book_id=book_id,kind=4,page=page,text=text,pages_read=amount,
                           minutes_read=minutes,timestamp=timestamp,commit=False)
    conn.execute('UPDATE activities SET base_page=?,seconds_read=? WHERE id=?',(base,seconds,aid))
    conn.execute("UPDATE books SET current_page=?,status='읽는 중' WHERE id=?",(page,book_id))
    return aid


def save(conn,session_id,page):
    with database.transaction(conn,lock_reading=True):
        session=database.lock_rows(conn,'SELECT * FROM reading_sessions WHERE id=?',(session_id,)).fetchone()
        if session is None: raise ValueError('독서 세션을 찾을 수 없습니다.')
        if session['state']=='saved': return session['activity_id']
        if session['state']!='stopped': raise ValueError('먼저 타이머를 멈춰주세요.')
        book=database.lock_rows(conn,'SELECT * FROM books WHERE id=?',(session['book_id'],)).fetchone()
        if (book['current_page'] or 0)!=session['base_page']:
            raise ValueError('독서 중 진도가 변경됐습니다. 현재 진도를 확인한 후 수동 기록해주세요.')
        aid=_write_progress(conn,session['book_id'],session['base_page'],page,elapsed(session),session['stopped_at'])
        conn.execute("UPDATE reading_sessions SET state='saved',activity_id=? WHERE id=?",(aid,session_id))
    return aid


def finish(conn,session_id,page,now=None):
    """End a reading at `page`. Only the page range is recorded, not the time."""
    now=int(time.time()) if now is None else now
    with database.transaction(conn,lock_reading=True):
        session=database.lock_rows(conn,'SELECT * FROM reading_sessions WHERE id=?',(session_id,)).fetchone()
        if session is None: raise ValueError('읽기 기록을 찾을 수 없습니다.')
        if session['state']=='saved': return session['activity_id']
        if session['state'] not in ('running','stopped'): raise ValueError('이미 취소된 읽기입니다. 다시 시작해주세요.')
        book=database.lock_rows(conn,'SELECT * FROM books WHERE id=?',(session['book_id'],)).fetchone()
        if (book['current_page'] or 0)!=session['base_page']:
            raise ValueError('읽는 사이 진도가 바뀌었습니다. 이번 읽기를 취소하고 다시 시작해주세요.')
        aid=_write_progress(conn,session['book_id'],session['base_page'],page,None,now)
        conn.execute("UPDATE reading_sessions SET state='saved',stopped_at=?,activity_id=? WHERE id=?",
                     (session['stopped_at'] or now,aid,session_id))
    return aid


def manual(conn,book_id,page,minutes=None):
    with database.transaction(conn,lock_reading=True):
        existing=active(conn,lock=True)
        if existing and is_stale(existing):
            conn.execute("UPDATE reading_sessions SET state='cancelled' WHERE id=? AND state IN ('running','stopped')",(existing['id'],))
            existing=None
        if existing: raise ValueError('진행 중인 읽기를 먼저 마치거나 취소해주세요.')
        book=database.lock_rows(conn,'SELECT * FROM books WHERE id=?',(book_id,)).fetchone()
        if book is None: raise ValueError('책을 찾을 수 없습니다.')
        if minutes is not None and minutes<=0: raise ValueError('읽은 시간은 1분 이상이어야 합니다.')
        seconds=None if minutes is None else round(minutes*60)
        return _write_progress(conn,book_id,page=page,base=book['current_page'] or 0,seconds=seconds)
