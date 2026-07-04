"""Teses gráficas derivadas de snapshots, reutilizando Healthbox e Bulkowski."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.bulkowski_engine import analyze_pattern_for_asset
from app.healthbox_engine import build_healthbox, healthbox_score
from app.graphical_diagnostics import diagnose_graphical_thesis
from app.strategy_mapper import build_strategy_mapping
from app.strategy_screener import screen_strategies_for_thesis, summarize_strategy_screening


STATUSES = ("compra_operavel", "interesse_compra", "venda_operavel", "interesse_venda", "neutra_observar", "evitar", "inconclusiva")
MANUAL_WARNING = "Sem cadeia real, validar opção manualmente no book/corretora."


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_trade_region(thesis: dict[str, Any]) -> str:
    if thesis.get("missing_fields"):
        return "inconclusiva"
    price, support, resistance = (_number(thesis.get(key)) for key in ("preco_atual", "suporte", "resistencia"))
    trend = thesis.get("direcao_tese")
    if price is None or support is None or resistance is None or support >= resistance:
        return "inconclusiva"
    if price < support or price > resistance:
        return "evitar"
    ratio = _number(thesis.get("relacao_alvo_risco"))
    health_score = _number(thesis.get("healthbox_score"))
    rvol = _number(thesis.get("rvol"))
    rsi = _number(thesis.get("rsi"))
    distance_support = ((price - support) / price) * 100 if price else None
    distance_resistance = ((resistance - price) / price) * 100 if price else None
    near_support = distance_support is not None and 0 <= distance_support <= 3
    near_resistance = distance_resistance is not None and 0 <= distance_resistance <= 3
    health_ok = health_score is not None and health_score >= 60
    volume_ok = rvol is not None and rvol >= 0.8
    strong_blocker = (rsi is not None and rsi >= 75 and trend == "altista") or (rsi is not None and rsi <= 25 and trend == "baixista")
    if trend == "altista":
        if near_support and ratio is not None and ratio > 1 and health_ok and volume_ok and not strong_blocker:
            return "compra_operavel"
        if near_support or near_resistance or (ratio is not None and ratio >= 0.8 and health_ok):
            return "interesse_compra"
    if trend == "baixista":
        if near_resistance and ratio is not None and ratio > 1 and health_ok and volume_ok and not strong_blocker:
            return "venda_operavel"
        if near_resistance or near_support or (ratio is not None and ratio >= 0.8 and health_ok):
            return "interesse_venda"
    if trend == "neutra":
        return "neutra_observar"
    return "evitar"


def suggest_option_structure(thesis: dict[str, Any]) -> str:
    if thesis.get("status") in {"compra_operavel", "interesse_compra"}:
        return "call_debit_spread ou bull_put_spread"
    if thesis.get("status") in {"venda_operavel", "interesse_venda"}:
        return "put_debit_spread ou bear_call_spread"
    return "apenas observar"


def suggest_target_delta(thesis: dict[str, Any]) -> str | None:
    return "0,40 a 0,60 na ponta comprada (delta-alvo; não calculado)" if thesis.get("status") in {"compra_operavel", "interesse_compra", "venda_operavel", "interesse_venda"} else None


def suggest_expiration_window(thesis: dict[str, Any]) -> str | None:
    return "15 a 45 dias, sujeito à validação da cadeia EOD" if thesis.get("status") in {"compra_operavel", "interesse_compra", "venda_operavel", "interesse_venda"} else None


def suggest_strike_region(thesis: dict[str, Any]) -> str | None:
    if thesis.get("status") in {"compra_operavel", "interesse_compra"}:
        return f"ponta vendida próxima do alvo/resistência {thesis.get('resistencia')}"
    if thesis.get("status") in {"venda_operavel", "interesse_venda"}:
        return f"ponta vendida próxima do alvo/suporte {thesis.get('suporte')}"
    return None


def build_graphical_thesis(
    asset_snapshot: dict[str, Any], healthbox: dict[str, Any] | None = None,
    bulkowski: dict[str, Any] | None = None,
) -> dict[str, Any]:
    health = healthbox or build_healthbox(asset_snapshot)
    bulk = bulkowski or analyze_pattern_for_asset(asset_snapshot)
    price = _number(asset_snapshot.get("preco_atual"))
    support = _number(asset_snapshot.get("suporte"))
    resistance = _number(asset_snapshot.get("resistencia"))
    trend = str(asset_snapshot.get("tendencia") or health.get("tendencia") or "").lower()
    direction = "altista" if trend == "alta" else "baixista" if trend == "baixa" else "neutra" if trend == "lateral" else "inconclusiva"
    missing = [name for name, value in (("preco_atual", price), ("suporte", support), ("resistencia", resistance)) if value is None]
    if direction == "inconclusiva":
        missing.append("tendencia")
    target = resistance if direction == "altista" else support if direction == "baixista" else None
    invalidation = support if direction == "altista" else resistance if direction == "baixista" else None
    target_distance = abs(target - price) if target is not None and price is not None else None
    graphical_risk = abs(price - invalidation) if invalidation is not None and price is not None else None
    ratio = target_distance / graphical_risk if target_distance is not None and graphical_risk not in {None, 0} else None
    trigger = resistance if direction == "altista" else support if direction == "baixista" else None
    trigger_distance = abs(trigger - price) if trigger is not None and price is not None else None
    thesis = {
        "ativo": asset_snapshot.get("ativo"), "preco_atual": price, "direcao_tese": direction,
        "regiao_entrada_grafica": f"entre {support} e {price}, após confirmação" if direction == "altista" and support is not None and price is not None else f"entre {price} e {resistance}, após confirmação" if direction == "baixista" and resistance is not None and price is not None else "apenas observar",
        "suporte": support, "resistencia": resistance, "invalidacao": invalidation, "alvo": target,
        "distancia_ate_alvo": round(target_distance, 4) if target_distance is not None else None,
        "risco_grafico": round(graphical_risk, 4) if graphical_risk is not None else None,
        "relacao_alvo_risco": round(ratio, 4) if ratio is not None else None,
        "healthbox_usado": health, "healthbox_score": healthbox_score(health).get("score"),
        "rvol": health.get("rvol"), "rsi": health.get("rsi"),
        "bulkowski_usado": bulk, "bulkowski_status": bulk.get("status"),
        "missing_fields": list(dict.fromkeys(missing)), "cadeia_opcoes_status": "pendente",
        "opcao_validacao": "opcao_pendente_validacao_manual", "aviso": MANUAL_WARNING,
        "fonte": asset_snapshot.get("fonte"), "coleta": asset_snapshot.get("coleta"),
        "tipo_dado": asset_snapshot.get("tipo_dado"), "data_frequency": asset_snapshot.get("data_frequency") or "EOD",
    }
    thesis["status"] = classify_trade_region(thesis)
    if thesis["status"] == "neutra_observar" and price is not None and support is not None and resistance is not None:
        distance_support = abs(price - support) / price * 100 if price else None
        distance_resistance = abs(resistance - price) / price * 100 if price else None
        probable = "altista" if distance_support is not None and distance_resistance is not None and distance_support <= distance_resistance else "baixista"
        near_boundary = min(distance_support, distance_resistance) if distance_support is not None and distance_resistance is not None else None
        score_value = _number(thesis.get("healthbox_score"))
        if near_boundary is not None and near_boundary <= 5 and score_value is not None and score_value >= 50:
            thesis["direcao_tese"] = probable
            thesis["status"] = "interesse_compra" if probable == "altista" else "interesse_venda"
            thesis["alvo"] = resistance if probable == "altista" else support
            thesis["invalidacao"] = support if probable == "altista" else resistance
            target_distance = abs(thesis["alvo"] - price)
            graphical_risk = abs(price - thesis["invalidacao"])
            thesis["distancia_ate_alvo"] = round(target_distance, 4)
            thesis["risco_grafico"] = round(graphical_risk, 4)
            thesis["relacao_alvo_risco"] = round(target_distance / graphical_risk, 4) if graphical_risk else None
    status_reasons = {
        "compra_operavel": "tendência favorável, preço perto do suporte, alvo maior que risco e confirmação mínima de Healthbox/volume",
        "interesse_compra": "contexto altista próximo de suporte/rompimento ou relação alvo/risco perto do mínimo; falta confirmação completa",
        "venda_operavel": "tendência baixista, preço perto da resistência, alvo maior que risco e confirmação mínima de Healthbox/volume",
        "interesse_venda": "contexto baixista próximo de resistência/perda de suporte ou relação alvo/risco perto do mínimo; falta confirmação completa",
        "neutra_observar": "tendência lateral sem gatilho direcional confirmado",
        "evitar": "preço fora da região válida ou requisitos mínimos não atendidos",
        "inconclusiva": "dados críticos ausentes para definir região e risco",
    }
    effective_direction = thesis.get("direcao_tese")
    effective_trigger = resistance if effective_direction == "altista" else support if effective_direction == "baixista" else None
    effective_trigger_distance = abs(effective_trigger - price) if effective_trigger is not None and price is not None else None
    thesis["gatilho_confirmacao"] = f"rompimento confirmado de {effective_trigger} com volume" if effective_trigger is not None else "aguardar confirmação direcional"
    thesis["distancia_ate_gatilho"] = round(effective_trigger_distance, 4) if effective_trigger_distance is not None else None
    thesis["motivo_status"] = status_reasons[thesis["status"]]
    thesis["tipo_estrutura_sugerida"] = suggest_option_structure(thesis)
    thesis["delta_alvo"] = suggest_target_delta(thesis)
    thesis["vencimento_ideal"] = suggest_expiration_window(thesis)
    thesis["regiao_strike_sugerida"] = suggest_strike_region(thesis)
    thesis.update(diagnose_graphical_thesis(thesis))
    thesis.update(build_strategy_mapping(thesis))
    thesis.update(screen_strategies_for_thesis(thesis))
    return thesis


def rank_graphical_theses(theses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {"compra_operavel": 0, "interesse_compra": 1, "venda_operavel": 2, "interesse_venda": 3, "neutra_observar": 4, "evitar": 5, "inconclusiva": 6}
    return sorted(theses, key=lambda item: (priority.get(item.get("status"), 5), -(_number(item.get("relacao_alvo_risco")) or -1), -(_number(item.get("healthbox_score")) or -1)))


def summarize_graphical_theses(theses: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(item.get("status", "inconclusiva") for item in theses)
    regimes = Counter(item.get("market_regime", "indefinido") for item in theses)
    return {
        "total": len(theses),
        **{status: counts[status] for status in STATUSES},
        "with_options_chain": sum(item.get("cadeia_opcoes_status") == "disponivel_fonte" for item in theses),
        "pending_options_chain": sum(item.get("cadeia_opcoes_status") != "disponivel_fonte" for item in theses),
        "market_regimes": {regime: regimes[regime] for regime in (
            "alta_forte", "alta_moderada", "queda_forte", "queda_moderada",
            "lateral", "compressao", "indefinido",
        )},
        "strategy_candidates": sum(len(item.get("strategy_candidates") or []) for item in theses),
        "pending_strategy_validation": sum(item.get("strategy_status") == "pendente_validacao_opcoes" for item in theses),
        "strategy_screening": summarize_strategy_screening(theses),
        "manual_validation_plans": sum(
            bool(candidate.get("manual_validation_plan"))
            for item in theses for candidate in item.get("strategy_screening", [])
        ),
    }
