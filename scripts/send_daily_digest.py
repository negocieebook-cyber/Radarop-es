"""Envia o digest diário para o Telegram (uso manual ou GitHub Actions).

Uso:
    python scripts/send_daily_digest.py

Configuração: data/secrets/telegram.json (salvo pela aba Configurações > Rotinas)
ou variáveis de ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID.
O digest é informativo: resumo das rotinas e números do radar. Nenhuma ordem
é enviada e nenhuma recomendação é feita.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from app.notify_engine import load_telegram_config, send_daily_digest

    config = load_telegram_config()
    if not config.get("bot_token") or not config.get("chat_id"):
        print("Telegram não configurado: salve token e chat_id em data/secrets/telegram.json ou defina as variáveis de ambiente.")
        return 2
    result = send_daily_digest(config)
    if result.get("success"):
        print("Digest enviado com sucesso.")
        return 0
    print(f"Falha ao enviar digest: {result.get('error')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
