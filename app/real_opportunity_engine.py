"""Opportunity Engine real EOD experimental, separado do motor mockado."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.healthbox_engine import build_healthbox, healthbox_confirms_strategy, healthbox_score
from app.conditional_entry_engine import calculate_entry_conditions, summarize_conditional_entries
from app.funnel_diagnostics import what_needs_to_change
from app.options_math import calculate_option_strategy
from app.providers.brapi_options_provider import PRICE_ALIASES, pick_first_available, to_float_or_none
from app.options_update_orchestrator import OPTIONS_SNAPSHOTS_DIR
from app.update_orchestrator import SNAPSHOTS_FILE


REAL_DATA_TYPE = "DADOS REAIS EOD / EXPERIMENTAL"
EOD_WARNING = "Preço indicativo EOD; não usar como ordem a mercado."
STRATEGY_NAMES = {
    "call_debit_spread": "Trava de alta com call",
    "put_debit_spread": "Trava de baixa com put",
    "bull_put_spread": "Venda de put travada",
    "bear_call_spread": "Venda de call travada",
}


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def load_real_market_snapshots() -> list[dict[str, Any]]:
    value = _read(SNAPSHOTS_FILE, [])
    return value if isinstance(value, list) else []


def load_real_options_snapshots() -> dict[str, dict[str, Any]]:
    if not OPTIONS_SNAPSHOTS_DIR.exists():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(OPTIONS_SNAPSHOTS_DIR.glob("*.json")):
        value = _read(path, {})
        if isinstance(value, dict):
            result[path.stem.upper()] = value
    return result


def get_market_snapshot_for_asset(ticker: str) -> dict[str, Any] | None:
    symbol = str(ticker).strip().upper()
    return next((item for item in load_real_market_snapshots() if str(item.get("ativo", "")).upper() == symbol), None)


def get_options_snapshot_for_asset(ticker: str) -> dict[str, Any] | None:
    return load_real_options_snapshots().get(str(ticker).strip().upper())


def resolve_option_price(option: dict[str, Any]) -> dict[str, Any]:
    bid, ask = _number(option.get("bid")), _number(option.get("ask"))
    if bid is not None and ask is not None:
        mid = (bid + ask) / 2
        if mid > 0:
            return {"price": round(mid, 6), "price_basis": "mid", "is_executable_price": True, "warning": "Mid calculado de bid/ask EOD; confirmar no pregão."}
    close = _number(option.get("close"))
    if close is not None and close > 0:
        return {"price": close, "price_basis": "close_eod", "is_executable_price": False, "warning": EOD_WARNING}
    average = _number(option.get("average"))
    if average is not None and average > 0:
        return {"price": average, "price_basis": "average_eod", "is_executable_price": False, "warning": EOD_WARNING}
    alias_value = _number(option.get("price_alias_value"))
    alias_source = option.get("price_alias_source")
    if alias_value is None and isinstance(option.get("raw"), dict):
        raw_value, raw_source = pick_first_available(option["raw"], PRICE_ALIASES)
        alias_value, alias_source = to_float_or_none(raw_value), raw_source
    if alias_value is not None and alias_value > 0 and alias_source:
        return {"price": alias_value, "price_basis": f"alias_eod:{alias_source}", "is_executable_price": False, "warning": EOD_WARNING}
    zero_fields = [field for field in ("bid", "ask", "close", "average") if _number(option.get(field)) == 0]
    basis = "preço_zerado" if zero_fields else "indisponível"
    warning = f"Preço zerado nos campos: {', '.join(zero_fields)}; não utilizado." if zero_fields else "Preço da opção indisponível nos dados EOD."
    return {"price": None, "price_basis": basis, "is_executable_price": False, "warning": warning}


def _indicative_price(option: dict[str, Any]) -> dict[str, Any]:
    """Compatibilidade interna e com validações anteriores."""
    return resolve_option_price(option)


def _liquidity(options: list[dict[str, Any]]) -> str:
    rank = {"alta": 4, "média": 3, "baixa": 2, "indisponível": 1, "ilíquida": 0}
    values = [str(item.get("liquidity_status") or "indisponível") for item in options]
    return min(values, key=lambda value: rank.get(value, 1)) if values else "indisponível"


def _days(expiration: Any) -> int | None:
    try:
        return (date.fromisoformat(str(expiration)) - datetime.now(timezone.utc).date()).days
    except (TypeError, ValueError):
        return None


def _make_candidate(strategy: str, bought: dict[str, Any], sold: dict[str, Any]) -> dict[str, Any]:
    bought_price, sold_price = _indicative_price(bought), _indicative_price(sold)
    basis = f"compra:{bought_price['price_basis']} | venda:{sold_price['price_basis']}"
    missing = []
    if bought_price["price"] is None:
        missing.append("preço da opção comprada")
    if sold_price["price"] is None:
        missing.append("preço da opção vendida")
    if bought.get("strike") is None:
        missing.append("strike comprado")
    if sold.get("strike") is None:
        missing.append("strike vendido")
    expiration = bought.get("expiration_date")
    return {
        "ativo": bought.get("underlying_symbol") or sold.get("underlying_symbol"),
        "estrategia": STRATEGY_NAMES[strategy], "tipo_estrutura": strategy,
        "opcoes_usadas": [bought.get("symbol"), sold.get("symbol")], "vencimento": expiration,
        "vencimento_dias": _days(expiration), "strike_comprado": bought.get("strike"),
        "strike_vendido": sold.get("strike"), "premio_pago": bought_price["price"],
        "premio_recebido": sold_price["price"], "quantidade": 100,
        "price_basis": basis, "is_executable_price": bought_price["is_executable_price"] and sold_price["is_executable_price"],
        "aviso_preco": f"Compra: {bought_price['warning']} Venda: {sold_price['warning']}", "liquidez": _liquidity([bought, sold]),
        "spread_disponivel": bought.get("spread_pct") is not None and sold.get("spread_pct") is not None,
        "campos_ausentes": missing, "fonte": "brapi_options", "coleta": max(str(bought.get("date") or ""), str(sold.get("date") or "")) or None,
        "tipo_dado": REAL_DATA_TYPE, "status_dado": "experimental EOD",
    }


def _pairs(options: list[dict[str, Any]], side: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    eligible = [
        item for item in options
        if item.get("side") == side and item.get("fonte") == "brapi_options"
        and item.get("liquidity_status") != "ilíquida" and resolve_option_price(item)["price"] is not None
        and _number(item.get("strike")) is not None and item.get("expiration_date")
    ]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in eligible:
        key = (str(item.get("underlying_symbol") or ""), str(item["expiration_date"]))
        grouped.setdefault(key, []).append(item)
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for key in sorted(grouped):
        ordered = sorted(grouped[key], key=lambda item: float(item["strike"]))
        pairs.extend(zip(ordered, ordered[1:]))
    return pairs


def diagnose_pairing_inputs(options: list[dict[str, Any]]) -> dict[str, Any]:
    calls = [item for item in options if item.get("side") == "call"]
    puts = [item for item in options if item.get("side") == "put"]
    calls_price = [item for item in calls if resolve_option_price(item)["price"] is not None]
    puts_price = [item for item in puts if resolve_option_price(item)["price"] is not None]
    liquid = [item for item in options if item.get("liquidity_status") != "ilíquida"]
    return {
        "calls_available": len(calls), "puts_available": len(puts),
        "calls_with_price": len(calls_price), "puts_with_price": len(puts_price),
        "possible_call_pairs": max(0, len([item for item in calls_price if item.get("liquidity_status") != "ilíquida"]) - 1),
        "possible_put_pairs": max(0, len([item for item in puts_price if item.get("liquidity_status") != "ilíquida"]) - 1),
        "discarded_missing_price": len(options) - len(calls_price) - len(puts_price),
        "discarded_illiquid": len(options) - len(liquid),
        "discarded_missing_expiration": sum(not item.get("expiration_date") for item in options),
    }


def pair_real_call_debit_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_make_candidate("call_debit_spread", lower, higher) for lower, higher in _pairs(options, "call")]


def pair_real_put_debit_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_make_candidate("put_debit_spread", higher, lower) for lower, higher in _pairs(options, "put")]


def pair_real_bull_put_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_make_candidate("bull_put_spread", lower, higher) for lower, higher in _pairs(options, "put")]


def pair_real_bear_call_spreads(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_make_candidate("bear_call_spread", higher, lower) for lower, higher in _pairs(options, "call")]


def _score(candidate: dict[str, Any], calculation: dict[str, Any], healthbox_result: dict[str, Any], confirmation: str) -> dict[str, Any]:
    critical = list(candidate.get("campos_ausentes", []))
    if not calculation.get("can_calculate"):
        critical.extend(calculation.get("missing_fields", []))
    if healthbox_result.get("score") is None:
        critical.extend(healthbox_result.get("missing_fields", []))
    if critical:
        return {"score": None, "score_status": "não calculado por falta de dados", "breakdown": {}, "missing_fields": list(dict.fromkeys(critical))}
    liquidity_points = {"alta": 20, "média": 15, "baixa": 8, "indisponível": 0}.get(candidate.get("liquidez"), 0)
    rr = _number(calculation.get("risk_reward"))
    breakdown = {
        "matemática": 25, "liquidez": liquidity_points,
        "healthbox": round(min(20, healthbox_result["score"] * 0.2)),
        "risco_retorno": 15 if rr is not None and rr >= 1 else 10 if rr is not None and rr >= 0.5 else 5,
        "vencimento": 10 if candidate.get("vencimento_dias") is not None and 15 <= candidate["vencimento_dias"] <= 90 else 5,
        "fonte_coleta": 10 if candidate.get("fonte") and candidate.get("coleta") else 0,
    }
    return {"score": min(100, sum(breakdown.values())), "score_status": "experimental calculado", "breakdown": breakdown, "missing_fields": []}


def evaluate_real_candidate(candidate: dict[str, Any], market_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    calculation = calculate_option_strategy(candidate)
    if market_snapshot is None:
        healthbox = None
        health_score = {"score": None, "status": "indisponível", "missing_fields": ["snapshot de mercado"], "breakdown": {}}
        confirmation = "indisponível por falta de dados"
    else:
        healthbox = build_healthbox(market_snapshot)
        health_score = healthbox_score(healthbox)
        confirmation = healthbox_confirms_strategy(healthbox, str(candidate.get("tipo_estrutura")))
    score = _score(candidate, calculation, health_score, confirmation)
    math_complete = calculation.get("can_calculate") and all(calculation.get(field) is not None for field in ("max_loss", "max_profit", "break_even"))
    reasons: list[str] = []
    if market_snapshot is None:
        status, decision = "inconclusivo", "evitar"
        reasons.append("sem snapshot de mercado real")
    elif not math_complete:
        status, decision = "evitar", "evitar"
        reasons.append("matemática incompleta")
    elif candidate.get("liquidez") == "ilíquida":
        status, decision = "evitar", "evitar"
        reasons.append("liquidez ilíquida")
    elif _number(calculation.get("risk_reward")) is not None and float(calculation["risk_reward"]) < 0.25:
        status, decision = "evitar", "evitar"
        reasons.append("risco/retorno ruim")
    elif confirmation == "não confirma":
        status, decision = "evitar", "evitar"
        reasons.append("Healthbox real contraria a estrutura")
    else:
        attention = []
        if not candidate.get("is_executable_price"):
            attention.append("preço baseado em close/average EOD")
        if confirmation != "confirma":
            attention.append("Healthbox em atenção")
        if candidate.get("liquidez") in {"baixa", "indisponível"}:
            attention.append("liquidez baixa ou indisponível")
        if candidate.get("vencimento_dias") is not None and candidate["vencimento_dias"] <= 7:
            attention.append("vencimento muito curto")
        if not candidate.get("spread_disponivel"):
            attention.append("spread bid/ask indisponível")
        attention.append("Bulkowski real ainda não integrado")
        if attention:
            status, decision, reasons = "atenção", "Estudar amanhã / dados EOD", attention
        else:
            status, decision, reasons = "estudar", "Estudar amanhã / dados EOD", ["critérios experimentais mínimos atendidos"]
    missing = list(dict.fromkeys(candidate.get("campos_ausentes", []) + calculation.get("missing_fields", []) + score.get("missing_fields", [])))
    result = {
        **candidate, "calculation": calculation, "custo_liquido": calculation.get("net_cost"),
        "credito_liquido": calculation.get("net_credit"), "ganho_maximo": calculation.get("max_profit"),
        "perda_maxima": calculation.get("max_loss"), "break_even": calculation.get("break_even"),
        "risco_retorno": calculation.get("risk_reward"), "healthbox": healthbox,
        "healthbox_score": health_score.get("score"), "healthbox_status": confirmation,
        "tendencia": market_snapshot.get("tendencia") if market_snapshot else None,
        "rsi": market_snapshot.get("rsi") if market_snapshot else None,
        "atr": market_snapshot.get("atr_percent") if market_snapshot else None,
        "rvol": market_snapshot.get("rvol") if market_snapshot else None,
        "suporte": market_snapshot.get("suporte") if market_snapshot else None,
        "resistencia": market_snapshot.get("resistencia") if market_snapshot else None,
        **score, "status": status, "decisao": decision, "motivo": "; ".join(reasons),
        "campos_ausentes": missing,
    }
    result.update(calculate_entry_conditions(result))
    result["what_needs_to_change"] = what_needs_to_change(result)
    return result


def _inconclusive(ticker: str, reason: str, options_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {
        "ativo": ticker, "estrategia": "indisponível", "tipo_estrutura": None, "status": "inconclusivo",
        "decisao": "evitar", "motivo": reason, "score": None,
        "score_status": "não calculado por falta de dados", "vencimento": None,
        "strike_comprado": None, "strike_vendido": None, "price_basis": "indisponível",
        "is_executable_price": False, "aviso_preco": EOD_WARNING, "perda_maxima": None,
        "ganho_maximo": None, "break_even": None, "risco_retorno": None,
        "healthbox_score": None, "healthbox_status": "indisponível", "liquidez": "indisponível",
        "campos_ausentes": [reason], "fonte": "brapi_options", "coleta": (options_snapshot or {}).get("coleta"),
        "tipo_dado": REAL_DATA_TYPE, "status_dado": (options_snapshot or {}).get("status_dado", "indisponível"),
    }
    result.update(calculate_entry_conditions(result))
    result["what_needs_to_change"] = what_needs_to_change(result)
    return result


def build_real_candidates_for_asset(ticker: str) -> list[dict[str, Any]]:
    symbol = str(ticker).strip().upper()
    options_snapshot = get_options_snapshot_for_asset(symbol)
    if not options_snapshot:
        return [_inconclusive(symbol, "sem snapshot de opções")]
    if options_snapshot.get("access_status") == "sem_acesso":
        return [_inconclusive(symbol, "sem acesso no plano atual", options_snapshot)]
    if not options_snapshot.get("success") or not options_snapshot.get("series"):
        return [_inconclusive(symbol, options_snapshot.get("error") or "opções indisponíveis na fonte atual", options_snapshot)]
    market = get_market_snapshot_for_asset(symbol)
    price = _number((market or {}).get("preco_atual"))
    chains = options_snapshot.get("chains") if isinstance(options_snapshot.get("chains"), list) else []
    if not chains:
        chains = [{
            "expiration_date": options_snapshot.get("expiration_used"),
            "vencimento_dias": _days(options_snapshot.get("expiration_used")),
            "series": options_snapshot.get("series", []),
        }]
    chains = sorted(chains, key=lambda chain: (0 if isinstance(chain.get("vencimento_dias"), int) and 15 <= chain["vencimento_dias"] <= 45 else 1, chain.get("vencimento_dias") if isinstance(chain.get("vencimento_dias"), int) else 999))
    raw: list[dict[str, Any]] = []
    empty_chains: list[dict[str, Any]] = []
    for chain in chains:
        options = list(chain.get("series", []))
        pairing_diagnostics = diagnose_pairing_inputs(options)
        pairing_options = [
            item for item in options
            if item.get("liquidity_status") != "ilíquida"
            and resolve_option_price(item)["price"] is not None
            and _number(item.get("strike")) is not None
            and item.get("expiration_date")
        ]
        if price is not None:
            pairing_options = sorted(pairing_options, key=lambda item: abs((_number(item.get("strike")) or price) - price))[:32]
        chain_candidates = (
            pair_real_call_debit_spreads(pairing_options) + pair_real_put_debit_spreads(pairing_options)
            + pair_real_bull_put_spreads(pairing_options) + pair_real_bear_call_spreads(pairing_options)
        )[:30]
        if not chain_candidates:
            empty_chains.append(chain)
        for candidate in chain_candidates:
            candidate["vencimento"] = chain.get("expiration_date") or candidate.get("vencimento")
            candidate["vencimento_dias"] = chain.get("vencimento_dias") if chain.get("vencimento_dias") is not None else _days(candidate.get("vencimento"))
            candidate["expiration_source"] = "options_snapshot.chains" if options_snapshot.get("chains") else "snapshot_legado"
            candidate["data_frequency"] = "EOD"
            candidate["pairing_diagnostics"] = pairing_diagnostics
        raw.extend(chain_candidates)
        if len(raw) >= 120:
            raw = raw[:120]
            break
    if not raw and not empty_chains:
        return [_inconclusive(symbol, "nenhum pareamento elegível com preço indicativo disponível", options_snapshot)]
    for candidate in raw:
        candidate["coleta"] = options_snapshot.get("coleta")
    evaluated = [evaluate_real_candidate(candidate, market) for candidate in raw]
    for chain in empty_chains:
        placeholder = _inconclusive(symbol, "nenhum pareamento elegível neste vencimento", options_snapshot)
        placeholder.update(
            vencimento=chain.get("expiration_date"), vencimento_dias=chain.get("vencimento_dias"),
            expiration_source="options_snapshot.chains", data_frequency="EOD",
        )
        placeholder.update(calculate_entry_conditions(placeholder))
        placeholder["what_needs_to_change"] = what_needs_to_change(placeholder)
        evaluated.append(placeholder)
    return evaluated[:120]


def generate_real_eod_opportunities(tickers: list[str] | None = None) -> list[dict[str, Any]]:
    symbols = tickers or sorted(set(load_real_options_snapshots()) | {str(item.get("ativo")) for item in load_real_market_snapshots() if item.get("ativo")})
    return [candidate for symbol in symbols for candidate in build_real_candidates_for_asset(symbol)]


def split_real_opportunities_by_status(opportunities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {status: [item for item in opportunities if item.get("status") == status] for status in ("estudar", "atenção", "evitar", "inconclusivo")}


def summarize_real_opportunities(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(item.get("status", "inconclusivo") for item in opportunities)
    assets = sorted({str(item.get("ativo")) for item in opportunities if item.get("ativo")})
    options_snapshots = load_real_options_snapshots()
    with_options = [symbol for symbol in assets if options_snapshots.get(symbol, {}).get("success") and options_snapshots[symbol].get("series")]
    conditional = summarize_conditional_entries(opportunities)
    return {
        "assets_analyzed": len(assets), "assets_with_options": len(with_options),
        "assets_without_options": len(assets) - len(with_options), "candidates": len(opportunities),
        "estudar": counts["estudar"], "atenção": counts["atenção"], "evitar": counts["evitar"],
        "inconclusivo": counts["inconclusivo"], "data_type": REAL_DATA_TYPE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "conditional": conditional,
    }
