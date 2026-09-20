"""인용구/메일 본문 생성. 개인 메모는 명시적으로 선택한 경우만 포함한다."""
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode,quote


def citation(book,row):
    stamp=datetime.fromtimestamp(int(row['date']),ZoneInfo('Asia/Seoul')).strftime('%Y.%m.%d %H:%M')
    return f"『{book['title']}』 · {book['author'] or '저자 미상'} · p.{row['page'] or 0} · {stamp}"


def quote_text(book,row,include_notes=False):
    parts=[row['quote']] if row['quote'] else []
    if include_notes and row['text']: parts.append('내 생각 / 메모\n'+row['text'])
    parts.append(citation(book,row))
    return '\n\n'.join(parts)


def export_book(conn,book,include_notes=False):
    rows=conn.execute('SELECT * FROM activities WHERE book_id=? AND kind IN (0,2) AND deleted_at IS NULL ORDER BY page,date,rowid',(book['id'],)).fetchall()
    records=[quote_text(book,r,include_notes) for r in rows if r['quote'] or (include_notes and r['text'])]
    return f"{book['title']} — {book['author'] or '저자 미상'}\n\n"+'\n\n──────────\n\n'.join(records)


def mailto(subject,body):
    return 'mailto:?'+urlencode({'subject':subject,'body':body},quote_via=quote)
