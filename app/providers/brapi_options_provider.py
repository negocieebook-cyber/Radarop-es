"""Cliente isolado para testar dados EOD de opções da brapi."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

EOD_NOTE = "Dados de opções EOD/fim de pregão quando disponíveis."
PRICE_ALIASES = ("last", "lastPrice", "regularMarketPrice", "price", "premio", "theoreticalPrice", "settlement", "closePrice")


def pick_first_available(raw: dict[str, Any], aliases: tuple[str, ...] | list[str]) -> tuple[Any, str | None]:
    for alias in aliases:
        if alias in raw and raw[alias] is not None:
            return raw[alias], alias
    return None, None


def to_float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int_or_none(value: Any) -> int | None:
    number = to_float_or_none(value)
    return int(number) if number is not None and number.is_integer() else None


def normalize_side(value: Any) -> str | None:
    normalized = str(value).strip().lower() if value is not None else ""
    if normalized in {"call", "c", "compra"}:
        return "call"
    if normalized in {"put", "p", "venda"}:
        return "put"
    return None


def normalize_date(value: Any) -> str | int | None:
    if value is None or isinstance(value, bool):
        return None
    return int(value) if isinstance(value, (int, float)) else str(value)


class BrapiOptionsProvider:
    BASE_URL = "https://brapi.dev/api/v2/options"

    def __init__(self, token: str | None = None, timeout: int = 20) -> None:
        configured = token if token is not None else os.getenv("BRAPI_TOKEN")
        placeholders = {"cole_sua_chave_aqui", "SUA_CHAVE_DA_BRAPI_AQUI"}
        self.token = configured if configured and configured not in placeholders else None
        self.timeout = timeout
        self.last_error: str | None = None
        self.last_collection: str | None = None
        self.last_status_code: int | None = None

    def get_provider_name(self) -> str:
        return "brapi_options"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _error(self, message: str, status_code: int | None = None, access_status: str | None = None) -> dict[str, Any]:
        denied = access_status == "sem_acesso" or status_code in {401, 403}
        self.last_error = message
        self.last_status_code = status_code
        return {
            "success": False,
            "provider": "brapi_options",
            "error": message,
            "status_code": status_code,
            "access_status": "sem_acesso" if denied else (access_status or "indisponível"),
            "data": [],
            "fonte": "brapi_options",
            "tipo_dado": "indisponível",
            "status_dado": "erro",
            "observacao": EOD_NOTE,
        }

    def normalize_http_error(self, status_code: int, payload: Any = None) -> dict[str, Any]:
        messages = {
            401: "autenticação da brapi inválida ou ausente",
            403: "acesso negado; o plano atual pode não incluir opções",
            404: "endpoint ou dados de opções não encontrados",
            429: "limite de chamadas da brapi atingido",
            500: "erro interno da brapi",
        }
        api_message = payload.get("message") if isinstance(payload, dict) else None
        message = messages.get(status_code, f"brapi options retornou HTTP {status_code}")
        if api_message and status_code not in {401, 403}:
            message = f"{message}: {api_message}"
        return self._error(message, status_code)

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.token:
            return self._error("BRAPI_TOKEN não configurado", access_status="indisponível")
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, headers=self._headers(), timeout=self.timeout)
            self.last_status_code = response.status_code
            if response.status_code != 200:
                try:
                    payload = response.json()
                except ValueError:
                    payload = None
                return self.normalize_http_error(response.status_code, payload)
            try:
                return {"success": True, "payload": response.json(), "status_code": response.status_code}
            except ValueError:
                return self._error("resposta JSON inválida da brapi options", response.status_code)
        except requests.Timeout:
            return self._error("timeout ao consultar a brapi options")
        except requests.RequestException:
            return self._error("erro de conexão com a brapi options")

    def normalize_expirations_response(self, response_json: dict[str, Any], underlying: str | None = None) -> dict[str, Any]:
        collected_at = datetime.now(timezone.utc).isoformat()
        raw = response_json.get("expirations", []) if isinstance(response_json, dict) else []
        expirations = sorted({str(item) for item in raw if item}) if isinstance(raw, list) else []
        self.last_collection = collected_at
        return {
            "success": bool(expirations),
            "underlying": str(response_json.get("underlying") or underlying or "").upper(),
            "expirations": expirations,
            "count": len(expirations),
            "access_status": "disponível" if expirations else "indisponível",
            "fonte": "brapi_options",
            "tipo_dado": "coletado",
            "status_dado": "atualizado" if expirations else "indisponível",
            "coleta": collected_at,
            "observacao": EOD_NOTE,
            "error": None if expirations else "nenhum vencimento disponível",
        }

    @staticmethod
    def _liquidity(trades: Any) -> str:
        if not isinstance(trades, (int, float)) or isinstance(trades, bool):
            return "indisponível"
        if trades >= 500:
            return "alta"
        if trades >= 100:
            return "média"
        if trades >= 20:
            return "baixa"
        return "ilíquida"

    def normalize_chain_response(self, response_json: dict[str, Any], underlying_price: float | None = None) -> list[dict[str, Any]]:
        series = response_json.get("series", []) if isinstance(response_json, dict) else []
        normalized: list[dict[str, Any]] = []
        expected = (
            "symbol", "underlying_symbol", "side", "market", "strike", "expiration_date",
            "first_trade_date", "last_trade_date", "date", "open", "high", "low", "average",
            "close", "bid", "ask", "trades", "volume", "financial_volume",
        )
        for item in series if isinstance(series, list) else []:
            if not isinstance(item, dict):
                continue
            bid = to_float_or_none(item.get("bid"))
            ask = to_float_or_none(item.get("ask"))
            mid = (bid + ask) / 2 if bid is not None and ask is not None else None
            spread_abs = ask - bid if bid is not None and ask is not None else None
            spread_pct = spread_abs / mid * 100 if spread_abs is not None and mid not in {None, 0} else None
            strike = to_float_or_none(item.get("strike"))
            side = normalize_side(item.get("side"))
            close = to_float_or_none(item.get("close"))
            average = to_float_or_none(item.get("average"))
            alias_value_raw, alias_source = pick_first_available(item, PRICE_ALIASES)
            alias_value = to_float_or_none(alias_value_raw)
            trades = to_int_or_none(pick_first_available(item, ("trades", "numberOfTrades", "number_of_trades"))[0])
            volume = to_int_or_none(pick_first_available(item, ("volume", "quantity", "businessVolume"))[0])
            financial_volume = to_float_or_none(pick_first_available(item, ("financialVolume", "financial_volume"))[0])
            if mid is not None:
                normalized_price, normalized_basis, normalized_source = mid, "mid", "bid+ask"
            elif close is not None:
                normalized_price, normalized_basis, normalized_source = close, "close_eod", "close"
            elif average is not None:
                normalized_price, normalized_basis, normalized_source = average, "average_eod", "average"
            elif alias_value is not None:
                normalized_price, normalized_basis, normalized_source = alias_value, f"alias_eod:{alias_source}", alias_source
            else:
                normalized_price, normalized_basis, normalized_source = None, "indisponível", None
            if underlying_price is None or strike is None or side not in {"call", "put"}:
                moneyness = "indisponível"
            elif side == "call":
                moneyness = "ITM" if underlying_price > strike else "OTM" if underlying_price < strike else "ATM"
            else:
                moneyness = "ITM" if underlying_price < strike else "OTM" if underlying_price > strike else "ATM"
            record = {
                "symbol": item.get("symbol"),
                "underlying_symbol": item.get("underlyingSymbol"),
                "side": side,
                "market": item.get("market"),
                "strike": strike,
                "expiration_date": normalize_date(item.get("expirationDate")),
                "first_trade_date": normalize_date(item.get("firstTradeDate")),
                "last_trade_date": normalize_date(item.get("lastTradeDate")),
                "date": normalize_date(item.get("date")),
                "open": to_float_or_none(item.get("open")),
                "high": to_float_or_none(item.get("high")),
                "low": to_float_or_none(item.get("low")),
                "average": average,
                "close": close,
                "bid": bid,
                "ask": ask,
                "trades": trades,
                "volume": volume,
                "financial_volume": financial_volume,
                "mid": round(mid, 6) if mid is not None else None,
                "spread_abs": round(spread_abs, 6) if spread_abs is not None else None,
                "spread_pct": round(spread_pct, 4) if spread_pct is not None else None,
                "liquidity_status": self._liquidity(trades),
                "moneyness": moneyness,
                "normalized_price": round(normalized_price, 6) if normalized_price is not None else None,
                "normalized_price_basis": normalized_basis,
                "normalized_price_source": normalized_source,
                "price_alias_value": alias_value,
                "price_alias_source": alias_source,
                "price_value_status": "ausente" if normalized_price is None else "zerado" if normalized_price == 0 else "válido" if normalized_price > 0 else "inválido",
                "raw": dict(item),
                "raw_keys": sorted(item.keys()),
                "fonte": "brapi_options",
                "tipo_dado": "coletado",
                "status_dado": "atualizado",
                "observacao": EOD_NOTE,
            }
            record["campos_ausentes"] = [field for field in expected if record.get(field) is None]
            normalized.append(record)
        return normalized

    def get_expirations(self, underlying: str, include_expired: bool = False) -> dict[str, Any]:
        symbol = str(underlying).strip().upper()
        request = self._request("expirations", {"underlying": symbol, "includeExpired": str(include_expired).lower()})
        return self.normalize_expirations_response(request["payload"], symbol) if request.get("success") else request

    def get_chain(self, underlying: str, expiration_date: str, side: str | None = None, min_strike: float | None = None, max_strike: float | None = None, date: str | None = None) -> dict[str, Any]:
        symbol = str(underlying).strip().upper()
        params: dict[str, Any] = {"underlying": symbol, "expirationDate": expiration_date}
        params.update({key: value for key, value in {"side": side, "minStrike": min_strike, "maxStrike": max_strike, "date": date}.items() if value is not None})
        request = self._request("chain", params)
        if not request.get("success"):
            return request
        collected_at = datetime.now(timezone.utc).isoformat()
        data = self.normalize_chain_response(request["payload"])
        self.last_collection = collected_at
        return {
            "success": bool(data), "provider": "brapi_options", "underlying": symbol,
            "expiration_date": expiration_date, "data": data, "count": len(data),
            "calls": sum(item["side"] == "call" for item in data),
            "puts": sum(item["side"] == "put" for item in data),
            "access_status": "disponível" if data else "indisponível", "error": None if data else "cadeia sem séries",
            "fonte": "brapi_options", "tipo_dado": "coletado",
            "status_dado": "atualizado" if data else "indisponível", "coleta": collected_at, "observacao": EOD_NOTE,
        }

    def get_historical(self, symbol: str, range: str | None = None) -> dict[str, Any]:
        params = {"symbol": str(symbol).strip().upper()}
        if range:
            params["expirationDate"] = range
        request = self._request("historical", params)
        if not request.get("success"):
            return request
        collected_at = datetime.now(timezone.utc).isoformat()
        self.last_collection = collected_at
        return {"success": True, "provider": "brapi_options", "data": request["payload"], "access_status": "disponível", "fonte": "brapi_options", "tipo_dado": "coletado", "status_dado": "atualizado", "coleta": collected_at, "observacao": EOD_NOTE}

    def get_provider_status(self) -> dict[str, Any]:
        return {
            "provider": "brapi_options", "configured": bool(self.token), "token_detected": bool(self.token),
            "status": "pronto para teste EOD" if self.token else "token ausente",
            "last_collection": self.last_collection, "last_error": self.last_error,
            "last_status_code": self.last_status_code, "realtime": False, "observacao": EOD_NOTE,
        }
