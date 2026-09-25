"""Retrospectiva das candidatas da Abertura: resultado estimado no vencimento.

Avalia cada candidata cujo vencimento já passou usando o fechamento EOD do
ativo na data do vencimento (ou no último pregão anterior disponível) do
histórico gratuito do opcoes.net.br. O resultado é uma ESTIMATIVA do payoff
da estrutura por contrato; não registra execução real e não presume saída.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import streamlit as st

from app.opening_watchlist import load_opening_watchlist
from app.providers.opcoes_net_provider import fetch_asset_history
from app.storage import load_positions


RETROSPECTIVE_NOTE = (
    "Resultado estimado com o fechamento EOD do ativo no vencimento (ou no último pregão anterior disponível), "
    "via histórico do opcoes.net.br. Não registra execução, saída real ou custos."
)
INVALIDATED_NOTE = "Tese registrada como invalidada; a saída real não foi registrada no app."
HISTORY_CACHE_TTL_SECONDS = 21600
PRICE_LOOKBACK_DAYS = 10


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


@st.cache_data(ttl=HISTORY_CACHE_TTL_SECONDS, show_spinner=False)
def _cached_history(symbol: str) -> dict[str, Any]:
    return fetch_asset_history(symbol)


def price_at_expiry(symbol: str, target: date) -> tuple[float | None, str | None, str | None]:
    """Fecha no pregão do vencimento ou no último anterior disponível (até 10 dias)."""
    history = _cached_history(symbol)
    if not history.get("success"):
        return None, None, f"histórico indisponível: {history.get('error')}"
    by_date = {str(candle.get("date")): candle for candle in history.get("candles", [])}
    candle = by_date.get(target.isoformat())
    if candle is None:
        for offset in range(1, PRICE_LOOKBACK_DAYS + 1):
            candle = by_date.get((target - timedelta(days=offset)).isoformat())
            if candle is not None:
                break
    if not candle:
        return None, None, "nenhum pregão encontrado na janela do vencimento"
    close = _number(candle.get("close"))
    return close, str(candle.get("date")), None if close is not None else "fechamento ausente no candle"


def _payoff_estimates(
    structure: str,
    strikes: dict[str, float | None],
    price: float,
    entry: float | None,
) -> dict[str, Any]:
    bought = strikes.get("comprado")
    sold = strikes.get("vendido")
    missing: list[str] = []
    if structure in {"call_debit_spread", "put_debit_spread", "bull_put_spread", "bear_call_spread"}:
        if bought is None:
            missing.append("strike comprado")
        if sold is None:
            missing.append("strike vendido")
        if entry is None:
            missing.append("referência de entrada")
        if missing:
            return {"calculated": False, "pnl_per_unit": None, "missing_fields": missing}
        width = abs(sold - bought)  # type: ignore[operator]
        if structure == "call_debit_spread":
            intrinsic = min(max(price - bought, 0.0), width)  # type: ignore[type-var, operator]
            pnl = intrinsic - entry
        elif structure == "put_debit_spread":
            intrinsic = min(max(bought - price, 0.0), width)  # type: ignore[type-var, operator]
            pnl = intrinsic - entry
        elif structure == "bull_put_spread":
            loss = min(max(sold - price, 0.0), width)  # type: ignore[type-var, operator]
            pnl = entry - loss
        else:
            loss = min(max(price - sold, 0.0), width)  # type: ignore[type-var, operator]
            pnl = entry - loss
    elif structure == "long_call":
        if bought is None or entry is None:
            missing.extend(field for field, value in (("strike comprado", bought), ("referência de entrada", entry)) if value is None)
            return {"calculated": False, "pnl_per_unit": None, "missing_fields": missing}
        pnl = max(price - bought, 0.0) - entry
    elif structure == "long_put":
        if bought is None or entry is None:
            missing.extend(field for field, value in (("strike comprado", bought), ("referência de entrada", entry)) if value is None)
            return {"calculated": False, "pnl_per_unit": None, "missing_fields": missing}
        pnl = max(bought - price, 0.0) - entry
    elif structure == "covered_call":
        if sold is None or entry is None:
            missing.extend(field for field, value in (("strike vendido", sold), ("referência de entrada", entry)) if value is None)
            return {"calculated": False, "pnl_per_unit": None, "missing_fields": missing}
        pnl = entry - max(price - sold, 0.0)
    else:
        return {"calculated": False, "pnl_per_unit": None, "missing_fields": [f"estrutura não suportada: {structure or 'ausente'}"]}
    return {"calculated": True, "pnl_per_unit": round(pnl, 4), "missing_fields": []}


def evaluate_expired_item(item: dict[str, Any], positions_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    asset = str(item.get("ativo") or "").upper()
    structure = str(item.get("tipo_estrutura") or "")
    expiry = _parse_date(item.get("vencimento"))
    converted = positions_by_id.get(str(item.get("position_id"))) if item.get("position_id") else None
    if converted:
        entry = _number(converted.get("preco_real_entrada"))
        entry_source = "preço real de entrada registrado na posição"
    else:
        entry = _number(item.get("preco_eod_referencia"))
        entry_source = "referência EOD da candidata (entrada real não registrada)"
    strikes_raw = item.get("strikes") if isinstance(item.get("strikes"), dict) else {}
    strikes = {"comprado": _number(strikes_raw.get("comprado")), "vendido": _number(strikes_raw.get("vendido"))}
    record: dict[str, Any] = {
        "id": item.get("id"),
        "ativo": asset,
        "estrategia": item.get("estrategia"),
        "tipo_estrutura": structure,
        "vencimento": item.get("vencimento"),
        "strikes": strikes,
        "entrada_referencia": entry,
        "entrada_fonte": entry_source,
        "status_registrado": item.get("status"),
        "convertida": bool(converted),
        "resultado": "inconclusivo",
        "pnl_por_unidade_estimado": None,
        "pnl_total_estimado": None,
        "preco_vencimento": None,
        "data_preco_vencimento": None,
        "ganho_maximo": _number(item.get("ganho_maximo")),
        "perda_maxima": _number(item.get("perda_maxima")),
        "break_even": _number(item.get("break_even")),
        "observacao": RETROSPECTIVE_NOTE,
        "tipo_dado": "DADOS REAIS EOD / ESTIMATIVA",
        "fonte": "opcoes_net_br (histórico)",
        "coleta": _now(),
        "error": None,
    }
    if not asset:
        record["error"] = "ativo ausente na candidata"
        return record
    if item.get("status") == "invalidado" and not converted:
        record["resultado"] = "inconclusivo"
        record["observacao"] = f"{INVALIDATED_NOTE} {RETROSPECTIVE_NOTE}"
        return record
    if expiry is None:
        record["error"] = "vencimento ausente ou inválido"
        return record
    price, price_date, price_error = price_at_expiry(asset, expiry)
    record["preco_vencimento"] = price
    record["data_preco_vencimento"] = price_date
    if price is None:
        record["error"] = price_error or "preço do vencimento indisponível"
        return record
    estimate = _payoff_estimates(structure, strikes, price, entry)
    if not estimate["calculated"]:
        record["error"] = "estimativa indisponível: " + ", ".join(estimate["missing_fields"])
        return record
    pnl = estimate["pnl_per_unit"]
    quantity = _number(converted.get("quantidade")) if converted else None
    record["pnl_por_unidade_estimado"] = pnl
    record["pnl_total_estimado"] = round(pnl * quantity, 2) if quantity is not None else None
    tolerance = 0.0001
    if pnl > tolerance:
        record["resultado"] = "ganho estimado"
    elif pnl < -tolerance:
        record["resultado"] = "perda estimada"
    else:
        record["resultado"] = "zerado"
    return record


def summarize_retrospective(items: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [item for item in items if item.get("pnl_por_unidade_estimado") is not None]
    by_strategy: dict[str, dict[str, Any]] = {}
    for item in scored:
        strategy = str(item.get("tipo_estrutura") or "indisponível")
        bucket = by_strategy.setdefault(strategy, {"n": 0, "ganhos": 0, "perdas": 0, "zerados": 0, "soma_pnl_estimado": 0.0})
        bucket["n"] += 1
        pnl = float(item["pnl_por_unidade_estimado"])
        bucket["soma_pnl_estimado"] += pnl
        if item.get("resultado") == "ganho estimado":
            bucket["ganhos"] += 1
        elif item.get("resultado") == "perda estimada":
            bucket["perdas"] += 1
        else:
            bucket["zerados"] += 1
    for bucket in by_strategy.values():
        bucket["taxa_ganho"] = round(bucket["ganhos"] / bucket["n"], 4) if bucket["n"] else None
        bucket["soma_pnl_estimado"] = round(bucket["soma_pnl_estimado"], 4)
    return {
        "vencidas": len(items),
        "avaliadas": len(scored),
        "inconclusivas": len(items) - len(scored),
        "ganhos": sum(1 for item in scored if item.get("resultado") == "ganho estimado"),
        "perdas": sum(1 for item in scored if item.get("resultado") == "perda estimada"),
        "zerados": sum(1 for item in scored if item.get("resultado") == "zerado"),
        "por_estrategia": by_strategy,
    }


def build_retrospective() -> dict[str, Any]:
    items = load_opening_watchlist()
    positions_by_id = {str(position.get("id")): position for position in load_positions()}
    today = date.today()
    expired: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    for item in items:
        expiry = _parse_date(item.get("vencimento"))
        if expiry is None or expiry > today:
            active.append({
                "id": item.get("id"),
                "ativo": item.get("ativo"),
                "estrategia": item.get("estrategia"),
                "tipo_estrutura": item.get("tipo_estrutura"),
                "vencimento": item.get("vencimento"),
                "status": item.get("status"),
                "convertida": bool(item.get("converted_to_position")),
                "observacao": "Vencimento futuro ou ausente; aguarda avaliação.",
            })
        else:
            expired.append(evaluate_expired_item(item, positions_by_id))
    summary = summarize_retrospective(expired)
    return {
        "generated_at": _now(),
        "expired": expired,
        "active": active,
        "summary": summary,
        "tipo_dado": "DADOS REAIS EOD / ESTIMATIVA",
        "fonte": "opcoes_net_br (histórico)",
        "data_frequency": "EOD",
        "observacao": RETROSPECTIVE_NOTE,
    }
