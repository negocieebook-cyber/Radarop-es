"""Mapeia regime gráfico para famílias de estratégias, sem aprovar ordens."""

from __future__ import annotations

from typing import Any


REGIMES = (
    "alta_forte",
    "alta_moderada",
    "queda_forte",
    "queda_moderada",
    "lateral",
    "compressao",
    "indefinido",
)
STRATEGY_WARNING = (
    "Estratégia sugerida pelo gráfico. Validar cadeia, prêmio, spread e perda máxima antes de operar."
)
REGIME_STRATEGY_IDS = {
    "alta_forte": ("long_call", "call_debit_spread", "bull_put_spread"),
    "alta_moderada": ("call_debit_spread", "bull_put_spread", "cash_secured_put"),
    "queda_forte": ("long_put", "put_debit_spread"),
    "queda_moderada": ("put_debit_spread", "bear_call_spread"),
    "lateral": ("iron_condor", "iron_butterfly", "call_butterfly", "put_butterfly", "calendar_spread", "short_straddle_travado", "short_strangle_travado"),
    "compressao": ("long_straddle", "long_strangle", "backspread_call", "backspread_put"),
    "indefinido": (),
}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _context(thesis: dict[str, Any]) -> dict[str, Any]:
    health = thesis.get("healthbox_usado") or {}
    bulk = thesis.get("bulkowski_usado") or {}
    price = _number(thesis.get("preco_atual"))
    support = _number(thesis.get("suporte"))
    resistance = _number(thesis.get("resistencia"))
    atr = _number(health.get("atr_percent") or thesis.get("atr_percent"))
    adr = _number(health.get("adr_percent") or thesis.get("adr_percent"))
    rsi = _number(thesis.get("rsi") if thesis.get("rsi") is not None else health.get("rsi"))
    rvol = _number(thesis.get("rvol") if thesis.get("rvol") is not None else health.get("rvol"))
    health_score = _number(thesis.get("healthbox_score"))
    trend = str(health.get("tendencia") or thesis.get("direcao_tese") or "").lower()
    inside_range = (
        price is not None and support is not None and resistance is not None
        and support < resistance and support <= price <= resistance
    )
    range_percent = (
        (resistance - support) / price * 100
        if inside_range and price not in {None, 0}
        else None
    )
    breakout = bool(bulk.get("rompimento") not in {None, "", "indisponível", "não confirmado", False})
    return {
        "price": price, "support": support, "resistance": resistance,
        "atr": atr, "adr": adr, "rsi": rsi, "rvol": rvol,
        "health_score": health_score, "trend": trend,
        "inside_range": inside_range, "range_percent": range_percent,
        "breakout": breakout,
    }


def classify_market_regime(thesis: dict[str, Any]) -> str:
    context = _context(thesis)
    if thesis.get("missing_fields") or context["price"] is None:
        return "indefinido"
    trend = context["trend"]
    direction = thesis.get("direcao_tese")
    neutral_trend = trend in {"lateral", "neutra"} or direction == "neutra"
    neutral_rsi = context["rsi"] is not None and 40 <= context["rsi"] <= 60
    normal_rvol = context["rvol"] is not None and context["rvol"] <= 1.2
    range_compatible = (
        context["range_percent"] is not None
        and context["atr"] is not None and context["adr"] is not None
        and 0 < context["atr"] <= context["range_percent"]
        and 0 < context["adr"] <= context["range_percent"]
    )
    if (
        neutral_trend and context["inside_range"] and neutral_rsi and normal_rvol
        and range_compatible and not context["breakout"]
    ):
        compressed = (
            context["rvol"] is not None and context["rvol"] < 0.8
            and context["atr"] is not None and context["atr"] <= 2
            and context["adr"] is not None and context["adr"] <= 2
        )
        return "compressao" if compressed else "lateral"
    directional = direction if direction in {"altista", "baixista"} else (
        "altista" if trend == "alta" else "baixista" if trend == "baixa" else None
    )
    if directional:
        strong = (
            context["health_score"] is not None and context["health_score"] >= 75
            and context["rvol"] is not None and context["rvol"] >= 1
            and not thesis.get("hard_technical_blockers")
        )
        if directional == "altista":
            return "alta_forte" if strong else "alta_moderada"
        return "queda_forte" if strong else "queda_moderada"
    return "indefinido"


def _candidate(name: str, category: str, priority: int, validations: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "strategy": name,
        "category": category,
        "priority": priority,
        "is_candidate": True,
        "status": "candidata_grafica",
        "requires_options_chain": name not in {"esperar", "acompanhar tese gráfica"},
        "required_validations": validations,
        **extra,
    }


def suggest_lateral_strategies(thesis: dict[str, Any]) -> list[dict[str, Any]]:
    common = ["suporte e resistência claros", "prêmio suficiente", "liquidez", "spread", "break-evens", "perda máxima calculada"]
    return [
        _candidate("iron condor", "lateral", 100, common, requires_lower_and_upper_break_even=True),
        _candidate("iron butterfly", "lateral", 92, common, requires_lower_and_upper_break_even=True),
        _candidate("butterfly", "lateral", 86, common),
        _candidate("calendar", "lateral", 80, common),
        _candidate("venda coberta", "lateral", 65, [*common, "confirmar que o usuário possui o ativo"], requires_underlying=True),
    ]


def suggest_directional_strategies(thesis: dict[str, Any]) -> list[dict[str, Any]]:
    regime = thesis.get("market_regime") or classify_market_regime(thesis)
    validations = ["cadeia real", "prêmio ou débito", "liquidez", "spread", "break-even", "perda máxima calculada"]
    mapping = {
        "alta_forte": [("call comprada", 100), ("call debit spread", 95), ("bull put spread", 80)],
        "alta_moderada": [("call debit spread", 100), ("bull put spread", 90), ("venda de put com caixa", 70)],
        "queda_forte": [("put comprada", 100), ("put debit spread", 95)],
        "queda_moderada": [("put debit spread", 100), ("bear call spread", 90)],
    }
    return [_candidate(name, "direcional", priority, validations) for name, priority in mapping.get(regime, [])]


def suggest_volatility_strategies(thesis: dict[str, Any]) -> list[dict[str, Any]]:
    validations = ["cadeia real", "volatilidade implícita", "evento ou catalisador", "custo", "break-evens", "perda máxima calculada"]
    return [
        _candidate("straddle comprado", "volatilidade", 100, validations),
        _candidate("strangle comprado", "volatilidade", 92, validations),
        _candidate("backspread", "volatilidade", 75, validations, advanced=True),
    ]


def suggest_strategy_family(thesis: dict[str, Any]) -> str:
    regime = thesis.get("market_regime") or classify_market_regime(thesis)
    if regime in {"alta_forte", "alta_moderada", "queda_forte", "queda_moderada"}:
        return "direcional"
    if regime == "lateral":
        return "lateral"
    if regime == "compressao":
        return "volatilidade"
    return "observação"


def _option_validation(candidate: dict[str, Any], thesis: dict[str, Any]) -> str:
    if not candidate.get("requires_options_chain"):
        return "candidata_grafica"
    if thesis.get("cadeia_opcoes_status") != "disponivel_fonte":
        return "pendente_validacao_opcoes"
    engine_candidates = thesis.get("options_validation_candidates") or []
    aliases = {
        "call debit spread": "call_debit_spread", "bull put spread": "bull_put_spread",
        "put debit spread": "put_debit_spread", "bear call spread": "bear_call_spread",
        "venda coberta": "covered_call", "venda de put com caixa": "cash_secured_put",
    }
    expected = aliases.get(candidate["strategy"])
    matching = [item for item in engine_candidates if item.get("tipo_estrutura") == expected] if expected else []
    if not matching:
        return "pendente_validacao_opcoes"
    for item in matching:
        loss = _number(item.get("perda_maxima"))
        break_even = item.get("break_even")
        liquidity = str(item.get("liquidez") or item.get("liquidity_status") or "").lower()
        price = item.get("entry_reference_price")
        if loss is not None and loss >= 0 and break_even is not None and price is not None and liquidity not in {"", "indisponível", "sem negócio", "ilíquida"}:
            return "validada_com_cadeia"
    return "rejeitada_por_opcoes"


def build_strategy_mapping(thesis: dict[str, Any]) -> dict[str, Any]:
    regime = classify_market_regime(thesis)
    working = {**thesis, "market_regime": regime}
    family = suggest_strategy_family(working)
    if regime == "lateral":
        candidates = suggest_lateral_strategies(working)
    elif regime == "compressao":
        candidates = suggest_volatility_strategies(working)
    elif regime == "indefinido":
        candidates = [
            _candidate("esperar", "observação", 100, ["dados gráficos completos"]),
            _candidate("acompanhar tese gráfica", "observação", 90, ["novo snapshot de mercado"]),
        ]
    else:
        candidates = suggest_directional_strategies(working)
    candidates = rank_strategy_candidates(candidates)
    for candidate in candidates:
        candidate["status"] = _option_validation(candidate, working)
    actionable = [item for item in candidates if item.get("requires_options_chain")]
    statuses = {item["status"] for item in actionable}
    if "validada_com_cadeia" in statuses:
        strategy_status = "validada_com_cadeia"
    elif actionable and statuses == {"rejeitada_por_opcoes"}:
        strategy_status = "rejeitada_por_opcoes"
    elif actionable:
        strategy_status = "pendente_validacao_opcoes"
    else:
        strategy_status = "candidata_grafica"
    return {
        "market_regime": regime,
        "strategy_candidates": candidates,
        "preferred_strategy_family": family,
        "preferred_strategy": candidates[0]["strategy"] if candidates else "esperar",
        "alternative_strategies": [item["strategy"] for item in candidates[1:]],
        "strategy_status": strategy_status,
        "strategy_warning": STRATEGY_WARNING,
    }


def rank_strategy_candidates(strategy_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(strategy_candidates, key=lambda item: (-int(item.get("priority") or 0), str(item.get("strategy") or "")))
