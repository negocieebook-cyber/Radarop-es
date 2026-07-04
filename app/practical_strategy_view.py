"""Seleção e resumo prático do Strategy Screener para uso diário."""

from __future__ import annotations

from typing import Any


STATUS_PRIORITY = {
    "apta_graficamente": 0,
    "possivel": 1,
    "pendente_validacao_opcoes": 2,
    "rejeitada": 3,
    "nao_aplicavel": 4,
}
COMPLEXITY_PRIORITY = {"simples": 0, "intermediária": 1, "avançada": 2}
CAPITAL_FIT_PRIORITY = {
    "cabe_bem": 0,
    "cabe_apertado": 1,
    "pendente_dados": 2,
    "exige_ativo_em_carteira": 2,
    "exige_caixa_para_exercicio": 2,
    "acima_do_capital": 3,
    "complexa_para_capital_pequeno": 4,
}


def matches_quick_objective_filter(thesis: dict[str, Any], selected: str) -> bool:
    if selected == "Todos":
        return True
    if selected == "Evitar":
        return thesis.get("practical_action") == "evitar_por_enquanto"
    mapping = {
        "Só prêmio": {"premio"},
        "Só direcional": {"direcional_alta", "direcional_baixa"},
        "Só lateralidade": {"lateralidade"},
        "Só proteção/carteira": {"protecao", "carteira"},
        "Só volatilidade": {"volatilidade_evento"},
    }
    if thesis.get("practical_action") in {"evitar_por_enquanto", "inconclusivo"}:
        return False
    objectives = {
        item.get("strategy_objective")
        for item in thesis.get("strategy_screening", [])
        if item.get("status") not in {"rejeitada", "nao_aplicavel"}
    }
    return bool(objectives & mapping.get(selected, set()))


def _rank_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        CAPITAL_FIT_PRIORITY.get(str(candidate.get("capital_fit_status")), 2),
        -int(candidate.get("suitability_score") or 0),
        STATUS_PRIORITY.get(str(candidate.get("status")), 5),
        COMPLEXITY_PRIORITY.get(str(candidate.get("complexidade")), 3),
        0 if candidate.get("risco_definido") else 1,
        0 if candidate.get("regime_compativel") else 1,
        len(candidate.get("dados_necessarios") or []),
        str(candidate.get("strategy_id") or ""),
    )


def select_top_strategies_for_thesis(
    thesis: dict[str, Any], limit: int = 3
) -> list[dict[str, Any]]:
    eligible = [
        item for item in thesis.get("strategy_screening", [])
        if item.get("status") not in {"rejeitada", "nao_aplicavel"}
    ]
    return sorted(eligible, key=_rank_key)[:max(0, limit)]


def select_best_strategy_for_thesis(thesis: dict[str, Any]) -> dict[str, Any] | None:
    top = select_top_strategies_for_thesis(thesis, 1)
    return top[0] if top else None


def summarize_strategy_for_user(strategy_candidate: dict[str, Any]) -> dict[str, Any]:
    plan = strategy_candidate.get("manual_validation_plan") or {}
    reasons = strategy_candidate.get("motivos_favoraveis") or strategy_candidate.get("motivos_contra") or []
    return {
        "strategy_id": strategy_candidate.get("strategy_id"),
        "strategy_name": strategy_candidate.get("strategy_name"),
        "score": strategy_candidate.get("suitability_score"),
        "status": strategy_candidate.get("status"),
        "reason": reasons[0] if reasons else "sem motivo calculável",
        "delta_target": plan.get("delta_target"),
        "strike_region": plan.get("strike_region"),
        "expiration_window": plan.get("expiration_window"),
        "max_debit_allowed": plan.get("max_debit_allowed"),
        "min_credit_required": plan.get("min_credit_required"),
        "book_checklist": list(plan.get("book_checklist") or []),
        "rejection_rules": list(plan.get("rejection_rules") or []),
        "warning": plan.get("warning"),
        "strategy_objective": strategy_candidate.get("strategy_objective"),
        "objective_label": strategy_candidate.get("objective_label"),
        "objective_description": strategy_candidate.get("objective_description"),
        "objective_warning": strategy_candidate.get("objective_warning"),
        "minimum_technical_capital": strategy_candidate.get("minimum_technical_capital"),
        "recommended_capital": strategy_candidate.get("recommended_capital"),
        "capital_required_estimate": strategy_candidate.get("capital_required_estimate"),
        "max_loss_estimate": strategy_candidate.get("max_loss_estimate"),
        "margin_proxy": strategy_candidate.get("margin_proxy"),
        "capital_fit_status": strategy_candidate.get("capital_fit_status"),
        "capital_fit_reason": strategy_candidate.get("capital_fit_reason"),
        "missing_capital_fields": list(strategy_candidate.get("missing_capital_fields") or []),
        "capital_warning": strategy_candidate.get("capital_warning"),
    }


def _practical_action(thesis: dict[str, Any], best: dict[str, Any] | None) -> str:
    thesis_status = thesis.get("status")
    regime = thesis.get("market_regime")
    if not best or thesis_status == "inconclusiva" or regime == "indefinido":
        return "inconclusivo"
    if thesis_status == "evitar" or thesis.get("hard_technical_blockers"):
        return "evitar_por_enquanto"
    if thesis_status in {"interesse_compra", "interesse_venda"}:
        return "aguardar_gatilho"
    if thesis_status == "neutra_observar" and regime not in {"lateral", "compressao"}:
        return "acompanhar"
    if best.get("status") in {"apta_graficamente", "pendente_validacao_opcoes"}:
        return "olhar_no_book"
    return "acompanhar"


def build_practical_strategy_summary(thesis: dict[str, Any]) -> dict[str, Any]:
    top = select_top_strategies_for_thesis(thesis, 3)
    best = top[0] if top else None
    rejected = [
        item for item in thesis.get("strategy_screening", [])
        if item.get("status") in {"rejeitada", "nao_aplicavel"}
    ]
    action = _practical_action(thesis, best)
    best_summary = summarize_strategy_for_user(best) if best else None
    user_summary = (
        f'{best_summary["strategy_name"]}: {best_summary["reason"]}. Ação: {action}.'
        if best_summary else "Nenhuma estratégia aplicável com os dados atuais."
    )
    return {
        "best_strategy": best_summary,
        "top_3_strategies": [summarize_strategy_for_user(item) for item in top],
        "rejected_count": len(rejected),
        "rejected_summary": [
            {
                "strategy_name": item.get("strategy_name"),
                "reason": (item.get("motivos_contra") or ["não aplicável"])[0],
            }
            for item in rejected[:5]
        ],
        "practical_action": action,
        "user_summary": user_summary,
    }
