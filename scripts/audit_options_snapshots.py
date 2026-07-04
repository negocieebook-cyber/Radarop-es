"""Audita os snapshots EOD salvos sem consultar a API."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.options_data_audit import build_options_audit_report  # noqa: E402


REPORT_FILE = ROOT / "data" / "runtime" / "options_data_audit_report.json"


def main() -> int:
    report = build_options_audit_report()
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = report["summary"]
    print(f"Ativos auditados: {summary['assets_audited']}")
    print(f"Séries totais: {summary['series_total']} (calls {summary['calls']}; puts {summary['puts']})")
    print(f"Vencimentos: {len(summary['expirations'])}")
    print(f"Com preço utilizável: {summary['with_usable_price']}; sem preço: {summary['without_usable_price']}")
    print(f"Com bid/ask: {summary['with_bid_ask']}; close: {summary['with_close']}; average: {summary['with_average']}")
    print(f"Com trades: {summary['with_trades']}; volume: {summary['with_volume']}")
    print("Campos raw mais comuns: " + ", ".join(list(summary["raw_field_inventory"])[:15]))
    print("Possíveis aliases: " + (", ".join(summary["possible_aliases"]) or "nenhum"))
    print("Causas de matemática incompleta: " + ("; ".join(f"{key}: {value}" for key, value in summary["math_incomplete_causes"].items()) or "nenhuma"))
    print(f"Relatório salvo: {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
