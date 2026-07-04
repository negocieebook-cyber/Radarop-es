"""Executa manualmente uma atualização persistente do Radar de Mercado."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.update_orchestrator import (  # noqa: E402
    SNAPSHOTS_FILE,
    default_watchlist,
    run_market_update,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza snapshots reais do Radar de Mercado via brapi.")
    parser.add_argument("--mode", choices=("intraday", "premarket", "close"), default="intraday")
    parser.add_argument(
        "--runner",
        choices=("local_script", "github_actions"),
        default=None,
        help="Origem da execução; se omitida, detecta GITHUB_ACTIONS=true ou usa local_script",
    )
    parser.add_argument("--tickers", help="Tickers separados por vírgula")
    args = parser.parse_args()
    tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()] if args.tickers else default_watchlist()
    runner = args.runner or ("github_actions" if os.getenv("GITHUB_ACTIONS", "").lower() == "true" else "local_script")
    result = run_market_update(tickers=tickers, mode=args.mode, runner=runner)
    print(f"Modo: {result['mode']}")
    print(f"Runner: {result['runner']}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Atualizados: {result['updated_count']}")
    print(f"Incompletos: {result['incomplete_count']}")
    print(f"Erros: {result['error_count']}")
    print(f"Arquivo salvo: {SNAPSHOTS_FILE}")
    if result["errors"]:
        print("Detalhes: " + " | ".join(result["errors"]))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
