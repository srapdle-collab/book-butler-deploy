"""소그룹 첫 화면에 날짜별로 보여주는 짧은 읽기 문장."""
from __future__ import annotations

from datetime import date


READING_QUOTES = (
    {"text": "오늘의 한 쪽이 내일의 생각을 바꿉니다.", "author": "읽담"},
    {"text": "좋은 문장은 다시 읽을 때 더 오래 남습니다.", "author": "읽담"},
    {"text": "읽은 것을 나누면 생각은 더 선명해집니다.", "author": "읽담"},
    {"text": "천천히 읽어도, 읽은 하루는 쌓입니다.", "author": "읽담"},
    {"text": "한 문장에 멈추는 시간도 독서입니다.", "author": "읽담"},
)


def daily_quote(day: date | None = None) -> dict[str, str]:
    """같은 날짜에는 모두에게 같은 문장을 보여준다."""
    current = day or date.today()
    return READING_QUOTES[current.toordinal() % len(READING_QUOTES)]
