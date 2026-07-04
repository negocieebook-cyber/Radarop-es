"""Persistência e resumo do teste isolado de opções EOD."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.providers.brapi_options_provider import BrapiOptionsProvider, EOD_NOTE


ROOT = Path(__file__).resolve().parent.parent
OPTIONS_SNAPSHOT_FILE = ROOT / "data" / "runtime" / "options_chain_snapshot.json"
OPTIONS_STATUS_FILE = ROOT / "data" / "runtime" / "options_update_status.json"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def fetch_options_expirations(underlying: str) -> dict[str, Any]:
    return BrapiOptionsProvider().get_expirations(underlying)


def fetch_options_chain_for_next_expiration(underlying: str, side: str | None = None) -> dict[str, Any]:
    provider = BrapiOptionsProvider()
    expirations = provider.get_expirations(underlying)
    if not expirations.get("success"):
        return expirations
    expiration = expirations["expirations"][0]
    result = provider.get_chain(underlying, expiration, side=side)
    result["expirations"] = expirations["expirations"]
    return result


def summarize_options_snapshot(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    value = snapshot or {}
    series = value.get("series", []) if isinstance(value.get("series"), list) else []
    missing = Counter(field for item in series for field in item.get("campos_ausentes", []))
    return {
        "underlying": value.get("underlying"), "success": bool(value.get("success")),
        "access_status": value.get("access_status", "indisponível"),
        "expiration_count": len(value.get("expirations", [])) or value.get("expirations_count", 0), "expiration_used": value.get("expiration_used"),
        "expirations_selected": value.get("expirations_selected", value.get("expirations_used", [])),
        "chains_count": len(value.get("chains", [])),
        "series_count": len(series), "calls": sum(item.get("side") == "call" for item in series),
        "puts": sum(item.get("side") == "put" for item in series),
        "normalized_price_count": sum(item.get("normalized_price") is not None and item.get("normalized_price") > 0 for item in series),
        "raw_preserved_count": sum(isinstance(item.get("raw"), dict) for item in series),
        "campos_ausentes_comuns": dict(missing.most_common(8)), "error": value.get("error"),
        "fonte": value.get("fonte", "brapi_options"), "coleta": value.get("coleta"),
        "status_dado": value.get("status_dado", "indisponível"), "observacao": EOD_NOTE,
    }


def save_options_snapshot(snapshot: dict[str, Any]) -> None:
    _write(OPTIONS_SNAPSHOT_FILE, snapshot)


def load_options_snapshot() -> dict[str, Any]:
    value = _read(OPTIONS_SNAPSHOT_FILE, {})
    return value if isinstance(value, dict) else {}


def save_options_update_status(status: dict[str, Any]) -> None:
    _write(OPTIONS_STATUS_FILE, status)


def load_options_update_status() -> dict[str, Any]:
    value = _read(OPTIONS_STATUS_FILE, {})
    return value if isinstance(value, dict) else {}


def build_options_snapshot(underlying: str) -> dict[str, Any]:
    symbol = str(underlying).strip().upper()
    collected_at = datetime.now(timezone.utc).isoformat()
    provider = BrapiOptionsProvider()
    expirations = provider.get_expirations(symbol)
    if not expirations.get("success"):
        snapshot = {**expirations, "underlying": symbol, "expirations": [], "expiration_used": None, "series": [], "coleta": collected_at}
    else:
        expiration = expirations["expirations"][0]
        chain = provider.get_chain(symbol, expiration)
        snapshot = {
            "success": bool(chain.get("success")), "underlying": symbol,
            "access_status": chain.get("access_status", "indisponível"),
            "expirations": expirations["expirations"], "expiration_used": expiration,
            "series": chain.get("data", []), "error": chain.get("error"),
            "fonte": "brapi_options", "tipo_dado": chain.get("tipo_dado", "indisponível"),
            "status_dado": chain.get("status_dado", "erro"), "coleta": chain.get("coleta", collected_at),
            "observacao": EOD_NOTE,
        }
    snapshot["summary"] = summarize_options_snapshot(snapshot)
    save_options_snapshot(snapshot)
    save_options_update_status({"last_update": snapshot["summary"], "opportunity_engine_status": "MOCK / EXEMPLO"})
    return snapshot
