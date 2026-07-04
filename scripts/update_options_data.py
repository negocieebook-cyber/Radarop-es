"""Executa a coleta multiativos de opções EOD sem expor credenciais."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.options_update_orchestrator import default_options_watchlist, run_options_update  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza snapshots EOD de opções via brapi.")
    parser.add_argument("--mode", default="close")
    parser.add_argument("--underlyings", help="Ativos separados por vírgula")
    parser.add_argument("--min-dte", type=int, default=7)
    parser.add_argument("--max-dte", type=int, default=60)
    parser.add_argument("--max-expirations", type=int, default=4)
    args = parser.parse_args()
    symbols = [item.strip().upper() for item in args.underlyings.split(",") if item.strip()] if args.underlyings else default_options_watchlist()
    result = run_options_update(symbols, mode=args.mode, max_expirations=args.max_expirations, min_dte=args.min_dte, max_dte=args.max_dte)
    print(f"Modo: {result['mode']}")
    print(f"Ativos consultados: {result['total_underlyings']} ({', '.join(result['underlyings'])})")
    print(f"Ativos disponíveis: {result['available_count']}")
    print(f"Ativos indisponíveis: {result['unavailable_count']}")
    print(f"Erros: {result['error_count']}")
    print(f"Vencimentos encontrados: {result['expirations_found']}")
    print(f"Vencimentos selecionados: {result['expirations_selected']}")
    for expiration, count in result["series_by_expiration"].items():
        print(f"Séries em {expiration}: {count}")
    print(f"Total de séries: {result['total_series']}")
    print(f"Calls: {result['total_calls']}")
    print(f"Puts: {result['total_puts']}")
    print(f"Arquivos salvos: {len(result['saved_files'])}")
    if result["errors"]:
        print("Motivos: " + " | ".join(result["errors"]))
    print("Opportunity Engine: MOCK / EXEMPLO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
