"""Avalia o catálogo de estratégias contra cada tese gráfica."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.capital_requirements import estimate_strategy_capital_required
from app.user_trading_profile import load_user_trading_profile

from app.options_strategy_catalog import get_strategy_catalog
from app.strategy_mapper import REGIME_STRATEGY_IDS, STRATEGY_WARNING, classify_market_regime
from app.conditional_entry_engine import calculate_max_debit_allowed, calculate_min_credit_required
from app.practical_strategy_view import build_practical_strategy_summary
from app.strategy_objective import build_strategy_objective_label, summarize_objectives_for_thesis
from app.daily_priority_engine import classify_practical_priority


MANUAL_PLAN_WARNING = (
    "Plano de validação manual; não é ordem. Não operar sem preço, spread, liquidez, perda máxima e break-even."
)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_strategy_catalog() -> list[dict[str, Any]]:
    return get_strategy_catalog()


def _available_data(thesis: dict[str, Any]) -> set[str]:
    available = {
        key for key, value in thesis.items()
        if not isinstance(value, (dict, list)) and value not in {None, "", "indisponível"}
    }
    if thesis.get("cadeia_opcoes_status") == "disponivel_fonte":
        available.add("cadeia_real")
    options = thesis.get("options_validation_candidates") or []
    if any(_number(item.get("perda_maxima")) is not None for item in options):
        available.add("perda_maxima")
    if any(item.get("break_even") is not None for item in options):
        available.update({"break_evens", "break_even_inferior", "break_even_superior"})
    if any(item.get("entry_reference_price") is not None for item in options):
        available.update({"premio", "custo"})
    if any(item.get("liquidez") not in {None, "", "indisponível", "sem negócio", "ilíquida"} for item in options):
        available.add("liquidez")
    return available


def _matching_option_candidates(strategy_id: str, thesis: dict[str, Any]) -> list[dict[str, Any]]:
    supported = {"call_debit_spread", "put_debit_spread", "bull_put_spread", "bear_call_spread", "covered_call", "cash_secured_put"}
    if strategy_id not in supported:
        return []
    return [item for item in (thesis.get("options_validation_candidates") or []) if item.get("tipo_estrutura") == strategy_id]


def _validated_by_options(strategy_id: str, thesis: dict[str, Any]) -> tuple[bool, bool]:
    matching = _matching_option_candidates(strategy_id, thesis)
    if not matching:
        return False, False
    for item in matching:
        loss = _number(item.get("perda_maxima"))
        liquidity = str(item.get("liquidez") or item.get("liquidity_status") or "").lower()
        if (
            loss is not None and loss >= 0
            and item.get("break_even") is not None
            and item.get("entry_reference_price") is not None
            and liquidity not in {"", "indisponível", "sem negócio", "ilíquida"}
        ):
            return True, True
    return False, True


def _first_matching_option(strategy_id: str, thesis: dict[str, Any]) -> dict[str, Any] | None:
    matches = _matching_option_candidates(strategy_id, thesis)
    return matches[0] if matches else None


def _real_delta(candidate: dict[str, Any] | None) -> Any:
    if not candidate:
        return None
    for key in ("delta", "delta_comprado", "delta_vendido", "deltas"):
        if candidate.get(key) is not None:
            return candidate[key]
    return None


def _actual_strikes(candidate: dict[str, Any] | None) -> str | None:
    if not candidate:
        return None
    values = []
    for key in ("strike_comprado", "strike_vendido", "strikes"):
        value = candidate.get(key)
        if value is not None:
            values.append(f"{key}: {value}")
    return "; ".join(values) or None


def build_manual_validation_plan(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any]
) -> dict[str, Any]:
    """Cria orientação relativa; números reais só vêm de candidatas da cadeia."""
    strategy_id = str(strategy_candidate.get("strategy_id") or strategy_candidate.get("id") or "")
    strategy_name = strategy_candidate.get("strategy_name") or strategy_candidate.get("nome")
    status = strategy_candidate.get("status")
    matching = _first_matching_option(strategy_id, thesis)
    chain_available = thesis.get("cadeia_opcoes_status") == "disponivel_fonte"
    if status in {"rejeitada", "nao_aplicavel"}:
        manual_status = "nao_aplicavel"
    elif chain_available and matching:
        manual_status = "validavel_com_cadeia"
    else:
        manual_status = "procurar_no_book"

    support = thesis.get("suporte")
    resistance = thesis.get("resistencia")
    target = thesis.get("alvo")
    invalidation = thesis.get("invalidacao")
    trigger = thesis.get("gatilho_confirmacao")
    delta_targets = {
        "long_call": "0,40 a 0,60 na call comprada",
        "long_put": "0,40 a 0,60 em módulo na put comprada",
        "call_debit_spread": "call comprada 0,45 a 0,60; call vendida perto do alvo",
        "put_debit_spread": "put comprada 0,45 a 0,60 em módulo; put vendida perto do alvo",
        "bull_put_spread": "put vendida 0,15 a 0,30 em módulo",
        "bear_call_spread": "call vendida 0,15 a 0,30",
        "iron_condor": "put e call vendidas 0,15 a 0,30 em módulo",
        "covered_call": "call vendida 0,20 a 0,35",
    }
    strike_regions = {
        "long_call": f"call próxima do preço atual/gatilho ({trigger}) ou levemente OTM",
        "long_put": f"put próxima do preço atual/gatilho de queda ({trigger}) ou levemente OTM",
        "call_debit_spread": f"comprar call perto do gatilho; vender call perto do alvo/resistência ({target or resistance})",
        "put_debit_spread": f"comprar put perto do gatilho; vender put perto do alvo/suporte ({target or support})",
        "bull_put_spread": f"vender put abaixo do suporte/invalidação ({support or invalidation}); comprar put abaixo",
        "bear_call_spread": f"vender call acima da resistência ({resistance}); comprar call acima",
        "iron_condor": f"put vendida abaixo do suporte ({support}); call vendida acima da resistência ({resistance}); proteções nas pontas",
        "iron_butterfly": "centro perto do preço atual; proteções compradas nas pontas",
        "calendar_spread": f"strike perto do preço atual ou alvo ({target}); comprar vencimento longo e vender curto",
        "covered_call": f"call vendida acima da resistência ({resistance}) ou no preço aceito para venda",
        "collar": f"put comprada abaixo do suporte ({support}); call vendida acima da resistência ({resistance})",
        "long_straddle": "call e put no mesmo strike ou próximas do preço atual",
        "long_strangle": "call OTM acima e put OTM abaixo do preço atual",
    }
    advanced = {"backspread_call", "backspread_put", "ratio_spread_travado", "diagonal_spread", "synthetic_long_stock", "synthetic_short_stock"}
    if strategy_id in advanced:
        strike_region = "definir somente com cadeia real, risco travado e perda máxima calculada"
    else:
        strike_region = strike_regions.get(strategy_id, "selecionar strikes conforme pernas, níveis gráficos e cadeia real")
    real_strikes = _actual_strikes(matching)
    if real_strikes:
        strike_region = f"strikes disponíveis na candidata real: {real_strikes}"

    expiration = "20 a 45 dias" if strategy_id in {"long_call", "long_put", "call_debit_spread", "put_debit_spread"} else strategy_candidate.get("vencimento_ideal")
    debit = calculate_max_debit_allowed(matching or {})
    credit = calculate_min_credit_required(matching or {})
    delta_target = _real_delta(matching) or delta_targets.get(strategy_id) or strategy_candidate.get("delta_alvo")
    checklist = [
        "confirmar preço ou prêmio atual no book",
        "confirmar bid/ask e spread",
        "confirmar liquidez e negócios",
        "calcular perda máxima e break-even",
        "conferir strikes contra suporte, resistência, alvo e invalidação",
    ]
    rejection_rules = list(strategy_candidate.get("motivos_contra") or [])
    rejection_rules.extend([
        "rejeitar se spread estiver aberto ou liquidez insuficiente",
        "rejeitar se perda máxima ou break-even não puderem ser calculados",
    ])
    special_rejections = {
        "long_call": ["rejeitar se theta estiver alto ou break-even ficar acima do alvo"],
        "long_put": ["rejeitar se o custo exigir queda maior que o alvo técnico"],
        "call_debit_spread": ["rejeitar se break-even ficar incoerente com o alvo de alta"],
        "put_debit_spread": ["rejeitar se break-even ficar incoerente com o alvo de queda"],
        "bull_put_spread": ["rejeitar se suporte estiver fraco ou crédito abaixo de 20% da largura"],
        "bear_call_spread": ["rejeitar se resistência estiver rompendo ou crédito abaixo de 20% da largura"],
        "iron_condor": ["rejeitar sem range claro, prêmio suficiente e break-evens fora do suporte/resistência"],
        "iron_butterfly": ["rejeitar se o ativo estiver perto de romper suporte ou resistência"],
        "calendar_spread": ["rejeitar sem leitura de volatilidade, theta e dois vencimentos líquidos"],
        "covered_call": ["não aplicável sem posse do ativo ou aceitação de exercício"],
        "collar": ["não aplicável sem posse do ativo"],
    }
    rejection_rules.extend(special_rejections.get(strategy_id, []))
    if strategy_id in {"long_straddle", "long_strangle"}:
        checklist.extend(["calcular custo total e dois break-evens", "confirmar catalisador e movimento necessário"])
        rejection_rules.append("sem cadeia, manter somente como estudo de compressão/evento")
    if strategy_id in advanced:
        checklist.append("validar estrutura avançada, ajustes e risco por cenário")
        rejection_rules.append("não recomendar como padrão para pequeno capital")
    return {
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "manual_validation_status": manual_status,
        "delta_target": delta_target,
        "strike_region": strike_region,
        "expiration_window": expiration,
        "max_debit_allowed": debit.get("max_debit_allowed"),
        "min_credit_required": credit.get("min_credit_required"),
        "structure_legs_description": list(strategy_candidate.get("pernas") or []),
        "book_checklist": list(dict.fromkeys(checklist)),
        "rejection_rules": list(dict.fromkeys(rejection_rules)),
        "warning": MANUAL_PLAN_WARNING,
    }


def evaluate_strategy_for_thesis(strategy: dict[str, Any], thesis: dict[str, Any]) -> dict[str, Any]:
    regime = thesis.get("market_regime") or classify_market_regime(thesis)
    strategy_id = str(strategy["id"])
    ideal = regime in strategy.get("regime_ideal", [])
    preferred_ids = REGIME_STRATEGY_IDS.get(regime, ())
    favorable: list[str] = []
    against: list[str] = []
    validations = list(dict.fromkeys([
        "cadeia real", "prêmio ou custo", "spread", "liquidez", "break-even", "perda máxima calculada",
    ]))
    score = 20
    hard_rejection = False

    if ideal:
        score += 45
        favorable.append(f"regime {regime} compatível")
    if strategy_id in preferred_ids:
        position = preferred_ids.index(strategy_id)
        score += max(10, 30 - position * 5)
        favorable.append("estratégia favorecida para o regime")
    if thesis.get("healthbox_score") is not None and _number(thesis.get("healthbox_score")) >= 60:
        score += 5
        favorable.append("Healthbox não bloqueia o estudo gráfico")

    if regime == "lateral" and strategy_id in {"long_call", "long_put"} and not thesis.get("catalisador"):
        hard_rejection = True
        against.append("opção direcional simples rejeitada em lateralidade sem catalisador")
    if strategy_id == "iron_condor":
        support, resistance = _number(thesis.get("suporte")), _number(thesis.get("resistencia"))
        if support is None or resistance is None or support >= resistance:
            hard_rejection = True
            against.append("iron condor exige suporte e resistência claros")
        else:
            favorable.append("suporte e resistência claros")
            validations = ["suporte", "resistência", "prêmio", "liquidez", "spread", "break-evens", "perda máxima"]
    if not strategy.get("risco_definido", False):
        hard_rejection = True
        against.append("estrutura com risco descoberto rejeitada")
    if strategy.get("status_padrao_sem_cadeia") == "rejeitada":
        hard_rejection = True
        against.append("catálogo determina rejeição padrão fora de estudo teórico completo")
    if regime == "indefinido" and strategy.get("complexidade") == "avançada":
        hard_rejection = True
        against.append("estrutura complexa rejeitada com tese indefinida")
    if strategy.get("exige_ativo") and not thesis.get("usuario_possui_ativo"):
        against.append("posse do ativo não confirmada")
    if strategy.get("exige_caixa") and not thesis.get("caixa_disponivel"):
        against.append("caixa necessário não confirmado")

    required = list(strategy.get("dados_obrigatorios") or [])
    available = _available_data(thesis)
    missing = [field for field in required if field not in available]
    if missing:
        score -= min(10, len(missing))
    chain_available = thesis.get("cadeia_opcoes_status") == "disponivel_fonte"
    validated, had_matching = _validated_by_options(strategy_id, thesis)

    if hard_rejection:
        status = "rejeitada"
        score = min(score, 25)
    elif ideal or strategy_id in preferred_ids:
        if strategy.get("exige_cadeia_real") and not validated:
            status = "rejeitada" if chain_available and had_matching else "pendente_validacao_opcoes"
            against.append(
                "estrutura encontrada sem perda máxima, break-even, preço ou liquidez válidos"
                if chain_available and had_matching
                else "cadeia e matemática de opções ainda não validaram a candidata"
            )
        else:
            status = "apta_graficamente"
            favorable.append("motor de opções forneceu perda máxima, break-even, preço e liquidez")
    elif score >= 45:
        status = "possivel"
    else:
        status = "nao_aplicavel"
        against.append("regime atual não favorece a estratégia")

    return {
        "strategy_id": strategy_id,
        "strategy_name": strategy.get("nome"),
        "explicacao_curta": strategy.get("explicacao_curta"),
        "pernas": list(strategy.get("pernas") or []),
        "tipo": strategy.get("tipo"),
        "complexidade": strategy.get("complexidade"),
        "risco_definido": strategy.get("risco_definido"),
        "regime_compativel": ideal,
        "tese_ideal": strategy.get("tese_ideal"),
        "quando_usar": strategy.get("quando_usar"),
        "quando_evitar": strategy.get("quando_evitar"),
        "principal_risco": strategy.get("quando_evitar"),
        "calculos_obrigatorios": list(strategy.get("calculos_obrigatorios") or []),
        "suitability_score": max(0, min(100, round(score))),
        "status": status,
        "motivos_favoraveis": list(dict.fromkeys(favorable)),
        "motivos_contra": list(dict.fromkeys(against)),
        "dados_necessarios": missing,
        "validacoes_obrigatorias": validations,
        "delta_alvo": strategy.get("delta_alvo_padrao"),
        "vencimento_ideal": strategy.get("vencimento_ideal"),
        "alertas": list(strategy.get("alertas") or []),
        "aviso": STRATEGY_WARNING,
    }


def rank_strategy_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {"apta_graficamente": 0, "pendente_validacao_opcoes": 1, "possivel": 2, "rejeitada": 3, "nao_aplicavel": 4}
    return sorted(candidates, key=lambda item: (priority.get(item.get("status"), 5), -int(item.get("suitability_score") or 0), str(item.get("strategy_id") or "")))


def screen_strategies_for_thesis(thesis: dict[str, Any]) -> dict[str, Any]:
    evaluated = [evaluate_strategy_for_thesis(strategy, thesis) for strategy in load_strategy_catalog()]
    profile = thesis.get("trading_profile") or load_user_trading_profile()
    for candidate in evaluated:
        candidate.update(build_strategy_objective_label(candidate, thesis))
        candidate["manual_validation_plan"] = build_manual_validation_plan(candidate, thesis)
        candidate.update(estimate_strategy_capital_required(candidate, thesis, profile))
        candidate["practical_priority"] = classify_practical_priority(candidate, thesis)
    results = rank_strategy_candidates(evaluated)
    candidates = [item for item in results if item["status"] in {"apta_graficamente", "pendente_validacao_opcoes", "possivel"}]
    rejected = [item for item in results if item["status"] in {"rejeitada", "nao_aplicavel"}]
    preferred = candidates[0] if candidates else None
    if any(item["status"] == "apta_graficamente" for item in candidates):
        overall = "validada_com_cadeia"
    elif any(item["status"] == "pendente_validacao_opcoes" for item in candidates):
        overall = "pendente_validacao_opcoes"
    elif candidates:
        overall = "estrategia_grafica_sugerida"
    else:
        overall = "rejeitada_por_opcoes"
    rejected_summary = [
        {
            "strategy_id": item["strategy_id"],
            "strategy_name": item["strategy_name"],
            "reason": (item["motivos_contra"] or ["não aplicável ao regime"])[0],
        }
        for item in rejected
    ]
    output = {
        "strategy_screening": results,
        "preferred_strategy": preferred["strategy_name"] if preferred else "esperar / acompanhar tese gráfica",
        "top_3_strategies": candidates[:3],
        "rejected_strategies_summary": rejected_summary,
        "strategy_status": overall,
    }
    output.update(build_practical_strategy_summary({**thesis, **output}))
    output.update(summarize_objectives_for_thesis({**thesis, **output}))
    return output


def summarize_strategy_screening(results: list[dict[str, Any]]) -> dict[str, Any]:
    screenings = [item for thesis in results for item in thesis.get("strategy_screening", [])]
    statuses = Counter(item.get("status") for item in screenings)
    preferred = Counter(thesis.get("preferred_strategy") for thesis in results)
    return {
        "theses_screened": sum(bool(thesis.get("strategy_screening")) for thesis in results),
        "strategies_evaluated": len(screenings),
        "strategies_per_thesis": len(load_strategy_catalog()),
        "statuses": dict(statuses),
        "top_preferred_strategies": dict(preferred.most_common(10)),
    }
