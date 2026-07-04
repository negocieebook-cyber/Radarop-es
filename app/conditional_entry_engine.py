"""Converte candidatas reais EOD em planos condicionais de observação."""

from __future__ import annotations

from collections import Counter
from typing import Any


MIN_RISK_REWARD = 1.2
MIN_CREDIT_RATIO = 0.20
EOD_WARNING = "Entrada condicional para validar no pregão. Preço EOD não é executável."
DEBIT_STRATEGIES = {"call_debit_spread", "put_debit_spread"}
CREDIT_STRATEGIES = {"bull_put_spread", "bear_call_spread"}


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _width(candidate: dict[str, Any]) -> float | None:
    bought, sold = _number(candidate.get("strike_comprado")), _number(candidate.get("strike_vendido"))
    if bought is None or sold is None or bought == sold:
        return None
    return abs(bought - sold)


def calculate_max_debit_allowed(candidate: dict[str, Any]) -> dict[str, Any]:
    width = _width(candidate)
    reference = _number(candidate.get("custo_liquido"))
    if candidate.get("tipo_estrutura") not in DEBIT_STRATEGIES or width is None or reference is None:
        return {"max_debit_allowed": None, "debit_watch_limit": None, "debit_reference_eod": reference, "debit_status": "indisponível", "observacao": "largura ou débito EOD indisponível"}
    maximum = round(width / (1 + MIN_RISK_REWARD), 4)
    watch = round(maximum * 1.15, 4)
    status = "aceitável" if reference <= maximum else "acompanhar" if reference <= watch else "caro"
    return {"max_debit_allowed": maximum, "debit_watch_limit": watch, "debit_reference_eod": reference, "debit_status": status, "observacao": f"débito máximo para risco/retorno mínimo {MIN_RISK_REWARD}"}


def calculate_min_credit_required(candidate: dict[str, Any]) -> dict[str, Any]:
    width = _width(candidate)
    reference = _number(candidate.get("credito_liquido"))
    if candidate.get("tipo_estrutura") not in CREDIT_STRATEGIES or width is None or reference is None:
        return {"min_credit_required": None, "credit_watch_limit": None, "credit_reference_eod": reference, "credit_status": "indisponível", "observacao": "largura ou crédito EOD indisponível"}
    minimum = round(width * MIN_CREDIT_RATIO, 4)
    watch = round(minimum * 0.85, 4)
    status = "aceitável" if reference >= minimum else "acompanhar" if reference >= watch else "baixo_demais"
    return {"min_credit_required": minimum, "credit_watch_limit": watch, "credit_reference_eod": reference, "credit_status": status, "observacao": f"crédito mínimo de {MIN_CREDIT_RATIO:.0%} da largura"}


def candidate_has_complete_math(candidate: dict[str, Any]) -> bool:
    return all(_number(candidate.get(field)) is not None for field in ("perda_maxima", "ganho_maximo", "break_even"))


def candidate_has_usable_price(candidate: dict[str, Any]) -> bool:
    strategy = candidate.get("tipo_estrutura")
    reference = candidate.get("custo_liquido") if strategy in DEBIT_STRATEGIES else candidate.get("credito_liquido") if strategy in CREDIT_STRATEGIES else None
    return _number(reference) is not None and reference >= 0


def candidate_has_acceptable_expiration(candidate: dict[str, Any]) -> bool:
    dte = candidate.get("vencimento_dias")
    return isinstance(dte, int) and 5 <= dte <= 60


def candidate_has_acceptable_liquidity(candidate: dict[str, Any]) -> bool:
    return candidate.get("liquidez") in {"alta", "média", "baixa"}


def _healthbox_directly_invalidates(candidate: dict[str, Any]) -> bool:
    if str(candidate.get("healthbox_status", "")).lower() == "tese invalidada":
        return True
    trend = str(candidate.get("tendencia") or "").lower()
    strategy = candidate.get("tipo_estrutura")
    return (strategy in {"call_debit_spread", "bull_put_spread"} and trend == "baixa") or (strategy in {"put_debit_spread", "bear_call_spread"} and trend == "alta")


def identify_hard_blockers(candidate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if _number(candidate.get("perda_maxima")) is None:
        blockers.append("perda máxima ausente")
    if _number(candidate.get("ganho_maximo")) is None:
        blockers.append("ganho máximo ausente")
    if _number(candidate.get("break_even")) is None:
        blockers.append("break-even ausente")
    if not candidate_has_usable_price(candidate):
        blockers.append("preço EOD ausente")
    if _number(candidate.get("strike_comprado")) is None or _number(candidate.get("strike_vendido")) is None:
        blockers.append("strike ausente")
    if not candidate.get("vencimento") or candidate.get("vencimento_dias") is None:
        blockers.append("vencimento ausente")
    if candidate.get("liquidez") == "ilíquida":
        blockers.append("liquidez ilíquida")
    if _width(candidate) is None:
        blockers.append("width inválido")
    if candidate.get("tipo_estrutura") in DEBIT_STRATEGIES and _number(candidate.get("custo_liquido")) is not None and candidate["custo_liquido"] < 0:
        blockers.append("custo líquido negativo")
    if candidate.get("tipo_estrutura") in CREDIT_STRATEGIES and _number(candidate.get("credito_liquido")) is not None and candidate["credito_liquido"] < 0:
        blockers.append("crédito líquido negativo")
    if _number(candidate.get("risco_retorno")) is None:
        blockers.append("risco/retorno impossível de calcular")
    if candidate.get("healthbox") is None or "sem snapshot de mercado" in str(candidate.get("motivo", "")):
        blockers.append("market snapshot ausente")
    if "sem acesso" in str(candidate.get("motivo", "")).lower() or "opções indisponíveis" in str(candidate.get("motivo", "")).lower():
        blockers.append("opções indisponíveis na fonte atual")
    dte = candidate.get("vencimento_dias")
    if isinstance(dte, int) and (dte < 5 or dte > 60):
        blockers.append("vencimento fora da faixa segura")
    if _healthbox_directly_invalidates(candidate):
        blockers.append("Healthbox invalida diretamente a tese")
    return list(dict.fromkeys(blockers))


def identify_soft_warnings(candidate: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    debit, credit = calculate_max_debit_allowed(candidate), calculate_min_credit_required(candidate)
    if str(candidate.get("data_frequency", "")).upper() == "EOD":
        warnings.append("preço EOD; confirmar preço, spread e liquidez no pregão")
    elif not candidate.get("is_executable_price"):
        warnings.append("preço apenas EOD; confirmar bid/ask no pregão")
    if candidate.get("volatilidade_implicita") is None and "volatilidade_implicita" in candidate:
        warnings.append("IV ausente")
    for field, label in (("greeks", "gregas ausentes"), ("open_interest", "open interest ausente")):
        if field in candidate and candidate.get(field) is None:
            warnings.append(label)
    health = str(candidate.get("healthbox_status") or "").lower()
    if health in {"atenção", "não confirma", "indisponível", "indisponível por falta de dados"} and not _healthbox_directly_invalidates(candidate):
        warnings.append("Healthbox neutro ou não confirmando")
    if _number(candidate.get("rvol")) is not None and candidate["rvol"] < 0.8:
        warnings.append("rVol baixo")
    rsi = _number(candidate.get("rsi"))
    if rsi is not None and 45 <= rsi <= 60:
        warnings.append("RSI neutro")
    if debit.get("debit_status") == "acompanhar":
        warnings.append("custo um pouco acima do máximo")
    if credit.get("credit_status") == "acompanhar":
        warnings.append("crédito um pouco abaixo do mínimo")
    if candidate.get("liquidez") in {"baixa", "média"}:
        warnings.append("liquidez baixa ou média")
    dte = candidate.get("vencimento_dias")
    if isinstance(dte, int) and 5 <= dte <= 10:
        warnings.append("vencimento entre 5 e 10 dias")
    if isinstance(dte, int) and 46 <= dte <= 60:
        warnings.append("vencimento entre 46 e 60 dias; observar liquidez")
    if not candidate.get("spread_disponivel"):
        warnings.append("spread precisa ser confirmado no pregão")
    if candidate.get("bulkowski_status") in {"inconclusivo", "indisponível"}:
        warnings.append("Bulkowski inconclusivo")
    return list(dict.fromkeys(warnings))


def build_confirmation_rules(candidate: dict[str, Any]) -> list[str]:
    strategy = candidate.get("tipo_estrutura")
    rules = ["confirmar preço atual no pregão; o preço EOD não é executável", "confirmar liquidez e spread das duas séries no pregão"]
    if strategy in {"call_debit_spread", "bull_put_spread"}:
        rules.extend(["ativo continuar acima do suporte", "tendência não virar baixa", "RSI não entrar em sobrecompra extrema"])
    if strategy == "call_debit_spread":
        rules.extend(["custo líquido não ultrapassar o débito máximo aceitável", "break-even permanecer coerente com resistência e alvo"])
    elif strategy == "put_debit_spread":
        rules.extend(["ativo continuar abaixo da resistência", "suporte perdido ou tendência de baixa permanecer confirmada", "custo líquido não ultrapassar o débito máximo aceitável"])
    elif strategy == "bull_put_spread":
        rules.extend(["strike vendido manter margem aceitável em relação ao suporte", "crédito no pregão ser igual ou maior que o mínimo exigido", "suporte não ser perdido"])
    elif strategy == "bear_call_spread":
        rules.extend(["ativo continuar abaixo da resistência", "crédito no pregão ser igual ou maior que o mínimo exigido", "resistência não ser rompida", "Healthbox não virar alta forte"])
    return list(dict.fromkeys(rules))


def build_invalidation_rules(candidate: dict[str, Any]) -> list[str]:
    strategy = candidate.get("tipo_estrutura")
    rules = ["spread ficar excessivamente aberto", "liquidez ficar ruim ou inexistente", "dados de opções continuarem desatualizados", "não haver preço atual no pregão", "Healthbox virar contra a estratégia"]
    if strategy in {"call_debit_spread", "bull_put_spread"}:
        rules.append("ativo perder o suporte em operação altista")
    if strategy in {"put_debit_spread", "bear_call_spread"}:
        rules.append("ativo romper a resistência em operação baixista")
    if strategy in DEBIT_STRATEGIES:
        rules.append("custo líquido ultrapassar o débito máximo aceitável")
    if strategy in CREDIT_STRATEGIES:
        rules.append("crédito ficar abaixo do mínimo exigido")
    if candidate.get("vencimento_dias") is not None and candidate["vencimento_dias"] <= 7:
        rules.append("vencimento ficar curto demais")
    return list(dict.fromkeys(rules))


def classify_conditional_entry(candidate: dict[str, Any]) -> dict[str, Any]:
    strategy = candidate.get("tipo_estrutura")
    debit = calculate_max_debit_allowed(candidate)
    credit = calculate_min_credit_required(candidate)
    dte = candidate.get("vencimento_dias")
    if dte is None:
        expiration_quality, expiration_note = "indisponível", "dias até vencimento indisponíveis"
    elif dte < 5:
        expiration_quality, expiration_note = "muito curto", "menos de 5 dias; evitar nesta fase"
    elif dte <= 10:
        expiration_quality, expiration_note = "curto", "5 a 10 dias; apenas acompanhar"
    elif dte <= 45:
        expiration_quality, expiration_note = "preferido", "11 a 45 dias; faixa preferida"
    elif dte <= 60:
        expiration_quality, expiration_note = "aceitável", "46 a 60 dias; observar liquidez"
    else:
        expiration_quality, expiration_note = "longo", "acima de 60 dias; evitar nesta fase"
    essential_missing = candidate.get("status") == "inconclusivo" or strategy not in DEBIT_STRATEGIES | CREDIT_STRATEGIES or any(
        marker in str(candidate.get("motivo", "")).lower() for marker in ("sem snapshot", "sem acesso", "opções indisponíveis")
    )
    blockers = identify_hard_blockers(candidate)
    warnings = identify_soft_warnings(candidate)
    rr = _number(candidate.get("risco_retorno"))
    severe_price = (strategy in DEBIT_STRATEGIES and debit["debit_status"] == "caro") or (strategy in CREDIT_STRATEGIES and credit["credit_status"] == "baixo_demais")
    if essential_missing:
        status, decision, notes = "inconclusivo", "inconclusivo", [candidate.get("motivo") or "dados insuficientes para calcular entrada condicional"]
    elif blockers:
        status, decision, notes = "evitar", "evitar", blockers
    elif severe_price:
        status, decision = "evitar", "evitar"
        notes = ["custo muito acima do máximo"] if strategy in DEBIT_STRATEGIES else ["crédito muito abaixo do mínimo"]
    elif rr is not None and rr < 0.20:
        status, decision, notes = "evitar", "evitar", ["risco/retorno muito ruim"]
    else:
        price_acceptable = debit["debit_status"] == "aceitável" if strategy in DEBIT_STRATEGIES else credit["credit_status"] == "aceitável"
        preferred_expiration = isinstance(dte, int) and 11 <= dte <= 45
        health_favorable = candidate.get("healthbox_status") == "confirma"
        if warnings or not price_acceptable or not preferred_expiration or not health_favorable:
            status, decision, notes = "acompanhar_na_abertura", "acompanhar na abertura", warnings or ["confirmar preço, spread e liquidez no pregão"]
        else:
            status, decision, notes = "entrada_condicional", "entrada condicional para validar no pregão", ["preço EOD dentro da faixa e critérios mínimos presentes"]
    return {
        "conditional_status": status, "conditional_decision": decision, "entry_notes": notes,
        "hard_blockers": blockers, "soft_warnings": warnings,
        "expiration_quality": expiration_quality, "expiration_note": expiration_note,
    }


def calculate_entry_conditions(candidate: dict[str, Any]) -> dict[str, Any]:
    debit = calculate_max_debit_allowed(candidate)
    credit = calculate_min_credit_required(candidate)
    classification = classify_conditional_entry(candidate)
    strategy = candidate.get("tipo_estrutura")
    reference = debit["debit_reference_eod"] if strategy in DEBIT_STRATEGIES else credit["credit_reference_eod"] if strategy in CREDIT_STRATEGIES else None
    if strategy in DEBIT_STRATEGIES:
        condition = f"débito no pregão <= {debit['max_debit_allowed']}" if debit["max_debit_allowed"] is not None else "débito máximo indisponível"
    elif strategy in CREDIT_STRATEGIES:
        condition = f"crédito no pregão >= {credit['min_credit_required']}" if credit["min_credit_required"] is not None else "crédito mínimo indisponível"
    else:
        condition = "condição de preço indisponível"
    return {
        **classification, "entry_reference_price": reference,
        "max_debit_allowed": debit["max_debit_allowed"], "debit_watch_limit": debit["debit_watch_limit"],
        "min_credit_required": credit["min_credit_required"], "credit_watch_limit": credit["credit_watch_limit"],
        "entry_price_condition": condition, "confirmation_rules": build_confirmation_rules(candidate),
        "invalidation_rules": build_invalidation_rules(candidate), "eod_warning": EOD_WARNING,
    }


def rank_conditional_entries(candidates: list[dict[str, Any]], top_n: int = 10) -> list[dict[str, Any]]:
    status_rank = {"entrada_condicional": 0, "acompanhar_na_abertura": 1, "evitar": 2, "inconclusivo": 3}
    liquidity_rank = {"alta": 4, "média": 3, "baixa": 2, "indisponível": 1, "ilíquida": 0}
    def key(item: dict[str, Any]) -> tuple[Any, ...]:
        return (
            status_rank.get(str(item.get("conditional_status")), 4),
            -(_number(item.get("score")) or -1), -(_number(item.get("risco_retorno")) or -1),
            -liquidity_rank.get(str(item.get("liquidez")), 1), -(_number(item.get("healthbox_score")) or -1),
        )
    return sorted(candidates, key=key)[:max(0, top_n)]


def summarize_conditional_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(item.get("conditional_status", "inconclusivo") for item in entries)
    return {
        "total": len(entries), "entrada_condicional": counts["entrada_condicional"],
        "acompanhar_na_abertura": counts["acompanhar_na_abertura"], "evitar": counts["evitar"],
        "inconclusivo": counts["inconclusivo"],
    }
