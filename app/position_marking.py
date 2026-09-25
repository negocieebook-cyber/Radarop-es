"""Marcação de posições com preços reais de opções da última sessão.

A marcação usa a grade pública do opcoes.net.br (sem autenticação). O preço
de cada perna é o último preço da última sessão gravada no banco do site
(dateLastQuotesInfo informa a data). Isso é marcação EOD, não cotação
intraday; o painel informa isso em todos os rótulos.

Convenção de sinal:
- estruturas de débito (call/put debit spread, long call/put): a marcação é o
  valor atual da estrutura comprada; P/L = marcação - entrada.
- estruturas de crédito (bull put, bear call, covered call): a marcação é o
  custo para fechar hoje; P/L = entrada (crédito recebido) - marcação.

O pareamento das pernas é feito por (lado, strike, vencimento) na cadeia
coletada, não pelo nome da série, para tolerar ajustes de provento.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import streamlit as st

from app.options_math import CALCULATORS
from app.position_monitor import CREDIT_ENTRY_STRATEGIES
from app.providers.opcoes_net_provider import fetch_options_chain

DEBIT_ENTRY_STRATEGIES = {"call_debit_spread", "put_debit_spread", "long_call", "long_put"}
MARK_BASIS_NOTE = "Marcação pelo último preço da última sessão (EOD), via opcoes.net.br. Não é cotação intraday."
SUPPORTED_MARKING_STRATEGIES = {
    "call_debit_spread", "put_debit_spread", "bull_put_spread", "bear_call_spread", "covered_call", "long_call", "long_put",
}
STRIKE_TOLERANCE = 0.005

LEG_RULES: dict[str, list[tuple[str, str, str]]] = {
    "call_debit_spread": [("comprado", "call", "buy"), ("vendido", "call", "sell")],
    "put_debit_spread": [("comprado", "put", "buy"), ("vendido", "put", "sell")],
    "bull_put_spread": [("vendido", "put", "sell"), ("comprado", "put", "buy")],
    "bear_call_spread": [("vendido", "call", "sell"), ("comprado", "call", "buy")],
    "covered_call": [("vendido", "call", "sell")],
    "long_call": [("comprado", "call", "buy")],
    "long_put": [("comprado", "put", "buy")],
}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def position_strikes(position: dict[str, Any]) -> dict[str, float | None]:
    strikes = position.get("strikes") if isinstance(position.get("strikes"), dict) else {}
    return {
        "comprado": _number(strikes.get("comprado")) or _number(position.get("strike_comprado")),
        "vendido": _number(strikes.get("vendido")) or _number(position.get("strike_vendido")),
    }


def resolve_expiration(position: dict[str, Any], chain: dict[str, Any]) -> tuple[str | None, bool]:
    """Devolve (vencimento usado, vencimento exato?). Sem vencimento registrado,
    usa o vencimento futuro mais próximo que tenha séries na cadeia."""
    registered = str(position.get("vencimento") or "").strip()
    if registered:
        return registered, True
    series_dates = {str(item.get("expiration_date")) for item in chain.get("series") or []}
    candidates: list[date] = []
    for item in chain.get("expirations") or []:
        try:
            parsed = date.fromisoformat(str(item.get("expiration_date")))
        except (TypeError, ValueError):
            continue
        if parsed >= date.today():
            candidates.append(parsed)
    if not candidates:
        return None, False
    with_series = [parsed for parsed in candidates if parsed.isoformat() in series_dates]
    target = min(with_series) if with_series else min(candidates)
    return target.isoformat(), False


def find_quote(series: list[dict[str, Any]], side: str, strike: float, expiration: str) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_trades = -1.0
    for item in series:
        if item.get("side") != side or item.get("expiration_date") != expiration:
            continue
        item_strike = _number(item.get("strike"))
        if item_strike is None or abs(item_strike - strike) > STRIKE_TOLERANCE:
            continue
        if _number(item.get("last")) is None:
            continue
        trades = _number(item.get("trades")) or 0.0
        if trades > best_trades:
            best, best_trades = item, trades
    return best


def _not_calculated(reason: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "calculated": False, "current_mark": None, "legs": [], "missing_legs": [],
        "mark_basis": MARK_BASIS_NOTE, "observacao": MARK_BASIS_NOTE, "error": reason, **(details or {}),
    }


def mark_position(position: dict[str, Any], chain: dict[str, Any]) -> dict[str, Any]:
    """Calcula o valor atual da estrutura por contrato com os preços da cadeia."""
    strategy = str(position.get("tipo_estrutura") or "")
    if strategy not in SUPPORTED_MARKING_STRATEGIES:
        return _not_calculated("estratégia não reconhecida para marcação", {"strategy": strategy})
    if not chain or not chain.get("success"):
        return _not_calculated("cadeia de opções indisponível", {"fonte": (chain or {}).get("fonte"), "error": (chain or {}).get("error")})
    expiration, exact = resolve_expiration(position, chain)
    if not expiration:
        return _not_calculated("vencimento da posição não encontrado na cadeia", {"vencimento_registrado": position.get("vencimento")})
    strikes = position_strikes(position)
    legs: list[dict[str, Any]] = []
    missing: list[str] = []
    for label, side, role in LEG_RULES[strategy]:
        strike = strikes.get(label)
        if strike is None:
            missing.append(f"strike {label} ausente na posição")
            continue
        quote = find_quote(chain.get("series") or [], side, strike, expiration)
        if quote is None:
            missing.append(f"{side} strike {strike} sem cotação no vencimento {expiration}")
            continue
        legs.append({
            "papel": label, "lado": side, "funcao": role, "strike": strike,
            "simbolo": quote.get("symbol"), "premio_ultima_sessao": _number(quote.get("last")),
            "negocios": quote.get("trades"), "volume_financeiro": quote.get("financial_volume"),
            "quote_date": quote.get("quote_date"), "iv": quote.get("iv"), "delta": quote.get("delta"),
            "liquidez": quote.get("liquidity_status"),
        })
    if missing or not legs:
        return _not_calculated("pernas sem cotação na cadeia atual", {"missing_legs": missing, "expiration_used": expiration, "vencimento_exato": exact})
    is_credit = strategy in CREDIT_ENTRY_STRATEGIES
    if is_credit:
        current_mark = sum(leg["premio_ultima_sessao"] for leg in legs if leg["funcao"] == "sell") - sum(
            leg["premio_ultima_sessao"] for leg in legs if leg["funcao"] == "buy"
        )
    else:
        current_mark = sum(leg["premio_ultima_sessao"] for leg in legs if leg["funcao"] == "buy") - sum(
            leg["premio_ultima_sessao"] for leg in legs if leg["funcao"] == "sell"
        )
    if current_mark is None or current_mark < 0:
        current_mark = max(current_mark or 0.0, 0.0)
    entry = _number(position.get("preco_real_entrada"))
    if entry is None:
        return _not_calculated("preço real de entrada ausente na posição", {"legs": legs, "expiration_used": expiration})
    pnl_per_unit = round(entry - current_mark, 4) if is_credit else round(current_mark - entry, 4)
    quantity = _number(position.get("quantidade"))
    return {
        "calculated": True,
        "current_mark": round(current_mark, 4),
        "pnl_per_unit": pnl_per_unit,
        "pnl_total": round(pnl_per_unit * quantity, 2) if quantity is not None else None,
        "pnl_percent": round((pnl_per_unit / entry) * 100, 2) if entry else None,
        "entrada_sinalizada_como": "crédito recebido" if is_credit else "débito pago",
        "legs": legs,
        "missing_legs": [],
        "expiration_used": expiration,
        "vencimento_exato": exact,
        "mark_basis": "última sessão (EOD)",
        "quote_dates": sorted({str(leg.get("quote_date")) for leg in legs if leg.get("quote_date")}),
        "fonte": chain.get("fonte") or "opcoes_net_br",
        "tipo_dado": "DADOS REAIS EOD / MARCAÇÃO",
        "coleta": chain.get("coleta"),
        "observacao": MARK_BASIS_NOTE,
        "error": None,
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_marking_chain(underlying: str) -> dict[str, Any]:
    return fetch_options_chain(str(underlying).upper(), load=500)


def build_option_mark(position: dict[str, Any]) -> dict[str, Any]:
    underlying = str(position.get("ativo") or "").upper()
    if not underlying:
        return _not_calculated("ativo ausente na posição")
    try:
        chain = load_marking_chain(underlying)
    except Exception as error:  # noqa: BLE001 - falha de rede não pode derrubar a página
        return _not_calculated(f"falha ao consultar cadeia: {type(error).__name__}")
    return mark_position(position, chain)


def build_option_mark_context(position: dict[str, Any]) -> dict[str, Any]:
    """Contexto extra para o position_monitor: option_mark + current_mark."""
    mark = build_option_mark(position)
    return {
        "option_mark": mark,
        "current_mark": mark.get("current_mark") if mark.get("calculated") else None,
        "option_mark_info": {
            "mark_basis": mark.get("mark_basis"),
            "expiration_used": mark.get("expiration_used"),
            "legs": mark.get("legs"),
            "quote_dates": mark.get("quote_dates"),
            "fonte": mark.get("fonte"),
            "coleta": mark.get("coleta"),
            "observacao": mark.get("observacao"),
        },
    }


def nearest_expiration_hint(chain: dict[str, Any], days_ahead: int = 1) -> str | None:
    for item in chain.get("expirations") or []:
        try:
            parsed = date.fromisoformat(str(item.get("expiration_date")))
        except (TypeError, ValueError):
            continue
        if parsed >= date.today() + timedelta(days=days_ahead):
            return parsed.isoformat()
    return None


def strategy_legs(strategy: str) -> list[tuple[str, str, str]] | None:
    return LEG_RULES.get(str(strategy or ""))


def calculators_supported(strategy: str) -> bool:
    return str(strategy or "") in CALCULATORS
