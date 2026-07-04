"""Perfil operacional local usado apenas para classificação informativa de capital."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.storage import load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
USER_TRADING_PROFILE_PATH = PROJECT_ROOT / "data" / "runtime" / "user_trading_profile.json"
DEFAULT_TRADING_PROFILE = {
    "capital_disponivel": None,
    "perda_maxima_por_operacao": None,
    "percentual_maximo_por_operacao": None,
    "multiplicador_contrato_padrao": None,
    "usar_multiplicador_padrao_se_fonte_ausente": False,
    "tolerancia_capital": "moderada",
}


def load_user_trading_profile() -> dict[str, Any]:
    value = load_json(USER_TRADING_PROFILE_PATH, {})
    return {**DEFAULT_TRADING_PROFILE, **(value if isinstance(value, dict) else {})}


def save_user_trading_profile(profile: dict[str, Any]) -> None:
    tolerance = profile.get("tolerancia_capital")
    if tolerance not in {"moderada", "conservadora", "agressiva"}:
        raise ValueError("tolerância de capital inválida")
    save_json(USER_TRADING_PROFILE_PATH, {**DEFAULT_TRADING_PROFILE, **profile})
