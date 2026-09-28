"""Today Library pull client. No operating credential is stored here."""
from __future__ import annotations

import requests

from lib import database, reading_chunks

TIMEOUT_SECONDS = 10


def book_snapshots(conn, *, owner_id: str) -> list[dict]:
    reading_chunks._require_owner(conn, owner_id)
    rows = database.execute(conn, "SELECT id, title, author, isbn, pages, status FROM books WHERE owner_id=? ORDER BY title, id", (owner_id,)).fetchall()
    return [{"bookId": row["id"], "title": row["title"], "author": row["author"],
             "isbn": row["isbn"], "totalPages": row["pages"], "status": row["status"] or ""}
            for row in rows]


def sync_once(conn, *, owner_id: str, url: str, token: str, sites_gate_key: str,
              http=requests) -> dict:
    """Pull at most 100 chunks, receipt each committed result, then replace books.

    The caller must pass the authenticated personal-library owner. Network/DB
    failures leave the remote chunk pending for the next invocation.
    """
    reading_chunks._require_owner(conn, owner_id)
    if not url or not token or not sites_gate_key or not url.startswith("https://"):
        return {"state": "not_configured", "received": 0}
    base = url.rstrip("/")
    headers = {"x-readdam-key": token, "OAI-Sites-Authorization": "Bearer " + sites_gate_key,
               "accept": "application/json"}
    try:
        response = http.get(base + "/api/readdam/outbox", headers=headers, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        return {"state": "retry", "received": 0}
    if response.status_code == 401:
        return {"state": "connection_key", "received": 0}
    if response.status_code != 200:
        return {"state": "retry", "received": 0}
    try:
        body = response.json()
    except ValueError:
        return {"state": "retry", "received": 0}
    outbox = body.get("chunks") if isinstance(body, dict) and body.get("schemaVersion") == 1 else None
    if not isinstance(outbox, list) or len(outbox) > 100:
        return {"state": "retry", "received": 0}

    received = 0
    for payload in outbox:
        try:
            result = reading_chunks.ingest(conn, payload, owner_id=owner_id)
        except Exception:
            return {"state": "db_retry", "received": received}
        receipt = {key: result.get(key) for key in ("chunkId", "payloadUpdatedAt", "result", "errorCode", "errorField")}
        try:
            response = http.post(base + "/api/readdam/receipts", headers=headers,
                                 json=receipt, timeout=TIMEOUT_SECONDS)
        except requests.RequestException:
            return {"state": "retry", "received": received}
        if response.status_code == 401:
            return {"state": "connection_key", "received": received}
        if response.status_code != 200:
            return {"state": "retry", "received": received}
        received += 1

    try:
        response = http.put(base + "/api/readdam/books", headers=headers,
                            json={"books": book_snapshots(conn, owner_id=owner_id)}, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        return {"state": "retry", "received": received}
    if response.status_code == 401:
        return {"state": "connection_key", "received": received}
    if response.status_code != 200:
        return {"state": "retry", "received": received}
    return {"state": "ok", "received": received}
