"""Validações transparentes para oportunidades de opções."""

from __future__ import annotations

from typing import Any

from app.data_quality import is_missing, missing_fields, required_fields_present
from app.healthbox_engine import classify_atr_percent, classify_relative_volume, classify_rsi
from app.options_math import calculate_option_strategy


def _result(valid: bool | None, status: str, reason: str, missing: list[str] | None = None) -> dict[str, Any]:
    return {"valid": valid, "status": status, "reason": reason, "missing_fields": missing or []}


def validate_opportunity_basic(opportunity: dict[str, Any]) -> dict[str, Any]:
    required = ("id", "ativo", "estrategia", "tipo_estrutura", "vencimento_dias", "tipo_dado", "fonte")
    missing = missing_fields(opportunity, required)
    return _result(not missing, "ok" if not missing else "incompleto", "campos básicos presentes" if not missing else "campos básicos ausentes", missing)


def validate_option_liquidity(opportunity: dict[str, Any]) -> dict[str, Any]:
    value = opportunity.get("liquidez_status")
    if is_missing(value):
        return _result(None, "indisponível", "liquidez não informada", ["liquidez_status"])
    normalized = str(value).lower()
    if normalized in {"alta", "média", "media", "adequada"}:
        return _result(True, "ok", f"liquidez {value} • MOCK / EXEMPLO")
    return _result(False, "atenção", f"liquidez {value} • MOCK / EXEMPLO")


def validate_risk_defined(opportunity: dict[str, Any]) -> dict[str, Any]:
    calculation = opportunity.get("calculation") or calculate_option_strategy(opportunity)
    if not calculation["can_calculate"]:
        return _result(None, "não calculado", "perda máxima não calculada", calculation["missing_fields"])
    if is_missing(calculation.get("max_loss")):
        return _result(None, "não calculado", "perda máxima indisponível", ["perda_maxima"])
    return _result(True, "ok", f"risco definido: {calculation['max_loss']}")


def validate_graphical_confirmation(opportunity: dict[str, Any]) -> dict[str, Any]:
    value = opportunity.get("grafico_status")
    if is_missing(value):
        return _result(None, "indisponível", "confirmação gráfica ausente", ["grafico_status"])
    normalized = str(value).lower()
    if normalized in {"confirmado", "confirma", "sim"}:
        return _result(True, "ok", "gráfico confirmado • MOCK / EXEMPLO")
    if normalized in {"não confirmado", "nao confirmado", "invalidado"}:
        return _result(False, "atenção", f"gráfico {value} • MOCK / EXEMPLO")
    return _result(None, "atenção", f"gráfico {value} • MOCK / EXEMPLO")


def validate_data_completeness(opportunity: dict[str, Any]) -> dict[str, Any]:
    required = ("ativo", "estrategia", "tipo_estrutura", "vencimento_dias", "liquidez_status", "grafico_status", "tipo_dado", "fonte")
    missing = missing_fields(opportunity, required)
    calculation = opportunity.get("calculation") or calculate_option_strategy(opportunity)
    missing = list(dict.fromkeys([*missing, *calculation["missing_fields"]]))
    return _result(not missing, "completo" if not missing else "incompleto", "dados mínimos presentes" if not missing else "dados necessários ausentes", missing)


def build_operation_checklist(opportunity: dict[str, Any]) -> list[dict[str, str]]:
    calculation = opportunity.get("calculation") or calculate_option_strategy(opportunity)
    liquidity = validate_option_liquidity(opportunity)
    graph = validate_graphical_confirmation(opportunity)
    covered_or_spread = opportunity.get("tipo_estrutura") in {"call_debit_spread", "put_debit_spread", "bull_put_spread", "bear_call_spread", "covered_call"}

    def item(question: str, status: str, detail: str) -> dict[str, str]:
        return {"question": question, "status": status, "detail": detail, "tipo_dado": "MOCK / EXEMPLO"}

    event = opportunity.get("evento_relevante")
    risk_reward = calculation.get("risk_reward")
    healthbox = opportunity.get("healthbox")
    healthbox_confirmation = opportunity.get("healthbox_confirmation")
    if healthbox:
        rsi_class = classify_rsi(healthbox.get("rsi"))
        rvol_class = classify_relative_volume(healthbox.get("rvol"))
        atr_class = classify_atr_percent(healthbox.get("atr_percent"))
        support_distance = healthbox.get("distancia_suporte_percent")
        resistance_distance = healthbox.get("distancia_resistencia_percent")
    else:
        rsi_class = rvol_class = atr_class = "indisponível"
        support_distance = resistance_distance = None
    checklist = [
        item("Gráfico confirma?", graph["status"], graph["reason"]),
        item("Liquidez existe?", liquidity["status"], liquidity["reason"]),
        item("Perda máxima calculada?", "ok" if calculation["can_calculate"] and not is_missing(calculation["max_loss"]) else "não calculado", str(calculation.get("max_loss") or "não calculado por falta de dados")),
        item("Ganho máximo calculado?", "ok" if calculation["can_calculate"] and not is_missing(calculation["max_profit"]) else "não calculado", str(calculation.get("max_profit") or "não calculado por falta de dados")),
        item("Break-even calculado?", "ok" if calculation["can_calculate"] and not is_missing(calculation["break_even"]) else "não calculado", str(calculation.get("break_even") or "não calculado por falta de dados")),
        item("Operação coberta ou travada?", "ok" if covered_or_spread else "atenção", "sim" if covered_or_spread else "estrutura não classificada como coberta/travada"),
        item("Dados têm fonte?", "ok" if not is_missing(opportunity.get("fonte")) else "indisponível", str(opportunity.get("fonte") or "fonte ausente")),
        item("Existe evento relevante?", "atenção" if is_missing(event) or "não identificado" in str(event).lower() else "ok", str(event or "indisponível")),
        item("Prêmio paga o risco?", "ok" if isinstance(risk_reward, (int, float)) and risk_reward >= 1 else "atenção" if isinstance(risk_reward, (int, float)) else "indisponível", f"risco/retorno {risk_reward:.2f}" if isinstance(risk_reward, (int, float)) else "não calculado"),
    ]
    checklist.extend(
        [
            item("Healthbox confirma?", "ok" if healthbox_confirmation == "confirma" else "atenção" if healthbox_confirmation == "atenção" else "indisponível" if not healthbox or "indisponível" in str(healthbox_confirmation) else "atenção", str(healthbox_confirmation or "indisponível")),
            item("RSI aceitável?", "ok" if rsi_class in {"neutro", "forte", "fraco"} else "indisponível" if rsi_class == "indisponível" else "atenção", rsi_class),
            item("rVol suficiente?", "ok" if rvol_class in {"normal", "alto", "muito alto"} else "indisponível" if rvol_class == "indisponível" else "atenção", rvol_class),
            item("Preço respeita suporte/resistência?", "ok" if isinstance(support_distance, (int, float)) and support_distance >= 0 and isinstance(resistance_distance, (int, float)) and resistance_distance <= 0 else "indisponível" if support_distance is None or resistance_distance is None else "atenção", "distâncias indisponíveis" if support_distance is None or resistance_distance is None else f"suporte {support_distance:.2f}% · resistência {resistance_distance:.2f}%"),
            item("Volatilidade está adequada?", "ok" if atr_class == "volatilidade normal" else "indisponível" if atr_class == "indisponível" else "atenção", atr_class),
        ]
    )
    return checklist
