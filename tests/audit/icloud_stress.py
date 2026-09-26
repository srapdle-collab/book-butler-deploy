"""Opt-in synthetic export audit in a NEW isolated iCloud subdirectory.

Never run automatically in pytest; no production credentials or DB are used.
Requires --icloud-parent and --scratch. Retains clearly labelled test artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def metadata(root):
    records = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            stat = path.lstat()
            records[str(path.relative_to(root))] = [stat.st_mode, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino]
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icloud-parent", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    parent = args.icloud_parent.resolve()
    assert parent.is_dir()
    scratch = args.scratch.resolve()
    assert scratch.is_dir() and "readdam-export-audit-" in scratch.name
    synthetic_db = scratch / "synthetic.sqlite"
    assert not synthetic_db.exists()
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["BOOK_BUTLER_DB_PATH"] = str(synthetic_db)
    # Prevent accidentally using a configured remote DB even if a caller changes routing.
    for key in ("BOOK_BUTLER_DATABASE_URL", "SUPABASE_DB_HOST", "SUPABASE_DB_PORT", "SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_NAME"):
        os.environ.pop(key, None)
    from migration.load_db import SCHEMA
    from lib import db, reading_chunks as chunks

    before = metadata(parent)
    output = parent / ("_읽담_검증전용_20260927_" + uuid.uuid4().hex[:8])
    assert not output.exists()
    conn = sqlite3.connect(synthetic_db)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    conn = db.get_connection(synthetic_db)
    titles = ["TEST 한글 검증용", 'TEST /특수:문자?*"<>|', "TEST 긴 제목 " + "가나다라마바사" * 12, "TEST 충돌 제목"]
    for i, title in enumerate(titles):
        conn.execute("INSERT INTO books(id,title,author,isbn,owner_id) VALUES(?,?,?,?,?)", (f"audit-book-{i}",title,"TEST 합성 저자",None if i == 1 else "9780000000002","audit-owner"))
    conn.commit()
    values = []
    for i in range(32):
        book_index = i % 3 if i < 30 else 3
        item = dict(book_id=f"audit-book-{book_index}", chunk_id=str(uuid.uuid4()), read_date="2026-09-27", page_start=45, page_end=52, minutes=None if i%4 == 0 else 15,
                    original_text=f"[TEST 검증전용 {i}] 합성 원문\n한글·줄바꿈·특수문자 %_", user_note=f"[TEST {i}] 사용자 자료 아님", tags=["검증전용", "한글"], illustration_tags=["TEST"], content_types=["insight"])
        if i >= 30:
            item["chunk_id"] = f"abcdef12-{'aaaa' if i == 30 else 'bbbb'}-4000-8000-000000000001"
        chunks.save(conn, **item)
        values.append(item)

    runs = []
    def export(label):
        result = subprocess.run([sys.executable,"-B",str(REPO / "tools/export_chunks.py"),"--output-root",str(output)],env=os.environ.copy(),text=True,capture_output=True,check=True)
        runs.append({"label":label,"stdout":result.stdout.strip()})
    def verify():
        archive = output / "독서조각"
        with (archive / "_index.csv").open(encoding="utf-8",newline="") as handle:
            rows = list(csv.DictReader(handle))
        records = {r["chunk_id"]:r for r in chunks.all_chunks(conn)}
        assert len(rows) == len(records) == 32
        assert len({r["상대경로"] for r in rows}) == 32
        for row in rows:
            chunk = records[row["chunkId"]]
            path = archive / row["상대경로"]
            assert path.is_file()
            text = path.read_text(encoding="utf-8")
            assert "chunkId: " + chunk["chunk_id"] in text
            assert "출처 앱: 읽담 (readdam)" in text
            assert "ISBN: " + (chunk["isbn"] or "미입력") in text
            assert "읽은 시간: " + (str(chunk["minutes"]) + "분" if chunk["minutes"] is not None else "미입력") in text
            assert row["updatedAt"] == chunk["updated_at"]
            assert row["contentHash"] == chunk["content_hash"]
        return rows
    export("initial 32 chunks")
    verify()
    files_before = {str(p.relative_to(output)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in output.rglob("*.txt")}
    for i in range(3): export(f"unchanged fresh subprocess {i+1}")
    assert files_before == {str(p.relative_to(output)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in output.rglob("*.txt")}
    values[0]["user_note"] = "[TEST 갱신] 긴 한글\n" * 1000
    values[0]["minutes"] = 22
    chunks.save(conn,**values[0])
    export("note/minutes update")
    verify()
    values[1].update(read_date="2027-01-01", page_start=60, page_end=65)
    chunks.save(conn,**values[1])
    export("date/pages move")
    verify()
    chunks.soft_delete(conn, values[2]["chunk_id"])
    export("soft delete moves generated txt")
    verify()
    export("final repeated subprocess")
    rows = verify()
    assert len(list(output.rglob("*.txt"))) == 32
    after = metadata(parent)
    changed = [name for name,stat in before.items() if after.get(name) != stat]
    assert not changed, f"Preexisting metadata changed: {len(changed)}"
    report = {"output_root":str(output),"synthetic_db":str(synthetic_db),"record_count":32,"active_txt":31,"soft_deleted_txt":1,
              "preexisting_entries_checked":len(before),"preexisting_entries_changed":len(changed),"runs":runs,"index_rows":rows,
              "limits":"isolated local iCloud directory; not production DB, shared original index, remote sync or concurrent exporters"}
    (scratch / "report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    conn.close()
    print(json.dumps({key:value for key,value in report.items() if key != "index_rows"},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
