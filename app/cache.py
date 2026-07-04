"""Cache JSON local do Data Provider Engine."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
    safe_prefix = "".join(char if char.isalnum() else "-" for char in key)[:40].strip("-") or "cache"
    return CACHE_DIR / f"{safe_prefix}-{digest}.json"


def save_cache(key: str, data: Any) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(key)
    temporary = path.with_suffix(".json.tmp")
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "key": key,
        "data": data,
    }
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return path


def load_cache(key: str) -> dict[str, Any] | None:
    path = cache_path(key)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("key") != key or "saved_at" not in payload or "data" not in payload:
            return None
        datetime.fromisoformat(str(payload["saved_at"]).replace("Z", "+00:00"))
        return payload
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def is_cache_fresh(key: str, max_age_minutes: int) -> bool:
    payload = load_cache(key)
    if payload is None or max_age_minutes < 0:
        return False
    saved_at = datetime.fromisoformat(str(payload["saved_at"]).replace("Z", "+00:00"))
    if saved_at.tzinfo is None:
        saved_at = saved_at.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - saved_at.astimezone(timezone.utc)).total_seconds()
    return age_seconds <= max_age_minutes * 60


def clear_cache(key: str | None = None) -> int:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    paths = [cache_path(key)] if key is not None else list(CACHE_DIR.glob("*.json"))
    removed = 0
    for path in paths:
        try:
            path.unlink(missing_ok=True)
            removed += 1
        except OSError:
            continue
    return removed
