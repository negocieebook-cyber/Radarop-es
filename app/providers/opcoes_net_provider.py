"""Provider público de cadeias de opções do opcoes.net.br, sem chave de API.

O próprio site alimenta sua grade de opções por um endpoint aberto:

    GET /api/v1?z={unix_ts // 10}&r0t=OptionsChain&r0p.underlying_asset_id=PETR4
                &r0p.skip=0&r0p.load=500&r0p.columns_info=false&r0p.underlying_quotes=true

Cada linha de série tem 23 posições, na ordem:

    0  identificador da série (letra do mês + strike original + código de ajuste)
    1  formador de mercado          2  estilo (A/E)         3  strike atual
    4  ATM/ITM/OTM                  5  distância % do strike 6  último preço
    7  variação %                   8  data/hora da cotação  9  nº de negócios
   10  volume financeiro           11  IQ                   12  coberto
   13  travado                     14  descoberto           15  titular (OI)
   16  lançador (OI)               17  vol. implícita (%)    18  delta
   19  gamma                       20  theta ($)            21  theta (%)
   22  vega

O identificador da série segue o padrão B3: letra do mês (A-L calls, M-X puts)
+ strike original x 100 + código de ajuste (W1..W9). O ticker completo é
root + sufixo (ex.: PETR + I296W4). O strike efetivo vem da coluna 3, que já
está ajustado por proventos; nunca é deduzido do ticker.

Cotações do endpoint são da última sessão gravada no banco do site
(LastQuotesInfo informa dateLastQuotesInDB e hasTodaysQuotesInDB).
"""

from __future__ import annotations

import re
import time
from datetime import date, datetime, timezone
from typing import Any

import requests

API_URL = "https://opcoes.net.br/api/v1"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
FREQUENCY_NOTE = "Cotações da última sessão gravada no banco do site. Não é tempo real."
MONTH_CALL_LETTERS = "ABCDEFGHIJKL"
MONTH_PUT_LETTERS = "MNOPQRSTUVWX"
SERIES_PATTERN = re.compile(r"^([A-X])(\d+)(W\d)?$")
COLUMN_NAMES = (
    "series_id", "market_maker", "style", "strike", "moneyness_raw", "distance_to_strike_pct",
    "last", "change_pct", "quote_date", "trades", "financial_volume", "iq",
    "covered_oi", "blocked_oi", "uncovered_oi", "holder_oi", "writer_oi",
    "iv", "delta", "gamma", "theta", "theta_pct", "vega",
)
# Campos esperados no formato normalizado usado pelo restante do app (mesma
# lista do provider brapi) para o relatório honesto de campos ausentes.
EXPECTED_SERIES_FIELDS = (
    "symbol", "underlying_symbol", "side", "market", "strike", "expiration_date",
    "first_trade_date", "last_trade_date", "date", "open", "high", "low", "average",
    "close", "bid", "ask", "trades", "volume", "financial_volume",
)
MONEYNESS_LETTERS = {"I": "ITM", "O": "OTM", "A": "ATM"}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def liquidity_from_trades(trades: Any) -> str:
    count = _int_or_none(trades)
    if count is None:
        return "indisponível"
    if count >= 500:
        return "alta"
    if count >= 100:
        return "média"
    if count >= 20:
        return "baixa"
    return "ilíquida"


def side_from_series_id(series_id: str) -> str | None:
    letter = str(series_id or "")[:1].upper()
    if not letter:
        return None
    if letter in MONTH_CALL_LETTERS:
        return "call"
    if letter in MONTH_PUT_LETTERS:
        return "put"
    return None


def month_letter_from_date(expiration: str | None) -> str | None:
    try:
        month = date.fromisoformat(str(expiration)).month
    except (TypeError, ValueError):
        return None
    return MONTH_CALL_LETTERS[month - 1]


def _api_get(requests_payload: list[dict[str, Any]], timeout: int = 25) -> dict[str, Any]:
    parts = [f"z={int(time.time() // 10)}"]
    for index, request in enumerate(requests_payload):
        parts.append(f"r{index}t={request['type']}")
        for key, value in sorted((request.get("params") or {}).items()):
            if value is None:
                continue
            parts.append(f"r{index}p.{key}={value}")
    try:
        response = requests.get(f"{API_URL}?{'&'.join(parts)}", headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=timeout)
        if response.status_code != 200:
            return {"success": False, "error": f"opcoes.net.br retornou HTTP {response.status_code}", "status_code": response.status_code, "data": None}
        return {"success": True, "payload": response.json(), "error": None}
    except requests.Timeout:
        return {"success": False, "error": "timeout ao consultar opcoes.net.br", "data": None}
    except (requests.RequestException, ValueError):
        return {"success": False, "error": "erro de conexão ou resposta inválida do opcoes.net.br", "data": None}


def fetch_last_quotes_info(timeout: int = 25) -> dict[str, Any]:
    collected_at = datetime.now(timezone.utc).isoformat()
    response = _api_get([{"type": "LastQuotesInfo"}], timeout=timeout)
    if not response.get("success"):
        return {
            "success": False, "fonte": "opcoes_net_br", "tipo_dado": "indisponível",
            "status_dado": "erro", "coleta": collected_at, "error": response.get("error"), "observacao": FREQUENCY_NOTE,
        }
    result = next(
        (item.get("results") for item in response["payload"].get("requests", []) if item.get("type") == "LastQuotesInfo"),
        {},
    )
    return {
        "success": True, "fonte": "opcoes_net_br", "tipo_dado": "coletado", "status_dado": "atualizado",
        "coleta": collected_at, "date_last_quotes_in_db": result.get("dateLastQuotesInDB"),
        "has_todays_quotes": bool(result.get("hasTodaysQuotesInDB")), "observacao": FREQUENCY_NOTE, "error": None,
    }


def _series_from_row(row: list[Any], underlying: str, expiration: str | None) -> dict[str, Any]:
    values = dict(zip(COLUMN_NAMES, row))
    series_id = str(values.get("series_id") or "").strip().upper()
    side = side_from_series_id(series_id)
    strike = _number(values.get("strike"))
    last = _number(values.get("last"))
    trades = _int_or_none(values.get("trades"))
    quote_date = values.get("quote_date")
    year = str(expiration or "")[:4] or ""
    ticker = f"{underlying}{series_id}" if series_id else None
    if ticker and year:
        ticker = f"{ticker}_{year}"
    iv = _number(values.get("iv"))
    moneyness = MONEYNESS_LETTERS.get(str(values.get("moneyness_raw") or "").strip().upper(), "indisponível")
    normalized: dict[str, Any] = {
        "symbol": ticker,
        "series_id": series_id or None,
        "underlying_symbol": underlying,
        "side": side,
        "market": "BOVESPA",
        "style": values.get("style") or None,
        "market_maker": bool(values.get("market_maker")) if values.get("market_maker") not in (None, "") else None,
        "strike": strike,
        "expiration_date": expiration,
        "quote_date": quote_date,
        "date": quote_date,
        "last": last,
        "close": last,
        "change_pct": _number(values.get("change_pct")),
        "trades": trades,
        "volume": None,
        "contracts_quantity": _int_or_none(values.get("iq")),
        "financial_volume": _number(values.get("financial_volume")),
        "holder_oi": _int_or_none(values.get("holder_oi")),
        "writer_oi": _int_or_none(values.get("writer_oi")),
        "covered_oi": _int_or_none(values.get("covered_oi")),
        "blocked_oi": _int_or_none(values.get("blocked_oi")),
        "uncovered_oi": _int_or_none(values.get("uncovered_oi")),
        "iv": round(iv, 4) if iv is not None else None,
        "delta": _number(values.get("delta")),
        "gamma": _number(values.get("gamma")),
        "theta": _number(values.get("theta")),
        "theta_pct": _number(values.get("theta_pct")),
        "vega": _number(values.get("vega")),
        "moneyness": moneyness,
        "moneyness_raw": values.get("moneyness_raw"),
        "distance_to_strike_pct": _number(values.get("distance_to_strike_pct")),
        "liquidity_status": liquidity_from_trades(trades),
        "normalized_price": last,
        "normalized_price_basis": "last_session" if last is not None else "indisponível",
        "normalized_price_source": "ultimo_pregao" if last is not None else None,
        "price_value_status": "ausente" if last is None else "zerado" if last == 0 else "válido",
        "fonte": "opcoes_net_br",
        "tipo_dado": "coletado",
        "status_dado": "atualizado" if last is not None else "sem cotação na última sessão",
        "observacao": FREQUENCY_NOTE,
    }
    normalized["campos_ausentes"] = [field for field in EXPECTED_SERIES_FIELDS if normalized.get(field) is None]
    return normalized


def _underlying_info(results: dict[str, Any]) -> dict[str, Any]:
    asset = results.get("underlying_asset") if isinstance(results.get("underlying_asset"), dict) else {}
    price = _number(asset.get("p"))
    return {
        "underlying_price": price,
        "underlying_price_status": "ausente" if price is None else "válido" if price > 0 else "zerado",
        "underlying_quote_date": asset.get("h"),
        "underlying_day_change_pct": _number(asset.get("c")),
        "underlying_open": _number(asset.get("ab")),
        "underlying_day_low": _number(asset.get("mi")),
        "underlying_day_high": _number(asset.get("ma")),
        "underlying_previous_close": _number(asset.get("yp")),
        "underlying_iv": _number(asset.get("i")),
        "open_interest_date": results.get("open_interest_date"),
    }


def normalize_options_chain_payload(payload: dict[str, Any], underlying: str) -> dict[str, Any]:
    results = next(
        (item.get("results") for item in payload.get("requests", []) if item.get("type") == "OptionsChain"),
        None,
    )
    if not isinstance(results, dict):
        return {"success": False, "underlying": underlying, "error": "resposta de cadeia indisponível", "series": [], "expirations": [], "fonte": "opcoes_net_br", "tipo_dado": "indisponível", "status_dado": "erro", "coleta": datetime.now(timezone.utc).isoformat()}
    today = datetime.now(timezone.utc).date()
    expirations: list[dict[str, Any]] = []
    all_series: list[dict[str, Any]] = []
    for entry in results.get("expirations", []) or []:
        if not isinstance(entry, dict):
            continue
        expiration = entry.get("dt")
        try:
            dte = (date.fromisoformat(str(expiration)) - today).days
        except (TypeError, ValueError):
            dte = _int_or_none(entry.get("du"))
        calls = entry.get("calls") or []
        puts = entry.get("puts") or []
        expirations.append({
            "expiration_date": expiration, "dte": dte, "weekly": not entry.get("m"),
            "calls_count": len(calls), "puts_count": len(puts), "series_count": len(calls) + len(puts),
        })
        for row in calls:
            all_series.append(_series_from_row(row, underlying, expiration))
        for row in puts:
            all_series.append(_series_from_row(row, underlying, expiration))
    quoted = sum(1 for item in all_series if item.get("last") is not None)
    collected_at = datetime.now(timezone.utc).isoformat()
    return {
        "success": bool(all_series),
        "underlying": underlying,
        **_underlying_info(results),
        "expirations": expirations,
        "series": all_series,
        "series_count": len(all_series),
        "calls_count": sum(item.get("side") == "call" for item in all_series),
        "puts_count": sum(item.get("side") == "put" for item in all_series),
        "quoted_count": quoted,
        "source": "opcoes_net_br",
        "fonte": "opcoes_net_br",
        "tipo_dado": "coletado" if all_series else "indisponível",
        "status_dado": "atualizado" if quoted else ("sem cotação na última sessão" if all_series else "indisponível"),
        "access_status": "disponível" if all_series else "indisponível",
        "data_frequency": "EOD",
        "coleta": collected_at,
        "error": None if all_series else "nenhuma série disponível",
        "observacao": FREQUENCY_NOTE,
    }


def fetch_options_chain(underlying: str, load: int = 500, timeout: int = 25) -> dict[str, Any]:
    symbol = str(underlying).strip().upper()
    if not symbol:
        return {"success": False, "underlying": symbol, "error": "ativo não informado", "series": [], "expirations": [], "fonte": "opcoes_net_br", "tipo_dado": "indisponível", "status_dado": "erro"}
    response = _api_get([{
        "type": "OptionsChain",
        "params": {"underlying_asset_id": symbol, "skip": 0, "load": load, "columns_info": "false", "underlying_quotes": "true"},
    }], timeout=timeout)
    if not response.get("success"):
        return {"success": False, "underlying": symbol, "error": response.get("error"), "series": [], "expirations": [], "fonte": "opcoes_net_br", "tipo_dado": "indisponível", "status_dado": "erro", "coleta": datetime.now(timezone.utc).isoformat(), "observacao": FREQUENCY_NOTE}
    return normalize_options_chain_payload(response["payload"], symbol)


HISTORY_NOTE = "Histórico diário do opcoes.net.br (dados B3). Fechamentos após o fim do pregão."
HISTORY_FIELDS = ("open", "high", "low", "close", "change", "log_change", "volume", "vol_ewma", "vol_impl", "vol_impl_calls", "vol_impl_puts")


def normalize_history_response(payload: dict[str, Any], symbol: str) -> dict[str, Any]:
    results = next(
        (item.get("results") for item in payload.get("requests", []) if item.get("type") == "QuotesHistoryByAsset"),
        None,
    )
    block = results.get(symbol) if isinstance(results, dict) else None
    if not isinstance(block, dict):
        return {"success": False, "underlying": symbol, "candles": [], "count": 0, "fonte": "opcoes_net_br", "tipo_dado": "indisponível", "status_dado": "erro", "error": "histórico indisponível", "coleta": datetime.now(timezone.utc).isoformat(), "observacao": HISTORY_NOTE}
    fields = block.get("data_fields") or []
    rows = block.get("data_rows") or []
    candles: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list):
            continue
        candle: dict[str, Any] = {"date": row[0] if fields and fields[0] == "date" else None}
        for index, field in enumerate(fields[1:], start=1):
            if field not in HISTORY_FIELDS:
                continue
            candle[field] = _number(row[index]) if index < len(row) else None
        candles.append(candle)
    candles = [candle for candle in candles if candle.get("date")]
    collected_at = datetime.now(timezone.utc).isoformat()
    return {
        "success": bool(candles),
        "underlying": symbol,
        "candles": candles,
        "count": len(candles),
        "first_date": candles[0].get("date") if candles else None,
        "last_date": candles[-1].get("date") if candles else None,
        "fonte": "opcoes_net_br",
        "tipo_dado": "coletado" if candles else "indisponível",
        "status_dado": "atualizado" if candles else "erro",
        "coleta": collected_at,
        "error": None if candles else "histórico sem candles",
        "observacao": HISTORY_NOTE,
        "data_frequency": "EOD",
    }


def fetch_asset_history(symbol: str, timeframe: str = "Day", timeout: int = 25) -> dict[str, Any]:
    ticker = str(symbol).strip().upper()
    if not ticker:
        return {"success": False, "underlying": ticker, "candles": [], "count": 0, "fonte": "opcoes_net_br", "tipo_dado": "indisponível", "status_dado": "erro", "error": "ativo não informado", "observacao": HISTORY_NOTE}
    response = _api_get([{"type": "QuotesHistoryByAsset", "params": {"assets_ids": ticker, "timeframe": timeframe}}], timeout=timeout)
    if not response.get("success"):
        return {"success": False, "underlying": ticker, "candles": [], "count": 0, "fonte": "opcoes_net_br", "tipo_dado": "indisponível", "status_dado": "erro", "error": response.get("error"), "coleta": datetime.now(timezone.utc).isoformat(), "observacao": HISTORY_NOTE}
    return normalize_history_response(response["payload"], ticker)
