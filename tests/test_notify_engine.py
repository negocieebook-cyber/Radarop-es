"""Auditoria do motor de notificações (Telegram) sem rede real."""

from __future__ import annotations

from app.notify_engine import (
    build_daily_digest,
    mask_token,
    send_message,
    telegram_status,
)


def test_mask_token() -> None:
    assert mask_token("") == "ausente"
    assert mask_token("12345678") == "********"
    assert mask_token("1234567890ABCDEFGHIJ").startswith("1234")
    assert mask_token("1234567890ABCDEFGHIJ").endswith("HIJ")
    assert "1234567890ABCDEFGHIJ" not in mask_token("1234567890ABCDEFGHIJ")


def test_send_message_without_config_fails_gracefully() -> None:
    result = send_message("teste", {"bot_token": "", "chat_id": ""})
    assert result["success"] is False
    assert "não configurado" in result["error"]


def test_status_reports_missing_config() -> None:
    status = telegram_status()
    assert "configured" in status
    assert "bot_token_masked" in status
    assert "não" not in status["bot_token_masked"]


def test_daily_digest_contains_honest_labels() -> None:
    text, meta = build_daily_digest()
    assert "Radar de Opções Brasil" in text
    assert "Digest informativo" in text
    assert "Nenhuma ordem é enviada" in text
    assert isinstance(meta, dict)
    assert "built_at" in meta
