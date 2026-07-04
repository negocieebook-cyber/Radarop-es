"""Carregamento e elegibilidade do universo MOCK / EXEMPLO."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


UNIVERSE_PATH = Path(__file__).resolve().parent.parent / "data" / "asset_universe_mock.json"
LIQUIDITY_RANK = {"indisponível": 0, "baixa": 1, "média": 2, "media": 2, "alta": 3}


def load_asset_universe() -> list[dict[str, Any]]:
    try:
        data = json.loads(UNIVERSE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def asset_is_eligible(asset: dict[str, Any]) -> dict[str, Any]:
    if not asset.get("tem_opcoes_mock"):
        return {"eligible": False, "status": "reprovado", "reason": "ativo sem opções mockadas"}
    liquidity = str(asset.get("liquidez_ativo_mock", "indisponível")).lower()
    if LIQUIDITY_RANK.get(liquidity, 0) <= 1:
        return {"eligible": False, "status": "reprovado", "reason": f"liquidez do ativo {liquidity}"}
    return {"eligible": True, "status": "elegível", "reason": "possui opções mockadas e liquidez mínima"}


def filter_optionable_assets(universe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**asset, "eligibility": asset_is_eligible(asset)} for asset in universe if asset.get("tem_opcoes_mock")]


def filter_by_asset_liquidity(universe: list[dict[str, Any]], min_status: str = "media") -> list[dict[str, Any]]:
    minimum = LIQUIDITY_RANK.get(min_status.lower(), 2)
    return [asset for asset in universe if LIQUIDITY_RANK.get(str(asset.get("liquidez_ativo_mock", "indisponível")).lower(), 0) >= minimum]


def get_asset_by_ticker(ticker: str) -> dict[str, Any] | None:
    return next((asset for asset in load_asset_universe() if asset.get("ticker") == ticker), None)


def build_universe_summary(universe: list[dict[str, Any]]) -> dict[str, int]:
    evaluations = [asset_is_eligible(asset) for asset in universe]
    return {
        "total_assets": len(universe),
        "with_mock_options": sum(bool(asset.get("tem_opcoes_mock")) for asset in universe),
        "eligible": sum(result["eligible"] for result in evaluations),
        "ineligible": sum(not result["eligible"] for result in evaluations),
    }
