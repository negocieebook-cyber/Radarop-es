"""Orquestra e persiste atualizações reais do Radar de Mercado."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.market_snapshot_engine import build_many_asset_snapshots


ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = ROOT / "data" / "runtime"
SNAPSHOTS_FILE = RUNTIME_DIR / "market_snapshots.json"
STATUS_FILE = RUNTIME_DIR / "update_status.json"
VALID_RUNNERS = {"local_script", "streamlit_app", "github_actions"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def default_watchlist() -> list[str]:
    return ["PETR4", "VALE3", "ITUB4", "BOVA11", "BBAS3", "B3SA3", "WEGE3", "PRIO3"]


def load_market_snapshots() -> list[dict[str, Any]]:
    value = _read_json(SNAPSHOTS_FILE, [])
    return value if isinstance(value, list) else []


def save_market_snapshots(snapshots: list[dict[str, Any]]) -> None:
    _write_json(SNAPSHOTS_FILE, snapshots)


def load_update_status() -> dict[str, Any]:
    default = {"last_updates": {}, "last_error": None, "notes": []}
    value = _read_json(STATUS_FILE, default)
    return value if isinstance(value, dict) else default


def save_update_status(status: dict[str, Any]) -> None:
    _write_json(STATUS_FILE, status)


def resolve_runner(runner: str | None = None) -> str:
    """Identifica quem disparou a coleta sem depender de informação sensível."""
    if runner:
        if runner not in VALID_RUNNERS:
            raise ValueError(f"runner inválido: {runner}")
        return runner
    return "github_actions" if os.getenv("GITHUB_ACTIONS", "").lower() == "true" else "local_script"


def classify_snapshot_age(finished_at: str | None) -> str:
    if not finished_at:
        return "indisponível"
    try:
        timestamp = datetime.fromisoformat(str(finished_at).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_minutes = max(0.0, (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds() / 60)
    except (TypeError, ValueError):
        return "indisponível"
    if age_minutes < 20:
        return "atualizado"
    if age_minutes <= 90:
        return "atrasado"
    return "muito atrasado"


def latest_update(status: dict[str, Any] | None = None) -> dict[str, Any] | None:
    updates = (status or load_update_status()).get("last_updates", {})
    candidates = [item for item in updates.values() if isinstance(item, dict) and item.get("finished_at")]
    if not candidates:
        return None
    return max(candidates, key=lambda item: str(item.get("finished_at", "")))


def summarize_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(item.get("status_dado", "erro")) for item in snapshots)
    trends = Counter(str(item.get("tendencia") or "indefinida") for item in snapshots)
    missing = Counter(
        field
        for item in snapshots
        for field in item.get("campos_ausentes", [])
        if field
    )
    sources = sorted({str(item.get("fonte")) for item in snapshots if item.get("fonte")})
    return {
        "total": len(snapshots),
        "completos": statuses["atualizado"],
        "incompletos": statuses["incompleto"],
        "erros": statuses["erro"],
        "por_tendencia": {
            "alta": trends["alta"],
            "baixa": trends["baixa"],
            "lateral": trends["lateral"],
            "indefinida": len(snapshots) - trends["alta"] - trends["baixa"] - trends["lateral"],
        },
        "campos_ausentes_mais_comuns": dict(missing.most_common()),
        "fonte": sources[0] if len(sources) == 1 else (", ".join(sources) if sources else "indisponível"),
    }


def run_market_update(
    tickers: list[str] | None = None,
    range: str = "3mo",
    interval: str = "1d",
    mode: str = "intraday",
    runner: str | None = None,
) -> dict[str, Any]:
    normalized = list(dict.fromkeys(str(item).strip().upper() for item in (tickers or default_watchlist()) if str(item).strip()))
    started_at = _now()
    errors: list[str] = []
    snapshots: list[dict[str, Any]] = []
    try:
        snapshots = build_many_asset_snapshots(normalized, range=range, interval=interval)
        save_market_snapshots(snapshots)
        errors = [f"{item.get('ativo', 'ativo desconhecido')}: dados indisponíveis" for item in snapshots if item.get("status_dado") == "erro"]
    except Exception as exc:  # a rotina deve registrar falha de fonte sem derrubar o chamador
        errors = [f"Falha na atualização: {exc}"]

    counts = summarize_snapshots(snapshots)
    finished_at = _now()
    result = {
        "success": not errors,
        "mode": mode,
        "runner": resolve_runner(runner),
        "started_at": started_at,
        "finished_at": finished_at,
        "total_tickers": len(normalized),
        "updated_count": counts["completos"],
        "incomplete_count": counts["incompletos"],
        "error_count": max(counts["erros"], len(errors)),
        "errors": errors,
        "source": "brapi",
        "opportunity_engine_status": "MOCK / EXEMPLO",
    }
    status = load_update_status()
    status.setdefault("last_updates", {})[mode] = result
    status["last_error"] = errors[-1] if errors else None
    status.setdefault("notes", [])
    save_update_status(status)
    return result


def get_last_update_summary() -> dict[str, Any]:
    status = load_update_status()
    latest = latest_update(status)
    return {
        **status,
        "latest_update": latest,
        "snapshot_age_status": classify_snapshot_age(latest.get("finished_at") if latest else None),
        "snapshot_summary": summarize_snapshots(load_market_snapshots()),
    }


def should_update(last_update: str | dict[str, Any] | None, frequency_minutes: int) -> dict[str, Any]:
    value = last_update.get("finished_at") if isinstance(last_update, dict) else last_update
    if not value:
        return {"should_update": True, "reason": "nenhuma atualização anterior registrada"}
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_minutes = max(0.0, (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds() / 60)
    except (TypeError, ValueError):
        return {"should_update": True, "reason": "data da última atualização inválida"}
    needed = age_minutes >= frequency_minutes
    return {
        "should_update": needed,
        "reason": f"snapshot com {age_minutes:.1f} min; frequência configurada em {frequency_minutes} min",
        "age_minutes": round(age_minutes, 2),
    }


def run_if_needed(mode: str, frequency_minutes: int, tickers: list[str] | None = None, runner: str | None = None) -> dict[str, Any]:
    previous = load_update_status().get("last_updates", {}).get(mode)
    decision = should_update(previous, frequency_minutes)
    if decision["should_update"]:
        return {**run_market_update(tickers=tickers, mode=mode, runner=runner), "skipped": False, "reason": decision["reason"]}
    return {
        "success": True,
        "mode": mode,
        "runner": resolve_runner(runner),
        "skipped": True,
        "reason": decision["reason"],
        "source": "brapi",
        "opportunity_engine_status": "MOCK / EXEMPLO",
        **summarize_snapshots(load_market_snapshots()),
    }
