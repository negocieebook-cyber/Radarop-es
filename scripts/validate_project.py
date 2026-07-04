"""Validação local do núcleo, sem rede e sem coleta de dados."""

from __future__ import annotations

import json
import sys
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data_quality import make_data_lineage  # noqa: E402
from app.data_contracts import (  # noqa: E402
    validate_asset_price,
    validate_graph_snapshot,
    validate_opportunity,
    validate_option,
)
from app.bulkowski_engine import analyze_pattern_for_asset, list_patterns  # noqa: E402
from app.cache import clear_cache, is_cache_fresh, load_cache, save_cache  # noqa: E402
from app.healthbox_engine import build_healthbox, healthbox_confirms_strategy, healthbox_score  # noqa: E402
from app.market_snapshot_engine import build_asset_snapshot_from_data, snapshot_to_healthbox  # noqa: E402
from app.mock_data import MOCK_ASSET_SNAPSHOTS, MOCK_MARKET_CONTEXT, MOCK_OPPORTUNITIES  # noqa: E402
from app.options_math import calculate_option_strategy  # noqa: E402
from app.opportunity_engine import (  # noqa: E402
    generate_daily_opportunities,
    load_options_chain,
    split_opportunities_by_status,
)
from app.position_monitor import (  # noqa: E402
    build_opening_position_status,
    build_position_status,
    calculate_gain_capture,
    calculate_position_pnl,
    generate_exit_alerts,
)
from app.opening_watchlist import (  # noqa: E402
    OPENING_WATCHLIST_PATH,
    build_manual_position,
    mark_as_converted,
    save_opening_watchlist,
)
from app.storage import POSITIONS_PATH, add_position, load_positions, save_positions  # noqa: E402
from app.pipeline_orchestrator import (  # noqa: E402
    GRAPHICAL_THESES_FILE,
    PIPELINE_STATUS_FILE,
    REAL_OPPORTUNITIES_FILE,
    load_real_opportunities_snapshot,
    run_pipeline,
)
from app.graphical_thesis_engine import (  # noqa: E402
    build_graphical_thesis,
    rank_graphical_theses,
    summarize_graphical_theses,
)
from app.graphical_diagnostics import rank_near_setups, summarize_graphical_diagnostics  # noqa: E402
from app.graphical_watchlist import (  # noqa: E402
    GRAPHICAL_WATCHLIST_PATH,
    add_to_graphical_watchlist,
    evaluate_graphical_watchlist_item,
    load_graphical_watchlist,
    save_graphical_watchlist,
    summarize_graphical_watchlist,
)
from app.strategy_mapper import (  # noqa: E402
    build_strategy_mapping,
    classify_market_regime,
    rank_strategy_candidates,
    suggest_directional_strategies,
    suggest_lateral_strategies,
    suggest_strategy_family,
    suggest_volatility_strategies,
)
from app.options_strategy_catalog import get_strategy_catalog  # noqa: E402
from app.strategy_screener import (  # noqa: E402
    build_manual_validation_plan,
    evaluate_strategy_for_thesis,
    load_strategy_catalog,
    rank_strategy_candidates as rank_screened_strategies,
    screen_strategies_for_thesis,
    summarize_strategy_screening,
)
from app.practical_strategy_view import (  # noqa: E402
    build_practical_strategy_summary,
    select_best_strategy_for_thesis,
    select_top_strategies_for_thesis,
    summarize_strategy_for_user,
)
from app.strategy_objective import (  # noqa: E402
    build_strategy_objective_label,
    classify_strategy_objective,
    summarize_objectives_for_thesis,
)
from app.daily_priority_engine import (  # noqa: E402
    build_daily_priority_list,
    classify_practical_priority,
    rank_by_objective,
    summarize_daily_priorities,
)
from app.practical_strategy_view import matches_quick_objective_filter  # noqa: E402
from app.capital_requirements import (  # noqa: E402
    classify_capital_fit,
    estimate_margin_proxy,
    estimate_max_loss_required,
    estimate_minimum_technical_capital,
    estimate_recommended_capital,
    estimate_strategy_capital_required,
    explain_capital_requirement,
)
from app.user_trading_profile import DEFAULT_TRADING_PROFILE, load_user_trading_profile  # noqa: E402
from app.manual_trade_simulator import (  # noqa: E402
    MANUAL_SIMULATIONS_PATH,
    SUPPORTED_STRATEGIES,
    build_manual_simulation_from_strategy,
    calculate_manual_strategy_risk,
    classify_manual_simulation_fit,
    delete_manual_simulation,
    list_manual_simulations,
    load_manual_simulations,
    save_manual_simulation,
)
from app.options_universe_discovery import (  # noqa: E402
    AVAILABILITY_FILE,
    discover_options_availability,
    get_available_option_tickers,
    load_options_universe_availability,
    save_options_universe_availability,
)
from app.providers.brapi_provider import BrapiProvider  # noqa: E402
from app.providers.brapi_options_provider import (  # noqa: E402
    BrapiOptionsProvider,
    normalize_side,
    pick_first_available,
    to_float_or_none,
    to_int_or_none,
)
from app.options_snapshot_engine import summarize_options_snapshot  # noqa: E402
from app.options_update_orchestrator import (  # noqa: E402
    OPTIONS_SNAPSHOTS_DIR,
    load_options_snapshot_for_asset,
    save_options_snapshot_for_asset,
    summarize_options_snapshots,
    _select_expirations,
)
from app.real_opportunity_engine import (  # noqa: E402
    EOD_WARNING,
    _indicative_price,
    resolve_option_price,
    build_real_candidates_for_asset,
    evaluate_real_candidate,
    pair_real_call_debit_spreads,
    summarize_real_opportunities,
)
from app.options_data_audit import (  # noqa: E402
    audit_option_series_fields,
    build_options_audit_report,
    find_possible_field_aliases,
)
from app.conditional_entry_engine import (  # noqa: E402
    build_confirmation_rules,
    build_invalidation_rules,
    calculate_entry_conditions,
    calculate_max_debit_allowed,
    calculate_min_credit_required,
    candidate_has_complete_math,
    candidate_has_usable_price,
    identify_hard_blockers,
    identify_soft_warnings,
    rank_conditional_entries,
    summarize_conditional_entries,
)
from app.funnel_diagnostics import (  # noqa: E402
    count_rejection_reasons,
    find_near_miss_candidates,
    summarize_real_eod_funnel,
    what_needs_to_change,
)
from app.scoring import score_opportunity  # noqa: E402
from app.source_registry import (  # noqa: E402
    build_source_summary,
    load_source_registry,
    validate_source_metadata,
)
from app.technical_indicators import (  # noqa: E402
    calculate_adr_percent,
    calculate_atr_percent,
    calculate_relative_volume,
    calculate_rsi,
    calculate_support_resistance,
    classify_trend,
)
from app.validators import build_operation_checklist  # noqa: E402
from app.universe import build_universe_summary, load_asset_universe  # noqa: E402
from app.update_orchestrator import (  # noqa: E402
    SNAPSHOTS_FILE,
    STATUS_FILE,
    load_market_snapshots,
    load_update_status,
    save_market_snapshots,
    save_update_status,
    should_update,
    summarize_snapshots,
)


def validate() -> int:
    print("VALIDAÇÃO DO RADAR — SOMENTE MOCK / EXEMPLO")
    for opportunity in MOCK_OPPORTUNITIES:
        calculation = calculate_option_strategy(opportunity)
        snapshot = next(
            item
            for item in MOCK_ASSET_SNAPSHOTS
            if item["ativo"] == opportunity["ativo"]
        )
        healthbox = build_healthbox(snapshot)
        evaluated = {
            **opportunity,
            "calculation": calculation,
            "healthbox": healthbox,
            "healthbox_score_result": healthbox_score(healthbox),
            "healthbox_confirmation": healthbox_confirms_strategy(
                healthbox, opportunity["tipo_estrutura"]
            ),
        }
        checklist = build_operation_checklist(evaluated)
        score = score_opportunity(evaluated)
        lineage = make_data_lineage(
            opportunity.get("fonte"),
            opportunity.get("tipo_dado"),
            opportunity.get("coleta"),
            "mock/exemplo",
        )
        output = {
            "ativo": opportunity.get("ativo"),
            "tipo_estrutura": opportunity.get("tipo_estrutura"),
            "calculo_ok": calculation["can_calculate"],
            "campos_ausentes": calculation["missing_fields"],
            "por_unidade": calculation["per_unit"],
            "por_lote": calculation["per_lot"],
            "score": score,
            "checklist_status": {
                item["question"]: item["status"] for item in checklist
            },
            "linhagem": lineage,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    incomplete = dict(MOCK_OPPORTUNITIES[0])
    incomplete.pop("fonte", None)
    incomplete_score = score_opportunity(incomplete)
    assert incomplete_score["score"] is None
    assert "fonte" in incomplete_score["missing_fields"]
    print(
        json.dumps(
            {"teste_dado_ausente": "ok", "resultado": incomplete_score},
            ensure_ascii=False,
            indent=2,
        )
    )
    patterns = list_patterns()
    assert patterns
    for pattern in patterns:
        assert pattern["taxa_falha"] == "indisponível"
        assert pattern["movimento_medio_pos_rompimento"] == "indisponível"
    analyses = [analyze_pattern_for_asset(snapshot) for snapshot in MOCK_ASSET_SNAPSHOTS]
    bova = next(item for item in analyses if item["ativo"] == "BOVA11")
    assert not bova["pattern_detected"]
    print(
        json.dumps(
            {
                "bulkowski_patterns_loaded": len(patterns),
                "analises": [
                    {
                        "ativo": item["ativo"],
                        "padrao": item["nome_padrao"],
                        "status": item["status"],
                        "taxa_falha": item["taxa_falha"],
                    }
                    for item in analyses
                ],
                "estatisticas_reais_inventadas": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    strategy_by_asset = {
        "PETR4": "call_debit_spread",
        "VALE3": "bull_put_spread",
        "ITUB4": "covered_call",
        "BOVA11": "put_debit_spread",
        "ABEV3": "covered_call",
    }
    healthbox_outputs = []
    for snapshot in MOCK_ASSET_SNAPSHOTS:
        healthbox = build_healthbox(snapshot)
        health_score = healthbox_score(healthbox)
        confirmation = healthbox_confirms_strategy(
            healthbox, strategy_by_asset[snapshot["ativo"]]
        )
        healthbox_outputs.append(
            {
                "ativo": snapshot["ativo"],
                "score": health_score,
                "confirmacao": confirmation,
                "campos_ausentes": healthbox["campos_ausentes"],
                "tipo_dado": healthbox["tipo_dado"],
            }
        )
    abev = next(item for item in healthbox_outputs if item["ativo"] == "ABEV3")
    assert abev["score"]["score"] is None
    assert abev["campos_ausentes"]
    assert abev["confirmacao"] == "indisponível por falta de dados"
    print(
        json.dumps(
            {"healthbox_validation": "ok", "ativos": healthbox_outputs},
            ensure_ascii=False,
            indent=2,
        )
    )
    sources = load_source_registry()
    source_validations = [validate_source_metadata(source) for source in sources]
    source_summary = build_source_summary()
    assert sources
    assert all(result["valid"] for result in source_validations)
    assert all(source["ultima_coleta"] is None for source in sources)
    assert source_summary["sources_implemented"] == 1
    assert source_summary["real_collection_enabled"] is False

    asset_contracts = [
        validate_asset_price(
            {
                "ticker": snapshot["ativo"],
                "preco": snapshot["preco_atual"],
                "data_referencia": snapshot["coleta"],
                "fonte": snapshot["fonte"],
                "tipo_dado": snapshot["tipo_dado"],
                "status_dado": snapshot["status_dado"],
            }
        )
        for snapshot in MOCK_ASSET_SNAPSHOTS
    ]
    graph_contracts = [validate_graph_snapshot(snapshot) for snapshot in MOCK_ASSET_SNAPSHOTS]
    opportunity_contracts = [validate_opportunity(item) for item in MOCK_OPPORTUNITIES]
    petr = MOCK_OPPORTUNITIES[0]
    option_contract = validate_option(
        {
            "codigo": "PETR4_CALL_MOCK",
            "ativo_objeto": petr["ativo"],
            "tipo": "call",
            "strike": petr["strike_comprado"],
            "vencimento": f"{petr['vencimento_dias']} dias (mock)",
            "premio": petr["premio_pago"],
            "fonte": petr["fonte"],
            "tipo_dado": petr["tipo_dado"],
            "status_dado": petr["status_dado"],
        }
    )
    contract_results = [*asset_contracts, *graph_contracts, *opportunity_contracts, option_contract]
    assert all(result["valid"] for result in contract_results)
    print(
        json.dumps(
            {
                "source_registry_validation": "ok",
                "summary": source_summary,
                "metadata_incomplete": [
                    result for result in source_validations if not result["valid"]
                ],
                "contracts_validated": len(contract_results),
                "real_collection_performed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    monitor_positions = [
        {
            "id": "monitor-petr4-mock",
            "ativo": "PETR4",
            "estrategia": "Trava de alta",
            "tipo_estrutura": "call_debit_spread",
            "preco_real_entrada": 0.42,
            "quantidade": 100,
            "ganho_maximo_por_unidade": 1.58,
            "perda_maxima_por_unidade": 0.42,
            "vencimento_dias": 28,
            "strikes": {"comprado": 37.0, "vendido": 39.0},
            "tipo_dado": "MOCK / EXEMPLO",
        },
        {
            "id": "monitor-vale3-mock",
            "ativo": "VALE3",
            "estrategia": "Put travada",
            "tipo_estrutura": "bull_put_spread",
            "preco_real_entrada": 0.45,
            "quantidade": 100,
            "ganho_maximo_por_unidade": 0.45,
            "perda_maxima_por_unidade": 1.55,
            "vencimento_dias": 21,
            "strikes": {"comprado": 60.0, "vendido": 62.0},
            "tipo_dado": "MOCK / EXEMPLO",
        },
        {
            "id": "monitor-bova11-mock",
            "ativo": "BOVA11",
            "estrategia": "Trava de alta",
            "tipo_estrutura": "call_debit_spread",
            "preco_real_entrada": 0.76,
            "quantidade": 100,
            "ganho_maximo_por_unidade": 1.24,
            "perda_maxima_por_unidade": 0.76,
            "vencimento_dias": 7,
            "strikes": {"comprado": 128.0, "vendido": 130.0},
            "tipo_dado": "MOCK / EXEMPLO",
        },
    ]
    pnl_test = calculate_position_pnl(monitor_positions[0], MOCK_MARKET_CONTEXT["PETR4"]["current_mark"])
    capture_test = calculate_gain_capture(monitor_positions[0], MOCK_MARKET_CONTEXT["PETR4"]["current_mark"])
    assert pnl_test["calculated"] and capture_test["calculated"]
    monitor_alerts = generate_exit_alerts(monitor_positions, MOCK_MARKET_CONTEXT)
    statuses = {item["ativo"]: item["status"] for item in monitor_alerts}
    assert statuses["PETR4"] == "realizar parcial"
    assert statuses["VALE3"] in {"atenção", "vencimento próximo"}
    assert statuses["BOVA11"] in {"tese invalidada", "sair agora"}
    assert len(set(statuses.values())) == 3
    no_context = build_position_status(monitor_positions[0], None)
    assert no_context["status"] == "inconclusivo por falta de dados"
    incomplete_position = {
        "id": "incomplete-mock",
        "ativo": "PETR4",
        "tipo_estrutura": "call_debit_spread",
        "quantidade": 100,
        "strikes": {"vendido": 39.0},
    }
    missing_result = build_position_status(incomplete_position, MOCK_MARKET_CONTEXT["PETR4"])
    assert missing_result["status"] == "inconclusivo por falta de dados"
    opening_position = {
        "id": "opening-position-real-context", "origem": "opening_watchlist", "data_frequency": "EOD",
        "ativo": "PETR4", "tipo_estrutura": "call_debit_spread", "preco_real_entrada": 0.55,
        "preco_eod_referencia": 0.50, "quantidade": 100, "vencimento_dias": 30,
        "strikes": {"comprado": 37.0, "vendido": 39.0}, "fonte": "brapi",
        "tipo_dado": "DADOS REAIS EOD / EXPERIMENTAL", "invalidation_rules": ["perda do suporte"],
    }
    favorable_context = {
        "asset_snapshot": {"ativo": "PETR4", "preco_atual": 38.0, "suporte": 37.0, "resistencia": 40.0, "status_dado": "atualizado", "coleta": "2026-07-02T10:00:00-03:00"},
        "healthbox": {"confirmation": "confirma", "rvol": 1.2}, "current_mark": None,
        "tipo_dado": "DADOS REAIS", "fonte": "brapi",
    }
    opening_favorable = build_opening_position_status(opening_position, favorable_context)
    assert opening_favorable["status"] == "manter em acompanhamento"
    assert opening_favorable["pnl"]["calculated"] is False
    assert opening_favorable["pnl"]["reason"] == "sem preço intraday da estrutura"
    assert opening_favorable["pnl"]["eod_used_as_current_mark"] is False
    opening_without_snapshot = build_opening_position_status(opening_position, None)
    assert opening_without_snapshot["status"] == "inconclusivo por falta de dados"
    lost_support_context = {**favorable_context, "asset_snapshot": {**favorable_context["asset_snapshot"], "preco_atual": 36.5}}
    opening_lost_support = build_opening_position_status(opening_position, lost_support_context)
    assert opening_lost_support["status"] == "tese invalidada" and opening_lost_support["severity"] == "vermelho"
    near_expiry_position = {**opening_position, "vencimento_dias": 7}
    opening_near_expiry = build_opening_position_status(near_expiry_position, favorable_context)
    assert opening_near_expiry["status"] == "vencimento próximo"
    print(
        json.dumps(
            {
                "position_monitor_validation": "ok",
                "results": [
                    {
                        "ativo": item["ativo"],
                        "status": item["status"],
                        "motivo": item["reason"],
                        "campos_ausentes": item.get("details", {}).get("missing_fields", []),
                    }
                    for item in monitor_alerts
                ],
                "sem_contexto": no_context,
                "dado_ausente": missing_result,
                "opening_watchlist_real_monitor": {
                    "favoravel": opening_favorable["status"],
                    "sem_snapshot": opening_without_snapshot["status"],
                    "suporte_perdido": opening_lost_support["status"],
                    "vencimento": opening_near_expiry["status"],
                    "pnl_opcao": opening_favorable["option_pnl_label"],
                    "eod_usado_como_marcacao": opening_favorable["eod_used_as_current_mark"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    file_backups = {
        path: path.read_bytes() if path.exists() else None
        for path in (OPENING_WATCHLIST_PATH, POSITIONS_PATH)
    }
    try:
        watch_item = {
            "id": "opening-validation-item",
            "candidate_id": "validation-item",
            "ativo": "PETR4",
            "estrategia": "Trava de alta",
            "tipo_estrutura": "call_debit_spread",
            "vencimento": "2026-08-21",
            "vencimento_dias": 50,
            "strikes": {"comprado": 37.0, "vendido": 39.0},
            "preco_eod_referencia": 0.42,
            "perda_maxima": 0.42,
            "ganho_maximo": 1.58,
            "break_even": 37.42,
            "risk_reward": 3.7619,
            "confirmation_rules": ["confirmar preço no pregão"],
            "invalidation_rules": ["não registrar sem preço real"],
            "fonte": "fixture local de validação",
            "coleta": None,
            "tipo_dado": "FIXTURE DE TESTE",
            "data_frequency": "EOD",
            "status": "aguardando confirmação",
        }
        save_opening_watchlist([watch_item])
        save_positions([])
        manual = build_manual_position(
            watch_item, 0.45, 100, "2026-07-02T10:15:00-03:00", "validação local"
        )
        assert manual["preco_real_entrada"] == 0.45 and manual["quantidade"] == 100
        assert manual["origem"] == "opening_watchlist"
        assert add_position(manual) is True
        assert add_position(manual) is False
        assert len(load_positions()) == 1
        assert mark_as_converted(watch_item["id"], manual["id"], manual["created_at"])
        converted = json.loads(OPENING_WATCHLIST_PATH.read_text(encoding="utf-8"))[0]
        assert converted["status"] == "entrada registrada" and converted["position_id"] == manual["id"]
        try:
            build_manual_position(watch_item, 0, 100, "2026-07-02T10:15:00-03:00")
            raise AssertionError("preço zero não foi bloqueado")
        except ValueError:
            pass
        print(json.dumps({
            "manual_opening_entry_validation": "ok",
            "position_saved": True,
            "duplicate_blocked": True,
            "watchlist_marked_converted": True,
            "zero_price_blocked": True,
            "orders_sent": False,
        }, ensure_ascii=False, indent=2))
    finally:
        for path, content in file_backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
    pipeline_backups = {
        path: path.read_bytes() if path.exists() else None
        for path in (
            REAL_OPPORTUNITIES_FILE,
            PIPELINE_STATUS_FILE,
            GRAPHICAL_THESES_FILE,
            GRAPHICAL_WATCHLIST_PATH,
        )
    }
    pipeline_candidates = [
        {"ativo": "PETR4", "conditional_status": "entrada_condicional", "score": 80, "liquidez": "alta", "risco_retorno": 2.0},
        {"ativo": "VALE3", "conditional_status": "acompanhar_na_abertura", "score": 70, "liquidez": "média", "risco_retorno": 1.5},
        {"ativo": "ITUB4", "conditional_status": "evitar", "score": 40},
        {"ativo": "BOVA11", "conditional_status": "inconclusivo", "score": None},
    ]
    health_fixture = {"tendencia": "alta", "rsi": 50, "rvol": 1.2, "suporte": 10, "resistencia": 14, "preco_atual": 10.2, "atr_percent": 2, "adr_percent": 2, "distancia_suporte_percent": 1.96, "distancia_resistencia_percent": 37.25, "campos_ausentes": []}
    bulk_fixture = {"pattern_detected": False, "nome_padrao": "padrão não detectado", "status": "padrão não detectado"}
    graphical_cases = [
        build_graphical_thesis({"ativo": "ALTA3", "preco_atual": 10.2, "suporte": 10, "resistencia": 14, "tendencia": "alta", "fonte": "fixture"}, health_fixture, bulk_fixture),
        build_graphical_thesis({"ativo": "IALT3", "preco_atual": 12, "suporte": 10, "resistencia": 14, "tendencia": "alta", "fonte": "fixture"}, {**health_fixture, "preco_atual": 12, "rvol": 0.5}, bulk_fixture),
        build_graphical_thesis({"ativo": "BAIX3", "preco_atual": 13.8, "suporte": 10, "resistencia": 14, "tendencia": "baixa", "fonte": "fixture"}, {**health_fixture, "tendencia": "baixa", "preco_atual": 13.8}, bulk_fixture),
        build_graphical_thesis({"ativo": "IBAX3", "preco_atual": 12, "suporte": 10, "resistencia": 14, "tendencia": "baixa", "fonte": "fixture"}, {**health_fixture, "tendencia": "baixa", "preco_atual": 12, "rvol": 0.5}, bulk_fixture),
        build_graphical_thesis({"ativo": "LATL3", "preco_atual": 12, "suporte": 10, "resistencia": 14, "tendencia": "lateral", "fonte": "fixture"}, {**health_fixture, "tendencia": "lateral", "preco_atual": 12}, bulk_fixture),
        build_graphical_thesis({"ativo": "FORA3", "preco_atual": 15, "suporte": 10, "resistencia": 14, "tendencia": "alta", "fonte": "fixture"}, {**health_fixture, "preco_atual": 15}, bulk_fixture),
        build_graphical_thesis({"ativo": "MISS3", "preco_atual": 11, "tendencia": "alta", "fonte": "fixture"}, health_fixture, bulk_fixture),
    ]
    graph_summary = summarize_graphical_theses(graphical_cases)
    assert graph_summary["compra_operavel"] == 1 and graph_summary["interesse_compra"] == 1
    assert graph_summary["venda_operavel"] == 1 and graph_summary["interesse_venda"] == 1
    assert graph_summary["neutra_observar"] == 1 and graph_summary["evitar"] == 1 and graph_summary["inconclusiva"] == 1
    assert graphical_cases[0]["delta_alvo"].startswith("0,40 a 0,60")
    assert "delta" not in graphical_cases[0] and graphical_cases[0]["cadeia_opcoes_status"] == "pendente"
    assert rank_graphical_theses(graphical_cases)[0]["status"] == "compra_operavel"
    assert all(0 <= item["near_setup_score"] <= 100 for item in graphical_cases)
    assert graphical_cases[-1]["hard_technical_blockers"]
    assert graphical_cases[1]["missing_confirmations"]
    fixture_near_setups = rank_near_setups(graphical_cases, 10)
    fixture_diagnostics = summarize_graphical_diagnostics(graphical_cases)
    assert fixture_near_setups and fixture_diagnostics["top_rejection_reasons"]
    print(json.dumps({"graphical_thesis_engine_validation": "ok", **graph_summary, "near_setups": len(fixture_near_setups), "diagnostics_present": True, "real_delta_invented": False, "orders_sent": False}, ensure_ascii=False, indent=2))
    lateral_thesis = graphical_cases[4]
    assert classify_market_regime(lateral_thesis) == "lateral"
    lateral_mapping = build_strategy_mapping(lateral_thesis)
    assert lateral_mapping["preferred_strategy"] == "iron condor"
    assert lateral_mapping["preferred_strategy_family"] == "lateral"
    assert lateral_mapping["strategy_status"] == "pendente_validacao_opcoes"
    assert {item["strategy"] for item in lateral_mapping["strategy_candidates"]} >= {
        "iron condor", "iron butterfly", "butterfly", "calendar",
    }
    assert all(item["status"] == "pendente_validacao_opcoes" for item in lateral_mapping["strategy_candidates"])
    compression_thesis = {
        **lateral_thesis,
        "rvol": 0.5,
        "healthbox_usado": {**lateral_thesis["healthbox_usado"], "rvol": 0.5, "atr_percent": 1.0, "adr_percent": 1.0},
    }
    assert classify_market_regime(compression_thesis) == "compressao"
    compression_mapping = build_strategy_mapping(compression_thesis)
    assert compression_mapping["preferred_strategy_family"] == "volatilidade"
    assert compression_mapping["preferred_strategy"] == "straddle comprado"
    assert classify_market_regime(graphical_cases[-1]) == "indefinido"
    assert suggest_strategy_family(graphical_cases[0]) == "direcional"
    assert suggest_lateral_strategies(lateral_thesis)[0]["strategy"] == "iron condor"
    assert suggest_directional_strategies(graphical_cases[0])
    assert suggest_volatility_strategies(compression_thesis)
    assert rank_strategy_candidates([
        {"strategy": "segunda", "priority": 2}, {"strategy": "primeira", "priority": 3},
    ])[0]["strategy"] == "primeira"
    chain_without_math = {
        **lateral_thesis,
        "cadeia_opcoes_status": "disponivel_fonte",
        "options_validation_candidates": [{"tipo_estrutura": "iron_condor", "perda_maxima": None}],
    }
    assert build_strategy_mapping(chain_without_math)["strategy_status"] == "pendente_validacao_opcoes"
    assert all("delta" not in item for item in lateral_mapping["strategy_candidates"])
    print(json.dumps({
        "strategy_mapper_validation": "ok",
        "lateral_regime": True,
        "compression_regime": True,
        "iron_condor_candidate": True,
        "pending_without_chain": True,
        "chain_alone_did_not_validate": True,
        "real_delta_invented": False,
        "orders_sent": False,
    }, ensure_ascii=False, indent=2))
    catalog = load_strategy_catalog()
    assert len(catalog) == 25 and len(get_strategy_catalog()) == 25
    required_catalog_fields = {
        "id", "nome", "explicacao_curta", "pernas", "tipo", "regime_ideal",
        "tese_ideal", "quando_usar", "quando_evitar", "categoria", "direcao", "complexidade",
        "exige_ativo", "exige_caixa", "exige_cadeia_real", "risco_definido",
        "perda_maxima_obrigatoria", "ganho_maximo_existe", "exige_volatilidade",
        "exige_gregas", "delta_alvo", "delta_alvo_padrao", "vencimento_ideal",
        "dados_obrigatorios", "calculos_obrigatorios", "alertas", "status_padrao_sem_cadeia",
    }
    assert all(required_catalog_fields <= set(strategy) for strategy in catalog)
    assert all(strategy["explicacao_curta"] and strategy["pernas"] and strategy["quando_usar"] and strategy["quando_evitar"] for strategy in catalog)
    lateral_screening = screen_strategies_for_thesis(lateral_thesis)
    assert len(lateral_screening["strategy_screening"]) == 25
    assert lateral_screening["preferred_strategy"] == "iron condor"
    assert [item["strategy_id"] for item in lateral_screening["top_3_strategies"]] == [
        "iron_condor", "iron_butterfly", "call_butterfly",
    ]
    lateral_results = {item["strategy_id"]: item for item in lateral_screening["strategy_screening"]}
    assert lateral_results["long_call"]["status"] == "rejeitada"
    assert lateral_results["long_put"]["status"] == "rejeitada"
    assert lateral_results["iron_condor"]["status"] == "pendente_validacao_opcoes"
    assert lateral_results["short_straddle_travado"]["status"] == "pendente_validacao_opcoes"
    assert lateral_results["short_strangle_travado"]["status"] == "pendente_validacao_opcoes"
    no_range = {**lateral_thesis, "suporte": None, "resistencia": None}
    no_range["market_regime"] = "lateral"
    iron_condor = next(item for item in catalog if item["id"] == "iron_condor")
    assert evaluate_strategy_for_thesis(iron_condor, no_range)["status"] == "rejeitada"
    undefined_screening = screen_strategies_for_thesis(graphical_cases[-1])
    undefined_results = {item["strategy_id"]: item for item in undefined_screening["strategy_screening"]}
    assert undefined_results["diagonal_spread"]["status"] == "rejeitada"
    assert undefined_results["synthetic_short_stock"]["status"] == "rejeitada"
    assert all(item["risco_definido"] for item in catalog if item["id"] in {"short_straddle_travado", "short_strangle_travado", "ratio_spread_travado"})
    assert all("delta" not in item for item in lateral_screening["strategy_screening"])
    assert all("delta_alvo" in item for item in lateral_screening["strategy_screening"])
    assert all(item.get("manual_validation_plan") for item in lateral_screening["strategy_screening"])
    assert all(item.get("strategy_objective") and item.get("objective_label") and item.get("objective_description") and item.get("objective_warning") for item in lateral_screening["strategy_screening"])
    iron_plan = lateral_results["iron_condor"]["manual_validation_plan"]
    assert iron_plan["manual_validation_status"] == "procurar_no_book"
    assert "0,15 a 0,30" in iron_plan["delta_target"]
    assert str(lateral_thesis["suporte"]) in iron_plan["strike_region"]
    assert str(lateral_thesis["resistencia"]) in iron_plan["strike_region"]
    assert iron_plan["max_debit_allowed"] is None and iron_plan["min_credit_required"] is None
    assert iron_plan["warning"].startswith("Plano de validação manual")
    call_spread_result = next(
        item for item in screen_strategies_for_thesis(graphical_cases[0])["strategy_screening"]
        if item["strategy_id"] == "call_debit_spread"
    )
    real_chain_thesis = {
        **graphical_cases[0],
        "cadeia_opcoes_status": "disponivel_fonte",
        "options_validation_candidates": [{
            "tipo_estrutura": "call_debit_spread",
            "strike_comprado": 10.0,
            "strike_vendido": 14.0,
            "custo_liquido": 1.0,
            "entry_reference_price": 1.0,
            "perda_maxima": 1.0,
            "break_even": 11.0,
            "liquidez": "alta",
            "delta_comprado": 0.52,
        }],
    }
    real_plan = build_manual_validation_plan(call_spread_result, real_chain_thesis)
    assert real_plan["manual_validation_status"] == "validavel_com_cadeia"
    assert real_plan["delta_target"] == 0.52
    assert real_plan["max_debit_allowed"] == round(4 / 2.2, 4)
    assert "strike_comprado: 10.0" in real_plan["strike_region"]
    assert rank_screened_strategies(list(reversed(lateral_screening["strategy_screening"]))) == lateral_screening["strategy_screening"]
    screening_summary = summarize_strategy_screening([
        {**lateral_thesis, **lateral_screening},
        {**graphical_cases[-1], **undefined_screening},
    ])
    assert screening_summary["theses_screened"] == 2
    assert screening_summary["strategies_evaluated"] == 50
    assert screening_summary["strategies_per_thesis"] == 25
    practical_lateral = build_practical_strategy_summary({**lateral_thesis, **lateral_screening})
    assert practical_lateral["best_strategy"]["strategy_name"] == "iron condor"
    assert practical_lateral["best_strategy"]["strategy_objective"] == "lateralidade"
    assert practical_lateral["best_strategy"]["objective_label"] == "Lateralidade"
    assert len(practical_lateral["top_3_strategies"]) == 3
    assert practical_lateral["rejected_count"] > 0
    assert practical_lateral["practical_action"] == "olhar_no_book"
    assert practical_lateral["user_summary"]
    assert select_best_strategy_for_thesis({**lateral_thesis, **lateral_screening})["strategy_id"] == "iron_condor"
    assert len(select_top_strategies_for_thesis({**lateral_thesis, **lateral_screening}, 3)) == 3
    assert summarize_strategy_for_user(lateral_results["iron_condor"])["delta_target"]
    tie_fixture = {
        "strategy_screening": [
            {"strategy_id": "advanced", "strategy_name": "Avançada", "suitability_score": 80, "status": "possivel", "complexidade": "avançada", "risco_definido": True, "regime_compativel": True, "dados_necessarios": []},
            {"strategy_id": "simple", "strategy_name": "Simples", "suitability_score": 80, "status": "possivel", "complexidade": "simples", "risco_definido": True, "regime_compativel": True, "dados_necessarios": []},
        ]
    }
    assert select_best_strategy_for_thesis(tie_fixture)["strategy_id"] == "simple"
    assert classify_strategy_objective(lateral_results["iron_condor"], lateral_thesis) == "lateralidade"
    assert classify_strategy_objective({"strategy_id": "bull_put_spread"}, graphical_cases[0]) == "premio"
    assert classify_strategy_objective({"strategy_id": "long_call"}, graphical_cases[0]) == "direcional_alta"
    assert classify_strategy_objective({"strategy_id": "protective_put"}, graphical_cases[0]) == "protecao"
    assert classify_strategy_objective({"strategy_id": "covered_call"}, lateral_thesis) == "carteira"
    assert classify_strategy_objective({"strategy_id": "long_straddle"}, compression_thesis) == "volatilidade_evento"
    assert classify_strategy_objective({"strategy_id": "synthetic_short_stock"}, graphical_cases[0]) == "estudo_avancado"
    assert build_strategy_objective_label(None, graphical_cases[-1])["strategy_objective"] == "esperar"
    objective_summary = summarize_objectives_for_thesis({**lateral_thesis, **lateral_screening, **practical_lateral})
    assert objective_summary["practical_objective"] == "lateralidade"
    priority_fixture = [
        {**graphical_cases[0], **screen_strategies_for_thesis(graphical_cases[0])},
        {**lateral_thesis, **lateral_screening, **practical_lateral},
        {**graphical_cases[-1], **undefined_screening},
    ]
    priorities = build_daily_priority_list(priority_fixture, limit_per_objective=5)
    assert set(priorities) == {
        "top_premio", "top_direcionais", "top_lateralidade",
        "top_protecao_carteira", "top_volatilidade_evento",
        "evitar_por_enquanto", "inconclusivas",
    }
    assert priorities["top_direcionais"]
    assert priorities["top_lateralidade"]
    assert all(len(items) <= 5 for items in priorities.values())
    assert len({item["ativo"] for item in priorities["top_lateralidade"]}) == len(priorities["top_lateralidade"])
    assert classify_practical_priority(lateral_results["iron_condor"], lateral_thesis) == "olhar_no_book"
    assert classify_practical_priority(None, graphical_cases[-1]) == "inconclusivo"
    assert rank_by_objective(list(reversed(priorities["top_lateralidade"])), "top_lateralidade") == priorities["top_lateralidade"]
    priority_summary = summarize_daily_priorities(priorities)
    assert priority_summary["total"] == sum(priority_summary["counts"].values())
    assert matches_quick_objective_filter({**lateral_thesis, **practical_lateral}, "Só lateralidade")
    assert not matches_quick_objective_filter({**lateral_thesis, **practical_lateral}, "Só direcional")
    capital_profile = {
        **DEFAULT_TRADING_PROFILE,
        "capital_disponivel": 10000,
        "perda_maxima_por_operacao": 500,
        "percentual_maximo_por_operacao": 10,
        "multiplicador_contrato_padrao": 100,
        "usar_multiplicador_padrao_se_fonte_ausente": True,
    }
    debit_fixture = {
        "strategy_id": "call_debit_spread", "tipo_estrutura": "call_debit_spread",
        "custo_liquido": 1.0, "perda_maxima": 1.0,
    }
    capital_result = estimate_strategy_capital_required(debit_fixture, graphical_cases[0], capital_profile)
    assert capital_result["minimum_technical_capital"] == 100
    assert capital_result["recommended_capital"] == 125
    assert capital_result["max_loss_estimate"] == 100
    assert capital_result["capital_fit_status"] == "cabe_bem"
    assert estimate_minimum_technical_capital(debit_fixture, graphical_cases[0], capital_profile) == 100
    assert estimate_recommended_capital(debit_fixture, graphical_cases[0], capital_profile) == 125
    assert estimate_max_loss_required(debit_fixture) == 1
    assert estimate_margin_proxy(debit_fixture) == 1
    fit_only_profile = {
        **capital_profile, "capital_disponivel": 150,
        "perda_maxima_por_operacao": None, "percentual_maximo_por_operacao": None,
    }
    assert classify_capital_fit({**capital_result, "strategy_id": "call_debit_spread"}, graphical_cases[0], fit_only_profile)["capital_fit_status"] == "cabe_apertado"
    assert classify_capital_fit({**capital_result, "strategy_id": "call_debit_spread"}, graphical_cases[0], {**capital_profile, "capital_disponivel": 50})["capital_fit_status"] == "acima_do_capital"
    pending_result = estimate_strategy_capital_required(debit_fixture, graphical_cases[0], DEFAULT_TRADING_PROFILE)
    assert pending_result["capital_fit_status"] == "pendente_dados" and pending_result["missing_capital_fields"]
    assert "Informe capital" in explain_capital_requirement(pending_result, graphical_cases[0], DEFAULT_TRADING_PROFILE)
    assert load_user_trading_profile().get("usar_multiplicador_padrao_se_fonte_ausente") is False
    capital_rank_fixture = {
        "strategy_screening": [
            {"strategy_id": "tight", "suitability_score": 99, "status": "possivel", "complexidade": "simples", "risco_definido": True, "regime_compativel": True, "capital_fit_status": "cabe_apertado"},
            {"strategy_id": "good", "suitability_score": 70, "status": "possivel", "complexidade": "simples", "risco_definido": True, "regime_compativel": True, "capital_fit_status": "cabe_bem"},
        ]
    }
    assert select_best_strategy_for_thesis(capital_rank_fixture)["strategy_id"] == "good"
    manual_backup = MANUAL_SIMULATIONS_PATH.read_bytes() if MANUAL_SIMULATIONS_PATH.exists() else None
    try:
        MANUAL_SIMULATIONS_PATH.write_text("[]", encoding="utf-8")
        def manual_case(strategy_id: str, legs: list[tuple[str, str, float | None, float]]) -> dict:
            return {
                **build_manual_simulation_from_strategy({"strategy_id": strategy_id, "strategy_name": strategy_id}, graphical_cases[0]),
                "source": "manual", "quantity": 1, "contract_multiplier": 100,
                "legs": [
                    {"type": leg_type, "action": action, "strike": strike, "premium": premium, "quantity": 1, "expiration": "2026-08-21"}
                    for leg_type, action, strike, premium in legs
                ],
            }
        long_call_manual = calculate_manual_strategy_risk(manual_case("long_call", [("call", "buy", 10, 1)]), capital_profile)
        assert long_call_manual["max_loss"] == 100 and long_call_manual["capital_required"] == 100
        assert long_call_manual["break_even_points"] == [11.0] and long_call_manual["source"] == "manual"
        debit_manual = calculate_manual_strategy_risk(manual_case("call_debit_spread", [("call", "buy", 10, 1.5), ("call", "sell", 14, .5)]), capital_profile)
        assert debit_manual["net_debit"] == 100 and debit_manual["max_loss"] == 100 and debit_manual["max_gain"] == 300
        credit_manual = calculate_manual_strategy_risk(manual_case("bull_put_spread", [("put", "sell", 10, 1.5), ("put", "buy", 8, .5)]), capital_profile)
        assert credit_manual["net_credit"] == 100 and credit_manual["max_loss"] == 100 and credit_manual["break_even_points"] == [9.0]
        condor_manual = calculate_manual_strategy_risk(manual_case("iron_condor", [("put", "buy", 8, .2), ("put", "sell", 9, .5), ("call", "sell", 11, .5), ("call", "buy", 12, .2)]), capital_profile)
        assert condor_manual["net_credit"] == 60 and condor_manual["max_loss"] == 40
        assert condor_manual["break_even_points"] == [8.4, 11.6]
        covered_case = manual_case("covered_call", [("stock", "buy", None, 10), ("call", "sell", 12, .5)])
        covered_manual = calculate_manual_strategy_risk(covered_case, capital_profile)
        assert covered_manual["capital_fit_status"] == "exige_ativo_em_carteira"
        assert "queda do ativo" in covered_manual["risk_note"].lower()
        cash_manual = calculate_manual_strategy_risk(manual_case("cash_secured_put", [("put", "sell", 10, 1)]), capital_profile)
        assert cash_manual["capital_required"] == 1000 and cash_manual["max_gain"] == 100
        assert len(SUPPORTED_STRATEGIES) == 12
        assert all(build_manual_simulation_from_strategy({"strategy_id": strategy}, graphical_cases[0])["legs"] for strategy in SUPPORTED_STRATEGIES)
        saved_manual = save_manual_simulation(debit_manual)
        assert load_manual_simulations() and list_manual_simulations()[0]["source"] == "manual"
        assert delete_manual_simulation(saved_manual["simulation_id"]) and not load_manual_simulations()
        assert classify_manual_simulation_fit(debit_manual, capital_profile)["capital_fit_status"] == "cabe_bem"
    finally:
        if manual_backup is None:
            if MANUAL_SIMULATIONS_PATH.exists(): MANUAL_SIMULATIONS_PATH.unlink()
        else:
            MANUAL_SIMULATIONS_PATH.write_bytes(manual_backup)
    print(json.dumps({
        "strategy_screener_validation": "ok",
        "catalog_size": len(catalog),
        "strategies_per_thesis": screening_summary["strategies_per_thesis"],
        "iron_condor_for_lateral": True,
        "directional_rejected_in_lateral_without_catalyst": True,
        "complex_rejected_when_undefined": True,
        "real_delta_invented": False,
        "manual_plans_for_all_candidates": True,
        "iron_condor_levels_relative_to_range": True,
        "practical_top_3": True,
        "advanced_avoided_on_tie": True,
        "objectives_attached_to_all_candidates": True,
        "daily_priorities_built": True,
        "quick_priority_filter": True,
        "capital_requirements": True,
        "capital_fit_ranking": True,
        "manual_trade_simulator": True,
        "manual_strategies_supported": len(SUPPORTED_STRATEGIES),
        "manual_source_preserved": True,
        "orders_sent": False,
    }, ensure_ascii=False, indent=2))
    save_graphical_watchlist([])
    added = add_to_graphical_watchlist(graphical_cases[0])
    duplicate = add_to_graphical_watchlist(graphical_cases[0])
    assert added["added"] and not duplicate["added"] and duplicate["reason"] == "duplicado"
    base_item = load_graphical_watchlist()[0]
    snapshots_by_status = {
        "aguardando gatilho": {
            "ativo": "ALTA3", "preco_atual": 11, "suporte": 10, "resistencia": 14,
            "tendencia": "alta", "rsi": 55, "rvol": 1.2, "atr_percent": 2,
            "adr_percent": 2, "distancia_suporte_percent": 9.09,
            "distancia_resistencia_percent": 27.27, "status_dado": "atualizado",
            "campos_ausentes": [],
        },
        "perto do gatilho": {
            "ativo": "ALTA3", "preco_atual": 13.8, "suporte": 10, "resistencia": 14,
            "tendencia": "alta", "rsi": 55, "rvol": 1.2, "atr_percent": 2,
            "adr_percent": 2, "distancia_suporte_percent": 27.54,
            "distancia_resistencia_percent": 1.45, "status_dado": "atualizado",
            "campos_ausentes": [],
        },
        "gatilho acionado": {
            "ativo": "ALTA3", "preco_atual": 14.1, "suporte": 10, "resistencia": 14,
            "tendencia": "alta", "rsi": 55, "rvol": 1.2, "atr_percent": 2,
            "adr_percent": 2, "distancia_suporte_percent": 29.08,
            "distancia_resistencia_percent": 0.71, "status_dado": "atualizado",
            "campos_ausentes": [],
        },
        "invalidada": {
            "ativo": "ALTA3", "preco_atual": 9.9, "suporte": 10, "resistencia": 14,
            "tendencia": "baixa", "status_dado": "atualizado", "campos_ausentes": [],
        },
    }
    evaluated_cases = [
        evaluate_graphical_watchlist_item(base_item, snapshot)
        for snapshot in snapshots_by_status.values()
    ]
    evaluated_cases.append(evaluate_graphical_watchlist_item(base_item, None))
    watchlist_summary = summarize_graphical_watchlist(evaluated_cases)
    assert all(
        watchlist_summary[status] == 1
        for status in (
            "aguardando gatilho",
            "perto do gatilho",
            "gatilho acionado",
            "invalidada",
            "inconclusiva por falta de dados",
        )
    )
    assert base_item["aviso"].startswith("tese gráfica não é ordem")
    print(json.dumps({
        "graphical_watchlist_validation": "ok",
        "saved": True,
        "duplicate_prevented": True,
        **watchlist_summary,
        "invented_data": False,
        "orders_sent": False,
    }, ensure_ascii=False, indent=2))
    try:
        with patch("app.pipeline_orchestrator.run_market_update", return_value={"success": True, "errors": [], "updated_count": 2}), \
             patch("app.pipeline_orchestrator.run_options_update", return_value={"success": True, "errors": [], "available_count": 2}), \
             patch("app.pipeline_orchestrator.generate_real_eod_opportunities", return_value=pipeline_candidates):
            pipeline_close = run_pipeline("close", ["PETR4", "VALE3"], max_expirations=2)
            pipeline_intraday = run_pipeline("intraday", ["PETR4", "VALE3"])
        saved_pipeline = load_real_opportunities_snapshot()
        assert pipeline_close["opportunities_snapshot"] is not None
        assert pipeline_close["graphical_theses_snapshot"] is not None
        assert saved_pipeline["entrada_condicional"] == 1
        assert saved_pipeline["acompanhar_na_abertura"] == 1
        assert saved_pipeline["data_frequency"] == "EOD"
        assert saved_pipeline["opportunity_engine"] == "real_experimental"
        assert pipeline_intraday["opportunities_snapshot"] is None
        assert "options" not in pipeline_intraday["phases"]
        print(json.dumps({
            "automatic_pipeline_validation": "ok", "close_snapshot_saved": True,
            "entrada_condicional": saved_pipeline["entrada_condicional"],
            "acompanhar_na_abertura": saved_pipeline["acompanhar_na_abertura"],
            "intraday_did_not_generate_eod": True, "internet_called": False,
        }, ensure_ascii=False, indent=2))
    finally:
        for path, content in pipeline_backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
    availability_backup = AVAILABILITY_FILE.read_bytes() if AVAILABILITY_FILE.exists() else None
    try:
        fake_provider = type("FakeOptionsProvider", (), {})()
        fake_provider.get_expirations = lambda ticker: (
            {"success": True, "expirations": ["2099-08-20"], "access_status": "disponível"}
            if ticker != "BOVA11" else
            {"success": False, "expirations": [], "access_status": "sem_acesso", "error": "acesso negado no teste"}
        )
        liquidity_series = {
            "PETR4": [{"side": "call", "volume": 20, "trades": 5, "bid": 1.0, "ask": 1.5, "spread_pct": 40.0}],
            "VALE3": [{"side": "put", "volume": 0, "trades": 0, "bid": 1.0, "ask": 1.2, "spread_pct": 18.0}],
            "ITUB4": [{"side": "call", "volume": 1000, "trades": 200, "bid": 1.0, "ask": 1.05, "spread_pct": 5.0}],
            "BBAS3": [{"side": "call", "volume": 2, "trades": 1, "bid": None, "ask": None, "spread_pct": None}],
        }
        fake_provider.get_chain = lambda ticker, expiration: {
            "success": True, "count": len(liquidity_series[ticker]),
            "calls": sum(item["side"] == "call" for item in liquidity_series[ticker]),
            "puts": sum(item["side"] == "put" for item in liquidity_series[ticker]),
            "data": liquidity_series[ticker],
        }
        with patch("app.options_universe_discovery.BrapiOptionsProvider", return_value=fake_provider), \
             patch("app.options_universe_discovery._dte", return_value=30):
            discover_options_availability(["PETR4", "VALE3"], max_expirations=1)
            availability = discover_options_availability(["ITUB4", "BBAS3", "BOVA11"], max_expirations=1, incremental=True)
        assert availability["available"] == ["PETR4", "VALE3", "ITUB4", "BBAS3"]
        assert availability["unavailable"] == ["BOVA11"]
        classes = {item["ticker"]: item["liquidity_class"] for item in availability["assets"]}
        statuses = {item["ticker"]: item["status"] for item in availability["assets"]}
        assert classes == {"PETR4": "baixa", "VALE3": "sem negócio", "ITUB4": "alta", "BBAS3": "muito baixa", "BOVA11": "indisponível"}
        assert statuses["PETR4"] == "disponivel_baixa_liquidez"
        assert statuses["VALE3"] == "disponivel_baixa_liquidez"
        assert statuses["BOVA11"] == "sem_acesso_fonte"
        assert get_available_option_tickers(include_low_liquidity=True) == ["PETR4", "VALE3", "ITUB4", "BBAS3"]
        assert get_available_option_tickers(include_low_liquidity=False) == ["ITUB4"]
        market_call = None
        with patch("app.pipeline_orchestrator.run_market_update", return_value={"success": True, "errors": []}) as market_mock, \
             patch("app.pipeline_orchestrator.save_pipeline_status"), \
             patch("app.pipeline_orchestrator.save_graphical_theses_snapshot"):
            cached_pipeline_result = run_pipeline("intraday", tickers=None)
            market_call = market_mock.call_args.kwargs["tickers"]
        assert cached_pipeline_result["option_tickers"] == ["PETR4", "VALE3", "ITUB4", "BBAS3"]
        stale = load_options_universe_availability()
        stale["generated_at"] = "2020-01-01T00:00:00+00:00"
        save_options_universe_availability(stale)
        assert get_available_option_tickers() == []
        print(json.dumps({
            "options_universe_discovery_validation": "ok", "tickers_tested": 5,
            "available": availability["available"], "unavailable": availability["unavailable"],
            "liquidity_classes": classes, "low_liquidity_kept": True,
            "incremental_batches_preserved": True, "source_denial_distinguished": True,
            "without_low_liquidity": ["ITUB4"],
            "pipeline_used_valid_cache": cached_pipeline_result["option_tickers"] == ["PETR4", "VALE3", "ITUB4", "BBAS3"],
            "stale_cache_rejected": True, "internet_called": False,
        }, ensure_ascii=False, indent=2))
    finally:
        if availability_backup is None:
            if AVAILABILITY_FILE.exists():
                AVAILABILITY_FILE.unlink()
        else:
            AVAILABILITY_FILE.write_bytes(availability_backup)
    universe = load_asset_universe()
    chain = load_options_chain()
    generated_opportunities = generate_daily_opportunities()
    opportunity_groups = split_opportunities_by_status(generated_opportunities)
    mglu = [item for item in generated_opportunities if item["ativo"] == "MGLU3"]
    abev = [item for item in generated_opportunities if item["ativo"] == "ABEV3"]
    no_options = [item for item in generated_opportunities if item["ativo"] == "WEGE3"]
    assert len(universe) >= 20
    assert chain
    assert mglu and all(item["status"] == "reprovada" for item in mglu)
    assert any("liquidez" in item["motivo"] for item in mglu)
    assert abev and all(item["status"] != "aprovada" for item in abev)
    assert no_options and all(item["status"] == "reprovada" for item in no_options)
    assert all(
        item.get("calculation", {}).get("max_loss") is not None
        for item in opportunity_groups["aprovada"]
    )
    print(
        json.dumps(
            {
                "opportunity_engine_validation": "ok",
                "universe": build_universe_summary(universe),
                "options_loaded": len(chain),
                "candidates_generated": len(generated_opportunities),
                "status_counts": {
                    status: len(items) for status, items in opportunity_groups.items()
                },
                "mglu_high_premium_rejected": True,
                "abev_incomplete_safe": True,
                "approved_without_max_loss": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    provider_without_token = BrapiProvider(token="")
    no_token_result = provider_without_token.get_quotes(["PETR4"])
    assert no_token_result["success"] is False
    assert "BRAPI_TOKEN" in no_token_result["error"]
    fake_quote = {
        "results": [
            {
                "symbol": "PETR4",
                "regularMarketPrice": 40.0,
                "regularMarketOpen": 39.5,
                "regularMarketDayHigh": 40.2,
                "regularMarketDayLow": 39.1,
                "regularMarketPreviousClose": 39.4,
                "regularMarketVolume": 1000,
                "regularMarketChangePercent": 1.52,
                "regularMarketTime": "2026-07-01T18:00:00Z",
            }
        ]
    }
    normalized_quotes = provider_without_token.normalize_quote_response(fake_quote)
    assert normalized_quotes[0]["ticker"] == "PETR4"
    assert normalized_quotes[0]["tipo_dado"] == "coletado"
    fake_history = {
        "results": [
            {
                "symbol": "PETR4",
                "historicalDataPrice": [
                    {"date": 1, "open": 39.0, "high": 40.0, "low": 38.8, "close": 39.8, "volume": 100, "adjustedClose": 39.8}
                ],
            }
        ]
    }
    normalized_history = provider_without_token.normalize_historical_response(fake_history)
    assert len(normalized_history[0]["candles"]) == 1
    cache_key = "validation:provider-engine"
    save_cache(cache_key, {"ok": True})
    assert is_cache_fresh(cache_key, 5)
    assert load_cache(cache_key)["data"]["ok"] is True
    clear_cache(cache_key)
    assert load_cache(cache_key) is None
    print(
        json.dumps(
            {
                "data_provider_validation": "ok",
                "without_token_safe": True,
                "internet_called": False,
                "normalized_quotes": len(normalized_quotes),
                "normalized_historical_assets": len(normalized_history),
                "cache_roundtrip": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    fake_candles = [
        {
            "date": index,
            "open": 20.0 + index * 0.1,
            "high": 20.5 + index * 0.1,
            "low": 19.5 + index * 0.1,
            "close": 20.2 + index * 0.1,
            "volume": 1000 + index * 10,
            "adjusted_close": 20.2 + index * 0.1,
        }
        for index in range(220)
    ]
    rsi_result = calculate_rsi(fake_candles, 14)
    insufficient_rsi = calculate_rsi(fake_candles[:5], 14)
    atr_result = calculate_atr_percent(fake_candles, 14)
    adr_result = calculate_adr_percent(fake_candles, 14)
    rvol_result = calculate_relative_volume(fake_candles, 20)
    levels_result = calculate_support_resistance(fake_candles, 20)
    trend_result = classify_trend(fake_candles, 9, 21)
    assert rsi_result["status"] == "calculado"
    assert insufficient_rsi["value"] is None and insufficient_rsi["reason"] == "histórico insuficiente"
    assert all(result["status"] == "calculado" for result in (atr_result, adr_result, rvol_result, levels_result, trend_result))

    fake_quote_result = {
        "success": True,
        "provider": "brapi",
        "coleta": "2026-07-01T18:00:00+00:00",
        "data": [{"ticker": "TEST3", "preco": 42.1, "abertura": 41.8, "maxima": 42.4, "minima": 41.5, "fechamento_anterior": 41.7, "volume": 5000, "fonte": "brapi", "tipo_dado": "coletado", "status_dado": "atualizado", "coleta": "2026-07-01T18:00:00+00:00"}],
    }
    fake_historical_result = {
        "success": True,
        "provider": "brapi",
        "coleta": "2026-07-01T18:00:00+00:00",
        "data": [{"ticker": "TEST3", "candles": fake_candles, "fonte": "brapi", "tipo_dado": "coletado", "status_dado": "atualizado", "coleta": "2026-07-01T18:00:00+00:00"}],
    }
    fake_snapshot = build_asset_snapshot_from_data("TEST3", fake_quote_result, fake_historical_result)
    fake_real_healthbox = snapshot_to_healthbox(fake_snapshot)
    assert fake_snapshot["fonte"] == "brapi"
    assert fake_snapshot["rsi"] is not None and fake_snapshot["rsi_200"] is not None
    assert fake_snapshot["suporte"] is not None and fake_snapshot["resistencia"] is not None
    assert fake_real_healthbox["score_result"]["score"] is not None
    print(
        json.dumps(
            {
                "technical_indicators_validation": "ok",
                "rsi": rsi_result,
                "insufficient_rsi": insufficient_rsi,
                "atr": atr_result,
                "adr": adr_result,
                "rvol": rvol_result,
                "support_resistance": levels_result,
                "trend": trend_result,
                "market_snapshot_fake": {"status": fake_snapshot["status_dado"], "missing_fields": fake_snapshot["campos_ausentes"], "healthbox_score": fake_real_healthbox["score_result"]["score"]},
                "internet_called": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    orchestrator_snapshots = [
        {"ativo": "TEST3", "status_dado": "atualizado", "tendencia": "alta", "campos_ausentes": [], "fonte": "brapi", "coleta": "2026-07-01T18:00:00+00:00", "tipo_dado": "coletado/calculado"},
        {"ativo": "FAKE4", "status_dado": "incompleto", "tendencia": "lateral", "campos_ausentes": ["rsi_200"], "fonte": "brapi", "coleta": "2026-07-01T18:00:00+00:00", "tipo_dado": "coletado/calculado"},
    ]
    orchestrator_summary = summarize_snapshots(orchestrator_snapshots)
    assert orchestrator_summary["completos"] == 1
    assert orchestrator_summary["incompletos"] == 1
    assert orchestrator_summary["campos_ausentes_mais_comuns"]["rsi_200"] == 1
    stale = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    fresh = datetime.now(timezone.utc).isoformat()
    assert should_update(stale, 15)["should_update"] is True
    assert should_update(fresh, 15)["should_update"] is False

    snapshot_backup = SNAPSHOTS_FILE.read_bytes() if SNAPSHOTS_FILE.exists() else None
    status_backup = STATUS_FILE.read_bytes() if STATUS_FILE.exists() else None
    try:
        save_market_snapshots(orchestrator_snapshots)
        save_update_status({"last_updates": {}, "last_error": None, "notes": ["teste offline"]})
        assert load_market_snapshots() == orchestrator_snapshots
        assert load_update_status()["notes"] == ["teste offline"]
    finally:
        if snapshot_backup is not None:
            SNAPSHOTS_FILE.write_bytes(snapshot_backup)
        elif SNAPSHOTS_FILE.exists():
            SNAPSHOTS_FILE.unlink()
        if status_backup is not None:
            STATUS_FILE.write_bytes(status_backup)
        elif STATUS_FILE.exists():
            STATUS_FILE.unlink()
    print(json.dumps({"update_orchestrator_validation": "ok", "internet_called": False, "summary": orchestrator_summary}, ensure_ascii=False, indent=2))
    options_provider = BrapiOptionsProvider(token="token-fake-offline")
    fake_expirations = options_provider.normalize_expirations_response(
        {"underlying": "PETR4", "expirations": ["2026-08-21", "2026-07-17"]}
    )
    assert fake_expirations["success"] is True
    assert fake_expirations["expirations"] == ["2026-07-17", "2026-08-21"]
    fake_chain = options_provider.normalize_chain_response(
        {
            "series": [
                {
                    "symbol": "PETRG300", "underlyingSymbol": "PETR4", "side": "call", "market": "equity",
                    "strike": 30.0, "expirationDate": "2026-07-17", "firstTradeDate": "2026-01-01",
                    "lastTradeDate": "2026-07-01", "date": 1782860400, "open": 4.0, "high": 4.5,
                    "low": 3.9, "average": 4.2, "close": 4.3, "bid": 4.1, "ask": 4.3,
                    "trades": 520, "volume": 1000, "financialVolume": 420000,
                },
                {
                    "symbol": "PETRS300", "underlyingSymbol": "PETR4", "side": "put", "market": "equity",
                    "strike": 30.0, "expirationDate": "2026-07-17", "bid": 1.0, "ask": 1.4, "trades": 10,
                },
            ]
        }
    )
    assert len(fake_chain) == 2
    assert fake_chain[0]["mid"] == 4.2 and fake_chain[0]["spread_abs"] == 0.2
    assert round(fake_chain[0]["spread_pct"], 4) == 4.7619
    assert fake_chain[0]["liquidity_status"] == "alta"
    assert fake_chain[1]["liquidity_status"] == "ilíquida"
    assert fake_chain[0]["moneyness"] == "indisponível"
    assert "delta" not in fake_chain[0] and "gamma" not in fake_chain[0]
    denied = options_provider.normalize_http_error(403, {"message": "forbidden"})
    assert denied["access_status"] == "sem_acesso" and denied["success"] is False
    empty_summary = summarize_options_snapshot({})
    assert empty_summary["series_count"] == 0 and empty_summary["status_dado"] == "indisponível"
    print(
        json.dumps(
            {
                "brapi_options_validation": "ok", "internet_called": False,
                "expirations": fake_expirations["count"], "series": len(fake_chain),
                "spread_calculated": True, "liquidity_classified": True,
                "fake_403_access_status": denied["access_status"], "greeks_invented": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    fake_asset_snapshots = {
        "ZZZZ1": {
            "underlying": "ZZZZ1", "success": True, "status_dado": "atualizado", "access_status": "disponível",
            "series_count": 2, "calls_count": 1, "puts_count": 1, "series": fake_chain,
            "coleta": "2026-07-02T18:00:00+00:00", "error": None,
        },
        "ZZZZ2": {
            "underlying": "ZZZZ2", "success": False, "status_dado": "erro", "access_status": "sem_acesso",
            "series_count": 0, "calls_count": 0, "puts_count": 0, "series": [],
            "coleta": "2026-07-02T18:00:00+00:00", "error": "plano sem acesso",
        },
        "ZZZZ3": {
            "underlying": "ZZZZ3", "success": False, "status_dado": "indisponível", "access_status": "indisponível",
            "series_count": 0, "calls_count": 0, "puts_count": 0, "series": [],
            "coleta": "2026-07-02T18:00:00+00:00", "error": "nenhuma série disponível",
        },
    }
    fake_paths = [OPTIONS_SNAPSHOTS_DIR / f"{symbol}.json" for symbol in fake_asset_snapshots]
    backups = {path: path.read_bytes() if path.exists() else None for path in fake_paths}
    try:
        for symbol, snapshot in fake_asset_snapshots.items():
            save_options_snapshot_for_asset(symbol, snapshot)
            assert load_options_snapshot_for_asset(symbol) == snapshot
        aggregate_options = summarize_options_snapshots(fake_asset_snapshots)
        assert aggregate_options["status"] == "parcial"
        assert aggregate_options["available_count"] == 1
        assert aggregate_options["unavailable_count"] == 2
        assert aggregate_options["error_count"] == 1
        assert aggregate_options["total_series"] == 2
        assert fake_chain[1]["open"] is None and "open" in fake_chain[1]["campos_ausentes"]
    finally:
        for path, backup in backups.items():
            if backup is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(backup)
    print(
        json.dumps(
            {
                "options_eod_orchestrator_validation": "ok", "internet_called": False,
                "available": aggregate_options["available_count"], "unavailable": aggregate_options["unavailable_count"],
                "errors": aggregate_options["error_count"], "missing_fields_preserved": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    price_mid = _indicative_price({"bid": 1.8, "ask": 2.2, "close": 1.9})
    price_close = _indicative_price({"bid": None, "ask": None, "close": 1.7})
    price_missing = _indicative_price({"bid": None, "ask": None, "close": None, "average": None})
    assert price_mid["price"] == 2.0 and price_mid["price_basis"] == "mid" and price_mid["is_executable_price"] is True
    assert price_close["price"] == 1.7 and price_close["price_basis"] == "close_eod" and price_close["is_executable_price"] is False
    assert price_missing["price"] is None and price_missing["price_basis"] == "indisponível"
    real_calls = [
        {
            "symbol": "TESTA100", "underlying_symbol": "TEST3", "side": "call", "strike": 40.0,
            "expiration_date": "2026-08-21", "bid": 1.8, "ask": 2.2, "close": 1.9,
            "spread_pct": 20.0, "liquidity_status": "média", "fonte": "brapi_options", "date": 1787000000,
        },
        {
            "symbol": "TESTA420", "underlying_symbol": "TEST3", "side": "call", "strike": 42.0,
            "expiration_date": "2026-08-21", "bid": None, "ask": None, "close": 1.0,
            "spread_pct": None, "liquidity_status": "baixa", "fonte": "brapi_options", "date": 1787000000,
        },
    ]
    real_pairs = pair_real_call_debit_spreads(real_calls)
    assert len(real_pairs) == 1
    assert "close_eod" in real_pairs[0]["price_basis"]
    assert "EOD" in real_pairs[0]["aviso_preco"] and real_pairs[0]["is_executable_price"] is False
    complete_market = {
        "ativo": "TEST3", "preco_atual": 41.0, "abertura": 40.5, "maxima": 41.5, "minima": 40.0,
        "fechamento_anterior": 40.4, "adr_percent": 2.0, "atr_percent": 2.1, "rvol": 1.1,
        "rsi": 55.0, "rsi_200": 53.0, "tendencia": "alta", "suporte": 39.0, "resistencia": 44.0,
        "volatilidade_implicita": None, "fonte": "brapi", "tipo_dado": "coletado", "coleta": "2026-07-02T18:00:00+00:00",
    }
    evaluated_real = evaluate_real_candidate(real_pairs[0], complete_market)
    assert evaluated_real["perda_maxima"] is not None and evaluated_real["break_even"] is not None
    assert evaluated_real["status"] in {"atenção", "evitar"}
    incomplete_candidate = {**real_pairs[0], "premio_pago": None}
    evaluated_incomplete = evaluate_real_candidate(incomplete_candidate, complete_market)
    assert evaluated_incomplete["status"] == "evitar" and evaluated_incomplete["perda_maxima"] is None
    with patch("app.real_opportunity_engine.get_options_snapshot_for_asset", return_value=None):
        without_snapshot = build_real_candidates_for_asset("NONE3")
    assert without_snapshot[0]["status"] == "inconclusivo" and "sem snapshot" in without_snapshot[0]["motivo"]
    denied_snapshot = {"success": False, "access_status": "sem_acesso", "status_dado": "erro", "series": [], "coleta": "2026-07-02T18:00:00+00:00"}
    with patch("app.real_opportunity_engine.get_options_snapshot_for_asset", return_value=denied_snapshot):
        without_access = build_real_candidates_for_asset("LOCK3")
    assert without_access[0]["status"] == "inconclusivo" and "sem acesso" in without_access[0]["motivo"]
    real_validation_summary = summarize_real_opportunities([evaluated_real, evaluated_incomplete, without_snapshot[0], without_access[0]])
    assert all(item.get("perda_maxima") is not None for item in [evaluated_real] if item.get("status") == "estudar")
    print(
        json.dumps(
            {
                "real_opportunity_engine_validation": "ok", "internet_called": False,
                "mid_tested": True, "close_eod_tested": True, "missing_price_tested": True,
                "without_snapshot": "inconclusivo", "without_access": "inconclusivo",
                "incomplete_math_never_study": evaluated_incomplete["status"] != "estudar",
                "eod_warning_present": "EOD" in evaluated_real["aviso_preco"],
                "summary": real_validation_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    conditional_base = {
        "ativo": "TEST3", "tipo_estrutura": "call_debit_spread", "strike_comprado": 40.0,
        "strike_vendido": 42.0, "premio_pago": 1.5, "premio_recebido": 0.7,
        "custo_liquido": 0.8, "credito_liquido": None, "perda_maxima": 0.8,
        "ganho_maximo": 1.2, "break_even": 40.8, "risco_retorno": 1.5,
        "liquidez": "alta", "healthbox_status": "confirma", "healthbox_score": 85,
        "healthbox": {"status_geral": "saudável"}, "tendencia": "alta",
        "vencimento": "2026-08-21", "vencimento_dias": 30, "campos_ausentes": [], "is_executable_price": True,
        "spread_disponivel": True, "score": 88, "status": "atenção",
    }
    acceptable_entry = {**conditional_base, **calculate_entry_conditions(conditional_base)}
    assert calculate_max_debit_allowed(conditional_base)["max_debit_allowed"] == 0.9091
    assert acceptable_entry["conditional_status"] == "entrada_condicional"
    expensive_base = {**conditional_base, "custo_liquido": 1.0, "perda_maxima": 1.0, "ganho_maximo": 1.0, "risco_retorno": 1.0}
    expensive_entry = {**expensive_base, **calculate_entry_conditions(expensive_base)}
    assert expensive_entry["conditional_status"] == "acompanhar_na_abertura"
    very_expensive_base = {**conditional_base, "custo_liquido": 1.2, "perda_maxima": 1.2, "ganho_maximo": 0.8, "risco_retorno": 0.6667}
    very_expensive_entry = {**very_expensive_base, **calculate_entry_conditions(very_expensive_base)}
    assert very_expensive_entry["conditional_status"] == "evitar"
    credit_low_base = {
        **conditional_base, "tipo_estrutura": "bull_put_spread", "strike_comprado": 38.0,
        "strike_vendido": 40.0, "premio_pago": 0.3, "premio_recebido": 0.5,
        "custo_liquido": None, "credito_liquido": 0.2, "perda_maxima": 1.8,
        "ganho_maximo": 0.2, "break_even": 39.8, "risco_retorno": 0.1111,
    }
    credit_low_entry = {**credit_low_base, **calculate_entry_conditions(credit_low_base)}
    assert calculate_min_credit_required(credit_low_base)["min_credit_required"] == 0.4
    assert credit_low_entry["conditional_status"] == "evitar"
    missing_loss_base = {**conditional_base, "perda_maxima": None}
    missing_loss_entry = {**missing_loss_base, **calculate_entry_conditions(missing_loss_base)}
    assert missing_loss_entry["conditional_status"] != "entrada_condicional"
    missing_price_base = {**conditional_base, "premio_pago": None, "custo_liquido": None, "perda_maxima": None}
    missing_price_entry = {**missing_price_base, **calculate_entry_conditions(missing_price_base)}
    assert missing_price_entry["conditional_status"] == "evitar"
    neutral_healthbox_base = {**conditional_base, "healthbox_status": "não confirma", "tendencia": "lateral"}
    neutral_healthbox_entry = {**neutral_healthbox_base, **calculate_entry_conditions(neutral_healthbox_base)}
    assert neutral_healthbox_entry["conditional_status"] == "acompanhar_na_abertura"
    eod_price_base = {**conditional_base, "data_frequency": "EOD"}
    eod_price_entry = {**eod_price_base, **calculate_entry_conditions(eod_price_base)}
    assert eod_price_entry["conditional_status"] == "acompanhar_na_abertura"
    assert not identify_hard_blockers(neutral_healthbox_entry) and identify_soft_warnings(neutral_healthbox_entry)
    assert candidate_has_complete_math(acceptable_entry) and candidate_has_usable_price(acceptable_entry)
    assert build_confirmation_rules(conditional_base)
    assert build_invalidation_rules(conditional_base)
    ranked_entries = rank_conditional_entries([missing_price_entry, credit_low_entry, expensive_entry, acceptable_entry], top_n=10)
    assert ranked_entries[0]["conditional_status"] == "entrada_condicional"
    conditional_summary = summarize_conditional_entries(ranked_entries)
    print(
        json.dumps(
            {
                "conditional_entry_engine_validation": "ok", "internet_called": False,
                "acceptable_debit": acceptable_entry["conditional_status"],
                "expensive_debit": expensive_entry["conditional_status"],
                "very_expensive_debit": very_expensive_entry["conditional_status"],
                "low_credit": credit_low_entry["conditional_status"],
                "missing_loss_never_entry": missing_loss_entry["conditional_status"] != "entrada_condicional",
                "missing_price": missing_price_entry["conditional_status"],
                "neutral_healthbox": neutral_healthbox_entry["conditional_status"],
                "eod_price_soft_warning": eod_price_entry["conditional_status"],
                "confirmation_rules": len(acceptable_entry["confirmation_rules"]),
                "invalidation_rules": len(acceptable_entry["invalidation_rules"]),
                "ranking_ok": True, "summary": conditional_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    today = datetime.now(timezone.utc).date()
    expiration_candidates = [
        (today + timedelta(days=3)).isoformat(), (today + timedelta(days=12)).isoformat(),
        (today + timedelta(days=25)).isoformat(), (today + timedelta(days=50)).isoformat(),
        (today + timedelta(days=75)).isoformat(),
    ]
    selected_expirations = _select_expirations(expiration_candidates, 7, 60, 4)
    assert [dte for _, dte in selected_expirations] == [25, 12, 50]
    preferred_entry = {**conditional_base, "vencimento_dias": 30, **calculate_entry_conditions({**conditional_base, "vencimento_dias": 30})}
    short_entry_base = {**conditional_base, "vencimento_dias": 7}
    short_entry = {**short_entry_base, **calculate_entry_conditions(short_entry_base)}
    very_short_base = {**conditional_base, "vencimento_dias": 3}
    very_short_entry = {**very_short_base, **calculate_entry_conditions(very_short_base)}
    long_entry_base = {**conditional_base, "vencimento_dias": 50}
    long_entry = {**long_entry_base, **calculate_entry_conditions(long_entry_base)}
    too_long_base = {**conditional_base, "vencimento_dias": 61}
    too_long_entry = {**too_long_base, **calculate_entry_conditions(too_long_base)}
    assert preferred_entry["expiration_quality"] == "preferido"
    assert short_entry["conditional_status"] == "acompanhar_na_abertura"
    assert very_short_entry["conditional_status"] == "evitar"
    assert long_entry["conditional_status"] == "acompanhar_na_abertura"
    assert too_long_entry["conditional_status"] == "evitar"
    near_miss_base = {**conditional_base, "custo_liquido": 1.2, "perda_maxima": 1.2, "ganho_maximo": 0.8, "risco_retorno": 0.6667, "vencimento_dias": 30}
    near_miss = {**near_miss_base, **calculate_entry_conditions(near_miss_base)}
    assert near_miss["conditional_status"] == "evitar"
    funnel_input = [preferred_entry, short_entry, near_miss, missing_price_entry]
    near_misses = find_near_miss_candidates(funnel_input, 10)
    assert near_misses and near_misses[0]["ativo"] == "TEST3"
    assert what_needs_to_change(near_miss)
    rejection_counts = count_rejection_reasons(funnel_input)
    assert "custo líquido acima do máximo" in rejection_counts
    funnel_summary = summarize_real_eod_funnel(funnel_input)
    assert funnel_summary["near_misses"]
    print(
        json.dumps(
            {
                "real_eod_funnel_validation": "ok", "internet_called": False,
                "selected_dtes": [dte for _, dte in selected_expirations],
                "preferred": preferred_entry["conditional_status"], "short": short_entry["conditional_status"],
                "very_short": very_short_entry["conditional_status"], "long": long_entry["conditional_status"],
                "too_long": too_long_entry["conditional_status"], "near_misses": len(near_misses),
                "rejection_reasons": rejection_counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    alias_raw = {
        "symbol": "TESTA450", "underlyingSymbol": "TEST3", "side": "C", "strike": "45.0",
        "expirationDate": "2026-08-21", "bid": None, "ask": None, "close": None, "average": None,
        "lastPrice": "2.35", "numberOfTrades": "25", "quantity": "1000", "financialVolume": "2350.5",
    }
    alias_normalized = options_provider.normalize_chain_response({"series": [alias_raw]})[0]
    assert alias_normalized["raw"] == alias_raw and "lastPrice" in alias_normalized["raw_keys"]
    assert alias_normalized["normalized_price"] == 2.35 and alias_normalized["normalized_price_basis"] == "alias_eod:lastPrice"
    assert alias_normalized["trades"] == 25 and alias_normalized["volume"] == 1000
    assert normalize_side("C") == "call" and to_float_or_none("2.35") == 2.35 and to_int_or_none("25") == 25
    assert pick_first_available(alias_raw, ("close", "lastPrice")) == ("2.35", "lastPrice")
    assert resolve_option_price(alias_normalized)["price_basis"] == "alias_eod:lastPrice"
    zero_price = resolve_option_price({"bid": 0, "ask": 0, "close": 0, "average": 0})
    assert zero_price["price"] is None and zero_price["price_basis"] == "preço_zerado"
    audit_fake_snapshots = {
        "TEST3": {
            "chains": [{"expiration_date": "2026-08-21", "series": [alias_normalized, *real_calls]}],
            "series": [alias_normalized, *real_calls], "success": True,
        }
    }
    audit_report = build_options_audit_report(audit_fake_snapshots)
    assert audit_report["summary"]["series_total"] == 3
    assert audit_report["summary"]["with_usable_price"] == 3
    assert "lastPrice" in audit_report["summary"]["possible_aliases"]
    assert find_possible_field_aliases(alias_normalized)["lastPrice"] == 1
    assert audit_option_series_fields(alias_normalized)["price"]["current_price_basis"] == "alias_eod:lastPrice"
    mixed_expiration_calls = [
        *real_calls,
        {**real_calls[0], "symbol": "TESTB100", "expiration_date": "2026-09-18", "strike": 40.0},
        {**real_calls[1], "symbol": "TESTB420", "expiration_date": "2026-09-18", "strike": 42.0},
    ]
    separated_pairs = pair_real_call_debit_spreads(mixed_expiration_calls)
    assert len(separated_pairs) == 2
    assert all(pair["vencimento"] in {"2026-08-21", "2026-09-18"} for pair in separated_pairs)
    print(
        json.dumps(
            {
                "options_data_audit_validation": "ok", "internet_called": False,
                "mid": price_mid["price_basis"], "close": price_close["price_basis"],
                "average": _indicative_price({"average": 1.4})["price_basis"],
                "missing": price_missing["price_basis"], "alias": alias_normalized["normalized_price_basis"],
                "raw_preserved": True, "zero_not_used": True, "pairing_separates_expirations": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
