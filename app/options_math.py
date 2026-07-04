"""Cálculos determinísticos de opções, sem obtenção ou inferência de dados."""

from __future__ import annotations

from typing import Any, Callable

from app.data_quality import is_missing, missing_fields


def _number(value: Any) -> float | None:
    if is_missing(value) or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _base(strategy: str, missing: list[str]) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "can_calculate": False,
        "missing_fields": missing,
        "net_cost": None,
        "net_credit": None,
        "max_profit": None,
        "max_loss": None,
        "break_even": None,
        "risk_reward": None,
        "per_unit": None,
        "per_lot": None,
        "notes": ["não calculado por falta de dados"] if missing else [],
    }


def _finish(
    result: dict[str, Any], quantity: Any, monetary_fields: tuple[str, ...]
) -> dict[str, Any]:
    result["can_calculate"] = True
    result["per_unit"] = {
        field: result[field]
        for field in (*monetary_fields, "break_even", "risk_reward")
        if field in result
    }
    qty = _number(quantity)
    if qty is None:
        result["notes"].append("quantidade ausente; valores por lote não calculados")
        return result
    if qty <= 0:
        result["can_calculate"] = False
        result["notes"].append("quantidade deve ser maior que zero")
        return result
    per_lot: dict[str, Any] = {"quantity": qty}
    for field in monetary_fields:
        value = result.get(field)
        per_lot[field] = round(value * qty, 2) if isinstance(value, (int, float)) else value
    per_lot["break_even"] = result.get("break_even")
    per_lot["risk_reward"] = result.get("risk_reward")
    result["per_lot"] = per_lot
    return result


def _debit_spread(record: dict[str, Any], strategy: str, put: bool = False) -> dict[str, Any]:
    required = ("strike_comprado", "strike_vendido", "premio_pago", "premio_recebido")
    missing = missing_fields(record, required)
    result = _base(strategy, missing)
    if missing:
        return result
    bought = _number(record["strike_comprado"])
    sold = _number(record["strike_vendido"])
    paid = _number(record["premio_pago"])
    received = _number(record["premio_recebido"])
    if None in (bought, sold, paid, received):
        result["missing_fields"] = [field for field in required if _number(record.get(field)) is None]
        result["notes"] = ["campos numéricos inválidos"]
        return result
    width = (bought - sold) if put else (sold - bought)
    net_cost = paid - received
    if width <= 0 or net_cost < 0 or net_cost > width:
        result["notes"] = ["strikes ou prêmios incompatíveis com a estrutura"]
        return result
    max_profit = width - net_cost
    result.update(
        net_cost=round(net_cost, 4),
        max_profit=round(max_profit, 4),
        max_loss=round(net_cost, 4),
        break_even=round(bought - net_cost if put else bought + net_cost, 4),
        risk_reward=round(max_profit / net_cost, 4) if net_cost > 0 else None,
        notes=[],
    )
    return _finish(result, record.get("quantidade"), ("net_cost", "max_profit", "max_loss"))


def calculate_call_debit_spread(record: dict[str, Any]) -> dict[str, Any]:
    return _debit_spread(record, "call_debit_spread")


def calculate_put_debit_spread(record: dict[str, Any]) -> dict[str, Any]:
    return _debit_spread(record, "put_debit_spread", put=True)


def _credit_spread(record: dict[str, Any], strategy: str, call: bool = False) -> dict[str, Any]:
    required = ("strike_vendido", "strike_comprado", "premio_recebido", "premio_pago")
    missing = missing_fields(record, required)
    result = _base(strategy, missing)
    if missing:
        return result
    sold = _number(record["strike_vendido"])
    bought = _number(record["strike_comprado"])
    received = _number(record["premio_recebido"])
    paid = _number(record["premio_pago"])
    if None in (sold, bought, received, paid):
        result["missing_fields"] = [field for field in required if _number(record.get(field)) is None]
        result["notes"] = ["campos numéricos inválidos"]
        return result
    width = (bought - sold) if call else (sold - bought)
    net_credit = received - paid
    if width <= 0 or net_credit < 0 or net_credit > width:
        result["notes"] = ["strikes ou prêmios incompatíveis com a estrutura"]
        return result
    max_loss = width - net_credit
    result.update(
        net_credit=round(net_credit, 4),
        max_profit=round(net_credit, 4),
        max_loss=round(max_loss, 4),
        break_even=round(sold + net_credit if call else sold - net_credit, 4),
        risk_reward=round(net_credit / max_loss, 4) if max_loss > 0 else None,
        notes=[],
    )
    return _finish(result, record.get("quantidade"), ("net_credit", "max_profit", "max_loss"))


def calculate_bull_put_spread(record: dict[str, Any]) -> dict[str, Any]:
    return _credit_spread(record, "bull_put_spread")


def calculate_bear_call_spread(record: dict[str, Any]) -> dict[str, Any]:
    return _credit_spread(record, "bear_call_spread", call=True)


def calculate_covered_call(record: dict[str, Any]) -> dict[str, Any]:
    required = ("preco_ativo", "strike_vendido", "premio_recebido")
    missing = missing_fields(record, required)
    result = _base("covered_call", missing)
    if missing:
        return result
    price, strike, premium = map(_number, (record["preco_ativo"], record["strike_vendido"], record["premio_recebido"]))
    if None in (price, strike, premium):
        result["missing_fields"] = [field for field in required if _number(record.get(field)) is None]
        result["notes"] = ["campos numéricos inválidos"]
        return result
    max_profit = strike - price + premium
    potential_numeric_loss = price - premium
    result.update(
        net_credit=round(premium, 4),
        effective_sale_price=round(strike + premium, 4),
        max_profit=round(max_profit, 4),
        max_loss="risco do ativo até zero",
        break_even=round(price - premium, 4),
        risk_reward=round(max_profit / potential_numeric_loss, 4) if potential_numeric_loss > 0 else None,
        notes=["perda máxima qualitativa: risco do ativo até zero"],
    )
    return _finish(result, record.get("quantidade"), ("net_credit", "max_profit", "max_loss"))


def calculate_long_call(record: dict[str, Any]) -> dict[str, Any]:
    required = ("strike", "premio_pago")
    missing = missing_fields(record, required)
    result = _base("long_call", missing)
    if missing:
        return result
    strike, premium = _number(record["strike"]), _number(record["premio_pago"])
    if None in (strike, premium):
        result["missing_fields"] = [field for field in required if _number(record.get(field)) is None]
        result["notes"] = ["campos numéricos inválidos"]
        return result
    result.update(net_cost=premium, max_profit="teoricamente ilimitado", max_loss=premium, break_even=round(strike + premium, 4), notes=[])
    return _finish(result, record.get("quantidade"), ("net_cost", "max_profit", "max_loss"))


def calculate_long_put(record: dict[str, Any]) -> dict[str, Any]:
    required = ("strike", "premio_pago")
    missing = missing_fields(record, required)
    result = _base("long_put", missing)
    if missing:
        return result
    strike, premium = _number(record["strike"]), _number(record["premio_pago"])
    if None in (strike, premium):
        result["missing_fields"] = [field for field in required if _number(record.get(field)) is None]
        result["notes"] = ["campos numéricos inválidos"]
        return result
    max_profit = strike - premium
    result.update(net_cost=premium, max_profit=round(max_profit, 4), max_loss=premium, break_even=round(strike - premium, 4), risk_reward=round(max_profit / premium, 4) if premium > 0 else None, notes=[])
    return _finish(result, record.get("quantidade"), ("net_cost", "max_profit", "max_loss"))


CALCULATORS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "call_debit_spread": calculate_call_debit_spread,
    "put_debit_spread": calculate_put_debit_spread,
    "bull_put_spread": calculate_bull_put_spread,
    "bear_call_spread": calculate_bear_call_spread,
    "covered_call": calculate_covered_call,
    "long_call": calculate_long_call,
    "long_put": calculate_long_put,
}


def calculate_option_strategy(record: dict[str, Any]) -> dict[str, Any]:
    strategy = record.get("tipo_estrutura")
    calculator = CALCULATORS.get(str(strategy))
    if calculator is None:
        result = _base(str(strategy or "indisponível"), ["tipo_estrutura"] if is_missing(strategy) else [])
        result["notes"] = ["estratégia não suportada"] if strategy else ["tipo de estrutura ausente"]
        return result
    return calculator(record)


def scale_option_value(value: Any, quantity: Any, contract_multiplier: Any) -> float | None:
    """Escala um valor por opção sem presumir lote ou multiplicador."""
    amount, qty, multiplier = _number(value), _number(quantity), _number(contract_multiplier)
    if amount is None or qty is None or multiplier is None or qty <= 0 or multiplier <= 0:
        return None
    return round(amount * qty * multiplier, 2)
