import sqlite3


def test_activity_row_mapping_preserves_sqlite_position_and_columns(tmp_path):
    from migration.migrate_to_supabase import source_table_rows

    path = tmp_path / 'source.db'
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE activities (id TEXT PRIMARY KEY, book_id TEXT, kind INTEGER, date INTEGER)')
    conn.execute("INSERT INTO activities VALUES ('first', 'book', 4, 10)")
    conn.execute("INSERT INTO activities VALUES ('second', 'book', 2, 20)")
    conn.commit()

    rows = source_table_rows(conn, 'activities')

    assert rows == [
        {'position': 1, 'id': 'first', 'book_id': 'book', 'kind': 4, 'date': 10},
        {'position': 2, 'id': 'second', 'book_id': 'book', 'kind': 2, 'date': 20},
    ]
