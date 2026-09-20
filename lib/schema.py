"""비파괴적 추가 스키마. 기존 기록과 사진 파일을 보존한다."""
def ensure_schema(conn):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='activities'").fetchone():
        return
    columns = {r[1] for r in conn.execute('PRAGMA table_info(activities)')}
    for name, kind in [('event_type', 'TEXT'), ('seconds_read', 'INTEGER'),
                       ('base_page', 'INTEGER'), ('deleted_at', 'INTEGER'), ('updated_at', 'INTEGER')]:
        if name not in columns:
            conn.execute(f'ALTER TABLE activities ADD COLUMN {name} {kind}')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS source_book_state (
            book_id TEXT PRIMARY KEY, raw_status INTEGER, raw_reading_now INTEGER,
            inferred_status TEXT, evidence TEXT
        );
        CREATE TABLE IF NOT EXISTS app_migrations (name TEXT PRIMARY KEY, applied_at INTEGER);
        CREATE TABLE IF NOT EXISTS reading_sessions (
            id TEXT PRIMARY KEY, book_id TEXT NOT NULL REFERENCES books(id),
            started_at INTEGER NOT NULL, stopped_at INTEGER, base_page INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('running','stopped','saved','cancelled')),
            activity_id TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_reading
        ON reading_sessions((1)) WHERE state IN ('running','stopped');
    ''')
    conn.commit()
