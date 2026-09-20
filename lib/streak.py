"""연속 읽기 스트릭 계산과 뱃지 판정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

BADGE_THRESHOLDS = [30, 60, 100, 200, 300, 365]
BADGE_LABELS = {30: "30일", 60: "60일", 100: "100일", 200: "200일", 300: "300일", 365: "1년"}


@dataclass
class StreakRun:
    start: date
    end: date
    length: int


def reading_days(timestamps: list[int]) -> list[date]:
    """활동 타임스탬프에서 하루 단위 고유 날짜 목록을 구한다."""
    days = {datetime.fromtimestamp(ts).date() for ts in timestamps}
    return sorted(days)


def compute_streak_runs(days: list[date]) -> list[StreakRun]:
    """연속된 날짜 구간(스트릭)의 목록을 구한다."""
    if not days:
        return []
    runs: list[StreakRun] = []
    start = prev = days[0]
    for day in days[1:]:
        if (day - prev).days == 1:
            prev = day
            continue
        runs.append(StreakRun(start, prev, (prev - start).days + 1))
        start = prev = day
    runs.append(StreakRun(start, prev, (prev - start).days + 1))
    return runs


def longest_streak(runs: list[StreakRun]) -> StreakRun | None:
    return max(runs, key=lambda r: r.length) if runs else None


def current_streak(days: list[date], today: date | None = None) -> int:
    """가장 최근 기록 기준 현재 연속 일수. 오늘/어제 기록이 없으면 0."""
    if not days:
        return 0
    today = today or date.today()
    day_set = set(days)
    if today in day_set:
        cursor = today
    elif (today - timedelta(days=1)) in day_set:
        cursor = today - timedelta(days=1)
    else:
        return 0
    count = 0
    while cursor in day_set:
        count += 1
        cursor -= timedelta(days=1)
    return count


def earned_badges(runs: list[StreakRun]) -> list[dict]:
    """각 임계값(30/60/100/200/300/365일)을 최초로 달성한 날짜를 구한다."""
    badges = []
    for threshold in BADGE_THRESHOLDS:
        earliest = None
        for run in runs:
            if run.length >= threshold:
                earned_date = run.start + timedelta(days=threshold - 1)
                if earliest is None or earned_date < earliest:
                    earliest = earned_date
        if earliest:
            badges.append(
                {"threshold": threshold, "label": BADGE_LABELS[threshold], "earned_date": earliest}
            )
    return badges
