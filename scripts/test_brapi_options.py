"""Testa vencimentos e cadeia EOD da brapi sem expor credenciais."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.options_snapshot_engine import OPTIONS_SNAPSHOT_FILE, build_options_snapshot, summarize_options_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Testa opções EOD da brapi.")
    parser.add_argument("--underlying", default="PETR4")
    args = parser.parse_args()
    summary = summarize_options_snapshot(build_options_snapshot(args.underlying))
    print(f"Underlying: {summary['underlying']}")
    print(f"Success: {summary['success']}")
    print(f"Access status: {summary['access_status']}")
    print(f"Vencimentos: {summary['expiration_count']}")
    print(f"Vencimento usado: {summary['expiration_used'] or 'indisponível'}")
    print(f"Séries: {summary['series_count']}")
    print(f"Calls: {summary['calls']}")
    print(f"Puts: {summary['puts']}")
    if summary.get("error"):
        print(f"Erro: {summary['error']}")
    print(f"Arquivo salvo: {OPTIONS_SNAPSHOT_FILE}")
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
