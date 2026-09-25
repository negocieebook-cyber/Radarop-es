"""Helpers compartilhados entre páginas (sem dependência de app.py)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.components import render_data_notice
from app.notices import RISK_NOTICE


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def history_event(event_type: str, opportunity: dict, message: str) -> dict:
    return {
        "id": str(uuid4()),
        "tipo": event_type,
        "ativo": opportunity.get("ativo"),
        "estrategia": opportunity.get("estrategia") or opportunity.get("estrutura_opcao_sugerida"),
        "data_hora": now_iso(),
        "mensagem": message,
        "tipo_dado": opportunity.get("tipo_dado", "MOCK / EXEMPLO"),
    }


def money(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value) if value is not None else "não calculado por falta de dados"


def render_global_risk_notice() -> None:
    render_data_notice(RISK_NOTICE)
