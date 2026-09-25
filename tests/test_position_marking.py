"""Auditoria da marcação de posições com cadeia sintética (sem rede)."""

from __future__ import annotations

import pytest

from app.position_marking import mark_position
from app.position_monitor import calculate_position_pnl


def _series(symbol: str, side: str, strike: float, last: float | None, trades: int | None, expiration: str = "2026-10-16") -> dict:
    return {
        "symbol": symbol, "side": side, "strike": strike, "expiration_date": expiration,
        "last": last, "close": last, "normalized_price": last, "normalized_price_basis": "last_session" if last is not None else "indisponível",
        "trades": trades, "liquidity_status": "média" if trades and trades >= 100 else "baixa",
        "fonte": "opcoes_net_br", "quote_date": "24/09/2026",
    }


def _chain(series: list[dict]) -> dict:
    return {
        "success": True, "fonte": "opcoes_net_br", "coleta": "2026-09-25T00:00:00+00:00",
        "series": series,
        "expirations": [{"expiration_date": "2026-10-16", "dte": 21}, {"expiration_date": "2026-10-23", "dte": 28}],
        "status_dado": "atualizado",
    }


DEBIT_POSITION = {
    "id": "p1", "origem": "opening_watchlist", "ativo": "PETR4", "tipo_estrutura": "call_debit_spread",
    "vencimento": "2026-10-16", "strikes": {"comprado": 48.86, "vendido": 49.36},
    "preco_real_entrada": 0.25, "quantidade": 1, "perda_maxima": 0.25, "ganho_maximo": 4.75,
    "ganho_maximo_por_unidade": 4.75, "data_frequency": "EOD",
}

CREDIT_POSITION = {
    "id": "p2", "origem": "opening_watchlist", "ativo": "PETR4", "tipo_estrutura": "bull_put_spread",
    "vencimento": "2026-10-16", "strikes": {"vendido": 48.86, "comprado": 48.36},
    "preco_real_entrada": 0.21, "quantidade": 2, "perda_maxima": 0.5, "ganho_maximo": 0.21,
    "ganho_maximo_por_unidade": 0.21, "data_frequency": "EOD",
}


def test_mark_debit_structure() -> None:
    chain = _chain([
        _series("PETR4J500_2026", "call", 48.86, 2.40, 392),
        _series("PETR4J21_2026", "call", 49.36, 2.15, 214),
    ])
    mark = mark_position(DEBIT_POSITION, chain)
    assert mark["calculated"] is True
    assert mark["current_mark"] == pytest.approx(0.25)
    assert mark["pnl_per_unit"] == pytest.approx(0.0)
    assert mark["expiration_used"] == "2026-10-16"
    assert mark["vencimento_exato"] is True
    assert len(mark["legs"]) == 2
    assert mark["legs"][0]["funcao"] == "buy"
    assert mark["legs"][1]["funcao"] == "sell"


def test_mark_credit_structure_inverts_sign() -> None:
    chain = _chain([
        _series("PETR4V500_2026", "put", 48.86, 1.60, 280),
        _series("PETR4V494_2026", "put", 48.36, 1.39, 231),
    ])
    mark = mark_position(CREDIT_POSITION, chain)
    assert mark["calculated"] is True
    assert mark["current_mark"] == pytest.approx(0.21)
    assert mark["pnl_per_unit"] == pytest.approx(0.0)
    assert mark["pnl_total"] == pytest.approx(0.0)
    assert mark["legs"][0]["funcao"] == "sell"
    assert mark["legs"][1]["funcao"] == "buy"


def test_pnl_monitor_respects_credit_entry() -> None:
    result = calculate_position_pnl(CREDIT_POSITION, 0.30)
    assert result["calculated"] is True
    assert result["pnl_per_unit"] == pytest.approx(-0.09)
    debit = calculate_position_pnl(DEBIT_POSITION, 0.30)
    assert debit["pnl_per_unit"] == pytest.approx(0.05)


def test_mark_missing_leg_is_honest() -> None:
    chain = _chain([
        _series("PETR4J500_2026", "call", 48.86, 2.40, 392),
        _series("PETR4J21_2026", "call", 49.36, None, 214),
    ])
    mark = mark_position(DEBIT_POSITION, chain)
    assert mark["calculated"] is False
    assert mark["current_mark"] is None
    assert "sem cotação" in mark["error"]
    assert len(mark["missing_legs"]) == 1


def test_mark_falls_back_to_nearest_expiration() -> None:
    position = {**DEBIT_POSITION, "vencimento": None}
    chain = _chain([
        _series("PETR4J500_2026", "call", 48.86, 2.40, 392, expiration="2026-10-23"),
        _series("PETR4J21_2026", "call", 49.36, 2.15, 214, expiration="2026-10-23"),
    ])
    mark = mark_position(position, chain)
    assert mark["calculated"] is True
    assert mark["expiration_used"] == "2026-10-23"
    assert mark["vencimento_exato"] is False


def test_mark_unknown_strategy_and_empty_chain() -> None:
    assert mark_position({**DEBIT_POSITION, "tipo_estrutura": "iron_condor"}, _chain([]))["calculated"] is False
    assert mark_position(DEBIT_POSITION, {"success": False})["calculated"] is False
