"""Notificações externas via Telegram: digest informativo diário.

Sem ordens, sem recomendações: o digest apenas resume o estado das rotinas
(mercado, opções, radar EOD, watchlist, posições e retrospectiva). O token do
bot fica salvo apenas em data/secrets/telegram.json e nunca é logado.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from app.formatting import format_dt
from app.options_update_orchestrator import load_options_eod_status
from app.pipeline_orchestrator import (
    load_pipeline_status,
    load_real_opportunities_snapshot,
)
from app.retrospective_engine import build_retrospective
from app.storage import load_json, load_positions, save_json
from app.update_orchestrator import load_update_status


ROOT = Path(__file__).resolve().parent.parent
TELEGRAM_CONFIG_PATH = ROOT / "data" / "secrets" / "telegram.json"
TELEGRAM_API_URL = "https://api.telegram.org"
DIGEST_NOTE = "Digest informativo. Nenhuma ordem é enviada e nenhum dado é publicado além deste canal."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_telegram_config() -> dict[str, Any]:
    config = load_json(TELEGRAM_CONFIG_PATH, {})
    if not isinstance(config, dict):
        config = {}
    if not config.get("bot_token"):
        config["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN") or ""
    if not config.get("chat_id"):
        config["chat_id"] = os.getenv("TELEGRAM_CHAT_ID") or ""
    return config


def save_telegram_config(bot_token: str, chat_id: str, enabled: bool = True) -> dict[str, Any]:
    if not bot_token or not str(bot_token).strip():
        raise ValueError("token do bot é obrigatório")
    if not chat_id or not str(chat_id).strip():
        raise ValueError("chat_id é obrigatório")
    config = {
        "bot_token": str(bot_token).strip(),
        "chat_id": str(chat_id).strip(),
        "enabled": bool(enabled),
        "saved_at": _now(),
    }
    save_json(TELEGRAM_CONFIG_PATH, config)
    return config


def clear_telegram_config() -> None:
    if TELEGRAM_CONFIG_PATH.exists():
        TELEGRAM_CONFIG_PATH.unlink()


def mask_token(token: str | None) -> str:
    value = str(token or "")
    if not value:
        return "ausente"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def telegram_status() -> dict[str, Any]:
    config = load_telegram_config()
    configured = bool(config.get("bot_token") and config.get("chat_id"))
    return {
        "configured": configured,
        "enabled": bool(config.get("enabled", True)),
        "chat_id": str(config.get("chat_id") or "") or "ausente",
        "bot_token_masked": mask_token(config.get("bot_token")),
        "source": "arquivo local" if TELEGRAM_CONFIG_PATH.exists() else "variáveis de ambiente",
        "saved_at": config.get("saved_at"),
        "observacao": "Token salvo apenas localmente; nunca é enviado para o log ou para terceiros.",
    }


def send_message(text: str, config: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    if config is None:
        config = load_telegram_config()
    token = str(config.get("bot_token") or "")
    chat_id = str(config.get("chat_id") or "")
    if not token or not chat_id:
        return {"success": False, "error": "Telegram não configurado (token ou chat_id ausente)", "status_code": None}
    try:
        response = requests.post(
            f"{TELEGRAM_API_URL}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text[:4000]},
            timeout=timeout,
        )
        payload: dict[str, Any] = {}
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code == 200 and payload.get("ok"):
            return {"success": True, "status_code": response.status_code, "error": None}
        description = payload.get("description") or f"HTTP {response.status_code}"
        return {"success": False, "error": f"Telegram recusou a mensagem: {description}", "status_code": response.status_code}
    except requests.Timeout:
        return {"success": False, "error": "timeout ao falar com o Telegram", "status_code": None}
    except requests.RequestException as exc:
        return {"success": False, "error": f"erro de conexão com o Telegram: {type(exc).__name__}", "status_code": None}


def _format_update_line(label: str, status: dict[str, Any]) -> str:
    if not status:
        return f"{label}: nenhuma atualização registrada"
    finished = format_dt(status.get("finished_at") or status.get("generated_at"), "indisponível")
    return (
        f"{label}: {status.get('status', 'indisponível')} · concluído {finished} · "
        f"fonte {status.get('source', 'indisponível')}"
    )


def build_daily_digest() -> tuple[str, dict[str, Any]]:
    market = load_update_status()
    options = (load_options_eod_status().get("last_update") or {})
    opportunities = load_real_opportunities_snapshot()
    pipeline = load_pipeline_status()
    retrospective = build_retrospective()
    summary = retrospective.get("summary", {})
    watchlist_counts = {status: sum(item.get("status") == status for item in retrospective.get("active", [])) for status in ("aguardando confirmação", "atenção", "invalidado", "inconclusivo")}
    positions = load_positions()
    lines = [
        "Radar de Opções Brasil — digest diário",
        "",
        _format_update_line("Mercado (EOD)", market),
        _format_update_line("Opções (EOD)", options),
        _format_update_line("Pipeline", pipeline),
    ]
    quotes_info = options.get("quotes_info") or {}
    if quotes_info:
        lines.append(
            f"Cotações no banco da fonte: {quotes_info.get('date_last_quotes_in_db') or 'indisponível'} · "
            f"coleta de hoje: {'sim' if quotes_info.get('has_todays_quotes') else 'não'}"
        )
    lines += [
        "",
        "Radar EOD (última rodada):",
        f"  estudar: {opportunities.get('estudar', 0) if opportunities else 'indisponível'} · atenção: {opportunities.get('atenção', 0) if opportunities else 'indisponível'} · evitar: {opportunities.get('evitar', 0) if opportunities else 'indisponível'} · inconclusivo: {opportunities.get('inconclusivo', 0) if opportunities else 'indisponível'}",
        f"  entrada condicional: {opportunities.get('entrada_condicional', 0) if opportunities else 'indisponível'} · acompanhar na abertura: {opportunities.get('acompanhar_na_abertura', 0) if opportunities else 'indisponível'}",
        "",
        "Watchlist da Abertura (em andamento): " + (", ".join(f"{key} {value}" for key, value in watchlist_counts.items()) or "vazia"),
        f"Posições registradas: {len(positions)}",
    ]
    if summary.get("vencidas"):
        lines.append(
            f"Retrospectiva: {summary.get('vencidas')} vencidas · ganhos estimados {summary.get('ganhos', 0)} · "
            f"perdas estimadas {summary.get('perdas', 0)}"
        )
    lines += ["", DIGEST_NOTE]
    meta = {
        "built_at": _now(),
        "market_status": (market or {}).get("status"),
        "options_status": options.get("status"),
        "pipeline_status": pipeline.get("status") if isinstance(pipeline, dict) else None,
        "opportunities_generated_at": (opportunities or {}).get("generated_at"),
    }
    return "\n".join(lines), meta


def send_daily_digest(config: dict[str, Any] | None = None) -> dict[str, Any]:
    if config is None:
        config = load_telegram_config()
    if not config.get("enabled", True):
        return {"success": False, "error": "notificações desativadas nas configurações", "status_code": None}
    text, meta = build_daily_digest()
    result = send_message(text, config)
    return {**result, "digest_meta": meta}
