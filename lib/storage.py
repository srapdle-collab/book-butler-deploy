"""Supabase Storage의 비공개 사진 버킷 접근 도우미."""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.parse import quote

import requests

BUCKET = "book-photos"


def _settings() -> tuple[str, str] | None:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    return (url, key) if url and key else None


def is_configured() -> bool:
    return _settings() is not None


def object_key(value: str, *, kind: str) -> str:
    """기존 파일 참조를 private bucket 내부의 안전한 경로로 정규화한다."""
    filename = Path(value).name
    if not filename:
        raise ValueError("사진 파일명이 비어 있습니다.")
    prefix = "covers" if kind == "cover" else "photos"
    return f"{prefix}/{filename}"


def _headers(content_type: str | None = None) -> dict[str, str]:
    settings = _settings()
    if settings is None:
        raise RuntimeError("Supabase Storage 설정이 없습니다.")
    _, key = settings
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _object_url(key: str) -> str:
    settings = _settings()
    if settings is None:
        raise RuntimeError("Supabase Storage 설정이 없습니다.")
    url, _ = settings
    return f"{url}/storage/v1/object/{BUCKET}/{quote(key, safe='/')}"


def ensure_bucket() -> None:
    """버킷을 한 번 만들고, 이미 있으면 그대로 사용한다."""
    settings = _settings()
    if settings is None:
        return
    url, _ = settings
    response = requests.request(
        "POST", f"{url}/storage/v1/bucket", headers=_headers("application/json"),
        json={"id": BUCKET, "name": BUCKET, "public": False}, timeout=30,
    )
    already_exists = response.status_code == 409
    if not already_exists:
        try:
            already_exists = response.json().get("code") == "BucketAlreadyExists"
        except ValueError:
            pass
    if response.status_code not in (200, 201) and not already_exists:
        response.raise_for_status()


def upload_photo(key: str, content: bytes, content_type: str | None = None) -> None:
    """비공개 버킷에 idempotent하게 사진을 올린다."""
    if not content:
        raise ValueError("사진 파일이 비어 있습니다.")
    content_type = content_type or mimetypes.guess_type(key)[0] or "application/octet-stream"
    headers = _headers(content_type)
    headers["x-upsert"] = "true"
    response = requests.request("POST", _object_url(key), headers=headers, data=content, timeout=60)
    response.raise_for_status()


def delete_photo(key: str) -> None:
    settings = _settings()
    if settings is None:
        return
    url, _ = settings
    response = requests.request(
        "DELETE", f"{url}/storage/v1/object/{BUCKET}", headers=_headers("application/json"),
        json={"prefixes": [key]}, timeout=30,
    )
    if response.status_code not in (200, 404):
        response.raise_for_status()


def signed_url(key: str, expires_in: int = 3600) -> str | None:
    """브라우저에 키를 노출하지 않는 짧은 만료의 사진 URL을 만든다."""
    settings = _settings()
    if settings is None:
        return None
    url, _ = settings
    try:
        response = requests.request(
            "POST", f"{url}/storage/v1/object/sign/{BUCKET}/{quote(key, safe='/')}",
            headers=_headers("application/json"), json={"expiresIn": expires_in}, timeout=30,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
    except requests.RequestException:
        return None
    signed = response.json().get("signedURL")
    if not signed:
        return None
    return signed if signed.startswith("http") else f"{url}/storage/v1{signed}"
