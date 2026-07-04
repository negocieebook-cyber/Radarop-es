"""Geração explicável de oportunidades sobre universo e opções MOCK / EXEMPLO."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from app.bulkowski_engine import analyze_pattern_for_asset
from app.data_quality import is_missing
from app.healthbox_engine import build_healthbox, healthbox_confirms_strategy, healthbox_score
from app.mock_data import MOCK_ASSET_SNAPSHOTS
from app.options_math import calculate_option_strategy
from app.scoring import score_opportunity
from app.universe import asset_is_eligible, load_asset_universe
from app.validators import build_operation_checklist


CHAIN_PATH = Path(__file__).resolve().parent.parent / "data" / "options_chain_mock.json"
MOCK_TYPE = "MOCK / EXEMPLO"
LIQUIDITY_RANK = {"indisponível": 0, "baixa": 1, "média": 2, "media": 2, "alta": 3}
STRATEGY_NAMES = {
    "call_debit_spread": "Trava de alta com call",
    "put_debit_spread": "Trava de baixa com put",
    "bull_put_spread": "Venda de put travada",
    "bear_call_spread": "Venda de call travada",
    "covered_call": "Venda coberta",
}


def load_options_chain() -> list[dict[str, Any]]:
    try:
        data = json.loads(CHAIN_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def get_options_for_asset(ticker: str) -> list[dict[str, Any]]:
    return [option for option in load_options_chain() if option.get("ativo_objeto") == ticker]


def _premium(option: dict[str, Any], side: str) -> Any:
    preferred = option.get("ask" if side == "buy" else "bid")
    return preferred if not is_missing(preferred) else option.get("premio")


def _liquidity(options: list[dict[str, Any]]) -> str:
    return min((str(item.get("liquidez_status", "indisponível")).lower() for item in options), key=lambda value: LIQUIDITY_RANK.get(value, 0), default="indisponível")


def _spread_status(options: list[dict[str, Any]]) -> tuple[str, float | None]:
    spreads = []
    for option in options:
        bid, ask = option.get("bid"), option.get("ask")
        if not isinstance(bid, (int, float)) or not isinstance(ask, (int, float)) or ask <= 0:
            return "indisponível", None
        midpoint = (bid + ask) / 2
        if midpoint <= 0:
            return "ruim", None
        spreads.append(((ask - bid) / midpoint) * 100)
    worst = max(spreads)
    return ("bom" if worst <= 10 else "médio" if worst <= 25 else "ruim"), round(worst, 2)


def _candidate(strategy: str, ticker: str, legs: list[dict[str, Any]], **inputs: Any) -> dict[str, Any]:
    spread_status, spread_percent = _spread_status(legs)
    return {
        "id": f"{ticker}-{strategy}-" + "-".join(leg["codigo"] for leg in legs),
        "ativo": ticker,
        "estrategia": STRATEGY_NAMES[strategy],
        "tipo_estrutura": strategy,
        "vencimento_dias": legs[0].get("vencimento_dias") if legs else None,
        "legs": [leg["codigo"] for leg in legs],
        "liquidez_status": _liquidity(legs),
        "spread_status": spread_status,
        "spread_percent": spread_percent,
        "fonte": "mock interno",
        "tipo_dado": MOCK_TYPE,
        "status_dado": "mock/exemplo",
        "quantidade": 100,
        **inputs,
    }


def pair_call_debit_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    calls = [item for item in options if item.get("tipo") == "CALL"]
    result = []
    for first, second in combinations(calls, 2):
        low, high = sorted((first, second), key=lambda item: item["strike"])
        if low.get("vencimento") == high.get("vencimento"):
            result.append(_candidate("call_debit_spread", low["ativo_objeto"], [low, high], strike_comprado=low["strike"], strike_vendido=high["strike"], premio_pago=_premium(low, "buy"), premio_recebido=_premium(high, "sell"), delta=low.get("delta"), theta=low.get("theta")))
    return result


def pair_put_debit_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    puts = [item for item in options if item.get("tipo") == "PUT"]
    result = []
    for first, second in combinations(puts, 2):
        low, high = sorted((first, second), key=lambda item: item["strike"])
        if low.get("vencimento") == high.get("vencimento"):
            result.append(_candidate("put_debit_spread", high["ativo_objeto"], [high, low], strike_comprado=high["strike"], strike_vendido=low["strike"], premio_pago=_premium(high, "buy"), premio_recebido=_premium(low, "sell"), delta=high.get("delta"), theta=high.get("theta")))
    return result


def pair_bull_put_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    puts = [item for item in options if item.get("tipo") == "PUT"]
    result = []
    for first, second in combinations(puts, 2):
        low, high = sorted((first, second), key=lambda item: item["strike"])
        if low.get("vencimento") == high.get("vencimento"):
            result.append(_candidate("bull_put_spread", high["ativo_objeto"], [high, low], strike_vendido=high["strike"], strike_comprado=low["strike"], premio_recebido=_premium(high, "sell"), premio_pago=_premium(low, "buy"), delta=high.get("delta"), theta=high.get("theta")))
    return result


def pair_bear_call_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    calls = [item for item in options if item.get("tipo") == "CALL"]
    result = []
    for first, second in combinations(calls, 2):
        low, high = sorted((first, second), key=lambda item: item["strike"])
        if low.get("vencimento") == high.get("vencimento"):
            result.append(_candidate("bear_call_spread", low["ativo_objeto"], [low, high], strike_vendido=low["strike"], strike_comprado=high["strike"], premio_recebido=_premium(low, "sell"), premio_pago=_premium(high, "buy"), delta=low.get("delta"), theta=low.get("theta")))
    return result


def build_covered_call_candidates(asset: dict[str, Any], options: list[dict[str, Any]], asset_snapshot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    price = (asset_snapshot or {}).get("preco_atual")
    calls = [item for item in options if item.get("tipo") == "CALL" and isinstance(price, (int, float)) and item.get("strike", 0) > price]
    return [_candidate("covered_call", asset["ticker"], [call], preco_ativo=price, strike_vendido=call["strike"], premio_recebido=_premium(call, "sell"), strike_comprado="não aplicável", delta=call.get("delta"), theta=call.get("theta")) for call in calls]


def generate_candidates_for_asset(asset: dict[str, Any], options: list[dict[str, Any]], asset_snapshot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    eligibility = asset_is_eligible(asset)
    if not eligibility["eligible"]:
        return [{"id": f"{asset['ticker']}-ineligible", "ativo": asset["ticker"], "estrategia": "nenhuma", "tipo_estrutura": None, "pre_rejected": True, "pre_rejection_reason": eligibility["reason"], "fonte": "mock interno", "tipo_dado": MOCK_TYPE, "status_dado": "mock/exemplo"}]
    if not options:
        return [{"id": f"{asset['ticker']}-no-chain", "ativo": asset["ticker"], "estrategia": "nenhuma", "tipo_estrutura": None, "pre_rejected": True, "pre_rejection_reason": "cadeia de opções mockada ausente", "fonte": "mock interno", "tipo_dado": MOCK_TYPE, "status_dado": "incompleto"}]
    return [*pair_call_debit_spreads(options), *pair_put_debit_spreads(options), *pair_bull_put_spreads(options), *pair_bear_call_spreads(options), *build_covered_call_candidates(asset, options, asset_snapshot)]


def _rejected(candidate: dict[str, Any], reason: str, missing: list[str] | None = None, status: str = "reprovada") -> dict[str, Any]:
    return {**candidate, "status": status, "decisao": "evitar" if status == "reprovada" else "esperar", "motivo": reason, "score": None, "score_result": {"score": None, "status": "score não calculado", "missing_fields": missing or []}, "calculation": {"can_calculate": False, "missing_fields": missing or [], "max_loss": None, "max_profit": None, "break_even": None}, "campos_ausentes": missing or [], "healthbox_status": "indisponível", "bulkowski_status": "indisponível", "risco_status": "não calculado", "tese": reason, "preco_planejado": 0.0, "premio_liquido": "não calculado", "perda_maxima": "não calculado por falta de dados", "ganho_maximo": "não calculado por falta de dados", "break_even": "não calculado por falta de dados", "strike_comprado": candidate.get("strike_comprado", "indisponível"), "strike_vendido": candidate.get("strike_vendido", "indisponível"), "delta": candidate.get("delta", "indisponível"), "theta": candidate.get("theta", "indisponível")}


def evaluate_candidate(candidate: dict[str, Any], asset_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    if candidate.get("pre_rejected"):
        return _rejected(candidate, candidate["pre_rejection_reason"])
    calculation = calculate_option_strategy(candidate)
    if not calculation["can_calculate"]:
        return _rejected(candidate, "cálculo de risco não realizado", calculation["missing_fields"])
    if any(is_missing(calculation.get(field)) for field in ("max_loss", "max_profit", "break_even")):
        return _rejected(candidate, "perda, ganho máximo ou break-even indisponível")
    if candidate.get("liquidez_status") in {"baixa", "indisponível"}:
        return _rejected(candidate, "liquidez insuficiente; prêmio alto não compensa ausência de liquidez")
    if candidate.get("spread_status") in {"ruim", "indisponível"}:
        return _rejected(candidate, "spread bid/ask ruim ou indisponível")
    if not asset_snapshot:
        return _rejected(candidate, "snapshot gráfico crítico ausente", ["asset_snapshot"], "score não calculado")

    healthbox = build_healthbox(asset_snapshot)
    health_result = healthbox_score(healthbox)
    health_confirmation = healthbox_confirms_strategy(healthbox, candidate["tipo_estrutura"])
    bulkowski = analyze_pattern_for_asset(asset_snapshot)
    graph_status = "confirmado" if bulkowski.get("confirmacao") == "confirmado no mock" else "pendente"
    enriched = {**candidate, "calculation": calculation, "perda_maxima": calculation["max_loss"], "ganho_maximo": calculation["max_profit"], "break_even": calculation["break_even"], "grafico_status": graph_status, "healthbox": healthbox, "healthbox_confirmation": health_confirmation}
    score_result = score_opportunity(enriched)
    if score_result["score"] is None or health_result["score"] is None:
        missing = list(dict.fromkeys([*score_result.get("missing_fields", []), *health_result.get("missing_fields", [])]))
        return _rejected(candidate, "score não calculado por falta de dados críticos", missing, "score não calculado")
    rr = calculation.get("risk_reward")
    if candidate["tipo_estrutura"] != "covered_call" and isinstance(rr, (int, float)) and rr < 0.5:
        return _rejected(candidate, "relação risco/retorno inferior ao mínimo mockado")
    if health_confirmation == "não confirma":
        return _rejected(candidate, "Healthbox contraria a estratégia")

    attention_reasons = []
    if candidate.get("liquidez_status") in {"média", "media"}:
        attention_reasons.append("liquidez média")
    if candidate.get("spread_status") == "médio":
        attention_reasons.append("spread médio")
    if health_confirmation == "atenção":
        attention_reasons.append("Healthbox em atenção")
    if bulkowski.get("status") in {"inconclusivo", "padrão não detectado"}:
        attention_reasons.append("Bulkowski inconclusivo")
    if (candidate.get("vencimento_dias") or 999) <= 14:
        attention_reasons.append("vencimento curto")
    status = "atenção" if attention_reasons else "aprovada"
    decision = "acompanhar" if attention_reasons else "estudar"
    reason = "; ".join(attention_reasons) if attention_reasons else "risco definido, liquidez mínima e filtros confirmados no mock"
    net = calculation.get("net_cost") if calculation.get("net_cost") is not None else calculation.get("net_credit")
    per_lot = calculation.get("per_lot") or {}
    result = {
        **enriched,
        "status": status,
        "decisao": decision,
        "motivo": reason,
        "tese": reason,
        "score": score_result["score"],
        "score_result": score_result,
        "cálculo": calculation,
        "campos_ausentes": [],
        "healthbox_status": health_confirmation,
        "healthbox_score_result": health_result,
        "bulkowski_status": bulkowski.get("status"),
        "bulkowski_analysis": bulkowski,
        "bulkowski_alignment": "favorece/acompanha a estratégia somente no cenário MOCK" if bulkowski.get("pattern_detected") else "Bulkowski: inconclusivo por falta de dados.",
        "risco_status": "calculado",
        "checklist": build_operation_checklist(enriched),
        "preco_planejado": net or 0.0,
        "premio_liquido": net,
        "perda_maxima": per_lot.get("max_loss", calculation["max_loss"]),
        "ganho_maximo": per_lot.get("max_profit", calculation["max_profit"]),
        "break_even": calculation["break_even"],
        "delta": candidate.get("delta", "indisponível"),
        "theta": candidate.get("theta", "indisponível"),
    }
    return result


def generate_daily_opportunities() -> list[dict[str, Any]]:
    chain = load_options_chain()
    results = []
    for asset in load_asset_universe():
        snapshot = next((item for item in MOCK_ASSET_SNAPSHOTS if item.get("ativo") == asset["ticker"]), None)
        candidates = generate_candidates_for_asset(asset, [item for item in chain if item.get("ativo_objeto") == asset["ticker"]], snapshot)
        results.extend(evaluate_candidate(candidate, snapshot) for candidate in candidates)
    return results


def split_opportunities_by_status(opportunities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"aprovada": [], "atenção": [], "reprovada": [], "score não calculado": []}
    for opportunity in opportunities:
        groups.setdefault(opportunity.get("status", "reprovada"), []).append(opportunity)
    return groups
