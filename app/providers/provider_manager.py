"""Seleção, cache e fallback explícito dos provedores."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from app.cache import CACHE_DIR, is_cache_fresh, load_cache, save_cache
from app.mock_data import MOCK_ASSET_SNAPSHOTS
from app.providers.brapi_provider import BrapiProvider


load_dotenv()


def _allow_fallback() -> bool:
    return os.getenv("ALLOW_MOCK_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "sim"}


def get_active_provider() -> BrapiProvider | None:
    name = os.getenv("DATA_PROVIDER", "brapi").strip().lower()
    return BrapiProvider() if name == "brapi" else None


def _mock_quote_fallback(tickers: list[str], original_error: str) -> dict[str, Any]:
    records = []
    for ticker in tickers:
        snapshot = next((item for item in MOCK_ASSET_SNAPSHOTS if item.get("ativo") == ticker), None)
        if snapshot:
            records.append({"ticker": ticker, "preco": snapshot.get("preco_atual"), "abertura": snapshot.get("abertura"), "maxima": snapshot.get("maxima"), "minima": snapshot.get("minima"), "fechamento_anterior": snapshot.get("fechamento_anterior"), "volume": None, "variacao_percentual": None, "market_time": None, "fonte": "mock fallback", "tipo_dado": "MOCK / EXEMPLO", "status_dado": "fallback por erro da fonte real", "coleta": "não aplicável", "raw": None})
    return {"success": bool(records), "provider": "mock fallback", "error": original_error, "status_code": None, "data": records, "tipo_dado": "MOCK / EXEMPLO", "status_dado": "fallback por erro da fonte real", "fallback_used": True}


def fetch_quotes(tickers: list[str], use_cache: bool = True, cache_minutes: int = 15) -> dict[str, Any]:
    normalized = sorted({str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()})
    key = f"quotes:{','.join(normalized)}"
    if use_cache and is_cache_fresh(key, cache_minutes):
        cached = load_cache(key)
        result = dict(cached["data"])
        result.update(from_cache=True, cache_saved_at=cached["saved_at"])
        return result
    provider = get_active_provider()
    if provider is None:
        result = {"success": False, "provider": "indisponível", "error": "DATA_PROVIDER não reconhecido", "status_code": None, "data": [], "tipo_dado": "indisponível", "status_dado": "erro"}
    else:
        result = provider.get_quotes(normalized)
    if result.get("success"):
        save_cache(key, result)
        result["from_cache"] = False
        return result
    return _mock_quote_fallback(normalized, result.get("error", "erro desconhecido")) if _allow_fallback() else result


def fetch_historical(tickers: list[str], range: str = "3mo", interval: str = "1d", use_cache: bool = True, cache_minutes: int = 60) -> dict[str, Any]:
    normalized = sorted({str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()})
    key = f"historical:{','.join(normalized)}:{range}:{interval}"
    if use_cache and is_cache_fresh(key, cache_minutes):
        cached = load_cache(key)
        result = dict(cached["data"])
        result.update(from_cache=True, cache_saved_at=cached["saved_at"])
        return result
    provider = get_active_provider()
    result = provider.get_historical(normalized, range, interval) if provider else {"success": False, "provider": "indisponível", "error": "DATA_PROVIDER não reconhecido", "status_code": None, "data": [], "tipo_dado": "indisponível", "status_dado": "erro"}
    if result.get("success"):
        save_cache(key, result)
        result["from_cache"] = False
        return result
    if _allow_fallback():
        return {"success": False, "provider": "mock fallback", "error": result.get("error"), "status_code": result.get("status_code"), "data": [], "tipo_dado": "MOCK / EXEMPLO", "status_dado": "fallback por erro da fonte real", "fallback_used": True, "note": "histórico mock não disponível; nenhum candle foi inventado"}
    return result


def provider_status() -> dict[str, Any]:
    provider = get_active_provider()
    status = provider.get_provider_status() if provider else {"provider": os.getenv("DATA_PROVIDER", "indisponível"), "configured": False, "token_detected": False, "status": "provider não reconhecido", "last_collection": None, "last_error": None}
    status.update({"fallback_allowed": _allow_fallback(), "cache_directory": str(CACHE_DIR), "cached_files": len(list(CACHE_DIR.glob("*.json"))) if CACHE_DIR.exists() else 0})
    return status
