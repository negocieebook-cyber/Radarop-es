"""Auditoria rastreável dos snapshots reais de opções EOD."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.options_update_orchestrator import load_all_options_snapshots
from app.providers.brapi_options_provider import PRICE_ALIASES
from app.real_opportunity_engine import diagnose_pairing_inputs, resolve_option_price


LIQUIDITY_ALIASES = ("numberOfTrades", "number_of_trades", "quantity", "businessVolume", "financialVolume", "openInterest", "open_interest")
PRICE_FIELDS = ("bid", "ask", "mid", "close", "average", "open", "high", "low")


def load_saved_option_snapshots() -> dict[str, dict[str, Any]]:
    return load_all_options_snapshots()


def _series(snapshots: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for snapshot in snapshots.values():
        chains = snapshot.get("chains") if isinstance(snapshot.get("chains"), list) else []
        if chains:
            result.extend(item for chain in chains for item in chain.get("series", []) if isinstance(item, dict))
        else:
            result.extend(item for item in snapshot.get("series", []) if isinstance(item, dict))
    return result


def extract_raw_field_inventory(snapshots: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = Counter(key for item in _series(snapshots) for key in (item.get("raw", {}) if isinstance(item.get("raw"), dict) else {}))
    return dict(counts.most_common())


def find_possible_field_aliases(series: dict[str, Any] | list[dict[str, Any]]) -> dict[str, int]:
    items = series if isinstance(series, list) else [series]
    aliases = Counter()
    for item in items:
        raw = item.get("raw", {}) if isinstance(item.get("raw"), dict) else {}
        for field in (*PRICE_ALIASES, *LIQUIDITY_ALIASES):
            if field in raw:
                aliases[field] += 1
    return dict(aliases.most_common())


def audit_price_fields(series: dict[str, Any]) -> dict[str, Any]:
    present = [field for field in PRICE_FIELDS if series.get(field) is not None]
    missing = [field for field in PRICE_FIELDS if series.get(field) is None]
    zero = [field for field in PRICE_FIELDS if isinstance(series.get(field), (int, float)) and series.get(field) == 0]
    invalid = [field for field in PRICE_FIELDS if series.get(field) is not None and not isinstance(series.get(field), (int, float))]
    resolution = resolve_option_price(series)
    aliases = find_possible_field_aliases(series)
    recommendation = "mapeamento atual suficiente"
    if resolution["price"] is None and aliases:
        recommendation = "revisar alias raw detectado; não mapear sem validar semântica"
    elif resolution["price"] is None:
        recommendation = "nenhum preço reconhecido; manter indisponível"
    return {
        "present_fields": present, "missing_fields": missing, "zero_fields": zero, "invalid_fields": invalid,
        "current_price": resolution["price"], "current_price_basis": resolution["price_basis"],
        "possible_raw_aliases": aliases, "mapping_recommendation": recommendation,
    }


def audit_liquidity_fields(series: dict[str, Any]) -> dict[str, Any]:
    fields = ("trades", "volume", "financial_volume", "bid", "ask", "spread_abs", "spread_pct")
    raw = series.get("raw", {}) if isinstance(series.get("raw"), dict) else {}
    return {
        "present_fields": [field for field in fields if series.get(field) is not None],
        "missing_fields": [field for field in fields if series.get(field) is None],
        "zero_fields": [field for field in fields if isinstance(series.get(field), (int, float)) and series.get(field) == 0],
        "possible_raw_aliases": [field for field in LIQUIDITY_ALIASES if field in raw],
        "liquidity_status": series.get("liquidity_status", "indisponível"),
    }


def audit_pairing_inputs(series: dict[str, Any]) -> dict[str, Any]:
    required = {
        "ativo": series.get("underlying_symbol"), "side": series.get("side"), "strike": series.get("strike"),
        "expiration_date": series.get("expiration_date"), "vencimento_dias": series.get("vencimento_dias"),
        "preço_indicativo": resolve_option_price(series)["price"], "liquidez_status": series.get("liquidity_status"),
    }
    return {"inputs": required, "missing_inputs": [field for field, value in required.items() if value is None]}


def audit_option_series_fields(series: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": series.get("symbol"), "price": audit_price_fields(series),
        "liquidity": audit_liquidity_fields(series), "pairing": audit_pairing_inputs(series),
        "raw_keys": series.get("raw_keys", sorted(series.get("raw", {}).keys()) if isinstance(series.get("raw"), dict) else []),
    }


def summarize_options_data_quality(snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
    items = _series(snapshots)
    price_audits = [audit_price_fields(item) for item in items]
    raw_inventory = extract_raw_field_inventory(snapshots)
    expirations = sorted({str(item.get("expiration_date")) for item in items if item.get("expiration_date")})
    math_causes = Counter()
    for item, price in zip(items, price_audits):
        if price["current_price"] is None:
            math_causes["preço indicativo ausente ou zerado"] += 1
        if item.get("strike") is None:
            math_causes["strike ausente"] += 1
        if item.get("expiration_date") is None:
            math_causes["vencimento ausente"] += 1
        if item.get("side") not in {"call", "put"}:
            math_causes["side inválido"] += 1
    return {
        "assets_audited": len(snapshots), "series_total": len(items),
        "calls": sum(item.get("side") == "call" for item in items), "puts": sum(item.get("side") == "put" for item in items),
        "expirations": expirations, "with_close": sum(item.get("close") is not None for item in items),
        "with_average": sum(item.get("average") is not None for item in items),
        "with_bid_ask": sum(item.get("bid") is not None and item.get("ask") is not None for item in items),
        "with_usable_price": sum(audit["current_price"] is not None for audit in price_audits),
        "without_usable_price": sum(audit["current_price"] is None for audit in price_audits),
        "with_trades": sum(item.get("trades") is not None for item in items),
        "with_volume": sum(item.get("volume") is not None for item in items),
        "zero_price_series": sum(bool(audit["zero_fields"]) for audit in price_audits),
        "raw_field_inventory": raw_inventory, "possible_aliases": find_possible_field_aliases(items),
        "math_incomplete_causes": dict(math_causes.most_common()),
    }


def build_options_audit_report(snapshots: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    values = snapshots if snapshots is not None else load_saved_option_snapshots()
    summary = summarize_options_data_quality(values)
    per_expiration: dict[str, Any] = {}
    for symbol, snapshot in values.items():
        chains = snapshot.get("chains", []) if isinstance(snapshot.get("chains"), list) else []
        for chain in chains:
            key = f"{symbol}:{chain.get('expiration_date')}"
            per_expiration[key] = diagnose_pairing_inputs(chain.get("series", []))
    return {"summary": summary, "pairing_by_expiration": per_expiration, "source": "saved_options_snapshots", "data_frequency": "EOD"}
