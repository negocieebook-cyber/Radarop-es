"""Registro de fontes futuras. Este módulo não realiza coleta de dados."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.data_quality import is_missing


REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "source_registry.json"
SOURCE_REQUIRED_FIELDS = (
    "id",
    "nome",
    "categoria",
    "tipo",
    "uso_previsto",
    "status",
    "custo",
    "frequencia_esperada",
    "confiabilidade",
    "observacao",
    "ultima_coleta",
    "campos_esperados",
)


def load_source_registry() -> list[dict[str, Any]]:
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def get_source_by_id(source_id: str) -> dict[str, Any] | None:
    return next((source for source in load_source_registry() if source.get("id") == source_id), None)


def list_sources_by_status(status: str | None = None) -> list[dict[str, Any]]:
    sources = load_source_registry()
    if is_missing(status):
        return sources
    return [source for source in sources if str(source.get("status", "")).casefold() == str(status).casefold()]


def validate_source_metadata(source: dict[str, Any]) -> dict[str, Any]:
    # ultima_coleta pode ser nula enquanto a fonte nunca tiver sido coletada.
    required_now = [field for field in SOURCE_REQUIRED_FIELDS if field != "ultima_coleta"]
    missing = [
        field
        for field in required_now
        if field not in source
        or source[field] is None
        or (isinstance(source[field], str) and not source[field].strip())
        or (isinstance(source[field], (list, dict)) and not source[field])
    ]
    if "ultima_coleta" not in source:
        missing.append("ultima_coleta")
    return {"valid": not missing, "missing_fields": missing, "source_id": source.get("id")}


def source_is_implemented(source_id: str) -> bool:
    source = get_source_by_id(source_id)
    return bool(source and str(source.get("status", "")).strip().lower() == "implementado")


def build_source_summary() -> dict[str, Any]:
    sources = load_source_registry()
    validations = [validate_source_metadata(source) for source in sources]
    return {
        "sources_registered": len(sources),
        "sources_implemented": sum(source_is_implemented(source.get("id", "")) for source in sources),
        "mock_sources": sum("mock" in str(source.get("status", "")).lower() for source in sources),
        "missing_metadata": sum(not result["valid"] for result in validations),
        "status": "mock/exemplo",
        "real_collection_enabled": False,
    }


def mark_source_status(source_id: str, status: str) -> bool:
    sources = load_source_registry()
    source = next((item for item in sources if item.get("id") == source_id), None)
    if source is None or is_missing(status):
        return False
    source["status"] = str(status).strip()
    temporary = REGISTRY_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(REGISTRY_PATH)
    return True
