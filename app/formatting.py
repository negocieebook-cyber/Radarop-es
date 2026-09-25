"""Formatação de valores para a camada de UI."""

from __future__ import annotations

from datetime import datetime, timezone


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
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_dt(value: object, fallback: str = "indisponível") -> str:
    parsed = _parse_dt(value)
    if parsed is None:
        return fallback
    return parsed.strftime("%d/%m/%Y %H:%M")


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
