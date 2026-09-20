"""수정·삭제는 원자적으로 처리. 삭제된 원본/사진을 보존해 복원을 지원한다."""
from __future__ import annotations
import time
from lib import db, reading

UNSET=object()


def get(conn,aid):
    row=conn.execute('SELECT rowid AS position,* FROM activities WHERE id=?',(aid,)).fetchone()
    if row is None: raise ValueError('기록을 찾을 수 없습니다.')
    return row


def is_latest(conn,row):
    latest=conn.execute('SELECT id FROM activities WHERE book_id=? AND kind=4 AND deleted_at IS NULL ORDER BY date DESC,rowid DESC LIMIT 1',
                        (row['book_id'],)).fetchone()
    return latest is not None and latest['id']==row['id']


def base_page(row):
    base=row['base_page']
    if base is None and row['page'] is not None and row['pages_read'] is not None:
        base=row['page']-row['pages_read']
    if base is None or base<0 or base>row['page']:
        return None
    return base


def check(conn,row,revision=UNSET):
    if row['deleted_at'] is not None: raise ValueError('이미 삭제된 기록입니다.')
    if row['kind'] not in (0,1,2,4):
        raise ValueError('시작·완독·중단·별점 기록은 책 관리에서 상태를 변경해주세요.')
    if revision is not UNSET and row['updated_at']!=revision:
        raise ValueError('다른 화면에서 기록이 바뀌었습니다. 다시 열어주세요.')
    timer=reading.active(conn)
    if row['kind']==4 and timer and timer['book_id']==row['book_id']:
        raise ValueError('타이머를 먼저 저장하거나 취소해주세요.')


def update(conn,aid,*,page,quote='',text='',minutes=None,expected_revision=UNSET):
    with conn:
        conn.execute('BEGIN IMMEDIATE')
        row=get(conn,aid); check(conn,row,expected_revision)
        db.validate_page(conn,row['book_id'],page)
        if row['kind']==4:
            if minutes is None or minutes<0: raise ValueError('시간을 0분 이상 입력해주세요.')
            base=base_page(row)
            amount=row['pages_read']
            if page!=row['page']:
                book=db.get_book(conn,row['book_id'])
                if not is_latest(conn,row) or book['current_page']!=row['page'] or book['status']!='읽는 중':
                    raise ValueError('현재 진도와 일치하는 최신 진도만 페이지를 수정할 수 있습니다.')
                if base is None or page<base: raise ValueError('시작 페이지를 확인할 수 없거나 그보다 앞선 페이지입니다.')
                amount=page-base
                conn.execute('UPDATE books SET current_page=? WHERE id=?',(page,row['book_id']))
            seconds=round(minutes*60)
            body=f'{amount}쪽을 {seconds/60:g}분 동안 읽었습니다' if amount is not None else f'{seconds/60:g}분 동안 읽었습니다'
            conn.execute('UPDATE activities SET page=?,text=?,pages_read=?,minutes_read=?,seconds_read=?,updated_at=? WHERE id=?',
                         (page,body,amount,seconds/60,seconds,time.time_ns(),aid))
        else:
            quote=quote.strip() or None; text=text.strip() or None
            if row['kind'] in (0,2) and not (quote or text): raise ValueError('인용문 또는 메모를 입력해주세요.')
            kind=1 if row['kind']==1 else 0 if text else 2
            conn.execute('UPDATE activities SET page=?,quote=?,text=?,kind=?,updated_at=? WHERE id=?',
                         (page,quote,text,kind,time.time_ns(),aid))


def delete(conn,aid,expected_revision=UNSET):
    with conn:
        conn.execute('BEGIN IMMEDIATE')
        row=get(conn,aid); check(conn,row,expected_revision)
        if row['kind']==4:
            book=db.get_book(conn,row['book_id'])
            if is_latest(conn,row) and book['current_page']==row['page'] and book['status']=='읽는 중':
                base=base_page(row)
                if base is None: raise ValueError('시작 페이지가 불명확해 최신 진도를 안전하게 되돌릴 수 없습니다.')
                conn.execute('INSERT OR REPLACE INTO deletion_page_effect VALUES (?,?,?)',(aid,row['page'],base))
                conn.execute('UPDATE books SET current_page=? WHERE id=?',(base,row['book_id']))
        conn.execute('UPDATE activities SET deleted_at=?,updated_at=? WHERE id=?',(int(time.time()),time.time_ns(),aid))


def restore(conn,aid):
    with conn:
        conn.execute('BEGIN IMMEDIATE')
        row=get(conn,aid)
        if row['deleted_at'] is None: return
        effect=conn.execute('SELECT * FROM deletion_page_effect WHERE activity_id=?',(aid,)).fetchone()
        if effect:
            book=db.get_book(conn,row['book_id'])
            if reading.active(conn) or book['current_page']!=effect['page_after'] or book['status']!='읽는 중':
                raise ValueError('삭제 이후 진도나 상태가 달라졌습니다. 타이머와 현재 진도를 확인해주세요.')
            newer=conn.execute('SELECT 1 FROM activities WHERE book_id=? AND kind=4 AND deleted_at IS NULL AND (date>? OR (date=? AND rowid>?))',
                               (row['book_id'],row['date'],row['date'],row['position'])).fetchone()
            if newer: raise ValueError('더 최근 진도가 있어 복원 시 현재 페이지가 충돌합니다.')
            conn.execute('UPDATE books SET current_page=? WHERE id=?',(effect['page_before'],row['book_id']))
            conn.execute('DELETE FROM deletion_page_effect WHERE activity_id=?',(aid,))
        conn.execute('UPDATE activities SET deleted_at=NULL,updated_at=? WHERE id=?',(time.time_ns(),aid))
