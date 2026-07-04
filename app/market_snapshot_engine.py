"""Monta snapshots de mercado reais/experimentais a partir da brapi."""

from __future__ import annotations

from typing import Any

from app.healthbox_engine import build_healthbox, healthbox_score
from app.providers.provider_manager import fetch_historical, fetch_quotes
from app.technical_indicators import (
    calculate_adr_percent,
    calculate_atr_percent,
    calculate_daily_change_percent,
    calculate_daily_range_percent,
    calculate_relative_volume,
    calculate_rsi,
    calculate_support_resistance,
    classify_trend,
)


def _value(result: dict[str, Any]) -> Any:
    return result.get("value") if result.get("status") == "calculado" else None


def build_asset_snapshot_from_data(ticker: str, quote_result: dict[str, Any], historical_result: dict[str, Any]) -> dict[str, Any]:
    quote = next((item for item in quote_result.get("data", []) if item.get("ticker") == ticker), None)
    historical = next((item for item in historical_result.get("data", []) if item.get("ticker") == ticker), None)
    candles = historical.get("candles", []) if historical else []
    quote_available = quote is not None
    history_available = bool(candles)

    daily_change = calculate_daily_change_percent(quote.get("preco") if quote else None, quote.get("fechamento_anterior") if quote else None)
    daily_range = calculate_daily_range_percent(quote.get("maxima") if quote else None, quote.get("minima") if quote else None, quote.get("preco") if quote else None)
    rsi = calculate_rsi(candles, 14)
    rsi_200 = calculate_rsi(candles, 200)
    atr = calculate_atr_percent(candles, 14)
    adr = calculate_adr_percent(candles, 14)
    rvol = calculate_relative_volume(candles, 20)
    levels = calculate_support_resistance(candles, 20)
    trend = classify_trend(candles, 9, 21)
    support, resistance = levels.get("support"), levels.get("resistance")
    price = quote.get("preco") if quote else None
    distance_support = ((price - support) / support * 100) if isinstance(price, (int, float)) and isinstance(support, (int, float)) and support != 0 else None
    distance_resistance = ((price - resistance) / resistance * 100) if isinstance(price, (int, float)) and isinstance(resistance, (int, float)) and resistance != 0 else None

    fields = {
        "preco_atual": price,
        "abertura": quote.get("abertura") if quote else None,
        "maxima": quote.get("maxima") if quote else None,
        "minima": quote.get("minima") if quote else None,
        "fechamento_anterior": quote.get("fechamento_anterior") if quote else None,
        "volume": quote.get("volume") if quote else None,
        "variacao_diaria_percent": _value(daily_change),
        "range_diario_percent": _value(daily_range),
        "adr_percent": _value(adr),
        "atr_percent": _value(atr),
        "rvol": _value(rvol),
        "rsi": _value(rsi),
        "rsi_200": _value(rsi_200),
        "tendencia": trend.get("value", "indefinida"),
        "suporte": support,
        "resistencia": resistance,
        "distancia_suporte_percent": round(distance_support, 4) if distance_support is not None else None,
        "distancia_resistencia_percent": round(distance_resistance, 4) if distance_resistance is not None else None,
        "volatilidade_implicita": None,
    }
    missing = [field for field, value in fields.items() if value is None]
    if not quote_available and not history_available:
        status = "erro"
    elif not quote_available or not history_available or missing:
        status = "incompleto"
    else:
        status = "atualizado"
    source = (quote or historical or {}).get("fonte", quote_result.get("provider", historical_result.get("provider", "indisponível")))
    data_type = "coletado/calculado" if quote_available and history_available else (quote or historical or {}).get("tipo_dado", "indisponível")
    return {
        "ativo": ticker,
        **fields,
        "campos_ausentes": missing,
        "fonte": source,
        "fonte_base": "brapi" if source == "brapi" else source,
        "tipo_dado": data_type,
        "status_dado": status,
        "coleta": (quote or historical or {}).get("coleta", quote_result.get("coleta", historical_result.get("coleta"))),
        "observacao": "Indicadores técnicos experimentais; suporte/resistência são extremos simples da janela.",
        "linhagem_campos": {
            "coletados": ["preco_atual", "abertura", "maxima", "minima", "fechamento_anterior", "volume"],
            "calculados": ["variacao_diaria_percent", "range_diario_percent", "adr_percent", "atr_percent", "rvol", "rsi", "rsi_200", "tendencia", "suporte", "resistencia", "distancia_suporte_percent", "distancia_resistencia_percent"],
            "indisponiveis": missing,
        },
    }


def build_asset_snapshot_from_provider(ticker: str, range: str = "3mo", interval: str = "1d") -> dict[str, Any]:
    normalized = str(ticker).strip().upper()
    quotes = fetch_quotes([normalized], use_cache=True, cache_minutes=15)
    historical = fetch_historical([normalized], range=range, interval=interval, use_cache=True, cache_minutes=60)
    return build_asset_snapshot_from_data(normalized, quotes, historical)


def build_many_asset_snapshots(tickers: list[str], range: str = "3mo", interval: str = "1d") -> list[dict[str, Any]]:
    return [build_asset_snapshot_from_provider(ticker, range, interval) for ticker in dict.fromkeys(str(item).strip().upper() for item in tickers if str(item).strip())]


def snapshot_to_healthbox(snapshot: dict[str, Any]) -> dict[str, Any]:
    healthbox = build_healthbox(snapshot)
    return {**healthbox, "score_result": healthbox_score(healthbox), "snapshot_status": snapshot.get("status_dado"), "fonte_base": snapshot.get("fonte_base")}


def get_snapshot_status(snapshot: dict[str, Any]) -> str:
    return str(snapshot.get("status_dado", "indisponível"))
