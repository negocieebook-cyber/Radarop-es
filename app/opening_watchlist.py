"""Lista persistente de candidatas EOD para validação na abertura."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.storage import load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OPENING_WATCHLIST_PATH = PROJECT_ROOT / "data" / "runtime" / "opening_watchlist.json"
ELIGIBLE_STATUSES = {"acompanhar_na_abertura", "entrada_condicional"}
EOD_NOTICE = "Preço EOD indicativo. Validar no pregão antes de qualquer decisão."


def load_opening_watchlist() -> list[dict[str, Any]]:
    data = load_json(OPENING_WATCHLIST_PATH, [])
    return data if isinstance(data, list) else []


def save_opening_watchlist(items: list[dict[str, Any]]) -> None:
    save_json(OPENING_WATCHLIST_PATH, items)


def _candidate_id(candidate: dict[str, Any]) -> str:
    existing = candidate.get("candidate_id") or candidate.get("id")
    if existing:
        return str(existing)
    strikes = candidate.get("strikes") or [candidate.get("strike_comprado"), candidate.get("strike_vendido")]
    identity = "|".join(
        str(value or "")
        for value in (
            candidate.get("ativo"), candidate.get("estrategia"), candidate.get("tipo_estrutura"),
            candidate.get("vencimento"), strikes, candidate.get("simbolo_comprado"), candidate.get("simbolo_vendido"),
        )
    )
    return sha256(identity.encode("utf-8")).hexdigest()[:20]


def build_watchlist_item(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = _candidate_id(candidate)
    strikes = candidate.get("strikes")
    if strikes is None:
        strikes = {
            "comprado": candidate.get("strike_comprado"),
            "vendido": candidate.get("strike_vendido"),
        }
    return {
        "id": f"opening-{candidate_id}",
        "candidate_id": candidate_id,
        "ativo": candidate.get("ativo"),
        "estrategia": candidate.get("estrategia"),
        "tipo_estrutura": candidate.get("tipo_estrutura"),
        "vencimento": candidate.get("vencimento"),
        "vencimento_dias": candidate.get("vencimento_dias") or candidate.get("dias_ate_vencimento"),
        "strikes": strikes,
        "custo_eod": candidate.get("custo_liquido"),
        "credito_eod": candidate.get("credito_liquido"),
        "preco_eod_referencia": candidate.get("entry_reference_price"),
        "max_debit_allowed": candidate.get("max_debit_allowed"),
        "min_credit_required": candidate.get("min_credit_required"),
        "perda_maxima": candidate.get("perda_maxima"),
        "ganho_maximo": candidate.get("ganho_maximo"),
        "break_even": candidate.get("break_even"),
        "risk_reward": candidate.get("risco_retorno") or candidate.get("risk_reward"),
        "liquidity_status": candidate.get("liquidity_status") or candidate.get("liquidez"),
        "healthbox_status": candidate.get("healthbox_status"),
        "conditional_status": candidate.get("conditional_status"),
        "confirmation_rules": list(candidate.get("confirmation_rules") or []),
        "invalidation_rules": list(candidate.get("invalidation_rules") or []),
        "hard_blockers": list(candidate.get("hard_blockers") or []),
        "soft_warnings": list(candidate.get("soft_warnings") or []),
        "what_needs_to_change": list(candidate.get("what_needs_to_change") or []),
        "fonte": candidate.get("fonte"),
        "coleta": candidate.get("coleta"),
        "tipo_dado": candidate.get("tipo_dado") or "DADOS REAIS EOD / EXPERIMENTAL",
        "data_frequency": "EOD",
        "status": "aguardando confirmação",
        "observacao": EOD_NOTICE,
    }


def item_exists(candidate_id: str) -> bool:
    return any(str(item.get("candidate_id")) == str(candidate_id) for item in load_opening_watchlist())


def add_to_opening_watchlist(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("conditional_status") not in ELIGIBLE_STATUSES:
        return {"added": False, "item": None, "reason": "status não elegível"}
    item = build_watchlist_item(candidate)
    if item_exists(item["candidate_id"]):
        return {"added": False, "item": item, "reason": "duplicado"}
    items = load_opening_watchlist()
    items.append(item)
    save_opening_watchlist(items)
    return {"added": True, "item": item, "reason": None}


def remove_from_opening_watchlist(item_id: str) -> bool:
    items = load_opening_watchlist()
    filtered = [item for item in items if str(item.get("id")) != str(item_id)]
    if len(filtered) == len(items):
        return False
    save_opening_watchlist(filtered)
    return True


def clear_opening_watchlist() -> None:
    save_opening_watchlist([])


def mark_as_converted(item_id: str, position_id: str, converted_at: str) -> bool:
    items = load_opening_watchlist()
    changed = False
    for item in items:
        if str(item.get("id")) == str(item_id):
            item.update(
                status="entrada registrada",
                converted_to_position=True,
                position_id=position_id,
                converted_at=converted_at,
            )
            changed = True
            break
    if changed:
        save_opening_watchlist(items)
    return changed


def build_manual_position(
    item: dict[str, Any], real_entry_price: float, quantity: int, entry_at: str, note: str = ""
) -> dict[str, Any]:
    if not isinstance(real_entry_price, (int, float)) or real_entry_price <= 0:
        raise ValueError("preço real de entrada deve ser maior que zero")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValueError("quantidade deve ser um inteiro maior que zero")
    if not entry_at:
        raise ValueError("data/hora de entrada é obrigatória")
    return {
        "id": str(uuid4()),
        "origem": "opening_watchlist",
        "watchlist_item_id": item.get("id"),
        "ativo": item.get("ativo"),
        "estrategia": item.get("estrategia"),
        "tipo_estrutura": item.get("tipo_estrutura"),
        "vencimento": item.get("vencimento"),
        "vencimento_dias": item.get("vencimento_dias"),
        "strikes": item.get("strikes"),
        "preco_eod_referencia": item.get("preco_eod_referencia"),
        "preco_real_entrada": float(real_entry_price),
        "quantidade": quantity,
        "data_entrada": entry_at,
        "perda_maxima": item.get("perda_maxima"),
        "ganho_maximo": item.get("ganho_maximo"),
        "ganho_maximo_por_unidade": item.get("ganho_maximo"),
        "perda_maxima_por_unidade": item.get("perda_maxima"),
        "break_even": item.get("break_even"),
        "risk_reward": item.get("risk_reward"),
        "confirmation_rules": list(item.get("confirmation_rules") or []),
        "invalidation_rules": list(item.get("invalidation_rules") or []),
        "fonte": item.get("fonte"),
        "coleta": item.get("coleta"),
        "tipo_dado": item.get("tipo_dado") or "DADOS REAIS EOD / EXPERIMENTAL",
        "data_frequency": "EOD",
        "status": "em acompanhamento",
        "observacao": note.strip(),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "aviso": "Entrada registrada manualmente pelo usuário após conferência no pregão.",
    }


def evaluate_watchlist_item(item: dict[str, Any], market_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classifica sem presumir execução; ausência de dado nunca vira confirmação."""
    evaluated = deepcopy(item)
    blockers = evaluated.get("hard_blockers") or []
    if blockers:
        evaluated["status"] = "invalidado"
        evaluated["evaluation_reason"] = "Há hard blockers registrados na análise EOD."
        return evaluated
    if not market_snapshot:
        evaluated["status"] = evaluated.get("status") or "aguardando confirmação"
        evaluated["evaluation_reason"] = "Aguardando dados do pregão para confirmar ou invalidar."
        return evaluated
    if market_snapshot.get("status_dado") == "erro":
        evaluated["status"] = "inconclusivo"
        evaluated["evaluation_reason"] = "Snapshot de mercado com erro; nenhuma conclusão foi presumida."
        return evaluated
    price = market_snapshot.get("preco_atual")
    support = market_snapshot.get("suporte")
    resistance = market_snapshot.get("resistencia")
    structure = str(evaluated.get("tipo_estrutura") or "")
    if not isinstance(price, (int, float)):
        evaluated["status"] = "inconclusivo"
        evaluated["evaluation_reason"] = "Preço atual ausente; confirmação não pode ser avaliada."
    elif structure in {"call_debit_spread", "bull_put_spread"} and isinstance(support, (int, float)) and price < support:
        evaluated["status"] = "invalidado"
        evaluated["evaluation_reason"] = "Preço abaixo do suporte registrado no snapshot."
    elif structure in {"put_debit_spread", "bear_call_spread"} and isinstance(resistance, (int, float)) and price > resistance:
        evaluated["status"] = "invalidado"
        evaluated["evaluation_reason"] = "Preço acima da resistência registrada no snapshot."
    else:
        evaluated["status"] = "atenção"
        evaluated["evaluation_reason"] = "Snapshot disponível, mas preço e liquidez das opções ainda exigem confirmação no pregão."
    return evaluated
