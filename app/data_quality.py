"""Regras de qualidade, completude e linhagem dos dados."""

from __future__ import annotations

from typing import Any, Iterable


MISSING_TEXTS = {
    "",
    "indisponível",
    "indisponivel",
    "não calculado",
    "nao calculado",
    "não calculado por falta de dados",
    "nao calculado por falta de dados",
    "fonte ausente",
    "none",
    "null",
}

DATA_TYPES = {"coletado", "calculado", "estimado", "indisponível", "mock/exemplo"}
DATA_STATUSES = {"atualizado", "atrasado", "incompleto", "indisponível", "mock/exemplo"}


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in MISSING_TEXTS
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def classify_data_status(value: Any) -> str:
    if is_missing(value):
        return "indisponível"
    if isinstance(value, dict):
        explicit_status = str(value.get("status", "")).strip().lower()
        if explicit_status in DATA_STATUSES:
            return explicit_status
        explicit_type = str(value.get("data_type", value.get("tipo_dado", ""))).strip().lower()
        if explicit_type == "mock / exemplo" or explicit_type == "mock/exemplo":
            return "mock/exemplo"
    if isinstance(value, str) and "mock" in value.lower():
        return "mock/exemplo"
    return "atualizado"


def missing_fields(record: dict[str, Any], required_fields: Iterable[str]) -> list[str]:
    return [field for field in required_fields if field not in record or is_missing(record.get(field))]


def required_fields_present(record: dict[str, Any], required_fields: Iterable[str]) -> bool:
    return not missing_fields(record, required_fields)


def make_data_lineage(
    source: str | None,
    data_type: str | None,
    collected_at: str | None,
    status: str | None,
) -> dict[str, str | None]:
    normalized_type = (data_type or "indisponível").strip().lower().replace(" / ", "/")
    normalized_status = (status or "indisponível").strip().lower().replace(" / ", "/")
    return {
        "source": source if not is_missing(source) else None,
        "data_type": normalized_type if normalized_type in DATA_TYPES else "indisponível",
        "collected_at": collected_at if not is_missing(collected_at) else None,
        "status": normalized_status if normalized_status in DATA_STATUSES else "indisponível",
    }
