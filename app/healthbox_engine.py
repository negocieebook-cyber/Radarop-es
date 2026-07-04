"""Motor Stock Healthbox para snapshots MOCK / EXEMPLO, sem coleta externa."""

from __future__ import annotations

from typing import Any

from app.data_quality import is_missing


UNAVAILABLE = "indisponível"
MOCK_TYPE = "MOCK / EXEMPLO"


def safe_float(value: Any) -> float | None:
    if is_missing(value) or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_percent_distance(price: Any, reference: Any) -> float | None:
    price_value = safe_float(price)
    reference_value = safe_float(reference)
    if price_value is None or reference_value in (None, 0):
        return None
    return round(((price_value - reference_value) / reference_value) * 100, 2)


def classify_rsi(rsi: Any) -> str:
    value = safe_float(rsi)
    if value is None:
        return UNAVAILABLE
    if value < 30:
        return "sobrevendido"
    if value < 45:
        return "fraco"
    if value < 60:
        return "neutro"
    if value <= 70:
        return "forte"
    return "sobrecomprado"


def classify_relative_volume(rvol: Any) -> str:
    value = safe_float(rvol)
    if value is None:
        return UNAVAILABLE
    if value < 0.8:
        return "baixo"
    if value <= 1.2:
        return "normal"
    if value <= 2.0:
        return "alto"
    return "muito alto"


def classify_atr_percent(atr_percent: Any) -> str:
    value = safe_float(atr_percent)
    if value is None:
        return UNAVAILABLE
    if value < 1.5:
        return "volatilidade baixa"
    if value <= 3.5:
        return "volatilidade normal"
    return "volatilidade alta"


def classify_trend(trend: Any) -> str:
    if is_missing(trend):
        return UNAVAILABLE
    normalized = str(trend).strip().lower()
    return normalized if normalized in {"alta", "baixa", "lateral", "indefinida"} else UNAVAILABLE


def _percent_change(current: Any, previous: Any) -> float | None:
    return calculate_percent_distance(current, previous)


def build_healthbox(asset_snapshot: dict[str, Any]) -> dict[str, Any]:
    numeric_fields = {
        field: safe_float(asset_snapshot.get(field))
        for field in (
            "preco_atual",
            "abertura",
            "maxima",
            "minima",
            "fechamento_anterior",
            "adr_percent",
            "atr_percent",
            "rvol",
            "rsi",
            "rsi_200",
            "suporte",
            "resistencia",
            "volatilidade_implicita",
        )
    }
    missing = [field for field, value in numeric_fields.items() if value is None]
    trend = classify_trend(asset_snapshot.get("tendencia"))
    if trend == UNAVAILABLE:
        missing.append("tendencia")

    daily_range = None
    if all(numeric_fields[field] is not None for field in ("maxima", "minima", "abertura")) and numeric_fields["abertura"] != 0:
        daily_range = round(
            ((numeric_fields["maxima"] - numeric_fields["minima"]) / numeric_fields["abertura"]) * 100,
            2,
        )
    variation = _percent_change(numeric_fields["preco_atual"], numeric_fields["fechamento_anterior"])
    distance_support = calculate_percent_distance(numeric_fields["preco_atual"], numeric_fields["suporte"])
    distance_resistance = calculate_percent_distance(numeric_fields["preco_atual"], numeric_fields["resistencia"])

    alerts: list[str] = []
    if distance_support is not None and distance_support < 0:
        alerts.append("preço abaixo do suporte MOCK / EXEMPLO")
    if distance_resistance is not None and abs(distance_resistance) <= 2:
        alerts.append("preço próximo da resistência MOCK / EXEMPLO")
    if classify_rsi(numeric_fields["rsi"]) in {"sobrecomprado", "sobrevendido"}:
        alerts.append(f"RSI {classify_rsi(numeric_fields['rsi'])} no snapshot mockado")
    critical = [
        field
        for field in ("preco_atual", "rsi", "rvol", "suporte", "resistencia")
        if numeric_fields[field] is None
    ]
    if trend == UNAVAILABLE:
        critical.append("tendencia")
    if numeric_fields["atr_percent"] is None and numeric_fields["adr_percent"] is None:
        critical.append("atr_percent ou adr_percent")
    if critical:
        general_status = "inconclusivo por falta de dados"
    elif distance_support is not None and distance_support < 0:
        general_status = "atenção: suporte perdido"
    elif trend in {"alta", "lateral"} and classify_rsi(numeric_fields["rsi"]) not in {"sobrecomprado", "sobrevendido"}:
        general_status = "saudável no cenário mockado"
    else:
        general_status = "atenção"

    return {
        "ativo": asset_snapshot.get("ativo", UNAVAILABLE),
        "preco_atual": numeric_fields["preco_atual"],
        "variacao_diaria_percent": variation,
        "range_diario_percent": daily_range,
        "adr_percent": numeric_fields["adr_percent"],
        "atr_percent": numeric_fields["atr_percent"],
        "atr_classificacao": classify_atr_percent(numeric_fields["atr_percent"]),
        "rvol": numeric_fields["rvol"],
        "rvol_classificacao": classify_relative_volume(numeric_fields["rvol"]),
        "rsi": numeric_fields["rsi"],
        "rsi_classificacao": classify_rsi(numeric_fields["rsi"]),
        "rsi_200": numeric_fields["rsi_200"],
        "tendencia": trend,
        "suporte": numeric_fields["suporte"],
        "resistencia": numeric_fields["resistencia"],
        "distancia_suporte_percent": distance_support,
        "distancia_resistencia_percent": distance_resistance,
        "volatilidade_implicita": numeric_fields["volatilidade_implicita"],
        "status_geral": general_status,
        "alertas": alerts,
        "campos_ausentes": list(dict.fromkeys(missing)),
        "fonte": asset_snapshot.get("fonte") or UNAVAILABLE,
        "tipo_dado": asset_snapshot.get("tipo_dado") or UNAVAILABLE,
        "coleta": asset_snapshot.get("coleta") or UNAVAILABLE,
    }


def healthbox_score(healthbox: dict[str, Any]) -> dict[str, Any]:
    required_missing: list[str] = []
    for field in ("preco_atual", "suporte", "resistencia", "rsi", "rvol"):
        if safe_float(healthbox.get(field)) is None:
            required_missing.append(field)
    if classify_trend(healthbox.get("tendencia")) == UNAVAILABLE:
        required_missing.append("tendencia")
    if safe_float(healthbox.get("atr_percent")) is None and safe_float(healthbox.get("adr_percent")) is None:
        required_missing.append("atr_percent ou adr_percent")
    if required_missing:
        return {"score": None, "status": "score não calculado", "missing_fields": required_missing, "breakdown": {}}

    trend = classify_trend(healthbox["tendencia"])
    trend_points = 25 if trend in {"alta", "baixa", "lateral"} else 10
    rsi_class = classify_rsi(healthbox["rsi"])
    rsi_points = 20 if rsi_class in {"neutro", "forte"} else 10 if rsi_class == "fraco" else 5
    rvol_class = classify_relative_volume(healthbox["rvol"])
    rvol_points = 20 if rvol_class == "alto" else 15 if rvol_class in {"normal", "muito alto"} else 5
    support_distance = healthbox.get("distancia_suporte_percent")
    resistance_distance = healthbox.get("distancia_resistencia_percent")
    levels_points = 15 if isinstance(support_distance, (int, float)) and support_distance >= 0 and isinstance(resistance_distance, (int, float)) and resistance_distance <= 0 else 7
    volatility_value = healthbox.get("atr_percent") if safe_float(healthbox.get("atr_percent")) is not None else healthbox.get("adr_percent")
    volatility_class = classify_atr_percent(volatility_value)
    volatility_points = 10 if volatility_class == "volatilidade normal" else 8 if volatility_class == "volatilidade baixa" else 4
    completeness_points = 10 if not healthbox.get("campos_ausentes") else 0
    breakdown = {
        "tendencia": trend_points,
        "rsi": rsi_points,
        "rvol": rvol_points,
        "suporte_resistencia": levels_points,
        "volatilidade": volatility_points,
        "completude": completeness_points,
    }
    return {"score": min(100, sum(breakdown.values())), "status": "calculado", "missing_fields": [], "breakdown": breakdown}


def healthbox_confirms_strategy(healthbox: dict[str, Any], strategy_type: str) -> str:
    score_result = healthbox_score(healthbox)
    if score_result["score"] is None:
        return "indisponível por falta de dados"
    trend = classify_trend(healthbox.get("tendencia"))
    rsi_class = classify_rsi(healthbox.get("rsi"))
    rvol_class = classify_relative_volume(healthbox.get("rvol"))
    support_distance = healthbox.get("distancia_suporte_percent")
    resistance_distance = healthbox.get("distancia_resistencia_percent")
    near_resistance = isinstance(resistance_distance, (int, float)) and abs(resistance_distance) <= 2
    support_lost = isinstance(support_distance, (int, float)) and support_distance < 0

    if strategy_type == "call_debit_spread":
        if trend == "alta" and rsi_class != "sobrecomprado" and rvol_class in {"normal", "alto"} and not near_resistance:
            return "confirma"
        return "atenção" if trend == "alta" else "não confirma"
    if strategy_type == "bull_put_spread":
        return "confirma" if trend in {"alta", "lateral"} and not support_lost else "não confirma"
    if strategy_type == "covered_call":
        return "confirma" if trend == "lateral" or near_resistance else "atenção"
    if strategy_type == "put_debit_spread":
        return "confirma" if trend == "baixa" and support_lost else "não confirma"
    if strategy_type == "bear_call_spread":
        below_resistance = isinstance(resistance_distance, (int, float)) and resistance_distance < 0
        return "confirma" if trend in {"baixa", "lateral"} and below_resistance else "não confirma"
    return "indisponível por falta de dados"
