from datetime import date

from lib.reading_quote import daily_quote


def test_daily_quote_is_stable_for_a_given_day():
    quote = daily_quote(date(2026, 9, 22))

    assert quote == daily_quote(date(2026, 9, 22))
    assert set(quote) == {"text", "author"}
    assert quote["text"]
    assert quote["author"]
