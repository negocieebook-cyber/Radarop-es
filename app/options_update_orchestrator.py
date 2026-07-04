"""Orquestra snapshots EOD de opções para vários ativos, sem gerar recomendações."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.providers.brapi_options_provider import BrapiOptionsProvider


ROOT = Path(__file__).resolve().parent.parent
OPTIONS_SNAPSHOTS_DIR = ROOT / "data" / "runtime" / "options_snapshots"
OPTIONS_EOD_STATUS_FILE = ROOT / "data" / "runtime" / "options_eod_status.json"
EOD_OBSERVATION = "Dados de opções EOD/fim de pregão. Não usar como tempo real intraday."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _asset(underlying: str) -> str:
    symbol = str(underlying).strip().upper()
    if not re.fullmatch(r"[A-Z0-9]+", symbol):
        raise ValueError(f"ativo inválido: {underlying}")
    return symbol


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


def default_options_watchlist() -> list[str]:
    return ["PETR4", "VALE3", "ITUB4", "BOVA11", "BBAS3", "BBDC4", "B3SA3"]


def load_options_eod_status() -> dict[str, Any]:
    value = _read(OPTIONS_EOD_STATUS_FILE, {})
    return value if isinstance(value, dict) else {}


def save_options_eod_status(status: dict[str, Any]) -> None:
    _write(OPTIONS_EOD_STATUS_FILE, status)


def save_options_snapshot_for_asset(underlying: str, snapshot: dict[str, Any]) -> Path:
    path = OPTIONS_SNAPSHOTS_DIR / f"{_asset(underlying)}.json"
    _write(path, snapshot)
    return path


def load_options_snapshot_for_asset(underlying: str) -> dict[str, Any]:
    value = _read(OPTIONS_SNAPSHOTS_DIR / f"{_asset(underlying)}.json", {})
    return value if isinstance(value, dict) else {}


def load_all_options_snapshots() -> dict[str, dict[str, Any]]:
    if not OPTIONS_SNAPSHOTS_DIR.exists():
        return {}
    snapshots: dict[str, dict[str, Any]] = {}
    for path in sorted(OPTIONS_SNAPSHOTS_DIR.glob("*.json")):
        value = _read(path, {})
        if isinstance(value, dict):
            snapshots[path.stem.upper()] = value
    return snapshots


def _missing_common(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(field for item in series for field in item.get("campos_ausentes", []) if field)
    return [{"field": field, "count": count} for field, count in counts.most_common(10)]


def _failed_snapshot(symbol: str, result: dict[str, Any], collected_at: str) -> dict[str, Any]:
    return {
        "underlying": symbol, "success": False, "source": "brapi_options", "fonte": "brapi_options",
        "tipo_dado": "indisponível", "status_dado": result.get("status_dado", "erro"),
        "access_status": result.get("access_status", "indisponível"), "data_frequency": "EOD",
        "coleta": collected_at, "expiration_used": None, "expirations_used": [], "expirations_selected": [], "expirations_count": 0,
        "chains": [],
        "series_count": 0, "calls_count": 0, "puts_count": 0, "series": [],
        "missing_common_fields": [], "error": result.get("error", "dados indisponíveis"),
        "errors": [result.get("error", "dados indisponíveis")], "observacao": EOD_OBSERVATION,
    }


def _expiration_dte(value: str) -> int | None:
    try:
        return (date.fromisoformat(value) - datetime.now(timezone.utc).date()).days
    except (TypeError, ValueError):
        return None


def _select_expirations(expirations: list[str], min_dte: int, max_dte: int, max_expirations: int) -> list[tuple[str, int]]:
    eligible = [(expiration, dte) for expiration in expirations if (dte := _expiration_dte(expiration)) is not None and min_dte <= dte <= max_dte]
    return sorted(eligible, key=lambda item: (0 if 15 <= item[1] <= 45 else 1, item[1]))[:max_expirations]


def _collect_asset(provider: BrapiOptionsProvider, symbol: str, max_expirations: int, min_dte: int, max_dte: int) -> dict[str, Any]:
    collected_at = _now()
    expirations_result = provider.get_expirations(symbol)
    if not expirations_result.get("success"):
        return _failed_snapshot(symbol, expirations_result, collected_at)
    expirations = expirations_result.get("expirations", [])
    selected_with_dte = _select_expirations(expirations, min_dte, max_dte, max_expirations)
    selected = [expiration for expiration, _ in selected_with_dte]
    if not selected:
        return _failed_snapshot(
            symbol,
            {"error": f"nenhum vencimento disponível entre {min_dte} e {max_dte} dias", "status_dado": "indisponível", "access_status": "disponível"},
            collected_at,
        ) | {"expirations_count": len(expirations)}
    all_series: list[dict[str, Any]] = []
    chains: list[dict[str, Any]] = []
    errors: list[str] = []
    access_status = "disponível"
    for expiration, dte in selected_with_dte:
        chain = provider.get_chain(symbol, expiration)
        if chain.get("success"):
            series = chain.get("data", [])
            all_series.extend(series)
            chains.append({
                "expiration_date": expiration, "vencimento_dias": dte,
                "series_count": len(series), "calls_count": sum(item.get("side") == "call" for item in series),
                "puts_count": sum(item.get("side") == "put" for item in series), "series": series,
            })
        else:
            errors.append(f"{expiration}: {chain.get('error', 'cadeia indisponível')}")
            if chain.get("access_status") == "sem_acesso":
                access_status = "sem_acesso"
    if all_series:
        status_dado = "atualizado" if not errors else "incompleto"
        success = True
        error = " | ".join(errors) if errors else None
    else:
        status_dado = "erro" if errors else "indisponível"
        success = False
        error = " | ".join(errors) if errors else "nenhuma série disponível nos vencimentos selecionados"
        if error and not errors:
            errors.append(error)
    return {
        "underlying": symbol, "success": success, "source": "brapi_options", "fonte": "brapi_options",
        "tipo_dado": "coletado" if all_series else "indisponível", "status_dado": status_dado,
        "access_status": access_status if all_series or errors else "indisponível", "data_frequency": "EOD",
        "coleta": collected_at, "expiration_used": selected[0] if selected else None,
        "expirations_used": selected, "expirations_selected": selected, "expirations_count": len(expirations), "chains": chains,
        "series_count": len(all_series), "calls_count": sum(item.get("side") == "call" for item in all_series),
        "puts_count": sum(item.get("side") == "put" for item in all_series), "series": all_series,
        "missing_common_fields": _missing_common(all_series), "error": error, "errors": errors,
        "observacao": EOD_OBSERVATION,
    }


def summarize_options_snapshots(snapshots: dict[str, dict[str, Any]] | list[dict[str, Any]]) -> dict[str, Any]:
    items = list(snapshots.values()) if isinstance(snapshots, dict) else list(snapshots)
    available = [item for item in items if item.get("success") and item.get("series_count", 0) > 0]
    unavailable = [item for item in items if item not in available]
    errors = [item for item in items if item.get("status_dado") == "erro"]
    if not items:
        general = "não atualizado"
    elif len(available) == len(items):
        general = "disponível"
    elif available:
        general = "parcial"
    else:
        general = "erro" if errors else "indisponível"
    latest = max((str(item.get("coleta")) for item in items if item.get("coleta")), default=None)
    return {
        "status": general, "total_underlyings": len(items), "available_count": len(available),
        "unavailable_count": len(unavailable), "error_count": len(errors),
        "total_series": sum(int(item.get("series_count", 0)) for item in items),
        "total_calls": sum(int(item.get("calls_count", 0)) for item in items),
        "total_puts": sum(int(item.get("puts_count", 0)) for item in items),
        "available_underlyings": [item.get("underlying") for item in available],
        "unavailable_underlyings": [item.get("underlying") for item in unavailable],
        "latest_collection": latest, "source": "brapi_options", "data_frequency": "EOD",
        "opportunity_engine_status": "MOCK / EXEMPLO",
    }


def run_options_update(underlyings: list[str] | None = None, mode: str = "close", max_expirations: int = 4, min_dte: int = 7, max_dte: int = 60) -> dict[str, Any]:
    if max_expirations < 1:
        raise ValueError("max_expirations deve ser pelo menos 1")
    if min_dte < 0 or max_dte < min_dte:
        raise ValueError("faixa de DTE inválida")
    symbols = list(dict.fromkeys(_asset(item) for item in (underlyings or default_options_watchlist())))
    started_at = _now()
    snapshots: dict[str, dict[str, Any]] = {}
    saved_files: list[str] = []
    provider = BrapiOptionsProvider()
    for symbol in symbols:
        try:
            snapshot = _collect_asset(provider, symbol, max_expirations, min_dte, max_dte)
        except Exception as exc:
            snapshot = _failed_snapshot(symbol, {"error": f"falha inesperada: {exc}", "status_dado": "erro"}, _now())
        snapshots[symbol] = snapshot
        saved_files.append(str(save_options_snapshot_for_asset(symbol, snapshot)))
    aggregate = summarize_options_snapshots(snapshots)
    asset_errors = [f"{symbol}: {item.get('error')}" for symbol, item in snapshots.items() if item.get("error")]
    result = {
        "success": aggregate["status"] == "disponível", "completed": True, "mode": mode,
        "started_at": started_at, "finished_at": _now(), "total_underlyings": len(symbols),
        "available_count": aggregate["available_count"], "unavailable_count": aggregate["unavailable_count"],
        "error_count": aggregate["error_count"], "total_series": aggregate["total_series"],
        "total_calls": aggregate["total_calls"], "total_puts": aggregate["total_puts"],
        "underlyings": symbols, "available_underlyings": aggregate["available_underlyings"],
        "unavailable_underlyings": aggregate["unavailable_underlyings"], "errors": asset_errors,
        "saved_files": saved_files, "status": aggregate["status"], "source": "brapi_options",
        "data_frequency": "EOD", "opportunity_engine_status": "MOCK / EXEMPLO",
        "min_dte": min_dte, "max_dte": max_dte, "max_expirations": max_expirations,
        "expirations_found": sum(int(item.get("expirations_count", 0)) for item in snapshots.values()),
        "expirations_selected": sum(len(item.get("expirations_selected", [])) for item in snapshots.values()),
        "series_by_expiration": {
            f"{symbol}:{chain['expiration_date']}": chain.get("series_count", 0)
            for symbol, snapshot in snapshots.items() for chain in snapshot.get("chains", [])
        },
    }
    save_options_eod_status({"last_update": result})
    return result


def get_last_options_update_summary() -> dict[str, Any]:
    status = load_options_eod_status()
    return {**status, "snapshot_summary": summarize_options_snapshots(load_all_options_snapshots())}
