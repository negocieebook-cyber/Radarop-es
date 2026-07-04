"""Contratos mínimos para validar dados sem preencher lacunas."""

from __future__ import annotations

from typing import Any, Iterable

from app.data_quality import missing_fields


ASSET_PRICE_CONTRACT = {
    "name": "AssetPriceContract",
    "required": ["ticker", "preco", "data_referencia", "fonte", "tipo_dado", "status_dado"],
    "optional": [],
}
OPTION_CONTRACT = {
    "name": "OptionContract",
    "required": ["codigo", "ativo_objeto", "tipo", "strike", "vencimento", "premio", "fonte", "tipo_dado", "status_dado"],
    "optional": ["bid", "ask", "volume", "posicao_em_aberto", "delta", "theta", "gamma", "vega", "iv"],
}
GRAPH_SNAPSHOT_CONTRACT = {
    "name": "GraphSnapshotContract",
    "required": ["ativo", "preco_atual", "tendencia", "fonte", "tipo_dado", "status_dado"],
    "optional": ["suporte", "resistencia", "rsi", "atr_percent", "rvol", "adr_percent", "volatilidade_implicita"],
}
OPPORTUNITY_CONTRACT = {
    "name": "OpportunityContract",
    "required": ["id", "ativo", "estrategia", "tipo_estrutura", "vencimento_dias", "fonte", "tipo_dado", "status_dado"],
    "optional": ["score", "ganho_maximo", "perda_maxima", "break_even", "liquidez_status", "grafico_status", "healthbox_status", "bulkowski_status"],
}
POSITION_CONTRACT = {
    "name": "PositionContract",
    "required": ["id", "opportunity_id", "ativo", "estrategia", "data_entrada", "preco_real_entrada", "quantidade", "status", "tipo_dado"],
    "optional": [],
}

CONTRACTS = {
    "Ativo": ASSET_PRICE_CONTRACT,
    "Opção": OPTION_CONTRACT,
    "Snapshot gráfico": GRAPH_SNAPSHOT_CONTRACT,
    "Oportunidade": OPPORTUNITY_CONTRACT,
    "Posição": POSITION_CONTRACT,
}


def validate_contract(record: dict[str, Any], required_fields: Iterable[str], record_type: str = "record") -> dict[str, Any]:
    missing = missing_fields(record, required_fields)
    return {"valid": not missing, "missing_fields": missing, "record_type": record_type}


def validate_asset_price(record: dict[str, Any]) -> dict[str, Any]:
    return validate_contract(record, ASSET_PRICE_CONTRACT["required"], ASSET_PRICE_CONTRACT["name"])


def validate_option(record: dict[str, Any]) -> dict[str, Any]:
    return validate_contract(record, OPTION_CONTRACT["required"], OPTION_CONTRACT["name"])


def validate_graph_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    return validate_contract(record, GRAPH_SNAPSHOT_CONTRACT["required"], GRAPH_SNAPSHOT_CONTRACT["name"])


def validate_opportunity(record: dict[str, Any]) -> dict[str, Any]:
    return validate_contract(record, OPPORTUNITY_CONTRACT["required"], OPPORTUNITY_CONTRACT["name"])


def validate_position(record: dict[str, Any]) -> dict[str, Any]:
    return validate_contract(record, POSITION_CONTRACT["required"], POSITION_CONTRACT["name"])
