"""Auditoria do provider opcoes.net.br com dados sintéticos (sem rede)."""

from __future__ import annotations

from app.providers.opcoes_net_provider import (
    liquidity_from_trades,
    normalize_history_response,
    normalize_options_chain_payload,
    side_from_series_id,
)

CALL_ROW = ["J21", 0, "E", 49.36, "O", -0.002, 2.15, 0.01, "24/09/2026", 214, 92900.0, 3, 1, 0, 2, 500, 300, 0.4104, 0.5516, 0.02, -0.03, -0.01, 0.8]
PUT_ROW = ["V21", 0, "E", 49.36, "I", 0.002, 1.83, -0.01, "24/09/2026", 279, 102000.0, 4, 2, 0, 1, 480, 320, 0.4237, -0.4503, 0.021, -0.028, -0.012, 0.82]
NO_QUOTE_ROW = ["I291W4", 0, "E", 27.92, "I", -0.4332, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

UNDERLYING_ASSET = {
    "t": "PETR4", "id": "PETR4", "p": 49.26, "c": -0.0068, "h": "24/09/2026",
    "ab": 49.7, "mi": 49.17, "ma": 50.24, "yp": 49.26, "i": 0.42,
}


def _payload() -> dict:
    return {
        "requests": [
            {
                "type": "OptionsChain",
                "results": {
                    "columns": None,
                    "open_interest_date": "2026-09-24",
                    "underlying_asset": UNDERLYING_ASSET,
                    "expirations": [
                        {"dt": "2026-10-16", "du": 21, "w": False, "m": True, "dc": 1, "calls": [CALL_ROW, NO_QUOTE_ROW], "puts": [PUT_ROW]},
                    ],
                },
            }
        ]
    }


def test_side_from_series_id() -> None:
    assert side_from_series_id("J21") == "call"
    assert side_from_series_id("V21") == "put"
    assert side_from_series_id("A500") == "call"
    assert side_from_series_id("X99") == "put"
    assert side_from_series_id("") is None


def test_liquidity_from_trades() -> None:
    assert liquidity_from_trades(600) == "alta"
    assert liquidity_from_trades(150) == "média"
    assert liquidity_from_trades(30) == "baixa"
    assert liquidity_from_trades(0) == "ilíquida"
    assert liquidity_from_trades(None) == "indisponível"


def test_normalize_chain_payload_maps_fields() -> None:
    result = normalize_options_chain_payload(_payload(), "PETR4")
    assert result["success"] is True
    assert result["source"] == "opcoes_net_br"
    assert result["series_count"] == 3
    assert result["calls_count"] == 2
    assert result["puts_count"] == 1
    assert result["quoted_count"] == 2
    assert result["underlying_price"] == 49.26
    assert result["open_interest_date"] == "2026-09-24"
    assert result["expirations"][0]["expiration_date"] == "2026-10-16"
    assert result["expirations"][0]["dte"] == 21
    call = result["series"][0]
    unquoted = result["series"][1]
    put = result["series"][2]
    assert call["symbol"] == "PETR4J21_2026"
    assert call["side"] == "call"
    assert call["strike"] == 49.36
    assert call["expiration_date"] == "2026-10-16"
    assert call["last"] == 2.15
    assert call["close"] == 2.15
    assert call["normalized_price"] == 2.15
    assert call["normalized_price_basis"] == "last_session"
    assert call["price_value_status"] == "válido"
    assert call["liquidity_status"] == "média"
    assert call["moneyness"] == "OTM"
    assert call["holder_oi"] == 500
    assert call["writer_oi"] == 300
    assert call["iv"] == 0.4104
    assert call["delta"] == 0.5516
    assert call["quote_date"] == "24/09/2026"
    assert call["date"] == "24/09/2026"
    assert put["side"] == "put"
    assert put["moneyness"] == "ITM"
    assert unquoted["last"] is None
    assert unquoted["price_value_status"] == "ausente"
    assert unquoted["status_dado"] == "sem cotação na última sessão"
    assert "close" not in call["campos_ausentes"]
    assert "date" in unquoted["campos_ausentes"]
    assert "close" in unquoted["campos_ausentes"]
    assert "trades" in unquoted["campos_ausentes"]
    assert "bid" in call["campos_ausentes"]


def test_normalize_history_response() -> None:
    payload = {
        "requests": [
            {
                "type": "QuotesHistoryByAsset",
                "results": {
                    "PETR4": {
                        "data_fields": ["date", "open", "high", "low", "close", "change", "volume", "vol_impl"],
                        "data_rows": [
                            ["2026-09-23", 49.1, 49.9, 48.9, 49.5, 0.004, 900000000.0, 0.41],
                            ["2026-09-24", 49.7, 50.24, 49.17, 49.26, -0.0068, 1723155166.0, 0.4197],
                        ],
                    }
                },
            }
        ]
    }
    result = normalize_history_response(payload, "PETR4")
    assert result["success"] is True
    assert result["count"] == 2
    assert result["last_date"] == "2026-09-24"
    assert result["candles"][1]["close"] == 49.26
    assert result["candles"][1]["volume"] == 1723155166.0
    assert result["candles"][1]["vol_impl"] == 0.4197
    assert "log_change" not in result["candles"][1]
