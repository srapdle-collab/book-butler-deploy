from pathlib import Path

from lib import db


def test_get_connection_uses_configured_database_path(tmp_path, monkeypatch):
    """테스트 DB 설정을 무시해 실제 사용자 DB를 수정하는 회귀를 막는다."""
    configured = tmp_path / "isolated.db"
    monkeypatch.setenv("BOOK_BUTLER_DB_PATH", str(configured))

    conn = db.get_connection()
    actual = Path(conn.execute("PRAGMA database_list").fetchone()[2])
    conn.close()

    assert actual == configured
