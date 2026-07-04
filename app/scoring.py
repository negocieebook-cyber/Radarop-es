"""Score explicável, calculado somente com campos críticos disponíveis."""

from __future__ import annotations

from typing import Any

from app.data_quality import is_missing, missing_fields
from app.healthbox_engine import healthbox_score
from app.options_math import calculate_option_strategy


CRITICAL_FIELDS = (
    "ativo",
    "estrategia",
    "vencimento_dias",
    "perda_maxima",
    "ganho_maximo",
    "break_even",
    "liquidez_status",
    "grafico_status",
    "tipo_dado",
    "fonte",
)


def score_opportunity(opportunity: dict[str, Any]) -> dict[str, Any]:
    calculation = opportunity.get("calculation") or calculate_option_strategy(opportunity)
    effective = dict(opportunity)
    if calculation["can_calculate"]:
        effective.setdefault("perda_maxima", calculation["max_loss"])
        effective.setdefault("ganho_maximo", calculation["max_profit"])
        effective.setdefault("break_even", calculation["break_even"])
    missing = missing_fields(effective, CRITICAL_FIELDS)
    if missing:
        return {"score": None, "status": "score não calculado", "reason": "campos críticos ausentes", "missing_fields": missing, "breakdown": {}, "healthbox_status": "indisponível" if not opportunity.get("healthbox") else healthbox_score(opportunity["healthbox"])["status"], "healthbox_score": None if not opportunity.get("healthbox") else healthbox_score(opportunity["healthbox"])["score"]}

    liquidity = str(effective["liquidez_status"]).lower()
    liquidity_points = 25 if liquidity == "alta" else 18 if liquidity in {"média", "media", "adequada"} else 5

    rr = calculation.get("risk_reward")
    risk_reward_points = 20 if isinstance(rr, (int, float)) and rr >= 3 else 16 if isinstance(rr, (int, float)) and rr >= 2 else 10 if isinstance(rr, (int, float)) and rr >= 1 else 0

    graph = str(effective["grafico_status"]).lower()
    graph_points = 5 if graph == "confirmado" else 3 if graph in {"parcial", "pendente"} else 0
    healthbox = opportunity.get("healthbox")
    health_result = healthbox_score(healthbox) if healthbox else {"score": None, "status": "indisponível"}
    healthbox_points = round(health_result["score"] / 10) if isinstance(health_result.get("score"), (int, float)) else 0
    risk_points = 15 if not is_missing(effective["perda_maxima"]) else 0
    days = effective["vencimento_dias"]
    expiry_points = 10 if isinstance(days, (int, float)) and 20 <= days <= 60 else 6 if isinstance(days, (int, float)) and 7 <= days <= 90 else 0
    source_points = 10 if not is_missing(effective["fonte"]) else 0
    simple = effective.get("tipo_estrutura") in {"call_debit_spread", "put_debit_spread", "bull_put_spread", "bear_call_spread", "covered_call", "long_call", "long_put"}
    simplicity_points = 5 if simple else 0
    breakdown = {
        "liquidez": liquidity_points,
        "risco_retorno": risk_reward_points,
        "grafico": graph_points,
        "healthbox": healthbox_points,
        "perda_maxima_definida": risk_points,
        "vencimento": expiry_points,
        "fonte": source_points,
        "simplicidade": simplicity_points,
    }
    return {"score": min(100, sum(breakdown.values())), "status": "calculado", "reason": "score calculado somente com dados MOCK / EXEMPLO disponíveis", "missing_fields": [], "breakdown": breakdown, "healthbox_status": health_result["status"], "healthbox_score": health_result.get("score")}
