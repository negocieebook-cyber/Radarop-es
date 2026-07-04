"""Descoberta real e cacheada de acesso a opções EOD por ativo."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.providers.brapi_options_provider import BrapiOptionsProvider
from app.storage import load_json, save_json


ROOT = Path(__file__).resolve().parent.parent
AVAILABILITY_FILE = ROOT / "data" / "runtime" / "options_universe_availability.json"
CANDIDATES_FILE = ROOT / "data" / "option_candidate_tickers.json"
LOW_LIQUIDITY_WARNING = "Liquidez baixa no mercado brasileiro. Validar book, spread e execução manualmente."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_options_universe_availability() -> dict[str, Any]:
    value = load_json(AVAILABILITY_FILE, {})
    return value if isinstance(value, dict) else {}


def save_options_universe_availability(data: dict[str, Any]) -> None:
    save_json(AVAILABILITY_FILE, data)


def load_option_candidate_tickers() -> list[str]:
    value = load_json(CANDIDATES_FILE, [])
    return list(dict.fromkeys(str(item).strip().upper() for item in value if str(item).strip())) if isinstance(value, list) else []


def ticker_checked_recently(item: dict[str, Any], max_age_hours: int = 72) -> bool:
    try:
        checked = datetime.fromisoformat(str(item.get("checked_at", "")).replace("Z", "+00:00"))
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - checked.astimezone(timezone.utc)).total_seconds() / 3600
        return 0 <= age <= max_age_hours
    except (TypeError, ValueError):
        return False


def _dte(expiration: str) -> int | None:
    try:
        return (date.fromisoformat(str(expiration)[:10]) - datetime.now(timezone.utc).date()).days
    except (TypeError, ValueError):
        return None


def summarize_options_availability(data: dict[str, Any]) -> dict[str, Any]:
    assets = data.get("assets", []) if isinstance(data, dict) else []
    liquidity_classes = {
        classification: sum(item.get("liquidity_class") == classification for item in assets)
        for classification in ("alta", "média", "baixa", "muito baixa", "sem negócio", "indisponível")
    }
    return {
        "tickers_tested": len(assets),
        "available_count": sum(item.get("has_options_access") is True for item in assets),
        "unavailable_count": sum(item.get("has_options_access") is False for item in assets),
        "error_count": sum(item.get("status") == "erro" for item in assets),
        "total_series": sum(int(item.get("series_count") or 0) for item in assets),
        "generated_at": data.get("generated_at") if isinstance(data, dict) else None,
        "source": "brapi_options",
        "data_frequency": "EOD",
        "liquidity_classes": liquidity_classes,
    }


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_options_liquidity(series: list[dict[str, Any]]) -> dict[str, Any]:
    if not series:
        return {"liquidity_class": "indisponível", "total_volume": None, "total_trades": None, "has_bid_ask": False, "average_spread_pct": None, "execution_warning": "Liquidez não avaliável por ausência de séries."}
    volumes = [_number(item.get("volume")) for item in series]
    trades = [_number(item.get("trades")) for item in series]
    observed_volume = [value for value in volumes if value is not None]
    observed_trades = [value for value in trades if value is not None]
    total_volume = sum(observed_volume) if observed_volume else None
    total_trades = sum(observed_trades) if observed_trades else None
    bid_ask = [item for item in series if _number(item.get("bid")) is not None and _number(item.get("ask")) is not None]
    spreads = [_number(item.get("spread_pct")) for item in bid_ask]
    valid_spreads = [value for value in spreads if value is not None and value >= 0]
    average_spread = round(sum(valid_spreads) / len(valid_spreads), 4) if valid_spreads else None
    has_bid_ask = bool(bid_ask)
    known_activity = total_volume is not None or total_trades is not None
    no_business = known_activity and (total_volume or 0) == 0 and (total_trades or 0) == 0
    if no_business:
        liquidity_class = "sem negócio"
    elif not known_activity and average_spread is None:
        liquidity_class = "indisponível"
    elif has_bid_ask and average_spread is not None and average_spread <= 10 and ((total_volume or 0) >= 500 or (total_trades or 0) >= 100):
        liquidity_class = "alta"
    elif has_bid_ask and average_spread is not None and average_spread <= 25 and ((total_volume or 0) > 0 or (total_trades or 0) > 0):
        liquidity_class = "média"
    elif ((total_volume is not None and 0 < total_volume <= 5) or (total_trades is not None and 0 < total_trades <= 2)):
        liquidity_class = "muito baixa"
    else:
        liquidity_class = "baixa"
    warning = None if liquidity_class in {"alta", "média"} else LOW_LIQUIDITY_WARNING if liquidity_class in {"baixa", "muito baixa", "sem negócio"} else "Liquidez indisponível; validar manualmente antes de qualquer decisão."
    return {"liquidity_class": liquidity_class, "total_volume": total_volume, "total_trades": total_trades, "has_bid_ask": has_bid_ask, "average_spread_pct": average_spread, "execution_warning": warning}


def discover_options_availability(
    tickers: list[str], min_dte: int = 7, max_dte: int = 60,
    max_expirations: int = 1, limit: int | None = None, incremental: bool = False,
) -> dict[str, Any]:
    if min_dte < 0 or max_dte < min_dte or max_expirations < 1:
        raise ValueError("parâmetros de vencimento inválidos")
    symbols = list(dict.fromkeys(str(t).strip().upper() for t in tickers if str(t).strip()))
    if limit is not None:
        symbols = symbols[:max(0, limit)]
    provider = BrapiOptionsProvider()
    assets: list[dict[str, Any]] = []
    errors: list[str] = []
    for symbol in symbols:
        checked_at = _now()
        expirations_result = provider.get_expirations(symbol)
        expirations = expirations_result.get("expirations", []) if expirations_result.get("success") else []
        selected = [value for value in expirations if (days := _dte(value)) is not None and min_dte <= days <= max_dte][:max_expirations]
        series_count = calls_count = puts_count = 0
        collected_series: list[dict[str, Any]] = []
        reasons: list[str] = []
        status = "indisponível"
        if not expirations_result.get("success"):
            reason = expirations_result.get("error") or "vencimentos indisponíveis"
            reasons.append(str(reason))
            if expirations_result.get("access_status") == "sem_acesso":
                status = "sem_acesso_fonte"
            elif expirations_result.get("status_dado") == "indisponível":
                status = "sem_opcoes_na_fonte"
            else:
                status = "erro"
        elif not selected:
            reasons.append(f"nenhum vencimento entre {min_dte} e {max_dte} dias")
        else:
            for expiration in selected:
                chain = provider.get_chain(symbol, expiration)
                if chain.get("success"):
                    chain_series = chain.get("data", [])
                    collected_series.extend(chain_series)
                    series_count += int(chain.get("count") or len(chain_series))
                    calls_count += int(chain.get("calls") or 0)
                    puts_count += int(chain.get("puts") or 0)
                else:
                    reasons.append(f"{expiration}: {chain.get('error') or 'cadeia indisponível'}")
            status = "disponível" if series_count > 0 else "indisponível"
        has_access = series_count > 0
        liquidity = classify_options_liquidity(collected_series)
        if has_access:
            status = "disponivel_baixa_liquidez" if liquidity["liquidity_class"] in {"baixa", "muito baixa", "sem negócio"} else "disponivel"
        reason = "; ".join(reasons) if reasons else "cadeia EOD acessível na fonte atual"
        if status == "erro":
            errors.append(f"{symbol}: {reason}")
        assets.append({
            "ticker": symbol, "has_options_access": has_access,
            "expirations_found": len(expirations), "expirations_selected": selected,
            "series_count": series_count, "calls_count": calls_count, "puts_count": puts_count,
            **liquidity,
            "status": status, "reason": reason, "checked_at": checked_at,
        })
    if incremental:
        existing = load_options_universe_availability()
        merged = {item.get("ticker"): item for item in existing.get("assets", []) if item.get("ticker")}
        merged.update({item["ticker"]: item for item in assets})
        assets = list(merged.values())
    candidate_tickers = load_option_candidate_tickers()
    data = {
        "generated_at": _now(), "source": "brapi_options", "tickers_tested": symbols,
        "available": [item["ticker"] for item in assets if item["has_options_access"]],
        "unavailable": [item["ticker"] for item in assets if not item["has_options_access"]],
        "errors": errors, "assets": assets, "data_frequency": "EOD",
        "candidate_tickers": candidate_tickers,
    }
    data["tickers_tested"] = [item["ticker"] for item in assets]
    data["available"] = [item["ticker"] for item in assets if item["has_options_access"]]
    data["unavailable"] = [item["ticker"] for item in assets if not item["has_options_access"]]
    data["errors"] = [f"{item['ticker']}: {item['reason']}" for item in assets if item.get("status") == "erro"]
    data["pending"] = [ticker for ticker in candidate_tickers if ticker not in set(data["tickers_tested"])]
    data["summary"] = summarize_options_availability(data)
    save_options_universe_availability(data)
    return data


def get_available_option_tickers(max_age_hours: int = 72, include_low_liquidity: bool = True) -> list[str]:
    data = load_options_universe_availability()
    generated_at = data.get("generated_at")
    if not generated_at:
        return []
    try:
        timestamp = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds() / 3600
    except (TypeError, ValueError):
        return []
    if not 0 <= age_hours <= max_age_hours:
        return []
    allowed = {"alta", "média", "baixa", "muito baixa", "sem negócio", "indisponível"} if include_low_liquidity else {"alta", "média"}
    return [item.get("ticker") for item in data.get("assets", []) if item.get("has_options_access") is True and item.get("liquidity_class", "indisponível") in allowed and item.get("ticker")]
