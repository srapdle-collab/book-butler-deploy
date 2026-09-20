"""인용구·메모의 공유/메일 본문을 생성한다."""
from urllib.parse import urlencode,quote
from lib import database


def citation(book,row):
    """공유할 기록의 출처. 기록일은 개인 독서 이력이므로 포함하지 않는다."""
    return f"『{book['title']}』 · {book['author'] or '저자 미상'} · p.{row['page'] or 0}"


def quote_text(book,row,include_notes=False):
    parts=[row['quote']] if row['quote'] else []
    if include_notes and row['text']: parts.append('내 생각 / 메모\n'+row['text'])
    parts.append(citation(book,row))
    return '\n\n'.join(parts)


def record_text(book,row):
    """인용구나 메모 한 건을 출처와 함께 공유할 텍스트로 만든다."""
    parts=[]
    if row['quote']:
        parts.append(row['quote'])
    if row['text']:
        parts.append(('내 생각 / 메모\n' if row['quote'] else '')+row['text'])
    parts.append(citation(book,row))
    return '\n\n'.join(parts)


def export_book(conn,book,include_notes=False):
    rows=conn.execute(f'SELECT * FROM activities WHERE book_id=? AND kind IN (0,2) AND deleted_at IS NULL ORDER BY page,date,{database.activity_position(conn)}',(book['id'],)).fetchall()
    records=[quote_text(book,r,include_notes) for r in rows if r['quote'] or (include_notes and r['text'])]
    return f"{book['title']} — {book['author'] or '저자 미상'}\n\n"+'\n\n──────────\n\n'.join(records)


def mailto(subject,body):
    return 'mailto:?'+urlencode({'subject':subject,'body':body},quote_via=quote)


def sms(body):
    """RFC 5724 형식으로 문자 작성 화면에 넘길 URL을 만든다."""
    return 'sms:?'+urlencode({'body':body},quote_via=quote)
