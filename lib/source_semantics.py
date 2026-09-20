"""북스윙 백업을 대조해 확인한 의미. 원본 kind 번호는 바꾸지 않는다."""
from __future__ import annotations


def source_event(kind: int) -> str | None:
    return {3: 'timer_started', 5: 'reading_started', 6: 'completed', 7: 'stopped'}.get(kind)


def classify_book(raw: dict) -> tuple[str, str]:
    lifecycle = sorted((a for a in raw.get('activities', []) if a.get('kind') in (5, 6, 7)),
                       key=lambda a: a.get('date', 0))
    latest = lifecycle[-1]['kind'] if lifecycle else None
    if raw.get('status') == 2 and latest == 5:
        return '읽는 중', 'status=2, 마지막 생명주기 kind=5(시작) 일치'
    if raw.get('status') == 1:
        if latest == 6:
            return '완독', 'status=1, 마지막 생명주기 kind=6; 완독횟수와 kind=6 수 대조'
        if latest == 7:
            return '읽기 중단', 'status=1, 마지막 생명주기 kind=7(중단 추정)'
        if latest is None and not raw.get('readCount'):
            return '미독', 'status=1, 시작/완료/중단 기록 없음, readCount=0'
    return '확인 필요', '상태와 활동의 근거가 일치하지 않음; 자동 추정 제외'
