"""Indicadores técnicos puros calculados sobre candles normalizados."""

from __future__ import annotations

from statistics import mean
from typing import Any


SOURCE_BASE = "brapi"


def _result(value: Any, status: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"value": value, "status": status, "reason": reason, "source_base": SOURCE_BASE, **extra}


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract(candles: list[dict[str, Any]], field: str) -> list[float]:
    values = [safe_float(candle.get(field)) for candle in candles]
    return [value for value in values if value is not None]


def extract_closes(candles: list[dict[str, Any]]) -> list[float]:
    return _extract(candles, "close")


def extract_highs(candles: list[dict[str, Any]]) -> list[float]:
    return _extract(candles, "high")


def extract_lows(candles: list[dict[str, Any]]) -> list[float]:
    return _extract(candles, "low")


def extract_volumes(candles: list[dict[str, Any]]) -> list[float]:
    return _extract(candles, "volume")


def calculate_daily_change_percent(current_price: Any, previous_close: Any) -> dict[str, Any]:
    current, previous = safe_float(current_price), safe_float(previous_close)
    if current is None or previous in (None, 0):
        return _result(None, "indisponível", "preço atual ou fechamento anterior ausente")
    return _result(round(((current - previous) / previous) * 100, 4), "calculado", "variação percentual sobre fechamento anterior")


def calculate_daily_range_percent(high: Any, low: Any, reference_price: Any = None) -> dict[str, Any]:
    high_value, low_value = safe_float(high), safe_float(low)
    reference = safe_float(reference_price)
    if high_value is None or low_value is None:
        return _result(None, "indisponível", "máxima ou mínima ausente")
    denominator = reference if reference not in (None, 0) else low_value
    if denominator in (None, 0):
        return _result(None, "indisponível", "preço de referência inválido")
    return _result(round(((high_value - low_value) / denominator) * 100, 4), "calculado", "range diário percentual")


def calculate_sma(values: list[Any], period: int) -> dict[str, Any]:
    numeric = [safe_float(value) for value in values]
    if period <= 0 or len(numeric) < period or any(value is None for value in numeric[-period:]):
        return _result(None, "indisponível", "histórico insuficiente")
    return _result(round(mean(numeric[-period:]), 6), "calculado", f"média móvel simples de {period} períodos")


def calculate_rsi(candles: list[dict[str, Any]], period: int = 14) -> dict[str, Any]:
    closes = extract_closes(candles)
    if len(closes) < period + 1:
        return _result(None, "indisponível", "histórico insuficiente")
    changes = [current - previous for previous, current in zip(closes[-(period + 1):-1], closes[-period:])]
    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]
    average_gain, average_loss = mean(gains), mean(losses)
    if average_loss == 0:
        value = 50.0 if average_gain == 0 else 100.0
    else:
        value = 100 - (100 / (1 + average_gain / average_loss))
    return _result(round(value, 4), "calculado", f"RSI simples de {period} períodos")


def calculate_atr_percent(candles: list[dict[str, Any]], period: int = 14) -> dict[str, Any]:
    if len(candles) < period + 1:
        return _result(None, "indisponível", "histórico insuficiente")
    selected = candles[-(period + 1):]
    true_ranges: list[float] = []
    for previous, current in zip(selected[:-1], selected[1:]):
        high, low, previous_close = safe_float(current.get("high")), safe_float(current.get("low")), safe_float(previous.get("close"))
        if None in (high, low, previous_close):
            return _result(None, "indisponível", "high, low ou close ausente")
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    latest_close = safe_float(selected[-1].get("close"))
    if latest_close in (None, 0):
        return _result(None, "indisponível", "fechamento mais recente ausente")
    return _result(round((mean(true_ranges) / latest_close) * 100, 4), "calculado", f"ATR básico de {period} períodos em percentual")


def calculate_adr_percent(candles: list[dict[str, Any]], period: int = 14) -> dict[str, Any]:
    if len(candles) < period:
        return _result(None, "indisponível", "histórico insuficiente")
    ranges = []
    for candle in candles[-period:]:
        high, low, close = safe_float(candle.get("high")), safe_float(candle.get("low")), safe_float(candle.get("close"))
        if None in (high, low, close) or close == 0:
            return _result(None, "indisponível", "high, low ou close ausente")
        ranges.append(((high - low) / close) * 100)
    return _result(round(mean(ranges), 4), "calculado", f"ADR percentual médio de {period} períodos")


def calculate_relative_volume(candles: list[dict[str, Any]], period: int = 20) -> dict[str, Any]:
    volumes = extract_volumes(candles)
    if len(volumes) < period + 1:
        return _result(None, "indisponível", "histórico de volume insuficiente")
    baseline = mean(volumes[-(period + 1):-1])
    if baseline == 0:
        return _result(None, "indisponível", "média de volume inválida")
    return _result(round(volumes[-1] / baseline, 4), "calculado", f"volume atual sobre média dos {period} anteriores")


def calculate_support_resistance(candles: list[dict[str, Any]], lookback: int = 20) -> dict[str, Any]:
    if len(candles) < lookback:
        return _result(None, "indisponível", "histórico insuficiente", support=None, resistance=None, method="suporte_resistencia_simples_lookback")
    selected = candles[-lookback:]
    highs, lows = extract_highs(selected), extract_lows(selected)
    if len(highs) != lookback or len(lows) != lookback:
        return _result(None, "indisponível", "high ou low ausente", support=None, resistance=None, method="suporte_resistencia_simples_lookback")
    support, resistance = min(lows), max(highs)
    return _result({"support": support, "resistance": resistance}, "calculado", "extremos simples da janela; não são níveis profissionais definitivos", support=round(support, 6), resistance=round(resistance, 6), method="suporte_resistencia_simples_lookback")


def classify_trend(candles: list[dict[str, Any]], short_period: int = 9, long_period: int = 21) -> dict[str, Any]:
    closes = extract_closes(candles)
    if len(closes) < long_period:
        return _result("indefinida", "indisponível", "histórico insuficiente")
    short = calculate_sma(closes, short_period)["value"]
    long = calculate_sma(closes, long_period)["value"]
    price = closes[-1]
    if short is None or long is None:
        return _result("indefinida", "indisponível", "médias indisponíveis")
    proximity = abs(short - long) / long if long else 0
    if proximity <= 0.005:
        trend = "lateral"
    elif short > long and price > short:
        trend = "alta"
    elif short < long and price < short:
        trend = "baixa"
    else:
        trend = "lateral"
    return _result(trend, "calculado", f"SMA {short_period} versus SMA {long_period}", short_sma=short, long_sma=long)
