"""Approval diagnostics with no credentials or raw DB address in the output."""
from __future__ import annotations

import hashlib

from lib import database


# M1 READ ONLY reference, recorded after the same query is verified twice.
EXPECTED_M1_FINGERPRINT = "0e24f3776b78ec94"


def fingerprint_identity(identity):
    payload = "\x1f".join(str(part) for part in identity)
    return hashlib.sha256(("readdam-db-target-v1\x1f" + payload).encode()).hexdigest()[:16]


def compare_target(backend, fingerprint, expected):
    if backend != "postgres" and expected:
        same = "NO"
    elif not fingerprint or not expected:
        same = "UNKNOWN"
    else:
        same = "YES" if fingerprint == expected else "NO"
    return {"backend": backend, "fingerprint": fingerprint or "unavailable", "same_as_m1": same}


def new_attempt(chunk_id, book_id=None):
    return {
        "_book_id": book_id,
        "save_attempted": "YES", "target_chunk_id": str(chunk_id)[:8],
        "set_illustration_tags_called": "NO", "db_update_success": "NO",
        "postwrite_verify_success": "NO", "saved_tags_count": 0,
        "failure_stage": "not_called",
    }


def connection_target(conn):
    """Hash server-side identity only; do not inspect DSNs or Secrets."""
    if not database.is_postgres(conn):
        return compare_target("sqlite", None, EXPECTED_M1_FINGERPRINT)
    try:
        row = conn.execute(
            "SELECT current_database() AS db_name, inet_server_addr()::text AS server_addr, "
            "inet_server_port() AS server_port, oid::text AS db_oid, "
            "(SELECT min(id)::text FROM profiles) AS profile_marker "
            "FROM pg_database WHERE datname=current_database()"
        ).fetchone()
        if not row or not row["server_addr"] or row["server_port"] is None or not row["profile_marker"]:
            return compare_target("postgres", None, EXPECTED_M1_FINGERPRINT)
        identity = ("postgres", row["db_name"], row["server_addr"],
                    str(row["server_port"]), row["db_oid"], row["profile_marker"])
        return compare_target("postgres", fingerprint_identity(identity), EXPECTED_M1_FINGERPRINT)
    except Exception:
        return compare_target("postgres", None, EXPECTED_M1_FINGERPRINT)


def display_lines(diagnostic):
    keys = ("save_attempted", "target_chunk_id", "set_illustration_tags_called",
            "db_update_success", "postwrite_verify_success", "saved_tags_count", "failure_stage")
    return [f"{key}: {diagnostic[key]}" for key in keys]
