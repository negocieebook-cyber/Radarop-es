"""Diagnóstico explicável do funil de oportunidades reais EOD."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.conditional_entry_engine import (
    candidate_has_complete_math,
    candidate_has_usable_price,
    identify_hard_blockers,
    identify_soft_warnings,
    summarize_conditional_entries,
)


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _candidate_reasons(candidate: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    text = str(candidate.get("motivo") or "").lower()
    if "sem snapshot de opções" in text:
        reasons.append("sem snapshot de opções")
    if "sem acesso" in text:
        reasons.append("sem acesso a opções")
    if candidate.get("vencimento_dias") is not None and candidate["vencimento_dias"] < 5:
        reasons.append("vencimento curto demais")
    if candidate.get("liquidez") in {"baixa", "ilíquida", "indisponível"}:
        reasons.append("liquidez insuficiente")
    if not candidate.get("is_executable_price") and candidate.get("price_basis") != "indisponível":
        reasons.append("preço EOD apenas indicativo")
    if candidate.get("entry_reference_price") is None and candidate.get("tipo_estrutura"):
        reasons.append("preço da opção indisponível")
        basis = str(candidate.get("price_basis") or "")
        if "zerado" in basis:
            reasons.append("campo de preço zerado")
        elif "indisponível" in basis:
            reasons.extend(["bid/ask ausente", "close ausente", "average ausente", "raw sem campo de preço reconhecido"])
    if candidate.get("max_debit_allowed") is not None and candidate.get("custo_liquido") is not None and candidate["custo_liquido"] > candidate["max_debit_allowed"]:
        reasons.append("custo líquido acima do máximo")
    if candidate.get("min_credit_required") is not None and candidate.get("credito_liquido") is not None and candidate["credito_liquido"] < candidate["min_credit_required"]:
        reasons.append("crédito abaixo do mínimo")
    if _number(candidate.get("risco_retorno")) is not None and candidate["risco_retorno"] < 0.25:
        reasons.append("risco/retorno ruim")
    if candidate.get("healthbox_status") in {"não confirma", "indisponível", "indisponível por falta de dados"}:
        reasons.append("Healthbox não confirma")
    if not all(_number(candidate.get(field)) is not None for field in ("perda_maxima", "ganho_maximo", "break_even")):
        reasons.append("matemática incompleta")
        calculation = candidate.get("calculation", {})
        missing_math = calculation.get("missing_fields", []) if isinstance(calculation, dict) else []
        aliases = {
            "premio_pago": "prêmio pago ausente", "premio_recebido": "prêmio recebido ausente",
            "strike_comprado": "strike comprado ausente", "strike_vendido": "strike vendido ausente",
        }
        reasons.extend(aliases.get(field, f"cálculo sem {field}") for field in missing_math)
        notes = " ".join(map(str, calculation.get("notes", []))) if isinstance(calculation, dict) else ""
        if "incompatíveis" in notes:
            reasons.append("width ou prêmios inválidos para a estrutura")
        elif notes:
            reasons.append("cálculo retornou erro")
    if not candidate.get("spread_disponivel") and candidate.get("tipo_estrutura"):
        reasons.append("spread indisponível")
    pairing = candidate.get("pairing_diagnostics", {})
    if pairing:
        if pairing.get("calls_available", 0) < 2:
            reasons.append("sem calls suficientes")
        if pairing.get("puts_available", 0) < 2:
            reasons.append("sem puts suficientes")
        if pairing.get("discarded_missing_price", 0):
            reasons.append("opções filtradas por preço ausente")
        if pairing.get("discarded_illiquid", 0):
            reasons.append("opções filtradas por liquidez")
        if pairing.get("discarded_missing_expiration", 0):
            reasons.append("opções sem vencimento")
    reasons.extend(f"campo ausente: {field}" for field in candidate.get("campos_ausentes", []) if field)
    return list(dict.fromkeys(reasons)) or ([str(candidate.get("motivo"))] if candidate.get("motivo") else ["nenhum motivo padronizado"])


def extract_rejection_reasons(opportunities: list[dict[str, Any]]) -> list[str]:
    return [reason for candidate in opportunities if candidate.get("conditional_status") in {"evitar", "inconclusivo"} for reason in _candidate_reasons(candidate)]


def count_rejection_reasons(opportunities: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(extract_rejection_reasons(opportunities)).most_common())


def what_needs_to_change(candidate: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    if candidate.get("max_debit_allowed") is not None and (candidate.get("custo_liquido") is None or candidate["custo_liquido"] > candidate["max_debit_allowed"]):
        changes.append(f"custo líquido precisa cair para até R$ {candidate['max_debit_allowed']:.2f}")
    if candidate.get("min_credit_required") is not None and (candidate.get("credito_liquido") is None or candidate["credito_liquido"] < candidate["min_credit_required"]):
        changes.append(f"crédito precisa subir para pelo menos R$ {candidate['min_credit_required']:.2f}")
    if candidate.get("healthbox_status") != "confirma":
        changes.append("Healthbox precisa confirmar a estratégia")
    if candidate.get("liquidez") in {"baixa", "ilíquida", "indisponível"}:
        changes.append("liquidez precisa melhorar")
    if not candidate.get("spread_disponivel"):
        changes.append("confirmar bid/ask no pregão e manter spread em faixa aceitável")
    if candidate.get("vencimento_dias") is None or candidate.get("vencimento_dias", 0) < 11:
        changes.append("vencimento precisa estar na faixa preferida de 11 a 45 dias")
    if candidate.get("tipo_estrutura") in {"call_debit_spread", "bull_put_spread"}:
        changes.append("ativo precisa continuar acima do suporte")
    if candidate.get("tipo_estrutura") in {"put_debit_spread", "bear_call_spread"}:
        changes.append("ativo precisa continuar abaixo da resistência")
    if candidate.get("entry_reference_price") is None:
        changes.append("preço atual das duas opções precisa estar disponível no pregão")
    if candidate.get("healthbox_status") not in {"confirma", "atenção"}:
        changes.append("Healthbox precisa deixar de contrariar ou permanecer neutro")
    if candidate.get("liquidez") in {"alta", "média", "baixa"}:
        changes.append("liquidez precisa continuar com negócios no pregão")
    return list(dict.fromkeys(changes)) or ["manter os critérios atuais e confirmar preços no pregão"]


def find_near_miss_candidates(opportunities: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    candidates = []
    for item in opportunities:
        math_complete = all(_number(item.get(field)) is not None for field in ("perda_maxima", "ganho_maximo", "break_even"))
        dte = item.get("vencimento_dias")
        if item.get("conditional_status") != "evitar" or not math_complete or not isinstance(dte, int) or not 5 <= dte <= 60:
            continue
        reasons = _candidate_reasons(item)
        changes = what_needs_to_change(item)
        candidates.append({
            **item, "motivo_principal": reasons[0], "rejection_reasons": reasons,
            "what_needs_to_change": changes, "criteria_failed": len(reasons),
        })
    return sorted(candidates, key=lambda item: (item["criteria_failed"], -(_number(item.get("score")) or -1), -(_number(item.get("risco_retorno")) or -1)))[:limit]


def summarize_real_eod_funnel(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    conditional = summarize_conditional_entries(opportunities)
    missing = Counter(field for item in opportunities for field in item.get("campos_ausentes", []) if field)
    expirations = sorted({str(item.get("vencimento")) for item in opportunities if item.get("vencimento")})
    assets = sorted({str(item.get("ativo")) for item in opportunities if item.get("ativo")})
    without_access = sorted({str(item.get("ativo")) for item in opportunities if "sem acesso" in str(item.get("motivo", "")).lower()})
    assets_with_options = sorted(set(assets) - set(without_access) - {str(item.get("ativo")) for item in opportunities if "sem snapshot" in str(item.get("motivo", "")).lower()})
    hard_counts = Counter(blocker for item in opportunities for blocker in (item.get("hard_blockers") or identify_hard_blockers(item)))
    soft_counts = Counter(warning for item in opportunities for warning in (item.get("soft_warnings") or identify_soft_warnings(item)))
    complete_math_count = sum(candidate_has_complete_math(item) for item in opportunities)
    usable_price_count = sum(candidate_has_usable_price(item) for item in opportunities)
    zero_blockers_count = sum(not (item.get("hard_blockers") or identify_hard_blockers(item)) for item in opportunities)
    soft_only_count = sum(
        not (item.get("hard_blockers") or identify_hard_blockers(item))
        and bool(item.get("soft_warnings") or identify_soft_warnings(item))
        for item in opportunities
    )
    return {
        **conditional, "rejection_reasons": count_rejection_reasons(opportunities),
        "hard_blockers": dict(hard_counts.most_common()), "soft_warnings": dict(soft_counts.most_common()),
        "complete_math_count": complete_math_count, "usable_price_count": usable_price_count,
        "zero_hard_blockers_count": zero_blockers_count, "soft_warnings_only_count": soft_only_count,
        "missing_fields": dict(missing.most_common()), "expirations_analyzed": expirations,
        "assets": assets, "assets_with_options": assets_with_options, "assets_without_access": without_access,
        "near_misses": find_near_miss_candidates(opportunities, 10),
    }
