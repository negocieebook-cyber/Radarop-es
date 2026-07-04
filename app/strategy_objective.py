"""Etiquetas explicativas de objetivo para estratégias do Screener."""

from __future__ import annotations

from collections import Counter
from typing import Any


OBJECTIVE_META = {
    "premio": (
        "Para prêmio",
        "Busca receber prêmio com risco controlado e condições de mercado compatíveis.",
        "Prêmio não é lucro garantido. Validar perda máxima, break-even, liquidez e spread.",
    ),
    "direcional_alta": (
        "Direcional de alta",
        "Depende de movimento de alta coerente com a tese e o gatilho gráfico.",
        "Depende do movimento do ativo. Validar gatilho gráfico e custo da opção.",
    ),
    "direcional_baixa": (
        "Direcional de baixa",
        "Depende de movimento de baixa coerente com a tese e o gatilho gráfico.",
        "Depende do movimento do ativo. Validar gatilho gráfico e custo da opção.",
    ),
    "protecao": (
        "Proteção",
        "Busca limitar ou compensar parte do risco de uma posição existente.",
        "Proteção tem custo e pode reduzir retorno.",
    ),
    "carteira": (
        "Carteira",
        "Relaciona a estrutura à posse ou possível aquisição do ativo.",
        "Só faz sentido se você tiver ou aceitar ter o ativo.",
    ),
    "lateralidade": (
        "Lateralidade",
        "Busca trabalhar dentro de uma faixa de suporte e resistência.",
        "Depende de suporte/resistência claros e de o ativo permanecer no range.",
    ),
    "volatilidade_evento": (
        "Volatilidade/evento",
        "Busca capturar expansão de movimento ou volatilidade após compressão/evento.",
        "Exige movimento suficiente para pagar o custo da estrutura.",
    ),
    "estudo_avancado": (
        "Estudo avançado",
        "Estrutura complexa mantida para estudo e validação completa de cenários.",
        "Estratégia avançada. Não usar sem validação completa.",
    ),
    "esperar": (
        "Esperar",
        "Os dados ou o regime ainda não sustentam uma escolha prática simples.",
        "Aguardar dados, regime e gatilho mais claros; nenhuma operação foi aprovada.",
    ),
}


def classify_strategy_objective(strategy: dict[str, Any] | None, thesis: dict[str, Any]) -> str:
    item = strategy or {}
    strategy_id = str(item.get("strategy_id") or item.get("id") or "")
    regime = thesis.get("market_regime")
    if not strategy_id:
        return "esperar"
    if strategy_id in {"synthetic_long_stock", "synthetic_short_stock", "ratio_spread_travado", "diagonal_spread"}:
        return "estudo_avancado"
    if strategy_id in {"protective_put", "collar"}:
        return "protecao"
    if strategy_id in {"covered_call", "cash_secured_put"}:
        return "carteira"
    if strategy_id in {"iron_condor", "iron_butterfly", "call_butterfly", "put_butterfly", "calendar_spread", "short_straddle_travado", "short_strangle_travado"}:
        return "lateralidade" if regime == "lateral" else "premio"
    if strategy_id in {"long_straddle", "long_strangle"}:
        return "volatilidade_evento"
    if strategy_id == "backspread_call":
        return "volatilidade_evento" if regime == "compressao" else "direcional_alta"
    if strategy_id == "backspread_put":
        return "volatilidade_evento" if regime == "compressao" else "direcional_baixa"
    if strategy_id == "put_debit_spread" and thesis.get("objetivo_protecao"):
        return "protecao"
    if strategy_id in {"long_call", "call_debit_spread"}:
        return "direcional_alta"
    if strategy_id in {"long_put", "put_debit_spread"}:
        return "direcional_baixa"
    if strategy_id in {"bull_put_spread", "bear_call_spread"}:
        return "premio"
    return "estudo_avancado" if item.get("complexidade") == "avançada" else "esperar"


def build_strategy_objective_label(
    strategy_candidate: dict[str, Any] | None, thesis: dict[str, Any]
) -> dict[str, str]:
    objective = classify_strategy_objective(strategy_candidate, thesis)
    label, description, warning = OBJECTIVE_META[objective]
    return {
        "strategy_objective": objective,
        "objective_label": label,
        "objective_description": description,
        "objective_warning": warning,
    }


def summarize_objectives_for_thesis(thesis: dict[str, Any]) -> dict[str, Any]:
    candidates = thesis.get("strategy_screening", [])
    counts = Counter(item.get("strategy_objective", "esperar") for item in candidates)
    best = thesis.get("best_strategy") or {}
    practical = (
        "esperar"
        if thesis.get("market_regime") == "indefinido" or not best
        else best.get("strategy_objective") or classify_strategy_objective(best, thesis)
    )
    label, description, warning = OBJECTIVE_META[practical]
    return {
        "objective_counts": dict(counts),
        "practical_objective": practical,
        "practical_objective_label": label,
        "practical_objective_description": description,
        "practical_objective_warning": warning,
    }
