"""Pipeline persistente de dados reais EOD, sem ordens e sem dados inventados."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.conditional_entry_engine import rank_conditional_entries, summarize_conditional_entries
from app.healthbox_engine import healthbox_confirms_strategy
from app.market_snapshot_engine import snapshot_to_healthbox
from app.opening_watchlist import evaluate_watchlist_item, load_opening_watchlist
from app.options_update_orchestrator import run_options_update
from app.options_universe_discovery import get_available_option_tickers
from app.options_universe_discovery import load_option_candidate_tickers, load_options_universe_availability
from app.graphical_thesis_engine import (
    build_graphical_thesis,
    rank_graphical_theses,
    summarize_graphical_theses,
)
from app.graphical_diagnostics import rank_near_setups, summarize_graphical_diagnostics
from app.strategy_mapper import build_strategy_mapping
from app.strategy_screener import screen_strategies_for_thesis
from app.graphical_watchlist import (
    evaluate_graphical_watchlist_item,
    load_graphical_watchlist,
    save_graphical_watchlist,
    summarize_graphical_watchlist,
)
from app.position_monitor import build_position_status
from app.real_opportunity_engine import generate_real_eod_opportunities
from app.storage import load_json, load_positions, save_json
from app.update_orchestrator import default_watchlist, load_market_snapshots, run_market_update


ROOT = Path(__file__).resolve().parent.parent
REAL_OPPORTUNITIES_FILE = ROOT / "data" / "runtime" / "real_opportunities_snapshot.json"
PIPELINE_STATUS_FILE = ROOT / "data" / "runtime" / "pipeline_status.json"
GRAPHICAL_THESES_FILE = ROOT / "data" / "runtime" / "graphical_theses_snapshot.json"
GRAPHICAL_CANDIDATES_FILE = ROOT / "data" / "graphical_candidate_tickers.json"
EOD_WARNING = "Dados EOD. Validar no pregão antes de qualquer entrada."
VALID_MODES = {"premarket", "intraday", "close"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_real_opportunities_snapshot() -> dict[str, Any]:
    value = load_json(REAL_OPPORTUNITIES_FILE, {})
    return value if isinstance(value, dict) else {}


def save_real_opportunities_snapshot(data: dict[str, Any]) -> None:
    save_json(REAL_OPPORTUNITIES_FILE, data)


def load_pipeline_status() -> dict[str, Any]:
    value = load_json(PIPELINE_STATUS_FILE, {})
    return value if isinstance(value, dict) else {}


def save_pipeline_status(status: dict[str, Any]) -> None:
    save_json(PIPELINE_STATUS_FILE, status)


def load_graphical_theses_snapshot() -> dict[str, Any]:
    value = load_json(GRAPHICAL_THESES_FILE, {})
    return value if isinstance(value, dict) else {}


def save_graphical_theses_snapshot(data: dict[str, Any]) -> None:
    save_json(GRAPHICAL_THESES_FILE, data)


def _graphical_candidate_tickers() -> list[str]:
    configured = load_json(GRAPHICAL_CANDIDATES_FILE, [])
    if isinstance(configured, list) and configured:
        return list(dict.fromkeys(str(item).strip().upper() for item in configured if str(item).strip()))
    return load_option_candidate_tickers() or default_watchlist()


def summarize_pipeline_result(result: dict[str, Any]) -> dict[str, Any]:
    snapshot = result.get("opportunities_snapshot") or load_real_opportunities_snapshot()
    return {
        "mode": result.get("mode"), "success": result.get("success", False),
        "generated_at": snapshot.get("generated_at"), "total_candidates": snapshot.get("total_candidates", 0),
        "entrada_condicional": snapshot.get("entrada_condicional", 0),
        "acompanhar_na_abertura": snapshot.get("acompanhar_na_abertura", 0),
        "evitar": snapshot.get("evitar", 0), "inconclusivo": snapshot.get("inconclusivo", 0),
        "warnings": len(result.get("warnings", [])), "errors": len(result.get("errors", [])),
    }


def _real_contexts() -> dict[str, dict[str, Any]]:
    return {str(item.get("ativo")): item for item in load_market_snapshots() if item.get("ativo")}


def _evaluate_saved_items() -> dict[str, Any]:
    snapshots = _real_contexts()
    watchlist = [evaluate_watchlist_item(item, snapshots.get(str(item.get("ativo")))) for item in load_opening_watchlist()]
    graphical_watchlist = [
        evaluate_graphical_watchlist_item(item, snapshots.get(str(item.get("ativo"))))
        for item in load_graphical_watchlist()
    ]
    save_graphical_watchlist(graphical_watchlist)
    positions = []
    for position in load_positions():
        if position.get("origem") != "opening_watchlist":
            continue
        snapshot = snapshots.get(str(position.get("ativo")))
        context = None
        if snapshot:
            healthbox = snapshot_to_healthbox(snapshot)
            healthbox["confirmation"] = healthbox_confirms_strategy(healthbox, position.get("tipo_estrutura", ""))
            context = {"asset_snapshot": snapshot, "healthbox": healthbox, "current_mark": None, "tipo_dado": snapshot.get("tipo_dado"), "fonte": snapshot.get("fonte") or "brapi"}
        positions.append({"position_id": position.get("id"), "ativo": position.get("ativo"), **build_position_status(position, context)})
    return {
        "watchlist_evaluated": len(watchlist),
        "watchlist_statuses": {status: sum(item.get("status") == status for item in watchlist) for status in {"aguardando confirmação", "atenção", "invalidado", "inconclusivo"}},
        "graphical_watchlist_evaluated": len(graphical_watchlist),
        "graphical_watchlist_statuses": summarize_graphical_watchlist(graphical_watchlist),
        "opening_positions_evaluated": len(positions),
        "position_statuses": {status: sum(item.get("status") == status for item in positions) for status in {item.get("status") for item in positions}},
    }


def run_pipeline(mode: str = "close", tickers: list[str] | None = None, max_expirations: int = 4, graphical_limit: int = 30) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"modo inválido: {mode}")
    option_source = tickers if tickers is not None else (get_available_option_tickers(include_low_liquidity=True) or default_watchlist())
    option_symbols = list(dict.fromkeys(str(item).strip().upper() for item in option_source if str(item).strip()))
    if graphical_limit < 1:
        raise ValueError("graphical_limit deve ser pelo menos 1")
    market_source = tickers if tickers is not None else _graphical_candidate_tickers()[:graphical_limit]
    market_symbols = list(dict.fromkeys(str(item).strip().upper() for item in market_source if str(item).strip()))
    started_at = _now()
    runner = "github_actions" if os.getenv("GITHUB_ACTIONS", "").lower() == "true" else "local_script"
    errors: list[str] = []
    warnings: list[str] = [EOD_WARNING]
    if tickers is None and len(option_symbols) <= 1:
        warnings.append("Universo limitado pela fonte/cache; somente ativos acessíveis recentes serão processados.")
    phases: dict[str, Any] = {}
    try:
        phases["market"] = run_market_update(tickers=market_symbols, mode=mode, runner=runner)
        errors.extend(phases["market"].get("errors") or [])
    except Exception as exc:
        errors.append(f"market: {exc}")
        phases["market"] = {"success": False, "error": str(exc)}
    phases["monitoring"] = _evaluate_saved_items()
    opportunities_snapshot: dict[str, Any] | None = None
    if mode == "close":
        try:
            phases["options"] = run_options_update(option_symbols, mode="close", max_expirations=max_expirations)
            errors.extend(phases["options"].get("errors") or [])
        except Exception as exc:
            errors.append(f"options: {exc}")
            phases["options"] = {"success": False, "error": str(exc)}
        opportunities = generate_real_eod_opportunities(option_symbols)
        conditional = summarize_conditional_entries(opportunities)
        ranked = rank_conditional_entries(opportunities, top_n=10)
        opportunities_snapshot = {
            "generated_at": _now(), "mode": mode, "source": ["brapi", "brapi_options"],
            "tickers": option_symbols, "total_candidates": len(opportunities),
            "entrada_condicional": conditional["entrada_condicional"],
            "acompanhar_na_abertura": conditional["acompanhar_na_abertura"],
            "evitar": conditional["evitar"], "inconclusivo": conditional["inconclusivo"],
            "top_entries": ranked, "opportunities": opportunities, "warnings": warnings,
            "errors": errors, "data_frequency": "EOD", "opportunity_engine": "real_experimental",
            "aviso": EOD_WARNING,
        }
        save_real_opportunities_snapshot(opportunities_snapshot)
    market_snapshots = load_market_snapshots()
    availability = {
        item.get("ticker"): item
        for item in load_options_universe_availability().get("assets", [])
        if item.get("ticker")
    }
    generated_option_assets = {
        item.get("ativo") for item in (opportunities_snapshot or {}).get("opportunities", [])
    }
    graphical_theses = []
    for snapshot in market_snapshots:
        thesis = build_graphical_thesis(snapshot)
        access = availability.get(thesis.get("ativo"), {})
        if access.get("has_options_access"):
            thesis["cadeia_opcoes_status"] = "disponivel_fonte"
            thesis["opcao_validacao"] = (
                "validada_pelo_motor_real_experimental"
                if mode == "close" and thesis.get("ativo") in generated_option_assets
                else "cadeia_disponivel_validacao_pendente"
            )
        else:
            thesis["cadeia_opcoes_status"] = "indisponivel_fonte" if access else "pendente"
            thesis["opcao_validacao"] = "opcao_pendente_validacao_manual"
        thesis["options_validation_candidates"] = [
            item for item in (opportunities_snapshot or {}).get("opportunities", [])
            if item.get("ativo") == thesis.get("ativo")
        ]
        thesis.update(build_strategy_mapping(thesis))
        thesis.update(screen_strategies_for_thesis(thesis))
        thesis.pop("options_validation_candidates", None)
        graphical_theses.append(thesis)
    graphical_theses = rank_graphical_theses(graphical_theses)
    graphical_snapshot = {
        "generated_at": _now(), "mode": mode, "source": "brapi_market_snapshots",
        "tickers": [item.get("ativo") for item in market_snapshots],
        "summary": summarize_graphical_theses(graphical_theses), "theses": graphical_theses,
        "diagnostics": summarize_graphical_diagnostics(graphical_theses),
        "near_setups": rank_near_setups(graphical_theses, 10),
        "data_frequency": "EOD" if mode == "close" else mode,
        "aviso": "Teses gráficas não são ordens. Sem cadeia real, validar opção manualmente no book/corretora.",
    }
    save_graphical_theses_snapshot(graphical_snapshot)
    result = {
        "mode": mode, "runner": runner, "started_at": started_at, "finished_at": _now(),
        "success": not errors, "tickers": market_symbols, "option_tickers": option_symbols,
        "phases": phases, "warnings": warnings,
        "errors": errors, "opportunities_snapshot": opportunities_snapshot,
        "graphical_theses_snapshot": graphical_snapshot,
        "opportunity_engine_mock_status": "separado / preservado",
    }
    status = {"last_run": result, "summary": summarize_pipeline_result(result)}
    save_pipeline_status(status)
    return result
