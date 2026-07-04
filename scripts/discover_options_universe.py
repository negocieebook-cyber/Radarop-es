"""Executa descoberta real de disponibilidade de opções sem imprimir token."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.options_universe_discovery import (  # noqa: E402
    discover_options_availability, get_available_option_tickers,
    load_option_candidate_tickers, load_options_universe_availability,
    save_options_universe_availability, summarize_options_availability,
    ticker_checked_recently,
)
from app.universe import load_asset_universe  # noqa: E402

FALLBACK = ["PETR4", "VALE3", "ITUB4", "BOVA11", "BBAS3", "BBDC4", "B3SA3", "ABEV3", "WEGE3", "PRIO3"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Descobre acesso real a opções EOD por ativo.")
    parser.add_argument("--tickers", help="Tickers separados por vírgula")
    parser.add_argument("--from-candidates", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=15)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--min-dte", type=int, default=7)
    parser.add_argument("--max-dte", type=int, default=60)
    parser.add_argument("--max-expirations", type=int, default=1)
    parser.add_argument("--include-low-liquidity", choices=("true", "false"), default="true")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size deve ser pelo menos 1")
    if args.tickers:
        tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()]
    elif args.from_candidates:
        tickers = load_option_candidate_tickers()
    else:
        tickers = [str(item.get("ticker", "")).upper() for item in load_asset_universe() if item.get("ticker")] or FALLBACK
    if args.limit is not None:
        tickers = tickers[:max(0, args.limit)]
    existing = load_options_universe_availability()
    existing_by_ticker = {item.get("ticker"): item for item in existing.get("assets", []) if item.get("ticker")}
    pending_run = [ticker for ticker in tickers if args.force or not ticker_checked_recently(existing_by_ticker.get(ticker, {}))]
    result = existing
    for start in range(0, len(pending_run), args.batch_size):
        batch = pending_run[start:start + args.batch_size]
        result = discover_options_availability(batch, args.min_dte, args.max_dte, args.max_expirations, incremental=True)
        print(f"Lote concluído: {start // args.batch_size + 1} · {len(batch)} ticker(s)")
    if not pending_run:
        result = existing
        print("Nenhum ticker pendente neste recorte; cache recente reaproveitado.")
    all_candidates = load_option_candidate_tickers()
    tested = {item.get("ticker") for item in result.get("assets", [])}
    result["candidate_tickers"] = all_candidates
    result["pending"] = [ticker for ticker in all_candidates if ticker not in tested]
    result["summary"] = summarize_options_availability(result)
    result["summary"].update(total_candidates=len(all_candidates), pending_count=len(result["pending"]))
    save_options_universe_availability(result)
    summary = result["summary"]
    print(f"Tickers testados: {summary['tickers_tested']}")
    print(f"Disponíveis: {summary['available_count']}")
    print("Ativos disponíveis: " + (", ".join(result["available"]) or "nenhum"))
    selected = get_available_option_tickers(include_low_liquidity=args.include_low_liquidity == "true")
    print("Ativos selecionados pelo cache: " + (", ".join(selected) or "nenhum"))
    print(f"Sem acesso/dados: {summary['unavailable_count']}")
    print(f"Erros registrados: {summary['error_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
