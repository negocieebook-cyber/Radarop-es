"""Diagnóstico explicável e ranking conservador de quase setups gráficos."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def diagnose_graphical_thesis(thesis: dict[str, Any]) -> dict[str, Any]:
    price = _number(thesis.get("preco_atual"))
    support = _number(thesis.get("suporte"))
    resistance = _number(thesis.get("resistencia"))
    ratio = _number(thesis.get("relacao_alvo_risco"))
    risk = _number(thesis.get("risco_grafico"))
    health_score = _number(thesis.get("healthbox_score"))
    rvol = _number(thesis.get("rvol"))
    rsi = _number(thesis.get("rsi"))
    direction = thesis.get("direcao_tese")
    hard: list[str] = []
    soft: list[str] = []
    missing: list[str] = []
    rejection: list[str] = []
    for field in thesis.get("missing_fields", []):
        label = f"sem {field}"
        hard.append(label)
        rejection.append(label)
    directional = direction in {"altista", "baixista"}
    if directional and thesis.get("alvo") is None:
        hard.append("sem alvo")
    if directional and thesis.get("invalidacao") is None:
        hard.append("sem invalidação")
    if directional and ratio is not None and ratio < 0.5:
        hard.append("relação alvo/risco muito ruim")
    if price is not None and support is not None and resistance is not None and not support <= price <= resistance:
        hard.append("preço fora da faixa suporte/resistência")
    if health_score is not None and health_score < 45:
        hard.append("Healthbox invalida")
    if price and risk is not None and risk / price * 100 > 10:
        hard.append("risco gráfico muito alto")
    if rvol is not None and rvol < 0.8:
        soft.extend(["rVol baixo", "falta confirmação de volume"])
        missing.append("confirmação de volume")
    if rsi is not None and 40 <= rsi <= 60:
        soft.append("RSI neutro")
    if thesis.get("bulkowski_status") in {None, "inconclusivo", "padrão não detectado"}:
        soft.append("Bulkowski inconclusivo")
    buy_distance = abs(resistance - price) / price * 100 if price and resistance is not None else None
    sell_distance = abs(price - support) / price * 100 if price and support is not None else None
    probable = direction
    if direction == "neutra" and buy_distance is not None and sell_distance is not None:
        probable = "altista" if sell_distance <= buy_distance else "baixista"
    trigger_distance = buy_distance if probable == "altista" else sell_distance if probable == "baixista" else None
    if trigger_distance is not None and 3 < trigger_distance <= 8:
        soft.append("distância até gatilho ainda moderada")
    if directional and ratio is not None and 0.5 <= ratio < 1:
        soft.append("alvo/risco perto do mínimo")
        missing.append("melhora da relação alvo/risco")
    if not hard and trigger_distance is not None and trigger_distance <= 5:
        soft.append("perto da região, mas sem gatilho")
        missing.append("confirmação de candle/rompimento")
    rejection.extend(hard)
    if thesis.get("status") in {"evitar", "neutra_observar", "inconclusiva"} and not rejection:
        rejection.append(thesis.get("motivo_status") or "setup ainda não confirmado")
    completeness = 20 if not thesis.get("missing_fields") else max(0, 20 - 5 * len(thesis.get("missing_fields", [])))
    health_points = min(20, max(0, (health_score or 0) / 5))
    proximity = 0
    if trigger_distance is not None:
        proximity = 25 if trigger_distance <= 2 else 18 if trigger_distance <= 5 else 10 if trigger_distance <= 10 else 0
    ratio_points = 20 if ratio is not None and ratio >= 1 else 15 if ratio is not None and ratio >= 0.8 else 8 if ratio is not None and ratio >= 0.5 else 0
    volume_points = 10 if rvol is not None and rvol >= 0.8 else 3 if rvol is not None else 0
    bulk_points = 5 if thesis.get("bulkowski_status") not in {None, "inconclusivo", "padrão não detectado"} else 0
    score = round(max(0, min(100, completeness + health_points + proximity + ratio_points + volume_points + bulk_points - min(40, 15 * len(hard)))))
    what = list(dict.fromkeys(missing))
    if hard:
        what.extend(f"resolver: {item}" for item in hard)
    if not what and thesis.get("status") not in {"compra_operavel", "venda_operavel"}:
        what.append("aguardar gatilho gráfico confirmado")
    primary = (hard or soft or rejection or [thesis.get("motivo_status") or "sem motivo calculável"])[0]
    return {
        "rejection_reasons": list(dict.fromkeys(rejection)),
        "missing_confirmations": list(dict.fromkeys(missing)),
        "hard_technical_blockers": list(dict.fromkeys(hard)),
        "soft_technical_warnings": list(dict.fromkeys(soft)),
        "near_setup_score": score,
        "distance_to_buy_trigger": round(buy_distance, 4) if buy_distance is not None else None,
        "distance_to_sell_trigger": round(sell_distance, 4) if sell_distance is not None else None,
        "direcao_provavel": probable,
        "what_needs_to_happen": list(dict.fromkeys(what)),
        "primary_reason": primary,
    }


def rank_near_setups(theses: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    eligible = [item for item in theses if item.get("status") not in {"compra_operavel", "venda_operavel", "inconclusiva"} and len(item.get("hard_technical_blockers", [])) <= 1]
    return sorted(eligible, key=lambda item: (-int(item.get("near_setup_score") or 0), len(item.get("hard_technical_blockers", []))))[:limit]


def summarize_graphical_diagnostics(theses: list[dict[str, Any]]) -> dict[str, Any]:
    rejection = Counter(reason for item in theses for reason in item.get("rejection_reasons", []))
    confirmations = Counter(reason for item in theses for reason in item.get("missing_confirmations", []))
    regimes = Counter(item.get("market_regime", "indefinido") for item in theses)
    strategy_rejections = Counter(
        rejected.get("reason", "sem motivo")
        for thesis in theses for rejected in thesis.get("rejected_strategies_summary", [])
    )
    return {"top_rejection_reasons": dict(rejection.most_common(10)), "top_missing_confirmations": dict(confirmations.most_common(10)), "near_setups_count": len(rank_near_setups(theses, 10)), "market_regimes": dict(regimes), "top_strategy_rejections": dict(strategy_rejections.most_common(10))}
