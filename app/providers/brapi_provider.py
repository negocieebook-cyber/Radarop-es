"""Provider brapi para cotações e histórico de ativos brasileiros."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv

from app.providers.base import BaseProvider


load_dotenv()


class BrapiProvider(BaseProvider):
    QUOTE_URL = "https://brapi.dev/api/quote/{tickers}"
    HISTORICAL_URL = "https://brapi.dev/api/v2/stocks/historical"

    def __init__(self, token: str | None = None, timeout: int = 15) -> None:
        configured = token if token is not None else os.getenv("BRAPI_TOKEN")
        placeholders = {"cole_sua_chave_aqui", "SUA_CHAVE_DA_BRAPI_AQUI"}
        self.token = configured if configured and configured not in placeholders else None
        self.timeout = timeout
        self.last_error: str | None = None
        self.last_collection: str | None = None
        self.last_auth_mode: str | None = None

    def get_provider_name(self) -> str:
        return "brapi"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _error(self, message: str, status_code: int | None = None) -> dict[str, Any]:
        self.last_error = message
        return {"success": False, "provider": "brapi", "error": message, "status_code": status_code, "data": [], "tipo_dado": "indisponível", "status_dado": "erro"}

    def _request(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        """Tenta header primeiro e query somente após falha explícita de autenticação."""
        response = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        self.last_auth_mode = "authorization_header"
        if response.status_code in {401, 403} and self.token:
            query_params = dict(params or {})
            query_params["token"] = self.token
            response = requests.get(url, params=query_params, timeout=self.timeout)
            self.last_auth_mode = "query_fallback"
        return response

    def get_quotes(self, tickers: list[str]) -> dict[str, Any]:
        symbols = [str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()]
        if not symbols:
            return self._error("nenhum ticker informado")
        if not self.token:
            return self._error("BRAPI_TOKEN não configurado")
        try:
            response = self._request(self.QUOTE_URL.format(tickers=",".join(symbols)))
            if response.status_code == 400 and len(symbols) > 1:
                combined_results: list[dict[str, Any]] = []
                failed_symbols: list[str] = []
                for symbol in symbols:
                    single_response = self._request(self.QUOTE_URL.format(tickers=symbol))
                    if single_response.status_code != 200:
                        failed_symbols.append(symbol)
                        continue
                    try:
                        single_payload = single_response.json()
                    except ValueError:
                        failed_symbols.append(symbol)
                        continue
                    single_results = single_payload.get("results", []) if isinstance(single_payload, dict) else []
                    if isinstance(single_results, list):
                        combined_results.extend(single_results)
                if combined_results:
                    data = self.normalize_quote_response({"results": combined_results})
                    self.last_collection = datetime.now(timezone.utc).isoformat()
                    self.last_error = None
                    return {"success": True, "provider": "brapi", "error": None, "status_code": 200, "data": data, "tipo_dado": "coletado", "status_dado": "atualizado" if not failed_symbols else "incompleto", "coleta": self.last_collection, "batch_mode": "individual_fallback", "failed_symbols": failed_symbols}
            if response.status_code != 200:
                return self._error(f"brapi retornou HTTP {response.status_code}", response.status_code)
            try:
                payload = response.json()
            except ValueError:
                return self._error("resposta JSON inválida da brapi", response.status_code)
            data = self.normalize_quote_response(payload)
            self.last_collection = datetime.now(timezone.utc).isoformat()
            self.last_error = None
            return {"success": True, "provider": "brapi", "error": None, "status_code": response.status_code, "data": data, "tipo_dado": "coletado", "status_dado": "atualizado", "coleta": self.last_collection}
        except requests.Timeout:
            return self._error("timeout ao consultar a brapi")
        except requests.RequestException:
            return self._error("erro de conexão com a brapi")

    def get_historical(self, tickers: list[str], range: str = "3mo", interval: str = "1d") -> dict[str, Any]:
        symbols = [str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()]
        if not symbols:
            return self._error("nenhum ticker informado")
        if not self.token:
            return self._error("BRAPI_TOKEN não configurado")
        try:
            response = self._request(self.HISTORICAL_URL, {"symbols": ",".join(symbols), "range": range, "interval": interval})
            if response.status_code != 200:
                return self._error(f"brapi retornou HTTP {response.status_code}", response.status_code)
            try:
                payload = response.json()
            except ValueError:
                return self._error("resposta JSON inválida da brapi", response.status_code)
            data = self.normalize_historical_response(payload)
            self.last_collection = datetime.now(timezone.utc).isoformat()
            self.last_error = None
            return {"success": True, "provider": "brapi", "error": None, "status_code": response.status_code, "data": data, "tipo_dado": "coletado", "status_dado": "atualizado", "coleta": self.last_collection}
        except requests.Timeout:
            return self._error("timeout ao consultar histórico da brapi")
        except requests.RequestException:
            return self._error("erro de conexão com a brapi")

    def normalize_quote_response(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        collected_at = datetime.now(timezone.utc).isoformat()
        results = response_json.get("results", []) if isinstance(response_json, dict) else []
        normalized = []
        for item in results if isinstance(results, list) else []:
            normalized.append({
                "ticker": item.get("symbol"), "preco": item.get("regularMarketPrice"), "abertura": item.get("regularMarketOpen"),
                "maxima": item.get("regularMarketDayHigh"), "minima": item.get("regularMarketDayLow"), "fechamento_anterior": item.get("regularMarketPreviousClose"),
                "volume": item.get("regularMarketVolume"), "variacao_percentual": item.get("regularMarketChangePercent"), "market_time": item.get("regularMarketTime"),
                "fonte": "brapi", "tipo_dado": "coletado", "status_dado": "atualizado" if item.get("regularMarketPrice") is not None else "indisponível", "coleta": collected_at, "raw": item,
            })
        return normalized

    def normalize_historical_response(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        collected_at = datetime.now(timezone.utc).isoformat()
        results = response_json.get("results", []) if isinstance(response_json, dict) else []
        normalized = []
        for item in results if isinstance(results, list) else []:
            data_block = item.get("data", {}) if isinstance(item.get("data"), dict) else {}
            raw_candles = item.get("historicalDataPrice", data_block.get("historicalDataPrice", []))
            candles = [
                {"date": candle.get("date"), "open": candle.get("open"), "high": candle.get("high"), "low": candle.get("low"), "close": candle.get("close"), "volume": candle.get("volume"), "adjusted_close": candle.get("adjustedClose")}
                for candle in raw_candles if isinstance(candle, dict)
            ]
            normalized.append({"ticker": item.get("symbol"), "candles": candles, "fonte": "brapi", "tipo_dado": "coletado", "status_dado": "atualizado" if candles else "indisponível", "coleta": collected_at, "raw": item})
        return normalized

    def get_provider_status(self) -> dict[str, Any]:
        return {"provider": "brapi", "configured": bool(self.token), "token_detected": bool(self.token), "status": "pronto" if self.token else "token ausente", "last_collection": self.last_collection, "last_error": self.last_error, "last_auth_mode": self.last_auth_mode}
