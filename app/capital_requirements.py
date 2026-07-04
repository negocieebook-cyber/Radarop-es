"""Estimativas informativas de capital, sem substituir margem de corretora."""

from __future__ import annotations

from typing import Any


CAPITAL_WARNING = "Capital estimado não substitui a margem exigida pela corretora."
TOLERANCE_BUFFER = {"agressiva": 1.0, "moderada": 1.25, "conservadora": 1.5}


def recommend_capital_amount(capital: float | None, tolerance: str = "moderada") -> float | None:
    if capital is None:
        return None
    return round(capital * TOLERANCE_BUFFER.get(tolerance, 1.25), 2)
DEBIT_IDS = {"long_call", "long_put", "call_debit_spread", "put_debit_spread", "calendar_spread", "diagonal_spread", "long_straddle", "long_strangle"}
CREDIT_IDS = {"bull_put_spread", "bear_call_spread", "iron_condor", "iron_butterfly", "short_straddle_travado", "short_strangle_travado"}
ASSET_IDS = {"covered_call", "protective_put", "collar"}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _strategy_id(candidate: dict[str, Any]) -> str:
    return str(candidate.get("strategy_id") or candidate.get("id") or candidate.get("tipo_estrutura") or "")


def _matching_option_candidate(candidate: dict[str, Any], thesis: dict[str, Any]) -> dict[str, Any]:
    strategy_id = _strategy_id(candidate)
    if candidate.get("tipo_estrutura") == strategy_id:
        return candidate
    for item in thesis.get("options_validation_candidates", []) or []:
        if item.get("tipo_estrutura") == strategy_id:
            return item
    return {}


def _multiplier(source: dict[str, Any], profile: dict[str, Any]) -> float | None:
    for key in ("multiplicador_contrato", "contract_multiplier", "contractMultiplier", "contract_size"):
        value = _number(source.get(key))
        if value is not None and value > 0:
            return value
    if profile.get("usar_multiplicador_padrao_se_fonte_ausente"):
        value = _number(profile.get("multiplicador_contrato_padrao"))
        return value if value is not None and value > 0 else None
    return None


def _width(source: dict[str, Any]) -> float | None:
    bought = _number(source.get("strike_comprado"))
    sold = _number(source.get("strike_vendido"))
    return abs(bought - sold) if bought is not None and sold is not None and bought != sold else None


def estimate_max_loss_required(strategy_candidate: dict[str, Any]) -> float | None:
    value = _number(strategy_candidate.get("perda_maxima"))
    return value if value is not None and value >= 0 else None


def estimate_margin_proxy(strategy_candidate: dict[str, Any]) -> float | None:
    value = _number(strategy_candidate.get("capital_em_risco"))
    if value is not None and value >= 0:
        return value
    return estimate_max_loss_required(strategy_candidate)


def _estimate_base(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any], profile: dict[str, Any]
) -> tuple[float | None, float | None, float | None, list[str]]:
    strategy_id = _strategy_id(strategy_candidate)
    source = _matching_option_candidate(strategy_candidate, thesis)
    multiplier = _multiplier(source, profile)
    missing: list[str] = []
    if multiplier is None:
        missing.append("multiplicador")

    explicit_loss = estimate_max_loss_required(source)
    if explicit_loss is not None and multiplier is not None:
        total_loss = explicit_loss * multiplier
        return total_loss, total_loss, total_loss, missing

    if strategy_id in ASSET_IDS:
        if not thesis.get("usuario_possui_ativo"):
            return None, None, None, [*missing, "ativo em carteira"]
        if strategy_id == "covered_call":
            price = _number(thesis.get("preco_atual"))
            if price is None:
                missing.append("preço do ativo")
                return None, None, None, missing
            if multiplier is None:
                return None, None, None, missing
            capital = price * multiplier
            return capital, capital, capital, missing

    if strategy_id == "cash_secured_put":
        strike = _number(source.get("strike_vendido"))
        if strike is None:
            missing.append("strike vendido")
        if strike is None or multiplier is None:
            return None, None, None, missing
        capital = strike * multiplier
        return capital, capital, capital, missing

    if strategy_id in DEBIT_IDS:
        cost = _number(source.get("custo_liquido"))
        if cost is None:
            cost = _number(source.get("premio_pago"))
        if cost is None:
            cost = _number(source.get("custo_total"))
        if cost is None:
            missing.append("custo ou prêmio")
        if cost is None or multiplier is None:
            return None, None, None, missing
        total = cost * multiplier
        return total, total, total, missing

    if strategy_id in CREDIT_IDS:
        width = _width(source)
        credit = _number(source.get("credito_liquido"))
        if width is None:
            missing.append("largura da estrutura")
        if credit is None:
            missing.append("crédito")
        if width is None or credit is None or multiplier is None:
            return None, None, None, missing
        risk = max(0.0, width - credit) * multiplier
        return risk, risk, risk, missing

    missing.append("modelo de capital da estrutura")
    return None, None, None, missing


def estimate_minimum_technical_capital(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any], profile: dict[str, Any]
) -> float | None:
    minimum, _, _, _ = _estimate_base(strategy_candidate, thesis, profile)
    return round(minimum, 2) if minimum is not None else None


def estimate_recommended_capital(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any], profile: dict[str, Any]
) -> float | None:
    minimum = estimate_minimum_technical_capital(strategy_candidate, thesis, profile)
    if minimum is None:
        return None
    factor = TOLERANCE_BUFFER.get(str(profile.get("tolerancia_capital")), 1.25)
    return round(minimum * factor, 2)


def estimate_strategy_capital_required(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any], profile: dict[str, Any]
) -> dict[str, Any]:
    minimum, required, loss, missing = _estimate_base(strategy_candidate, thesis, profile)
    recommendation = estimate_recommended_capital(strategy_candidate, thesis, profile)
    margin = required if _strategy_id(strategy_candidate) in CREDIT_IDS | {"cash_secured_put"} else None
    result = {
        "minimum_technical_capital": round(minimum, 2) if minimum is not None else None,
        "recommended_capital": recommendation,
        "capital_required_estimate": round(required, 2) if required is not None else None,
        "max_loss_estimate": round(loss, 2) if loss is not None else None,
        "margin_proxy": round(margin, 2) if margin is not None else None,
        "missing_capital_fields": list(dict.fromkeys(missing)),
    }
    fit = classify_capital_fit({**strategy_candidate, **result}, thesis, profile)
    result.update(fit)
    result["capital_fit_reason"] = explain_capital_requirement({**strategy_candidate, **result}, thesis, profile)
    result["capital_warning"] = CAPITAL_WARNING
    return result


def classify_capital_fit(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any], profile: dict[str, Any]
) -> dict[str, str]:
    strategy_id = _strategy_id(strategy_candidate)
    if strategy_id in ASSET_IDS and not thesis.get("usuario_possui_ativo"):
        return {"capital_fit_status": "exige_ativo_em_carteira"}
    required = _number(strategy_candidate.get("capital_required_estimate"))
    loss = _number(strategy_candidate.get("max_loss_estimate"))
    if required is None or loss is None or strategy_candidate.get("missing_capital_fields"):
        return {"capital_fit_status": "pendente_dados"}
    capital = _number(profile.get("capital_disponivel"))
    if capital is None:
        return {"capital_fit_status": "pendente_dados"}
    loss_limits = []
    explicit = _number(profile.get("perda_maxima_por_operacao"))
    if explicit is not None:
        loss_limits.append(explicit)
    percent = _number(profile.get("percentual_maximo_por_operacao"))
    if percent is not None:
        loss_limits.append(capital * percent / 100)
    loss_limit = min(loss_limits) if loss_limits else None
    if strategy_id == "cash_secured_put" and required > capital:
        return {"capital_fit_status": "exige_caixa_para_exercicio"}
    if required > capital or (loss_limit is not None and loss > loss_limit):
        return {"capital_fit_status": "acima_do_capital"}
    if required > capital * 0.5 or (loss_limit is not None and loss > loss_limit * 0.8):
        return {"capital_fit_status": "cabe_apertado"}
    return {"capital_fit_status": "cabe_bem"}


def explain_capital_requirement(
    strategy_candidate: dict[str, Any], thesis: dict[str, Any], profile: dict[str, Any]
) -> str:
    status = strategy_candidate.get("capital_fit_status")
    if status == "cabe_bem":
        return "Capital e perda máxima estimada estão dentro dos limites informados."
    if status == "cabe_apertado":
        return "Cabe apertado. Validar se a perda máxima está confortável para você."
    if status == "acima_do_capital":
        return "Capital requerido ou perda máxima estimada excede o limite informado."
    if status == "exige_ativo_em_carteira":
        return "A estratégia exige o ativo em carteira; posse não foi confirmada."
    if status == "exige_caixa_para_exercicio":
        return "A estratégia exige caixa suficiente para eventual exercício."
    if status == "complexa_para_capital_pequeno":
        return "Estratégia avançada; revisar capital, ajustes e perda máxima antes de considerar."
    if _number(profile.get("capital_disponivel")) is None:
        return "Informe capital disponível para classificar encaixe."
    missing = strategy_candidate.get("missing_capital_fields") or []
    return "Dados insuficientes para estimar capital: " + ", ".join(missing)
