"""Simulações manuais de opções, sem cotação, corretora ou envio de ordens."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.capital_requirements import TOLERANCE_BUFFER
from app.storage import load_json, save_json


ROOT = Path(__file__).resolve().parent.parent
MANUAL_SIMULATIONS_PATH = ROOT / "data" / "runtime" / "manual_simulations.json"
MANUAL_WARNING = "Simulação manual; conferir book, liquidez, spread, exercício e perda máxima. Não é ordem."
SUPPORTED_STRATEGIES = (
    "long_call", "long_put", "call_debit_spread", "put_debit_spread",
    "bull_put_spread", "bear_call_spread", "iron_condor", "iron_butterfly",
    "covered_call", "cash_secured_put", "protective_put", "collar",
)
LEG_TEMPLATES = {
    "long_call": [("call", "buy")],
    "long_put": [("put", "buy")],
    "call_debit_spread": [("call", "buy"), ("call", "sell")],
    "put_debit_spread": [("put", "buy"), ("put", "sell")],
    "bull_put_spread": [("put", "sell"), ("put", "buy")],
    "bear_call_spread": [("call", "sell"), ("call", "buy")],
    "iron_condor": [("put", "buy"), ("put", "sell"), ("call", "sell"), ("call", "buy")],
    "iron_butterfly": [("put", "buy"), ("put", "sell"), ("call", "sell"), ("call", "buy")],
    "covered_call": [("stock", "buy"), ("call", "sell")],
    "cash_secured_put": [("put", "sell")],
    "protective_put": [("stock", "buy"), ("put", "buy")],
    "collar": [("stock", "buy"), ("put", "buy"), ("call", "sell")],
}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_manual_simulations() -> list[dict[str, Any]]:
    value = load_json(MANUAL_SIMULATIONS_PATH, [])
    return value if isinstance(value, list) else []


def list_manual_simulations() -> list[dict[str, Any]]:
    return sorted(load_manual_simulations(), key=lambda item: str(item.get("created_at") or ""), reverse=True)


def save_manual_simulation(simulation: dict[str, Any]) -> dict[str, Any]:
    item = {**simulation}
    item.setdefault("simulation_id", str(uuid4()))
    item.setdefault("created_at", datetime.now().astimezone().isoformat(timespec="seconds"))
    item["source"] = "manual"
    records = load_manual_simulations()
    records = [record for record in records if record.get("simulation_id") != item["simulation_id"]]
    records.append(item)
    save_json(MANUAL_SIMULATIONS_PATH, records)
    return item


def delete_manual_simulation(simulation_id: str) -> bool:
    records = load_manual_simulations()
    kept = [item for item in records if str(item.get("simulation_id")) != str(simulation_id)]
    if len(kept) == len(records):
        return False
    save_json(MANUAL_SIMULATIONS_PATH, kept)
    return True


def build_manual_simulation_from_strategy(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any]
) -> dict[str, Any]:
    strategy_id = str(strategy_candidate.get("strategy_id") or strategy_candidate.get("id") or "")
    expiration = strategy_candidate.get("expiration")
    legs = [
        {"type": leg_type, "action": action, "strike": None, "premium": None, "quantity": 1, "expiration": expiration}
        for leg_type, action in LEG_TEMPLATES.get(strategy_id, [])
    ]
    return {
        "simulation_id": str(uuid4()),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "manual",
        "ticker": thesis.get("ativo") or thesis.get("ticker"),
        "strategy_id": strategy_id,
        "strategy_name": strategy_candidate.get("strategy_name") or strategy_candidate.get("nome") or strategy_id,
        "objective_label": strategy_candidate.get("objective_label"),
        "thesis_status": thesis.get("status"),
        "regime": thesis.get("market_regime"),
        "expiration": expiration,
        "quantity": 1,
        "contract_multiplier": None,
        "has_underlying_position": False,
        "legs": legs,
    }


def _leg(simulation: dict[str, Any], leg_type: str, action: str) -> list[dict[str, Any]]:
    return [item for item in simulation.get("legs", []) if item.get("type") == leg_type and item.get("action") == action]


def _premium_total(legs: list[dict[str, Any]]) -> float:
    return sum((_number(item.get("premium")) or 0) * (_number(item.get("quantity")) or 1) for item in legs)


def _finish(simulation: dict[str, Any], values: dict[str, Any], missing: list[str], profile: dict[str, Any]) -> dict[str, Any]:
    for field in (
        "net_debit", "net_credit", "max_loss", "max_gain", "capital_required",
        "credit_to_width", "risk_note",
    ):
        values.setdefault(field, None)
    values.setdefault("break_even_points", [])
    quantity = _number(simulation.get("quantity"))
    multiplier = _number(simulation.get("contract_multiplier"))
    if quantity is None or quantity <= 0:
        missing.append("quantidade")
    if multiplier is None or multiplier <= 0:
        missing.append("multiplicador do contrato")
    scale = quantity * multiplier if quantity and quantity > 0 and multiplier and multiplier > 0 else None
    for field in ("net_debit", "net_credit", "max_loss", "max_gain", "capital_required"):
        value = values.get(field)
        if isinstance(value, (int, float)) and scale is not None and not values.get(f"{field}_already_total"):
            values[field] = round(value * scale, 2)
    values.pop("capital_required_already_total", None)
    values.pop("max_loss_already_total", None)
    values.pop("max_gain_already_total", None)
    values["break_even_points"] = [round(value, 4) for value in values.get("break_even_points", [])]
    values["missing_fields"] = list(dict.fromkeys(missing))
    values["source"] = "manual"
    values["warning"] = MANUAL_WARNING
    capital = _number(values.get("capital_required"))
    factor = TOLERANCE_BUFFER.get(str(profile.get("tolerancia_capital")), 1.25)
    values["recommended_capital"] = round(capital * factor, 2) if capital is not None else None
    loss = _number(values.get("max_loss"))
    gain = _number(values.get("max_gain"))
    values["risk_reward_ratio"] = round(gain / loss, 4) if gain is not None and loss and loss > 0 else None
    values.update(classify_manual_simulation_fit({**simulation, **values}, profile))
    return {**simulation, **values}


def calculate_manual_strategy_risk(simulation: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    strategy = str(simulation.get("strategy_id") or "")
    if strategy not in SUPPORTED_STRATEGIES:
        return _finish(simulation, {}, ["estratégia suportada"], profile)
    legs = simulation.get("legs", [])
    missing = []
    for index, item in enumerate(legs, 1):
        if item.get("type") != "stock" and _number(item.get("strike")) is None:
            missing.append(f"strike perna {index}")
        if _number(item.get("premium")) is None:
            missing.append(f"preço/prêmio perna {index}")
    if missing:
        return _finish(simulation, {}, missing, profile)

    buys = [item for item in legs if item.get("action") == "buy" and item.get("type") != "stock"]
    sells = [item for item in legs if item.get("action") == "sell"]
    debit = _premium_total(buys) - _premium_total(sells)
    credit = -debit
    values: dict[str, Any] = {"net_debit": round(debit, 4) if debit > 0 else None, "net_credit": round(credit, 4) if credit > 0 else None, "credit_to_width": None}

    if strategy in {"long_call", "long_put"}:
        option = legs[0]; strike = _number(option["strike"]); premium = _number(option["premium"])
        values.update(max_loss=premium, capital_required=premium, max_gain="ilimitado" if strategy == "long_call" else strike - premium, break_even_points=[strike + premium if strategy == "long_call" else strike - premium])
    elif strategy in {"call_debit_spread", "put_debit_spread", "bull_put_spread", "bear_call_spread"}:
        bought, sold = buys[0], sells[0]
        width = abs(_number(bought["strike"]) - _number(sold["strike"]))
        is_debit = strategy in {"call_debit_spread", "put_debit_spread"}
        net = debit if is_debit else credit
        if net < 0 or net > width:
            missing.append("prêmios compatíveis com a largura")
        else:
            loss = net if is_debit else width - net
            gain = width - net if is_debit else net
            sold_strike = _number(sold["strike"]); bought_strike = _number(bought["strike"])
            break_even = (bought_strike - net if strategy == "put_debit_spread" else bought_strike + net) if is_debit else (sold_strike - net if strategy == "bull_put_spread" else sold_strike + net)
            values.update(max_loss=loss, max_gain=gain, capital_required=loss, break_even_points=[break_even], credit_to_width=round(net / width, 4) if not is_debit and width else None)
    elif strategy in {"iron_condor", "iron_butterfly"}:
        put_bought = _leg(simulation, "put", "buy")[0]; put_sold = _leg(simulation, "put", "sell")[0]
        call_sold = _leg(simulation, "call", "sell")[0]; call_bought = _leg(simulation, "call", "buy")[0]
        put_width = abs(_number(put_sold["strike"]) - _number(put_bought["strike"]))
        call_width = abs(_number(call_bought["strike"]) - _number(call_sold["strike"]))
        width = max(put_width, call_width)
        if credit < 0 or credit > width:
            missing.append("crédito compatível com a maior largura")
        else:
            loss = width - credit
            values.update(max_loss=loss, max_gain=credit, capital_required=loss, break_even_points=[_number(put_sold["strike"]) - credit, _number(call_sold["strike"]) + credit], credit_to_width=round(credit / width, 4) if width else None)
    elif strategy == "cash_secured_put":
        sold = sells[0]; strike = _number(sold["strike"]); premium = _number(sold["premium"])
        values.update(net_credit=premium, max_loss=strike - premium, max_gain=premium, capital_required=strike, break_even_points=[strike - premium])
    else:
        stock = _leg(simulation, "stock", "buy")[0]
        stock_price = _number(stock.get("premium"))
        if strategy == "covered_call":
            call = _leg(simulation, "call", "sell")[0]; premium = _number(call["premium"]); strike = _number(call["strike"])
            values.update(net_credit=premium, max_loss=stock_price - premium, max_gain=strike - stock_price + premium, capital_required=stock_price, break_even_points=[stock_price - premium], risk_note="Risco principal: queda do ativo, descontado o prêmio recebido.")
            if not simulation.get("has_underlying_position"): missing.append("ativo em carteira")
        elif strategy == "protective_put":
            put = _leg(simulation, "put", "buy")[0]; premium = _number(put["premium"]); strike = _number(put["strike"])
            values.update(net_debit=premium, max_loss=stock_price - strike + premium, max_gain="ilimitado", capital_required=stock_price + premium, break_even_points=[stock_price + premium])
        else:
            put = _leg(simulation, "put", "buy")[0]; call = _leg(simulation, "call", "sell")[0]
            net = _number(put["premium"]) - _number(call["premium"])
            values.update(net_debit=net if net > 0 else None, net_credit=-net if net < 0 else None, max_loss=stock_price - _number(put["strike"]) + net, max_gain=_number(call["strike"]) - stock_price - net, capital_required=stock_price + max(net, 0), break_even_points=[stock_price + net])
    return _finish(simulation, values, missing, profile)


def classify_manual_simulation_fit(simulation: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
    missing = simulation.get("missing_fields") or []
    if simulation.get("strategy_id") == "covered_call" and "ativo em carteira" in missing:
        return {"capital_fit_status": "exige_ativo_em_carteira", "capital_fit_reason": "A simulação exige ativo em carteira; posição não confirmada."}
    capital = _number(simulation.get("capital_required")); loss = _number(simulation.get("max_loss"))
    available = _number(profile.get("capital_disponivel"))
    if missing or capital is None or loss is None or available is None:
        return {"capital_fit_status": "pendente_dados", "capital_fit_reason": "Faltam dados manuais, perda máxima ou capital disponível."}
    limits = []
    if _number(profile.get("perda_maxima_por_operacao")) is not None: limits.append(_number(profile["perda_maxima_por_operacao"]))
    if _number(profile.get("percentual_maximo_por_operacao")) is not None: limits.append(available * _number(profile["percentual_maximo_por_operacao"]) / 100)
    limit = min(limits) if limits else None
    if simulation.get("strategy_id") == "cash_secured_put" and capital > available:
        return {"capital_fit_status": "exige_caixa_para_exercicio", "capital_fit_reason": "O caixa informado não cobre eventual exercício."}
    if capital > available or (limit is not None and loss > limit):
        return {"capital_fit_status": "acima_do_capital", "capital_fit_reason": "Capital requerido ou perda máxima excede o limite informado."}
    if capital > available * 0.5 or (limit is not None and loss > limit * 0.8):
        return {"capital_fit_status": "cabe_apertado", "capital_fit_reason": "Cabe, mas ocupa parte relevante do capital ou do limite de perda."}
    return {"capital_fit_status": "cabe_bem", "capital_fit_reason": "Capital e perda máxima estão dentro dos limites manuais informados."}
