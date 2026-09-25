"""Formatação de valores para a camada de UI."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    BRASILIA_TZ = timezone(timedelta(hours=-3))

_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_dt(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    return parsed


def format_dt(value: object, fallback: str = "indisponível") -> str:
    if isinstance(value, str):
        trimmed = value.strip()
        if _DATE_ONLY_RE.match(trimmed):
            return f"{trimmed[8:10]}/{trimmed[5:7]}/{trimmed[0:4]}"
    parsed = _parse_dt(value)
    if parsed is None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback
    if parsed.tzinfo is None:
        return parsed.strftime("%d/%m/%Y %H:%M")
    return parsed.astimezone(BRASILIA_TZ).strftime("%d/%m/%Y %H:%M (Brasília)")


def format_dt_relative(value: object, fallback: str = "indisponível") -> str:
    parsed = _parse_dt(value)
    if parsed is None:
        return fallback
    minutes = int((datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 60)
    if minutes < 0:
        minutes = 0
    if minutes < 1:
        return "agora"
    if minutes < 60:
        return f"há {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"há {hours}h"
    days = hours // 24
    if days < 30:
        return f"há {days}d"
    return parsed.strftime("%d/%m/%Y")
