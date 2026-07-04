"""Organiza candidatas do Strategy Screener em prioridades diárias por objetivo."""

from __future__ import annotations

from typing import Any


OBJECTIVE_GROUPS = {
    "top_premio": {"premio"},
    "top_direcionais": {"direcional_alta", "direcional_baixa"},
    "top_lateralidade": {"lateralidade"},
    "top_protecao_carteira": {"protecao", "carteira"},
    "top_volatilidade_evento": {"volatilidade_evento"},
}
PREMIUM_PRIORITY = (
    "bull_put_spread", "bear_call_spread", "iron_condor", "iron_butterfly",
    "covered_call", "cash_secured_put",
)
DIRECTIONAL_PRIORITY = ("call_debit_spread", "put_debit_spread", "long_call", "long_put")
LATERAL_PRIORITY = ("iron_condor", "iron_butterfly", "call_butterfly", "put_butterfly", "calendar_spread")
COMPLEXITY = {"simples": 0, "intermediária": 1, "avançada": 2}
CAPITAL_FIT_PRIORITY = {
    "cabe_bem": 0, "cabe_apertado": 1, "pendente_dados": 2,
    "exige_ativo_em_carteira": 2, "exige_caixa_para_exercicio": 2,
    "acima_do_capital": 3, "complexa_para_capital_pequeno": 4,
}


def _plan_completeness(candidate: dict[str, Any]) -> int:
    plan = candidate.get("manual_validation_plan") or {}
    fields = ("delta_target", "strike_region", "expiration_window", "book_checklist", "rejection_rules")
    return sum(bool(plan.get(field)) for field in fields)


def _preference(strategy_id: str, objective: str) -> int:
    preferred = (
        PREMIUM_PRIORITY if objective == "top_premio" else
        DIRECTIONAL_PRIORITY if objective == "top_direcionais" else
        LATERAL_PRIORITY if objective == "top_lateralidade" else ()
    )
    return preferred.index(strategy_id) if strategy_id in preferred else len(preferred)


def rank_by_objective(
    strategies: list[dict[str, Any]], objective: str
) -> list[dict[str, Any]]:
    return sorted(
        strategies,
        key=lambda item: (
            CAPITAL_FIT_PRIORITY.get(str(item.get("capital_fit_status")), 2),
            -int(item.get("suitability_score") or 0),
            -int(item.get("near_setup_score") or 0),
            0 if item.get("regime_compativel") else 1,
            0 if item.get("risco_definido") else 1,
            COMPLEXITY.get(str(item.get("complexidade")), 3),
            -_plan_completeness(item),
            len(item.get("dados_necessarios") or []),
            1 if item.get("complexidade") == "avançada" else 0,
            _preference(str(item.get("strategy_id") or ""), objective),
            str(item.get("ativo") or ""),
        ),
    )


def classify_practical_priority(
    strategy_candidate: dict[str, Any] | None, thesis: dict[str, Any]
) -> str:
    if thesis.get("status") == "inconclusiva" or thesis.get("market_regime") == "indefinido":
        return "inconclusivo"
    if thesis.get("status") == "evitar" or thesis.get("hard_technical_blockers"):
        return "evitar_por_enquanto"
    if thesis.get("status") in {"interesse_compra", "interesse_venda"}:
        return "acompanhar_gatilho"
    if strategy_candidate and strategy_candidate.get("status") in {"apta_graficamente", "pendente_validacao_opcoes", "possivel"}:
        return "olhar_no_book"
    return "acompanhar_gatilho"


def _priority_item(thesis: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    plan = candidate.get("manual_validation_plan") or {}
    return {
        **candidate,
        "ativo": thesis.get("ativo"),
        "regime": thesis.get("market_regime"),
        "thesis_status": thesis.get("status"),
        "near_setup_score": thesis.get("near_setup_score"),
        "gatilho": thesis.get("gatilho_confirmacao"),
        "invalidacao": thesis.get("invalidacao"),
        "delta_target": plan.get("delta_target"),
        "strike_region": plan.get("strike_region"),
        "expiration_window": plan.get("expiration_window"),
        "practical_action": classify_practical_priority(candidate, thesis),
        "thesis": thesis,
    }


def _deduplicate_assets(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected = []
    seen = set()
    for item in items:
        asset = item.get("ativo")
        if asset in seen:
            continue
        seen.add(asset)
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def build_daily_priority_list(
    theses: list[dict[str, Any]], limit_per_objective: int = 5
) -> dict[str, list[dict[str, Any]]]:
    flattened = [
        _priority_item(thesis, candidate)
        for thesis in theses
        for candidate in thesis.get("strategy_screening", [])
        if candidate.get("status") not in {"rejeitada", "nao_aplicavel"}
        and thesis.get("status") not in {"evitar", "inconclusiva"}
        and thesis.get("market_regime") != "indefinido"
        and not thesis.get("hard_technical_blockers")
    ]
    priorities: dict[str, list[dict[str, Any]]] = {}
    for group, objectives in OBJECTIVE_GROUPS.items():
        eligible = [item for item in flattened if item.get("strategy_objective") in objectives]
        if group == "top_premio":
            eligible.extend(
                item for item in flattened
                if item.get("strategy_id") in PREMIUM_PRIORITY and item not in eligible
            )
        priorities[group] = _deduplicate_assets(rank_by_objective(eligible, group), limit_per_objective)
    avoid = [
        _priority_item(thesis, thesis.get("strategy_screening", [{}])[0])
        for thesis in theses if thesis.get("status") == "evitar" and thesis.get("strategy_screening")
    ]
    inconclusive = [
        _priority_item(thesis, thesis.get("strategy_screening", [{}])[0])
        for thesis in theses if thesis.get("status") == "inconclusiva" or thesis.get("market_regime") == "indefinido"
    ]
    priorities["evitar_por_enquanto"] = rank_by_objective(avoid, "evitar_por_enquanto")[:limit_per_objective]
    priorities["inconclusivas"] = rank_by_objective(inconclusive, "inconclusivas")[:limit_per_objective]
    return priorities


def summarize_daily_priorities(
    priorities: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    return {
        "total": sum(len(items) for items in priorities.values()),
        "counts": {group: len(items) for group, items in priorities.items()},
        "assets": {
            group: [item.get("ativo") for item in items]
            for group, items in priorities.items()
        },
    }
