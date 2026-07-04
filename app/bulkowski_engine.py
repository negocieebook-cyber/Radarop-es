"""Catálogo e análise estrutural Bulkowski, exclusivamente MOCK / EXEMPLO."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.data_quality import is_missing


PATTERNS_PATH = Path(__file__).resolve().parent.parent / "data" / "bulkowski_patterns_mock.json"
UNAVAILABLE = "indisponível"
MOCK_TYPE = "MOCK / EXEMPLO"


def load_bulkowski_patterns() -> list[dict[str, Any]]:
    try:
        data = json.loads(PATTERNS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def list_patterns() -> list[dict[str, Any]]:
    return load_bulkowski_patterns()


def get_pattern_by_id(pattern_id: str | None) -> dict[str, Any] | None:
    if is_missing(pattern_id):
        return None
    return next((item for item in load_bulkowski_patterns() if item.get("id") == pattern_id), None)


def filter_patterns(
    category: str | None = None,
    tipo: str | None = None,
    direcao: str | None = None,
) -> list[dict[str, Any]]:
    filters = {"categoria": category, "tipo": tipo, "direcao_teorica": direcao}
    return [
        pattern
        for pattern in load_bulkowski_patterns()
        if all(
            is_missing(expected)
            or str(pattern.get(field, "")).casefold() == str(expected).casefold()
            for field, expected in filters.items()
        )
    ]


def _not_detected() -> dict[str, Any]:
    return {
        "pattern_detected": False,
        "pattern": None,
        "status": "padrão não detectado",
        "tipo_dado": MOCK_TYPE,
    }


def detect_mock_pattern(asset_snapshot: dict[str, Any]) -> dict[str, Any]:
    pattern = get_pattern_by_id(asset_snapshot.get("mock_pattern_id"))
    if pattern is None:
        return _not_detected()
    return {
        "pattern_detected": True,
        "pattern": pattern,
        "status": "exemplo estrutural",
        "tipo_dado": MOCK_TYPE,
    }


def _state(value: Any, yes: str, no: str) -> str:
    if is_missing(value):
        return UNAVAILABLE
    return yes if value is True else no


def analyze_pattern_for_asset(asset_snapshot: dict[str, Any]) -> dict[str, Any]:
    detected = detect_mock_pattern(asset_snapshot)
    asset = asset_snapshot.get("ativo") or UNAVAILABLE
    if not detected["pattern_detected"]:
        return {
            "ativo": asset,
            "pattern_detected": False,
            "nome_padrao": "padrão não detectado",
            "categoria": UNAVAILABLE,
            "tipo": UNAVAILABLE,
            "direcao_teorica": UNAVAILABLE,
            "confirmacao": UNAVAILABLE,
            "rompimento": UNAVAILABLE,
            "pullback_throwback": UNAVAILABLE,
            "alvo_tecnico_metodo": UNAVAILABLE,
            "taxa_falha": UNAVAILABLE,
            "movimento_medio_pos_rompimento": UNAVAILABLE,
            "confiabilidade": UNAVAILABLE,
            "volume_confirma": UNAVAILABLE,
            "leitura": "não usar leitura gráfica como confirmação",
            "status": "padrão não detectado",
            "fonte_nome": UNAVAILABLE,
            "fonte_url": UNAVAILABLE,
            "tipo_dado": MOCK_TYPE,
            "status_dado": "não coletado",
        }

    pattern = detected["pattern"]
    breakout = _state(asset_snapshot.get("rompimento_confirmado"), "confirmado", "não confirmado")
    volume = _state(asset_snapshot.get("volume_confirma"), "confirma", "não confirma")
    pullback = _state(asset_snapshot.get("pullback_detectado"), "detectado", "não detectado")
    confirmed = breakout == "confirmado" and volume == "confirma"
    confirmation = "confirmado no mock" if confirmed else "inconclusivo no mock"
    direction = pattern.get("direcao_teorica", UNAVAILABLE)
    reading = (
        f"Padrão MOCK / EXEMPLO {pattern.get('nome')}; direção teórica {direction}. "
        + ("Rompimento e volume confirmam apenas o cenário mockado." if confirmed else "Sem confirmação conjunta de rompimento e volume.")
    )
    return {
        "ativo": asset,
        "pattern_detected": True,
        "nome_padrao": pattern.get("nome", UNAVAILABLE),
        "categoria": pattern.get("categoria", UNAVAILABLE),
        "tipo": pattern.get("tipo", UNAVAILABLE),
        "direcao_teorica": direction,
        "confirmacao": confirmation,
        "rompimento": breakout,
        "pullback_throwback": f"{pattern.get('pullback_throwback', UNAVAILABLE)}; snapshot: {pullback}",
        "alvo_tecnico_metodo": pattern.get("alvo_tecnico_metodo", UNAVAILABLE),
        "taxa_falha": pattern.get("taxa_falha", UNAVAILABLE),
        "movimento_medio_pos_rompimento": pattern.get("movimento_medio_pos_rompimento", UNAVAILABLE),
        "confiabilidade": pattern.get("confiabilidade", UNAVAILABLE),
        "volume_confirma": volume,
        "leitura": reading,
        "status": "exemplo estrutural" if confirmed else "inconclusivo",
        "fonte_nome": pattern.get("fonte_nome", UNAVAILABLE),
        "fonte_url": pattern.get("fonte_url", UNAVAILABLE),
        "tipo_dado": MOCK_TYPE,
        "status_dado": pattern.get("status_dado", "não coletado"),
    }


def build_bulkowski_summary(asset_snapshot: dict[str, Any]) -> dict[str, Any]:
    analysis = analyze_pattern_for_asset(asset_snapshot)
    if not analysis["pattern_detected"]:
        return {
            "ativo": analysis["ativo"],
            "resumo": "Bulkowski: inconclusivo por falta de dados.",
            "favorece_alta": None,
            "favorece_baixa": None,
            "status": analysis["status"],
            "tipo_dado": MOCK_TYPE,
        }
    direction = str(analysis["direcao_teorica"]).lower()
    confirmed = analysis["confirmacao"] == "confirmado no mock"
    return {
        "ativo": analysis["ativo"],
        "resumo": analysis["leitura"],
        "favorece_alta": confirmed and "alta" in direction,
        "favorece_baixa": confirmed and "baixa" in direction,
        "status": analysis["status"],
        "tipo_dado": MOCK_TYPE,
    }
