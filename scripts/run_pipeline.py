"""Executa o pipeline automático sem imprimir segredos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.pipeline_orchestrator import run_pipeline, summarize_pipeline_result  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline automático do Radar real EOD.")
    parser.add_argument("--mode", choices=("premarket", "intraday", "close"), default="close")
    parser.add_argument("--tickers", help="Tickers separados por vírgula")
    parser.add_argument("--max-expirations", type=int, default=4)
    parser.add_argument("--graphical-limit", type=int, default=30)
    args = parser.parse_args()
    tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()] if args.tickers else None
    result = run_pipeline(args.mode, tickers, args.max_expirations, args.graphical_limit)
    summary = summarize_pipeline_result(result)
    print(f"Modo: {summary['mode']}")
    print(f"Candidatas: {summary['total_candidates']}")
    print(f"Entradas condicionais: {summary['entrada_condicional']}")
    print(f"Acompanhar na abertura: {summary['acompanhar_na_abertura']}")
    print(f"Erros registrados: {summary['errors']}")
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
