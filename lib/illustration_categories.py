"""예화창고 카테고리 snapshot과 규칙 기반 추천.

실제 폴더는 Mac/iCloud가 정본이다. 이 모듈은 Git에 저장한 snapshot만 읽으며,
사용자 선택값은 snapshot에 있는 NFC canonical name으로만 돌려준다.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import tempfile
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "config" / "illustration_categories.json"
SNAPSHOT_VERSION = 1
RECOMMENDATION_VERSION = 2  # Includes unchecked folder-name matches.
MANAGED_TOP_LEVEL = frozenset({"독서조각", "읽담"})
VERIFICATION_PREFIX = "_읽담_검증전용_"


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def normalize(value: str | None) -> str:
    return " ".join(nfc(value or "").casefold().split())


def _string_list(value, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"snapshot {field} 형식이 올바르지 않습니다.")
    if len(value) > 8:
        raise ValueError(f"snapshot {field}는 카테고리당 8개 이하여야 합니다.")
    values = [nfc(item) for item in value]
    if len({normalize(item) for item in values}) != len(values):
        raise ValueError(f"snapshot {field}에 중복이 있습니다.")
    return values


def _validate_snapshot(raw) -> dict:
    if not isinstance(raw, dict) or set(raw) != {"version", "generatedAt", "categories"}:
        raise ValueError("snapshot 최상위 형식이 올바르지 않습니다.")
    if raw["version"] != SNAPSHOT_VERSION or not isinstance(raw["generatedAt"], str) or not raw["generatedAt"].strip():
        raise ValueError("snapshot version 또는 generatedAt이 올바르지 않습니다.")
    if not isinstance(raw["categories"], list):
        raise ValueError("snapshot categories 형식이 올바르지 않습니다.")
    categories, seen = [], set()
    for entry in raw["categories"]:
        if not isinstance(entry, dict) or set(entry) != {"canonical", "aliases", "keywords"}:
            raise ValueError("snapshot category 형식이 올바르지 않습니다.")
        canonical = entry["canonical"]
        if not isinstance(canonical, str) or not canonical.strip():
            raise ValueError("snapshot canonical name이 올바르지 않습니다.")
        if canonical != nfc(canonical):
            raise ValueError("snapshot canonical name은 NFC여야 합니다.")
        key = normalize(canonical)
        if key in seen:
            raise ValueError("snapshot canonical category가 중복됩니다.")
        seen.add(key)
        categories.append({
            "canonical": canonical,
            "aliases": _string_list(entry["aliases"], "aliases"),
            "keywords": _string_list(entry["keywords"], "keywords"),
        })
    aliases = set()
    canonical = {normalize(entry["canonical"]) for entry in categories}
    for entry in categories:
        for alias in entry["aliases"]:
            key = normalize(alias)
            if key in canonical or key in aliases:
                raise ValueError("snapshot alias는 canonical 또는 다른 alias와 중복될 수 없습니다.")
            aliases.add(key)
    return {"version": SNAPSHOT_VERSION, "generatedAt": raw["generatedAt"], "categories": categories}


def load_snapshot(path: Path | str | None = None) -> dict:
    snapshot_path = Path(path or DEFAULT_SNAPSHOT)
    try:
        raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("예화 카테고리 snapshot이 없습니다.") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("예화 카테고리 snapshot을 읽을 수 없습니다.") from exc
    return _validate_snapshot(raw)


def canonical_names(snapshot: dict) -> list[str]:
    return [entry["canonical"] for entry in snapshot["categories"]]


def canonicalize_selection(snapshot: dict, values) -> list[str]:
    if not isinstance(values, (list, tuple)) or any(not isinstance(value, str) for value in values):
        raise ValueError("예화 태그 선택 형식이 올바르지 않습니다.")
    requested = {normalize(value) for value in values if value.strip()}
    actual = {normalize(entry["canonical"]): entry["canonical"] for entry in snapshot["categories"]}
    unknown = requested - set(actual)
    if unknown:
        raise ValueError("예화 태그는 snapshot의 실제 카테고리만 선택할 수 있습니다.")
    return [entry["canonical"] for entry in snapshot["categories"] if normalize(entry["canonical"]) in requested]


def recommend(snapshot: dict, *, originalText: str | None, userNote: str | None, tags) -> list[dict]:
    body = normalize(f"{originalText or ''} {userNote or ''}")
    normalized_tags = {normalize(tag) for tag in tags or [] if isinstance(tag, str) and tag.strip()}
    results = []
    for entry in snapshot["categories"]:
        terms = [entry["canonical"], *entry["aliases"]]
        normalized_terms = [normalize(term) for term in terms]
        score = 3 if normalized_tags.intersection(normalized_terms) else 0
        if body and any(term in body for term in normalized_terms):
            score += 2
        score += min(2, sum(keyword in body for keyword in {normalize(item) for item in entry["keywords"]} if keyword))
        if score >= 2:
            results.append({"canonical": entry["canonical"], "score": score, "defaultChecked": score >= 3})
    if not results and body:
        # A standalone word from an existing folder name is only a weak lead.
        # Similar folders may share that word, so show each candidate unchecked.
        body_words = set(re.findall(r"[^\W_]+", body))
        for entry in snapshot["categories"]:
            name_words = re.findall(r"[^\W_]+", normalize(entry["canonical"]))
            if any(len(word) >= 2 and word in body_words for word in name_words):
                results.append({"canonical": entry["canonical"], "score": 1, "defaultChecked": False})
    return sorted(results, key=lambda item: (-item["score"], canonical_names(snapshot).index(item["canonical"])))[:3]


def _ignored(name: str) -> bool:
    canonical = nfc(name)
    return name.startswith(".") or canonical in MANAGED_TOP_LEVEL or canonical.startswith(VERIFICATION_PREFIX)


def _rename_candidates(removed: list[str], added: list[str]) -> list[dict]:
    candidates = []
    for old in removed:
        for new in added:
            score = SequenceMatcher(a=normalize(old), b=normalize(new)).ratio()
            if score >= 0.8:
                candidates.append({"from": old, "to": new})
    return candidates


def _write_snapshot(path: Path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
        temporary = Path(handle.name)
    try:
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def refresh_snapshot(root: Path | str, snapshot_path: Path | str = DEFAULT_SNAPSHOT, *, generated_at: str | None = None) -> dict:
    """Read top-level directory names only and atomically refresh the local snapshot."""
    root = Path(root)
    snapshot_path = Path(snapshot_path)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("예화창고 루트 디렉터리가 안전하지 않습니다.")
    previous = load_snapshot(snapshot_path) if snapshot_path.exists() else {
        "version": SNAPSHOT_VERSION, "generatedAt": "", "categories": []
    }
    found, ignored, non_directories = [], [], []
    for item in root.iterdir():
        if _ignored(item.name):
            ignored.append(nfc(item.name))
        elif item.is_symlink():
            raise ValueError("심볼릭 링크는 예화 카테고리가 될 수 없습니다.")
        elif item.is_dir():
            found.append(nfc(item.name))
        else:
            non_directories.append(nfc(item.name))
    if len(set(normalize(item) for item in found)) != len(found):
        raise ValueError("NFC 기준으로 충돌하는 실제 카테고리 폴더가 있습니다.")
    actual = sorted(found, key=normalize)
    previous_by_name = {entry["canonical"]: entry for entry in previous["categories"]}
    added = [name for name in actual if name not in previous_by_name]
    removed = [name for name in previous_by_name if name not in set(actual)]
    snapshot = {
        "version": SNAPSHOT_VERSION,
        "generatedAt": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "categories": [
            {"canonical": name, "aliases": previous_by_name.get(name, {}).get("aliases", []),
             "keywords": previous_by_name.get(name, {}).get("keywords", [])}
            for name in actual
        ],
    }
    _write_snapshot(snapshot_path, snapshot)
    return {
        "added": added,
        "removed": removed,
        "renameCandidates": _rename_candidates(removed, added),
        "ignored": sorted(ignored, key=normalize),
        "nonDirectories": sorted(non_directories, key=normalize),
        "categories": actual,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="실제 예화창고 최상위 폴더명만 읽어 snapshot을 갱신합니다.")
    parser.add_argument("--root", type=Path, required=True, help="예화창고 루트")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT, help="갱신할 snapshot JSON")
    args = parser.parse_args()
    print(json.dumps(refresh_snapshot(args.root, args.snapshot), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
