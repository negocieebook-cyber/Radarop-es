from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from app.bulkowski_engine import analyze_pattern_for_asset, list_patterns
from app.data_contracts import CONTRACTS
from app.healthbox_engine import build_healthbox, healthbox_confirms_strategy, healthbox_score
from app.market_snapshot_engine import build_many_asset_snapshots, snapshot_to_healthbox
from app.options_snapshot_engine import (
    build_options_snapshot,
    fetch_options_expirations,
    load_options_snapshot,
    summarize_options_snapshot,
)
from app.options_update_orchestrator import (
    get_last_options_update_summary,
    load_all_options_snapshots,
    run_options_update,
)
from app.options_universe_discovery import (
    discover_options_availability,
    load_option_candidate_tickers,
    load_options_universe_availability,
    summarize_options_availability,
)
from app.real_opportunity_engine import (
    generate_real_eod_opportunities,
    load_real_options_snapshots,
    split_real_opportunities_by_status,
    summarize_real_opportunities,
)
from app.conditional_entry_engine import rank_conditional_entries, summarize_conditional_entries
from app.funnel_diagnostics import summarize_real_eod_funnel
from app.options_data_audit import build_options_audit_report
from app.pipeline_orchestrator import (
    load_graphical_theses_snapshot,
    load_real_opportunities_snapshot,
    run_pipeline,
)
from app.opening_watchlist import (
    EOD_NOTICE,
    add_to_opening_watchlist,
    build_manual_position,
    evaluate_watchlist_item,
    load_opening_watchlist,
    mark_as_converted,
    remove_from_opening_watchlist,
)
from app.graphical_watchlist import (
    add_to_graphical_watchlist,
    load_graphical_watchlist,
    remove_from_graphical_watchlist,
    summarize_graphical_watchlist,
)
from app.practical_strategy_view import build_practical_strategy_summary, matches_quick_objective_filter
from app.daily_priority_engine import build_daily_priority_list
from app.capital_requirements import classify_capital_fit, explain_capital_requirement
from app.user_trading_profile import load_user_trading_profile, save_user_trading_profile
from app.manual_trade_simulator import (
    SUPPORTED_STRATEGIES,
    build_manual_simulation_from_strategy,
    calculate_manual_strategy_risk,
    delete_manual_simulation,
    list_manual_simulations,
    save_manual_simulation,
)
from app.update_orchestrator import (
    default_watchlist,
    get_last_update_summary,
    load_market_snapshots,
    run_market_update,
)
from app.components import (
    alerts_section,
    inject_styles,
    metric_card,
    mock_badge,
    opportunity_card,
    positions_table,
    render_alert_card,
    render_action_summary,
    render_compact_thesis_card,
    render_data_notice,
    render_data_status_strip,
    render_decision_card,
    render_empty_state,
    render_info_panel,
    render_market_card,
    render_options_status_card,
    render_options_eod_status_card,
    render_real_opportunity_card,
    render_graphical_thesis_card,
    render_practical_strategy_card,
    render_full_strategy_screening,
    render_daily_priority_item,
    render_daily_priority_plan,
    render_manual_simulation,
    render_graphical_watchlist_card,
    render_real_engine_status_card,
    render_top_conditional_entries,
    render_update_status_card,
    render_section_title,
    render_status_badge,
    sources_table,
)
from app.mock_data import (
    MOCK_ALERTS,
    MOCK_ASSET_SNAPSHOTS,
    MOCK_MARKET_CONTEXT,
    MOCK_OPPORTUNITIES,
    MOCK_POSITIONS,
)
from app.options_math import calculate_option_strategy
from app.opportunity_engine import generate_daily_opportunities, split_opportunities_by_status
from app.position_monitor import build_position_status, generate_exit_alerts
from app.providers.provider_manager import fetch_historical, fetch_quotes, provider_status
from app.scoring import score_opportunity
from app.source_registry import build_source_summary, load_source_registry
from app.storage import (
    add_history_event,
    add_position,
    load_history,
    load_positions,
    save_history,
    save_positions,
)
from app.validators import build_operation_checklist
from app.universe import load_asset_universe


st.set_page_config(page_title="Radar de Opções Brasil", page_icon="📡", layout="wide")
inject_styles()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def history_event(event_type: str, opportunity: dict, message: str) -> dict:
    return {
        "id": str(uuid4()),
        "tipo": event_type,
        "ativo": opportunity.get("ativo"),
        "estrategia": opportunity.get("estrategia") or opportunity.get("estrutura_opcao_sugerida"),
        "data_hora": now_iso(),
        "mensagem": message,
        "tipo_dado": opportunity.get("tipo_dado", "MOCK / EXEMPLO"),
    }


def money(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value) if value is not None else "não calculado por falta de dados"


def render_global_risk_notice() -> None:
    render_data_notice(
        "Este painel não envia ordens. Dados EOD precisam ser validados no book. Prêmio não é lucro garantido."
    )


def prepare_graphical_theses() -> tuple[dict, list[dict]]:
    graphical_snapshot = load_graphical_theses_snapshot()
    theses = [dict(item) for item in graphical_snapshot.get("theses", [])]
    profile = load_user_trading_profile()
    for thesis in theses:
        screening = []
        for candidate in thesis.get("strategy_screening", []):
            enriched = dict(candidate)
            fit = classify_capital_fit(enriched, thesis, profile)
            enriched.update(fit)
            enriched["capital_fit_reason"] = explain_capital_requirement(enriched, thesis, profile)
            screening.append(enriched)
        thesis["strategy_screening"] = screening
        thesis.update(build_practical_strategy_summary(thesis))
    return graphical_snapshot, theses


def build_decision_panel_groups(theses: list[dict], near_setups: list[dict]) -> tuple[dict[str, list[dict]], dict]:
    groups = {"olhar_primeiro": [], "aguardar_gatilho": [], "evitar": []}
    near_assets = {item.get("ativo") for item in near_setups}
    for thesis in theses:
        action = str(thesis.get("practical_action") or "inconclusivo")
        if action == "olhar_no_book":
            groups["olhar_primeiro"].append(thesis)
        elif action in {"aguardar_gatilho", "acompanhar"} or thesis.get("ativo") in near_assets:
            groups["aguardar_gatilho"].append(thesis)
        else:
            groups["evitar"].append(thesis)
    groups["olhar_primeiro"] = sorted(groups["olhar_primeiro"], key=lambda item: item.get("near_setup_score") or 0, reverse=True)
    groups["aguardar_gatilho"] = sorted(groups["aguardar_gatilho"], key=lambda item: item.get("near_setup_score") or 0, reverse=True)
    groups["evitar"] = sorted(groups["evitar"], key=lambda item: item.get("near_setup_score") or 0, reverse=True)
    summary = {
        "validated": len(groups["olhar_primeiro"]),
        "near_entries": len(near_setups),
        "watching": len(groups["aguardar_gatilho"]),
        "avoid": sum(1 for item in theses if str(item.get("practical_action") or "") == "evitar_por_enquanto"),
        "inconclusive": sum(1 for item in theses if str(item.get("practical_action") or "inconclusivo") == "inconclusivo"),
        "top_asset": groups["olhar_primeiro"][0].get("ativo") if groups["olhar_primeiro"] else "nenhum",
    }
    return groups, summary


def build_events_summary() -> dict:
    snapshot = load_real_opportunities_snapshot()
    opportunities = snapshot.get("opportunities", []) if isinstance(snapshot, dict) else []
    today = datetime.now().date()
    dated = []
    for item in opportunities:
        vencimento = item.get("vencimento")
        try:
            event_date = datetime.fromisoformat(str(vencimento)).date()
        except (TypeError, ValueError):
            continue
        delta = (event_date - today).days
        if delta >= 0:
            dated.append({"ativo": item.get("ativo"), "date": event_date.isoformat(), "days": delta})
    dated.sort(key=lambda item: item["days"])
    return {
        "within_2": sum(item["days"] <= 2 for item in dated),
        "within_5": sum(item["days"] <= 5 for item in dated),
        "next_asset": dated[0]["ativo"] if dated else None,
        "next_date": dated[0]["date"] if dated else None,
        "risk": "atenção" if dated and dated[0]["days"] <= 2 else "informativo" if dated else "sem evento",
    }


def handle_thesis_card_action(thesis: dict, action: str | None, key_suffix: str) -> None:
    if action == "simulate":
        best = thesis.get("best_strategy") or {}
        candidate = next(
            (item for item in thesis.get("strategy_screening", []) if item.get("strategy_id") == best.get("strategy_id")),
            best,
        )
        st.session_state["manual_simulation_seed"] = {"candidate": candidate, "thesis": thesis}
        st.info("Simulador preparado com os dados atuais da tese.")
    elif action == "follow":
        result = add_to_graphical_watchlist(thesis)
        if result["added"]:
            add_history_event(history_event("acompanhar_tese_grafica", result["item"], "Tese gráfica adicionada à watchlist persistente."))
            st.success("Tese salva para acompanhamento. Nenhuma ordem foi enviada.")
        elif result["reason"] == "duplicado":
            st.info("Esta tese já está em acompanhamento.")
        else:
            st.warning("A tese não está elegível para acompanhamento.")
    elif action == "details":
        with st.expander(f"Detalhes técnicos · {thesis.get('ativo')} · {key_suffix}", expanded=True):
            best = thesis.get("best_strategy") or {}
            bulkowski = thesis.get("bulkowski_usado") or {}
            st.write(
                {
                    "Healthbox": {
                        "score": thesis.get("healthbox_score"),
                        "status": thesis.get("healthbox_status"),
                        "confirma": thesis.get("healthbox_confirmation"),
                    },
                    "Bulkowski": {
                        "padrão": bulkowski.get("nome_padrao"),
                        "status": thesis.get("bulkowski_status"),
                        "rompimento": bulkowski.get("rompimento"),
                    },
                    "Strategy Screener": thesis.get("strategy_screening", []),
                    "capital": {
                        "status": best.get("capital_fit_status"),
                        "motivo": best.get("capital_fit_reason"),
                        "capital_minimo": best.get("minimum_technical_capital"),
                        "capital_recomendado": best.get("recommended_capital"),
                    },
                    "plano_manual": (best.get("manual_validation_plan") or {}),
                    "checklist_book": (best.get("manual_validation_plan") or {}).get("book_checklist", []),
                    "motivos_rejeicao": best.get("rejection_rules", []),
                    "campos_ausentes": thesis.get("missing_graphical_fields", []) or best.get("missing_capital_fields", []),
                }
            )


def decision_panel_page() -> None:
    update_summary = get_last_update_summary()
    graphical_snapshot, theses = prepare_graphical_theses()
    near_setups = graphical_snapshot.get("near_setups", [])[:10]
    groups, summary = build_decision_panel_groups(theses, near_setups)
    events_summary = build_events_summary()
    summary["events"] = events_summary["within_5"]

    latest = update_summary.get("latest_update") or {}
    title_left, title_right = st.columns([0.7, 0.3])
    with title_left:
        st.markdown("# Painel de decisão")
        st.caption("O que merece atenção hoje")
    with title_right:
        header_bits = [
            '<span class="status-badge status-info">Dados EOD</span>',
            f'<span class="status-badge {"status-approved" if latest.get("success", False) else "status-warning" if latest else "status-neutral"}">{("Atualizado" if latest.get("success", False) else "Parcial" if latest else "Sem leitura")}</span>',
            f'<span class="status-badge status-neutral">{latest.get("finished_at") or "sem horário"}</span>',
        ]
        st.markdown(f'<div class="header-meta">{"".join(header_bits)}</div>', unsafe_allow_html=True)
        if st.button("Atualizar", key="decision_panel_update_header"):
            result = run_market_update(
                tickers=default_watchlist(),
                range="3mo",
                interval="1d",
                mode="intraday",
                runner="streamlit_app",
            )
            if result.get("success"):
                st.success("Atualização concluída.")
            else:
                st.warning("Atualização concluída com dados parciais ou indisponíveis.")
            st.rerun()

    render_data_notice("Este painel não envia ordens. Valide preços e liquidez no book.")
    render_action_summary(summary)

    has_any_data = any(summary[key] for key in ("validated", "near_entries", "events", "avoid"))
    if not has_any_data:
        render_empty_state("Nenhuma leitura disponível", "Execute o pipeline ou atualize os dados.")
        c1, c2 = st.columns(2)
        if c1.button("Atualizar dados", key="empty_state_update_data"):
            result = run_market_update(
                tickers=default_watchlist(),
                range="3mo",
                interval="1d",
                mode="intraday",
                runner="streamlit_app",
            )
            if result.get("success"):
                st.success("Atualização concluída.")
            else:
                st.warning("Atualização concluída com dados parciais ou indisponíveis.")
            st.rerun()
        if c2.button("Ver status do pipeline", key="empty_state_pipeline_status"):
            st.session_state["sidebar_page"] = "Configurações"
            st.rerun()
        return

    left_col, right_col = st.columns([0.65, 0.35], gap="large")

    with left_col:
        sections = (
            ("Prioridade de hoje", "O que merece validação primeiro no book.", "olhar_primeiro"),
            ("Aguardar gatilho", "Ideias que ainda dependem de confirmação.", "aguardar_gatilho"),
            ("Evitar por enquanto", "Bloqueios, contexto ruim ou risco sem confirmação.", "evitar"),
        )
        for title, subtitle, key in sections:
            render_section_title(title, subtitle)
            items = groups[key]
            if not items:
                st.caption("Sem itens nesta seção no momento.")
                continue
            for index, thesis in enumerate(items[:6]):
                event_label = (
                    f'{events_summary["next_asset"]} · {events_summary["next_date"]}'
                    if events_summary["next_asset"] == thesis.get("ativo") and events_summary["next_date"]
                    else "sem evento próximo"
                )
                action = render_decision_card(
                    {
                        "card_key": f"decision_panel_{key}_{index}_{thesis.get('ativo')}",
                        "source_label": "PAINEL",
                        "ativo": thesis.get("ativo"),
                        "action_status": thesis.get("practical_action"),
                        "action_label": thesis.get("practical_action"),
                        "strategy_name": (thesis.get("best_strategy") or {}).get("strategy_name") or thesis.get("preferred_strategy"),
                        "score": (thesis.get("best_strategy") or {}).get("score") or thesis.get("near_setup_score"),
                        "event_label": event_label,
                        "gatilho_confirmacao": thesis.get("gatilho_confirmacao"),
                        "invalidacao": thesis.get("invalidacao"),
                        "cadeia_opcoes_status": thesis.get("cadeia_opcoes_status"),
                        "reason": (thesis.get("best_strategy") or {}).get("reason") or thesis.get("evaluation_reason"),
                    }
                )
                handle_thesis_card_action(thesis, action, f"{key}_{index}")

    with right_col:
        render_info_panel(
            "Eventos próximos",
            [
                ("Até 2 dias", events_summary["within_2"]),
                ("Até 5 dias", events_summary["within_5"]),
                ("Próximo ativo", events_summary["next_asset"] or "Nenhum resultado confirmado no período."),
                ("Data", events_summary["next_date"] or "indisponível"),
            ],
        )
        render_info_panel(
            "Status do pipeline",
            [
                ("Leitura", "Atualizado" if latest.get("success", False) else "Parcial" if latest else "Sem leitura"),
                ("Horário", latest.get("finished_at") or "indisponível"),
                ("Modo", latest.get("mode") or "indisponível"),
                ("Origem", latest.get("runner") or "indisponível"),
            ],
        )
        render_info_panel(
            "Qualidade dos dados",
            [
                ("Status", latest.get("source") or "indisponível"),
                ("Atualizados", latest.get("updated_count", 0)),
                ("Incompletos", latest.get("incomplete_count", 0)),
                ("Erros", latest.get("error_count", 0)),
            ],
        )
        render_info_panel(
            "Avisos importantes",
            [
                ("Regra 1", "Nenhuma tese vira ordem automaticamente."),
                ("Regra 2", "Dados EOD exigem conferência de preço e liquidez."),
                ("Regra 3", "MOCK e real continuam separados."),
                ("Risco", events_summary["risk"]),
            ],
        )

    if st.session_state.get("manual_simulation_seed"):
        with st.expander("Simular manualmente", expanded=True):
            manual_simulator_form(st.session_state["manual_simulation_seed"], "decision_panel_manual")


def manual_simulator_form(seed: dict | None = None, key_prefix: str = "manual") -> None:
    seed = seed or {}
    thesis = seed.get("thesis") or {}
    candidate = seed.get("candidate") or seed
    initial_strategy = str(candidate.get("strategy_id") or "long_call")
    if initial_strategy not in SUPPORTED_STRATEGIES:
        initial_strategy = "long_call"
    with st.form(f"{key_prefix}_form"):
        header = st.columns(4)
        strategy_id = header[0].selectbox("Estratégia", list(SUPPORTED_STRATEGIES), index=list(SUPPORTED_STRATEGIES).index(initial_strategy), key=f"{key_prefix}_strategy")
        ticker = header[1].text_input("Ativo", value=str(thesis.get("ativo") or seed.get("ticker") or ""), key=f"{key_prefix}_ticker")
        expiration = header[2].text_input("Vencimento", value=str(candidate.get("expiration") or ""), key=f"{key_prefix}_expiration")
        quantity = header[3].number_input("Quantidade de contratos", min_value=1, value=1, step=1, key=f"{key_prefix}_quantity")
        settings = st.columns(2)
        default_multiplier = load_user_trading_profile().get("multiplicador_contrato_padrao")
        multiplier_text = settings[0].text_input("Multiplicador do contrato", value="" if default_multiplier is None else str(default_multiplier), key=f"{key_prefix}_multiplier")
        has_underlying = settings[1].checkbox("Tenho o ativo em carteira", value=False, key=f"{key_prefix}_underlying", disabled=strategy_id != "covered_call")
        template = build_manual_simulation_from_strategy({**candidate, "strategy_id": strategy_id, "strategy_name": strategy_id}, thesis)
        legs = []
        st.markdown("#### Pernas manuais")
        for index, leg in enumerate(template.get("legs", [])):
            columns = st.columns((1, 1, 1, 1, 1))
            columns[0].text_input("Tipo", value=leg["type"], disabled=True, key=f"{key_prefix}_type_{strategy_id}_{index}")
            columns[1].text_input("Ação", value=leg["action"], disabled=True, key=f"{key_prefix}_action_{strategy_id}_{index}")
            strike_text = columns[2].text_input("Strike", value="", disabled=leg["type"] == "stock", key=f"{key_prefix}_strike_{strategy_id}_{index}")
            premium_label = "Preço do ativo" if leg["type"] == "stock" else "Prêmio"
            premium_text = columns[3].text_input(premium_label, value="", key=f"{key_prefix}_premium_{strategy_id}_{index}")
            leg_quantity = columns[4].number_input("Qtd. perna", min_value=1, value=1, step=1, key=f"{key_prefix}_leg_quantity_{strategy_id}_{index}")
            def optional_number(value: str) -> float | None:
                try:
                    return float(value.replace(",", ".")) if value.strip() else None
                except ValueError:
                    return None
            legs.append({**leg, "strike": optional_number(strike_text), "premium": optional_number(premium_text), "quantity": leg_quantity, "expiration": expiration or None})
        calculate = st.form_submit_button("Calcular simulação")
    if calculate:
        try:
            multiplier = float(multiplier_text.replace(",", ".")) if multiplier_text.strip() else None
        except ValueError:
            multiplier = None
        simulation = {
            **template,
            "ticker": ticker or None,
            "strategy_id": strategy_id,
            "strategy_name": strategy_id,
            "expiration": expiration or None,
            "quantity": quantity,
            "contract_multiplier": multiplier,
            "has_underlying_position": has_underlying,
            "legs": legs,
            "source": "manual",
        }
        st.session_state[f"{key_prefix}_result"] = calculate_manual_strategy_risk(simulation, load_user_trading_profile())
    result = st.session_state.get(f"{key_prefix}_result")
    if result:
        render_manual_simulation(result)
        if st.button("Salvar simulação manual", key=f"{key_prefix}_save"):
            saved = save_manual_simulation(result)
            st.session_state[f"{key_prefix}_result"] = saved
            st.success("Simulação manual salva. Nenhuma ordem foi criada.")


def manual_simulations_page() -> None:
    st.header("Simulador")
    st.warning("Valores desta tela são digitados manualmente e não são cotações validadas. Nenhuma ordem é enviada.")
    manual_simulator_form(st.session_state.get("manual_simulation_seed"), "manual_page")
    st.markdown("## Simulações salvas")
    simulations = list_manual_simulations()
    if not simulations:
        st.info("Nenhuma simulação manual salva.")
    for index, simulation in enumerate(simulations):
        render_manual_simulation(simulation)
        if st.button("Excluir simulação", key=f"delete_manual_{index}_{simulation.get('simulation_id')}"):
            delete_manual_simulation(str(simulation.get("simulation_id")))
            st.rerun()


def evaluate_opportunity(opportunity: dict) -> dict:
    calculation = calculate_option_strategy(opportunity)
    snapshot = next((item for item in MOCK_ASSET_SNAPSHOTS if item["ativo"] == opportunity["ativo"]), {})
    healthbox = build_healthbox(snapshot)
    healthbox_score_result = healthbox_score(healthbox)
    healthbox_confirmation = healthbox_confirms_strategy(healthbox, opportunity.get("tipo_estrutura", ""))
    evaluated = {
        **opportunity,
        "calculation": calculation,
        "healthbox": healthbox,
        "healthbox_score_result": healthbox_score_result,
        "healthbox_confirmation": healthbox_confirmation,
    }
    score_result = score_opportunity(evaluated)
    bulkowski = analyze_pattern_for_asset(snapshot)
    bullish_strategy = opportunity.get("tipo_estrutura") in {"call_debit_spread", "bull_put_spread"}
    if not bulkowski["pattern_detected"]:
        alignment = "Bulkowski: inconclusivo por falta de dados."
    elif bullish_strategy and "alta" in str(bulkowski["direcao_teorica"]).lower() and bulkowski["confirmacao"] == "confirmado no mock":
        alignment = "Favorece a estrutura de alta apenas no cenário MOCK confirmado."
    elif opportunity.get("tipo_estrutura") == "covered_call" and bulkowski["nome_padrao"] == "Retângulo":
        alignment = "Compatível com lateralidade, mas sem confirmação direcional."
    else:
        alignment = "Não favorece a estratégia de forma conclusiva."
    per_lot = calculation.get("per_lot") or {}
    evaluated.update(
        score=score_result.get("score"),
        score_result=score_result,
        checklist=build_operation_checklist(evaluated),
        bulkowski_analysis=bulkowski,
        bulkowski_alignment=alignment,
        strike_comprado=money(opportunity.get("strike_comprado")) if isinstance(opportunity.get("strike_comprado"), (int, float)) else opportunity.get("strike_comprado", "indisponível"),
        strike_vendido=money(opportunity.get("strike_vendido")) if isinstance(opportunity.get("strike_vendido"), (int, float)) else opportunity.get("strike_vendido", "indisponível"),
        premio_liquido=money(calculation.get("net_cost") if calculation.get("net_cost") is not None else calculation.get("net_credit")),
        perda_maxima=money(per_lot.get("max_loss") if per_lot else calculation.get("max_loss")),
        ganho_maximo=money(per_lot.get("max_profit") if per_lot else calculation.get("max_profit")),
        break_even=money(calculation.get("break_even")),
    )
    return evaluated


def register_quick_decision(action: str, opportunity: dict) -> None:
    if action == "skip":
        add_history_event(
            history_event(
                "nao_entrou",
                opportunity,
                "Decisão registrada: não entrou na oportunidade MOCK / EXEMPLO.",
            )
        )
        st.success(f"Decisão sobre {opportunity['ativo']} registrada no histórico.")
    elif action == "watch":
        add_history_event(
            history_event(
                "acompanhar_sem_entrar",
                opportunity,
                "Oportunidade MOCK / EXEMPLO marcada para acompanhamento sem entrada.",
            )
        )
        st.success(f"{opportunity['ativo']} foi marcada para acompanhamento.")


def entry_form(opportunity: dict) -> None:
    calculation = calculate_option_strategy(opportunity)
    per_lot = calculation.get("per_lot") or {}
    st.markdown("## Confirmar entrada — MOCK / EXEMPLO")
    st.warning(
        "Este formulário apenas salva um registro local. Não envia ordens e não se conecta a corretora."
    )
    with st.form("entry-form", clear_on_submit=False):
        left, right = st.columns(2)
        left.text_input("Ativo", value=opportunity["ativo"], disabled=True)
        right.text_input("Estratégia", value=opportunity["estrategia"], disabled=True)
        st.text_input(
            "Preço planejado (MOCK / EXEMPLO)",
            value=f"R$ {opportunity['preco_planejado']:.2f}".replace(".", ","),
            disabled=True,
        )
        price_col, quantity_col, date_col = st.columns(3)
        real_price = price_col.number_input(
            "Preço real de entrada",
            min_value=0.01,
            value=float(opportunity["preco_planejado"]),
            step=0.01,
            format="%.2f",
        )
        quantity = quantity_col.number_input(
            "Quantidade", min_value=1, value=1, step=1
        )
        entry_date = date_col.date_input("Data de entrada", value=date.today())
        note = st.text_area("Observação", placeholder="Contexto da decisão (opcional)")
        confirmed = st.form_submit_button("Confirmar entrada", type="primary")

    if confirmed:
        position = {
            "id": str(uuid4()),
            "opportunity_id": opportunity["id"],
            "ativo": opportunity["ativo"],
            "estrategia": opportunity["estrategia"],
            "tipo_estrutura": opportunity["tipo_estrutura"],
            "status": "em acompanhamento",
            "preco_planejado": opportunity["preco_planejado"],
            "preco_real_entrada": float(real_price),
            "quantidade": int(quantity),
            "data_entrada": entry_date.isoformat(),
            "observacao": note.strip(),
            "tipo_dado": "MOCK / EXEMPLO",
            "fonte": opportunity.get("fonte", "indisponível"),
            "fonte_oportunidade": "mock interno",
            "ganho_maximo": per_lot.get("max_profit", calculation.get("max_profit")),
            "perda_maxima": per_lot.get("max_loss", calculation.get("max_loss")),
            "ganho_maximo_por_unidade": calculation.get("max_profit"),
            "perda_maxima_por_unidade": calculation.get("max_loss"),
            "valores_maximos_escopo": "lote" if per_lot else "unidade",
            "break_even": calculation.get("break_even"),
            "vencimento_dias": opportunity["vencimento_dias"],
            "strikes": {
                "comprado": opportunity["strike_comprado"],
                "vendido": opportunity["strike_vendido"],
            },
            "created_at": now_iso(),
        }
        add_position(position)
        add_history_event(
            history_event(
                "entrada_confirmada",
                opportunity,
                f"Entrada MOCK / EXEMPLO confirmada: quantidade {int(quantity)}, preço R$ {real_price:.2f}.",
            )
        )
        st.session_state.pop("entry_opportunity_id", None)
        st.success(
            f"Entrada de {opportunity['ativo']} salva localmente. Nenhuma ordem foi enviada."
        )


def opportunity_detail(opportunity: dict) -> None:
    calculation = opportunity.get("calculation", {})
    healthbox = opportunity.get("healthbox", {})
    bulkowski = opportunity.get("bulkowski_analysis", {})
    st.markdown("## Detalhe da Oportunidade")
    mock_badge("DETALHE MOCK / EXEMPLO")
    summary = st.columns(5)
    for column, (label, value) in zip(
        summary,
        [
            ("Ativo", opportunity.get("ativo", "indisponível")),
            ("Estratégia", opportunity.get("estrategia", "indisponível")),
            ("Status", opportunity.get("status", "indisponível")),
            ("Decisão", opportunity.get("decisao", "esperar")),
            ("Score", opportunity.get("score", "não calculado")),
        ],
    ):
        column.metric(label, value if value is not None else "não calculado")
    st.info(f"**Motivo principal:** {opportunity.get('motivo', 'indisponível')}")

    st.markdown("### Matemática da operação")
    math_rows = [
        ("Estrutura", opportunity.get("tipo_estrutura")),
        ("Strike comprado", opportunity.get("strike_comprado")),
        ("Strike vendido", opportunity.get("strike_vendido")),
        ("Vencimento", f"{opportunity.get('vencimento_dias', 'indisponível')} dias"),
        ("Prêmio pago", opportunity.get("premio_pago", "indisponível")),
        ("Prêmio recebido", opportunity.get("premio_recebido", "indisponível")),
        ("Custo líquido", calculation.get("net_cost", "indisponível")),
        ("Crédito líquido", calculation.get("net_credit", "indisponível")),
        ("Ganho máximo", calculation.get("max_profit", "indisponível")),
        ("Perda máxima", calculation.get("max_loss", "indisponível")),
        ("Break-even", calculation.get("break_even", "indisponível")),
        ("Risco/retorno", calculation.get("risk_reward", "indisponível")),
        ("Campos ausentes", ", ".join(opportunity.get("campos_ausentes", [])) or "nenhum"),
    ]
    math_rows = [(label, str(value) if value is not None else "indisponível") for label, value in math_rows]
    st.dataframe(pd.DataFrame(math_rows, columns=["Campo", "Valor"]), width="stretch", hide_index=True)

    st.markdown("### Leitura gráfica")
    graph_rows = [
        ("Tendência", healthbox.get("tendencia", "indisponível")),
        ("Suporte", healthbox.get("suporte", "indisponível")),
        ("Resistência", healthbox.get("resistencia", "indisponível")),
        ("Rompimento", bulkowski.get("rompimento", "indisponível")),
        ("Pullback/throwback", bulkowski.get("pullback_throwback", "indisponível")),
        ("Healthbox score", opportunity.get("healthbox_score_result", {}).get("score", "não calculado")),
        ("Healthbox confirma", opportunity.get("healthbox_status", "indisponível")),
        ("Padrão Bulkowski", bulkowski.get("nome_padrao", "padrão não detectado")),
        ("Bulkowski confirmação", bulkowski.get("confirmacao", "indisponível")),
        ("Favorece a operação", opportunity.get("bulkowski_alignment", "inconclusivo")),
    ]
    graph_rows = [(label, str(value) if value is not None else "indisponível") for label, value in graph_rows]
    st.dataframe(pd.DataFrame(graph_rows, columns=["Leitura", "Resultado"]), width="stretch", hide_index=True)

    st.markdown("### Checklist da operação")
    checklist = list(opportunity.get("checklist", []))
    checklist.extend(
        [
            {"question": "Bulkowski confirma?", "status": "ok" if bulkowski.get("confirmacao") == "confirmado no mock" else "atenção", "detail": bulkowski.get("confirmacao", "indisponível")},
            {"question": "Melhor operar ou esperar?", "status": "ok" if opportunity.get("status") == "aprovada" else "atenção", "detail": opportunity.get("decisao", "esperar")},
        ]
    )
    for item in checklist:
        icon = "🟢" if item.get("status") == "ok" else "🟡" if item.get("status") in {"atenção", "não calculado"} else "⚪" if item.get("status") == "indisponível" else "🔴"
        st.markdown(f"{icon} **{item.get('question')}** — {item.get('detail', 'indisponível')}")

    st.markdown("### Controle de dados")
    st.write(
        {
            "fonte": opportunity.get("fonte", "fonte ausente"),
            "tipo_dado": opportunity.get("tipo_dado", "indisponível"),
            "status_dado": opportunity.get("status_dado", "indisponível"),
            "campos_ausentes": opportunity.get("campos_ausentes", []),
        }
    )
    decision = "Evitar" if opportunity.get("status") == "reprovada" else opportunity.get("decisao", "esperar").title()
    st.markdown(f"### Decisão final: {decision}")
    if opportunity.get("status") == "reprovada":
        st.error("A operação não passou nos filtros mínimos.")


def show_opportunities(opportunities: list[dict] | None = None) -> None:
    opportunities = generate_daily_opportunities() if opportunities is None else opportunities
    groups = split_opportunities_by_status(opportunities)
    st.markdown("## Oportunidades geradas pelo motor")
    for status, title in (("aprovada", "Aprovadas"), ("atenção", "Atenção")):
        st.markdown(f"### {title} ({len(groups[status])})")
        if not groups[status]:
            st.info(f"Nenhuma oportunidade em {title.lower()} nesta execução MOCK / EXEMPLO.")
            continue
        items = groups[status]
        for start in range(0, len(items), 2):
            columns = st.columns(2)
            for column, opportunity in zip(columns, items[start : start + 2]):
                with column:
                    action = opportunity_card(opportunity)
                    if action == "enter":
                        st.session_state["entry_opportunity_id"] = opportunity["id"]
                    elif action == "detail":
                        st.session_state["detail_opportunity_id"] = opportunity["id"]
                    elif action:
                        register_quick_decision(action, opportunity)

    for status, title in (("reprovada", "Reprovadas"), ("score não calculado", "Score não calculado")):
        st.markdown(f"### {title} ({len(groups[status])})")
        if groups[status]:
            rows = [
                {
                    "Ativo": item["ativo"],
                    "Estratégia": item.get("estrategia", "nenhuma"),
                    "Motivo": item["motivo"],
                    "Campos ausentes": ", ".join(item.get("campos_ausentes", [])) or "nenhum",
                    "Por que não operar": item["motivo"],
                    "Tipo do dado": item["tipo_dado"],
                }
                for item in groups[status]
            ]
            with st.expander(f"Ver {len(rows)} operações em {title.lower()} e seus motivos", expanded=False):
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.caption("Nenhum item nesta categoria.")

    selected_id = st.session_state.get("entry_opportunity_id")
    selected = next((item for item in opportunities if item["id"] == selected_id), None)
    if selected:
        entry_form(selected)
    detail_id = st.session_state.get("detail_opportunity_id")
    detailed = next((item for item in opportunities if item["id"] == detail_id), None)
    if detailed:
        opportunity_detail(detailed)


def show_data_control() -> None:
    st.markdown("## Controle de Fonte dos Dados")
    st.info(
        "**Mockados:** exemplos explícitos. **Indisponíveis:** fonte/valor ausente. "
        "**Calculados:** exigem fórmula e entradas válidas. **Estimados:** exigem modelo e rótulo. "
        "Sem dado crítico, nenhum score ou oportunidade real deve ser produzido."
    )
    rows = []
    for opportunity in MOCK_OPPORTUNITIES:
        for field in ("strike_comprado", "strike_vendido", "premio_pago", "premio_recebido", "liquidez_status", "grafico_status"):
            rows.append(
                {
                    "Ativo": opportunity["ativo"],
                    "Campo": field,
                    "Fonte": opportunity.get("fonte", "fonte ausente"),
                    "Tipo do dado": opportunity.get("tipo_dado", "indisponível"),
                    "Status": "mock/exemplo" if opportunity.get(field) is not None else "indisponível",
                    "Observação": "valor demonstrativo" if opportunity.get(field) is not None else "campo ausente",
                }
            )
    sources_table(rows)


def show_bulkowski_engine() -> None:
    st.markdown("## Bulkowski Pattern Engine — exemplo estrutural")
    st.warning(
        "Base mockada. Nenhuma estatística real foi coletada ainda. O sistema não copia texto integral do ThePatternSite. Estatísticas ausentes aparecem como indisponível."
    )
    patterns = list_patterns()
    catalog_rows = [
        {
            "ID": item["id"],
            "Padrão": item["nome"],
            "Categoria": item["categoria"],
            "Tipo": item["tipo"],
            "Direção teórica": item["direcao_teorica"],
            "Taxa de falha": item["taxa_falha"],
            "Status": item["status_dado"],
        }
        for item in patterns
    ]
    with st.expander(f"Padrões disponíveis na base mockada ({len(catalog_rows)})"):
        st.dataframe(pd.DataFrame(catalog_rows), width="stretch", hide_index=True)

    analyses = [analyze_pattern_for_asset(snapshot) for snapshot in MOCK_ASSET_SNAPSHOTS]
    analysis_rows = [
        {
            "Ativo": item["ativo"],
            "Padrão detectado": item["nome_padrao"],
            "Tipo": item["tipo"],
            "Direção teórica": item["direcao_teorica"],
            "Confirmação": item["confirmacao"],
            "Rompimento": item["rompimento"],
            "Pullback/throwback": item["pullback_throwback"],
            "Alvo técnico": item["alvo_tecnico_metodo"],
            "Taxa de falha": item["taxa_falha"],
            "Movimento médio pós-rompimento": item["movimento_medio_pos_rompimento"],
            "Confiabilidade": item["confiabilidade"],
            "Fonte": item["fonte_nome"],
            "Status": item["status"],
        }
        for item in analyses
    ]
    st.markdown("### Análise por ativo")
    st.dataframe(pd.DataFrame(analysis_rows), width="stretch", hide_index=True)
    if any(not item["pattern_detected"] for item in analyses):
        st.info("Ativos sem padrão: padrão não detectado — não usar leitura gráfica como confirmação.")


def show_healthbox_engine() -> None:
    st.markdown("## Stock Healthbox Engine — exemplo estrutural")
    st.warning(
        "Base mockada. Nenhum dado real de mercado foi coletado ainda. Campos ausentes não são preenchidos por chute. Healthbox é filtro, não recomendação isolada."
    )
    strategies = {
        "PETR4": "call_debit_spread",
        "VALE3": "bull_put_spread",
        "ITUB4": "covered_call",
        "BOVA11": "put_debit_spread",
        "ABEV3": "covered_call",
    }
    def display_value(value: object, suffix: str = "") -> str:
        return f"{value:.2f}{suffix}" if isinstance(value, (int, float)) else "indisponível"

    rows = []
    for snapshot in MOCK_ASSET_SNAPSHOTS:
        healthbox = build_healthbox(snapshot)
        score_result = healthbox_score(healthbox)
        confirmation = healthbox_confirms_strategy(healthbox, strategies.get(snapshot["ativo"], ""))
        rows.append(
            {
                "Ativo": healthbox["ativo"],
                "Tendência": healthbox["tendencia"],
                "Variação diária": display_value(healthbox["variacao_diaria_percent"], "%"),
                "Range diário": display_value(healthbox["range_diario_percent"], "%"),
                "ADR": display_value(healthbox["adr_percent"], "%"),
                "ATR": display_value(healthbox["atr_percent"], "%"),
                "rVol": display_value(healthbox["rvol"], "x"),
                "RSI": display_value(healthbox["rsi"]),
                "RSI 200": display_value(healthbox["rsi_200"]),
                "Suporte": display_value(healthbox["suporte"]),
                "Resistência": display_value(healthbox["resistencia"]),
                "Distância suporte": display_value(healthbox["distancia_suporte_percent"], "%"),
                "Distância resistência": display_value(healthbox["distancia_resistencia_percent"], "%"),
                "Score": str(score_result["score"]) if score_result["score"] is not None else "score não calculado",
                "Confirmação": confirmation,
                "Campos ausentes": ", ".join(healthbox["campos_ausentes"]) or "nenhum",
                "Tipo de dado": healthbox["tipo_dado"],
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def show_graphical_radar() -> None:
    graphical_snapshot = load_graphical_theses_snapshot()
    theses = graphical_snapshot.get("theses", [])
    summary = graphical_snapshot.get("summary", {})
    st.markdown("## Radar Gráfico de Regiões")
    profile = load_user_trading_profile()
    with st.expander("Perfil de capital", expanded=False):
        capital_columns = st.columns(3)
        capital_available = capital_columns[0].text_input("Capital disponível", value="" if profile.get("capital_disponivel") is None else str(profile["capital_disponivel"]), key="capital_available")
        max_loss = capital_columns[1].text_input("Perda máxima por operação", value="" if profile.get("perda_maxima_por_operacao") is None else str(profile["perda_maxima_por_operacao"]), key="capital_max_loss")
        max_percent = capital_columns[2].text_input("Percentual máximo por operação", value="" if profile.get("percentual_maximo_por_operacao") is None else str(profile["percentual_maximo_por_operacao"]), key="capital_max_percent")
        setting_columns = st.columns(3)
        multiplier = setting_columns[0].text_input("Multiplicador padrão", value="" if profile.get("multiplicador_contrato_padrao") is None else str(profile["multiplicador_contrato_padrao"]), key="capital_multiplier")
        use_multiplier = setting_columns[1].checkbox("Usar multiplicador padrão se a fonte estiver ausente", value=bool(profile.get("usar_multiplicador_padrao_se_fonte_ausente")), key="capital_use_multiplier")
        tolerance = setting_columns[2].selectbox("Tolerância", ["moderada", "conservadora", "agressiva"], index=["moderada", "conservadora", "agressiva"].index(profile.get("tolerancia_capital", "moderada")), key="capital_tolerance")
        if st.button("Salvar perfil de capital", key="save_capital_profile"):
            def optional_number(value: str) -> float | None:
                return float(value.replace(",", ".")) if value.strip() else None
            try:
                save_user_trading_profile({
                    "capital_disponivel": optional_number(capital_available),
                    "perda_maxima_por_operacao": optional_number(max_loss),
                    "percentual_maximo_por_operacao": optional_number(max_percent),
                    "multiplicador_contrato_padrao": optional_number(multiplier),
                    "usar_multiplicador_padrao_se_fonte_ausente": use_multiplier,
                    "tolerancia_capital": tolerance,
                })
                st.success("Perfil salvo. As estimativas sem fonte continuam pendentes, salvo uso explícito do multiplicador padrão.")
                st.rerun()
            except ValueError:
                st.error("Use apenas números válidos nos campos de capital.")
        st.caption("Capital estimado não substitui a margem exigida pela corretora. Cabe apertado não significa proibido; indica risco relevante para o capital informado.")
    for column, (label, key) in zip(st.columns(7), (
        ("Compra", "compra_operavel"), ("Interesse compra", "interesse_compra"),
        ("Venda", "venda_operavel"), ("Interesse venda", "interesse_venda"),
        ("Neutras", "neutra_observar"), ("Evitar", "evitar"), ("Inconclusivas", "inconclusiva"),
    )):
        column.metric(label, summary.get(key, 0))
    near_setups = graphical_snapshot.get("near_setups", [])[:10]
    if not theses:
        st.info("Nenhuma tese gráfica automática salva ainda. Execute o pipeline.")
        return
    for thesis in theses:
        for candidate in thesis.get("strategy_screening", []):
            fit = classify_capital_fit(candidate, thesis, profile)
            candidate.update(fit)
            candidate["capital_fit_reason"] = explain_capital_requirement(candidate, thesis, profile)
        thesis.update(build_practical_strategy_summary(thesis))

    priorities = build_daily_priority_list(theses, limit_per_objective=5)
    priority_groups = (
        ("Top para prêmio", "top_premio", "Prêmio não é lucro garantido. Validar perda máxima, break-even, spread e liquidez."),
        ("Top direcionais", "top_direcionais", "Depende do movimento do ativo. Validar gatilho gráfico e custo da opção."),
        ("Top lateralidade/range", "top_lateralidade", "Depende de suporte, resistência e permanência no range."),
        ("Top proteção/carteira", "top_protecao_carteira", "Proteção tem custo; confirmar posse ou aceitação do ativo."),
        ("Top volatilidade/evento", "top_volatilidade_evento", "Exige movimento suficiente para pagar o custo da estrutura."),
        ("Evitar por enquanto", "evitar_por_enquanto", "Teses com bloqueios ou contexto gráfico desfavorável."),
        ("Inconclusivas", "inconclusivas", "Dados insuficientes; aguardar nova coleta."),
    )
    st.markdown("### Prioridades por Objetivo")
    priority_tabs = st.tabs([label for label, _, _ in priority_groups])
    for tab, (label, group, warning) in zip(priority_tabs, priority_groups):
        with tab:
            st.caption(warning)
            items = priorities.get(group, [])
            if not items:
                st.info("Nenhuma prioridade nesta categoria com os dados atuais.")
            for priority_index, priority in enumerate(items):
                render_daily_priority_item(priority)
                render_daily_priority_plan(priority, f"priority_plan_{group}_{priority_index}")
                if priority.get("capital_fit_status") == "pendente_dados" and st.button("Simular manualmente", key=f"simulate_priority_{group}_{priority_index}_{priority.get('ativo')}"):
                    st.session_state["manual_simulation_seed"] = {"candidate": priority, "thesis": priority.get("thesis") or {}}
                if st.button("Acompanhar tese gráfica", key=f"follow_priority_{group}_{priority_index}_{priority.get('ativo')}"):
                    result = add_to_graphical_watchlist(priority.get("thesis") or {})
                    if result["added"]:
                        add_history_event(history_event("acompanhar_tese_grafica", result["item"], "Tese gráfica adicionada pela prioridade diária."))
                        st.success("Tese gráfica salva. Nenhuma entrada ou ordem foi registrada.")
                    elif result["reason"] == "duplicado":
                        st.info("Esta tese gráfica já está sendo acompanhada.")
                    else:
                        st.warning("A tese não está elegível para acompanhamento.")

    if st.session_state.get("manual_simulation_seed"):
        with st.expander("Simular com dados do book", expanded=True):
            manual_simulator_form(st.session_state["manual_simulation_seed"], "priority_manual")

    quick_columns = st.columns(2)
    quick_filter = quick_columns[0].selectbox(
        "Filtro rápido",
        ["Todos", "Só prêmio", "Só direcional", "Só lateralidade", "Só proteção/carteira", "Só volatilidade", "Evitar"],
        key="quick_priority_filter",
    )
    capital_filter = quick_columns[1].selectbox(
        "Encaixe no capital",
        ["todos", "cabe_bem", "cabe_apertado", "acima_do_capital", "pendente_dados"],
        key="capital_fit_filter",
    )

    filter_columns = st.columns(5)
    regime_filter = filter_columns[0].selectbox("Regime", ["todos", "alta", "queda", "lateral", "compressão", "indefinido"], key="practical_regime_filter")
    status_filter = filter_columns[1].selectbox("Status da tese", ["todos", "compra", "venda", "interesse", "neutro", "evitar"], key="practical_status_filter")
    strategy_filter = filter_columns[2].selectbox("Estratégia", ["todas", "trava", "iron condor", "butterfly", "calendar", "call", "put"], key="practical_strategy_filter")
    action_filter = filter_columns[3].selectbox("Ação prática", ["todas", "olhar_no_book", "acompanhar", "aguardar_gatilho", "evitar_por_enquanto", "inconclusivo"], key="practical_action_filter")
    objective_filter = filter_columns[4].selectbox("Objetivo", ["todos", "para prêmio", "direcional", "proteção", "carteira", "lateralidade", "volatilidade", "estudo avançado"], key="practical_objective_filter")

    def matches_filters(item: dict) -> bool:
        regime = str(item.get("market_regime") or "")
        status = str(item.get("status") or "")
        strategy = str((item.get("best_strategy") or {}).get("strategy_name") or "").lower()
        objective = str((item.get("best_strategy") or {}).get("strategy_objective") or item.get("practical_objective") or "")
        capital_fit = str((item.get("best_strategy") or {}).get("capital_fit_status") or "pendente_dados")
        regime_ok = regime_filter == "todos" or (regime_filter == "alta" and regime.startswith("alta_")) or (regime_filter == "queda" and regime.startswith("queda_")) or (regime_filter == "lateral" and regime == "lateral") or (regime_filter == "compressão" and regime == "compressao") or (regime_filter == "indefinido" and regime == "indefinido")
        status_ok = status_filter == "todos" or (status_filter == "compra" and status == "compra_operavel") or (status_filter == "venda" and status == "venda_operavel") or (status_filter == "interesse" and status in {"interesse_compra", "interesse_venda"}) or (status_filter == "neutro" and status == "neutra_observar") or (status_filter == "evitar" and status == "evitar")
        strategy_ok = strategy_filter == "todas" or (strategy_filter == "trava" and any(term in strategy for term in ("spread", "trava"))) or strategy_filter in strategy
        action_ok = action_filter == "todas" or item.get("practical_action") == action_filter
        objective_ok = objective_filter == "todos" or (objective_filter == "para prêmio" and objective == "premio") or (objective_filter == "direcional" and objective in {"direcional_alta", "direcional_baixa"}) or (objective_filter == "proteção" and objective == "protecao") or (objective_filter == "carteira" and objective == "carteira") or (objective_filter == "lateralidade" and objective == "lateralidade") or (objective_filter == "volatilidade" and objective == "volatilidade_evento") or (objective_filter == "estudo avançado" and objective == "estudo_avancado")
        capital_ok = capital_filter == "todos" or capital_fit == capital_filter
        return regime_ok and status_ok and strategy_ok and action_ok and objective_ok and capital_ok and matches_quick_objective_filter(item, quick_filter)

    filtered_theses = [item for item in theses if matches_filters(item)]
    st.caption(f"{len(filtered_theses)} de {len(theses)} teses exibidas.")
    with st.expander("Ver diagnóstico e quase setups", expanded=False):
        diagnostics = graphical_snapshot.get("diagnostics", {})
        st.write({"motivos de evitar": diagnostics.get("top_rejection_reasons", {}), "confirmações ausentes": diagnostics.get("top_missing_confirmations", {})})
        if near_setups:
            st.dataframe(pd.DataFrame(near_setups), width="stretch", hide_index=True)

    followable_statuses = {"compra_operavel", "interesse_compra", "venda_operavel", "interesse_venda"}
    near_assets = {item.get("ativo") for item in near_setups}
    for index, thesis in enumerate(filtered_theses):
        action = render_compact_thesis_card(thesis)
        handle_thesis_card_action(thesis, action, f"teses_{index}")
        with st.expander(f"Detalhes técnicos · {thesis.get('ativo')}", expanded=False):
            best = thesis.get("best_strategy") or {}
            bulkowski = thesis.get("bulkowski_usado") or {}
            st.write(
                {
                    "Healthbox": {
                        "score": thesis.get("healthbox_score"),
                        "status": thesis.get("healthbox_status"),
                        "confirmação": thesis.get("healthbox_confirmation"),
                    },
                    "Bulkowski": {
                        "padrão": bulkowski.get("nome_padrao"),
                        "status": thesis.get("bulkowski_status"),
                    },
                    "Strategy Screener": thesis.get("strategy_screening", []),
                    "capital": {
                        "status": best.get("capital_fit_status"),
                        "motivo": best.get("capital_fit_reason"),
                    },
                    "plano_manual": best.get("manual_validation_plan", {}),
                    "checklist_book": (best.get("manual_validation_plan") or {}).get("book_checklist", []),
                    "motivos_rejeicao": best.get("rejection_rules", []),
                    "campos_ausentes": thesis.get("missing_graphical_fields", []),
                }
            )


def graphical_watchlist_page() -> None:
    st.header("Teses")
    items = load_graphical_watchlist()
    summary = summarize_graphical_watchlist(items)
    st.caption("Acompanhamento de gatilhos com snapshots persistidos. Nenhuma tese representa entrada ou ordem.")
    labels = (
        ("Total de teses salvas", "total"),
        ("Aguardando gatilho", "aguardando gatilho"),
        ("Perto do gatilho", "perto do gatilho"),
        ("Gatilho acionado", "gatilho acionado"),
        ("Invalidada", "invalidada"),
        ("Inconclusiva", "inconclusiva por falta de dados"),
    )
    for column, (label, key) in zip(st.columns(6), labels):
        column.metric(label, summary.get(key, 0))
    if not items:
        st.info("Nenhuma tese gráfica salva.")
        return
    for item in items:
        render_graphical_watchlist_card(item)
        if st.button("Remover tese gráfica", key=f"remove_graphical_{item.get('id')}"):
            if remove_from_graphical_watchlist(str(item.get("id"))):
                add_history_event(history_event("remover_tese_grafica", item, "Tese gráfica removida da watchlist persistente."))
                st.rerun()


def dashboard_page() -> None:
    opportunities = generate_daily_opportunities()
    groups = split_opportunities_by_status(opportunities)
    summary = [
        (len(groups["aprovada"]), "Oportunidades aprovadas"),
        (len(groups["atenção"]), "Em atenção"),
        (len(groups["reprovada"]), "Reprovadas"),
        (len(groups["score não calculado"]), "Score não calculado"),
        (len(load_positions()), "Posições em acompanhamento"),
        (len(generate_exit_alerts(load_positions(), MOCK_MARKET_CONTEXT)), "Alertas de saída"),
    ]
    for start in range(0, len(summary), 3):
        for column, (value, label) in zip(st.columns(3), summary[start : start + 3]):
            with column:
                status = "approved" if "aprovad" in label.lower() else "warning" if "atenção" in label.lower() else "rejected" if "reprovad" in label.lower() else "teal" if "Posições" in label or "Alertas" in label else "neutral"
                metric_card(value, label, "Atualização do funil MOCK", status)
    opening_items = [evaluate_watchlist_item(item) for item in load_opening_watchlist()]
    opening_counts = {
        status: sum(item.get("status") == status for item in opening_items)
        for status in ("aguardando confirmação", "atenção", "invalidado", "inconclusivo")
    }
    st.markdown("### Acompanhamento da Abertura")
    opening_metrics = st.columns(5)
    opening_metrics[0].metric("Total", len(opening_items))
    opening_metrics[1].metric("Aguardando confirmação", opening_counts["aguardando confirmação"])
    opening_metrics[2].metric("Atenção", opening_counts["atenção"])
    opening_metrics[3].metric("Invalidados", opening_counts["invalidado"])
    opening_metrics[4].metric("Inconclusivos", opening_counts["inconclusivo"])
    if groups["aprovada"]:
        st.success(
            f"Hoje o radar encontrou {len(groups['aprovada'])} oportunidade(s) aprovada(s), "
            f"{len(groups['atenção'])} em atenção e {len(groups['reprovada'])} reprovada(s)."
        )
    else:
        st.warning("Melhor não operar por enquanto. Nenhuma oportunidade passou nos filtros mínimos.")
    st.markdown(
        '<div class="section-card"><div class="small-label">Resumo do Radar</div><h3>Leitura do dia</h3><p>As reprovações ocorrem principalmente por liquidez ruim, cálculo de risco ausente, contexto incompleto ou filtros gráficos contrariados.</p></div>',
        unsafe_allow_html=True,
    )
    render_options_eod_status_card(get_last_options_update_summary())
    saved_real = st.session_state.get("real_eod_opportunities")
    render_real_engine_status_card(
        load_real_options_snapshots(),
        summarize_real_opportunities(saved_real) if saved_real is not None else None,
    )
    saved_pipeline_snapshot = load_real_opportunities_snapshot()
    panel_real_candidates = saved_pipeline_snapshot.get("opportunities", [])
    pipeline_metrics = st.columns(6)
    pipeline_metrics[0].metric("Entradas condicionais EOD", saved_pipeline_snapshot.get("entrada_condicional", 0))
    pipeline_metrics[1].metric("Acompanhar abertura", saved_pipeline_snapshot.get("acompanhar_na_abertura", 0))
    pipeline_metrics[2].metric("Evitar EOD", saved_pipeline_snapshot.get("evitar", 0))
    pipeline_metrics[3].metric("Inconclusivas EOD", saved_pipeline_snapshot.get("inconclusivo", 0))
    pipeline_metrics[4].metric("Última geração", saved_pipeline_snapshot.get("generated_at", "não gerado"))
    pipeline_metrics[5].metric("Erros do pipeline", len(saved_pipeline_snapshot.get("errors", [])))
    render_top_conditional_entries(
        rank_conditional_entries(panel_real_candidates, top_n=5),
        summarize_real_eod_funnel(panel_real_candidates),
    )
    show_graphical_radar()
    show_real_market_radar()
    render_data_notice(
        "As oportunidades abaixo ainda são geradas pelo Opportunity Engine com dados MOCK / EXEMPLO. A ligação com o Radar de Mercado real será feita em etapa futura."
    )
    st.caption("Todos os candidatos e decisões abaixo são MOCK / EXEMPLO.")
    show_opportunities(opportunities)

    show_healthbox_engine()

    show_bulkowski_engine()

    st.markdown("## Checklist da Operação")
    for opportunity in MOCK_OPPORTUNITIES:
        evaluated = evaluate_opportunity(opportunity)
        with st.expander(f"{opportunity['ativo']} • {opportunity['estrategia']}"):
            for item in evaluated["checklist"]:
                icon = "🟢" if item["status"] == "ok" else "🟡" if item["status"] in {"atenção", "não calculado"} else "🔴"
                st.markdown(f"{icon} **{item['question']}** — {item['detail']} · `{item['tipo_dado']}`")

    st.markdown("## Posições em Acompanhamento — exemplo visual")
    st.caption(
        "Esta tabela é MOCK / EXEMPLO. Entradas confirmadas aparecem em Minhas Posições."
    )
    st.dataframe(pd.DataFrame(MOCK_POSITIONS), width="stretch", hide_index=True)

    st.markdown("## Alertas de Saída — exemplo")
    alerts_section(MOCK_ALERTS)
    show_data_control()


def show_real_market_radar() -> None:
    st.markdown("## Radar de Mercado — brapi experimental")
    st.info(
        "Esta seção usa dados reais/coletados da brapi quando disponíveis. As oportunidades de opções ainda permanecem MOCK / EXEMPLO."
    )
    ticker_text = st.text_input(
        "Ativos do Radar de Mercado",
        value=", ".join(default_watchlist()),
        key="market_radar_tickers",
    )
    if "market_radar_snapshots" not in st.session_state:
        st.session_state["market_radar_snapshots"] = load_market_snapshots()
    update_column, saved_column = st.columns(2)
    if update_column.button("Atualizar agora", key="update_market_radar"):
        tickers = [ticker.strip().upper() for ticker in ticker_text.split(",") if ticker.strip()]
        with st.spinner("Atualizando Radar de Mercado via brapi..."):
            result = run_market_update(
                tickers=tickers, range="3mo", interval="1d", mode="intraday", runner="streamlit_app"
            )
        st.session_state["market_radar_snapshots"] = load_market_snapshots()
        if result["success"]:
            st.success("Atualização concluída e snapshot salvo.")
        else:
            st.error("A atualização registrou erro de fonte. O app continua disponível; nenhum dado foi inventado.")
    if saved_column.button("Usar último snapshot salvo", key="load_saved_market_radar"):
        st.session_state["market_radar_snapshots"] = load_market_snapshots()

    snapshots = st.session_state.get("market_radar_snapshots")
    update_summary = get_last_update_summary()
    render_update_status_card(update_summary, update_summary["snapshot_summary"])
    latest = update_summary.get("latest_update") or {}
    st.caption("Usando último snapshot salvo em data/runtime/market_snapshots.json")
    st.caption(
        f"Fonte: {latest.get('source', 'indisponível')} · Coleta: {latest.get('finished_at', 'indisponível')} · "
        f"Status: {update_summary.get('snapshot_age_status', 'indisponível')}"
    )
    if not snapshots:
        st.warning("Nenhum snapshot salvo ainda. Clique em Atualizar agora.")
        return

    healthboxes = {snapshot["ativo"]: snapshot_to_healthbox(snapshot) for snapshot in snapshots}
    complete = sum(snapshot.get("status_dado") == "atualizado" for snapshot in snapshots)
    incomplete = sum(snapshot.get("status_dado") == "incompleto" for snapshot in snapshots)
    errors = sum(snapshot.get("status_dado") == "erro" for snapshot in snapshots)
    trends = {trend: sum(snapshot.get("tendencia") == trend for snapshot in snapshots) for trend in ("alta", "lateral", "baixa")}
    if errors == len(snapshots):
        st.error("Não foi possível atualizar o Radar de Mercado. Fonte indisponível ou dados ausentes.")
    else:
        st.success(
            f"Radar real atualizado: {len(snapshots)} ativo(s) consultado(s), {complete} completo(s), "
            f"{incomplete} incompleto(s) e {errors} com erro. Tendências detectadas: "
            f"{trends['alta']} em alta, {trends['lateral']} laterais e {trends['baixa']} em baixa."
        )

    for start in range(0, len(snapshots), 4):
        for column, snapshot in zip(st.columns(4), snapshots[start : start + 4]):
            with column:
                render_market_card(snapshot, healthboxes[snapshot["ativo"]])

    rows = []
    for snapshot in snapshots:
        score_result = healthboxes[snapshot["ativo"]].get("score_result", {})
        rows.append(
            {
                "Ativo": snapshot.get("ativo"), "Preço": snapshot.get("preco_atual"),
                "Variação diária %": snapshot.get("variacao_diaria_percent"), "Range diário %": snapshot.get("range_diario_percent"),
                "ADR %": snapshot.get("adr_percent"), "ATR %": snapshot.get("atr_percent"), "rVol": snapshot.get("rvol"),
                "RSI": snapshot.get("rsi"), "RSI 200": snapshot.get("rsi_200") if snapshot.get("rsi_200") is not None else "indisponível",
                "Tendência": snapshot.get("tendencia"), "Suporte": snapshot.get("suporte"), "Resistência": snapshot.get("resistencia"),
                "Distância suporte %": snapshot.get("distancia_suporte_percent"), "Distância resistência %": snapshot.get("distancia_resistencia_percent"),
                "Score Healthbox": score_result.get("score") if score_result.get("score") is not None else "Score Healthbox não calculado: dados insuficientes",
                "Campos ausentes": ", ".join(snapshot.get("campos_ausentes", [])) or "nenhum",
                "Fonte": snapshot.get("fonte"), "Tipo do dado": snapshot.get("tipo_dado"), "Status": snapshot.get("status_dado"), "Coleta": snapshot.get("coleta"),
            }
        )
    st.markdown("### Tabela Healthbox real")
    st.dataframe(pd.DataFrame(rows).astype(str), width="stretch", hide_index=True)


def opportunities_page() -> None:
    opportunities = generate_daily_opportunities()
    st.markdown("## Filtros")
    statuses = ["todas", "aprovada", "atenção", "reprovada", "score não calculado"]
    c1, c2, c3, c4 = st.columns(4)
    selected_status = c1.selectbox("Status", statuses)
    selected_asset = c2.selectbox("Ativo", ["todos", *sorted({item["ativo"] for item in opportunities})])
    selected_strategy = c3.selectbox("Estratégia", ["todas", *sorted({str(item.get("estrategia", "nenhuma")) for item in opportunities})])
    minimum_score = c4.slider("Score mínimo", 0, 100, 0)
    f1, f2, f3, f4 = st.columns(4)
    hide_rejected = f1.checkbox("Esconder reprovadas")
    risk_only = f2.checkbox("Apenas risco definido")
    health_only = f3.checkbox("Apenas Healthbox confirmando")
    bulk_only = f4.checkbox("Apenas Bulkowski confirmando")

    filtered = []
    for item in opportunities:
        if selected_status != "todas" and item.get("status") != selected_status:
            continue
        if hide_rejected and item.get("status") == "reprovada":
            continue
        if selected_asset != "todos" and item.get("ativo") != selected_asset:
            continue
        if selected_strategy != "todas" and item.get("estrategia") != selected_strategy:
            continue
        if minimum_score > 0 and (item.get("score") is None or item["score"] < minimum_score):
            continue
        if risk_only and not (item.get("calculation", {}).get("can_calculate") and item.get("calculation", {}).get("max_loss") is not None):
            continue
        if health_only and item.get("healthbox_status") != "confirma":
            continue
        if bulk_only and item.get("bulkowski_analysis", {}).get("confirmacao") != "confirmado no mock":
            continue
        filtered.append(item)
    st.caption(f"Exibindo {len(filtered)} de {len(opportunities)} resultados MOCK / EXEMPLO.")
    show_opportunities(filtered)
    show_data_control()


def real_eod_opportunities_page() -> None:
    st.header("Radar EOD")
    st.warning(
        "Dados de opções são EOD/fim de pregão. Esta seção não indica entrada imediata. "
        "Ela mostra estruturas condicionais para validar no pregão. Não envia ordens."
    )
    automatic_snapshot = load_real_opportunities_snapshot()
    if automatic_snapshot:
        st.info(f"Última geração automática: {automatic_snapshot.get('generated_at', 'indisponível')} · modo {automatic_snapshot.get('mode', 'indisponível')} · frequência EOD")
    if st.button("Gerar agora", key="generate_real_eod"):
        with st.spinner("Executando pipeline close e salvando resultado EOD..."):
            pipeline_result = run_pipeline("close", ["PETR4", "VALE3", "ITUB4", "BOVA11"])
            st.session_state["real_eod_opportunities"] = (pipeline_result.get("opportunities_snapshot") or {}).get("opportunities", [])
        if pipeline_result.get("errors"):
            st.warning("Pipeline concluído com erros de fonte registrados. Nenhum dado foi inventado.")
        else:
            st.success("Pipeline close concluído e snapshot salvo.")
    opportunities = st.session_state.get("real_eod_opportunities")
    if opportunities is None and automatic_snapshot:
        opportunities = automatic_snapshot.get("opportunities")
    if opportunities is None:
        st.info("Nenhum snapshot automático disponível. Use Gerar agora ou execute scripts/run_pipeline.py.")
        return
    universe_liquidity = {
        item.get("ticker"): item for item in load_options_universe_availability().get("assets", [])
        if item.get("ticker")
    }
    for item in opportunities:
        availability_item = universe_liquidity.get(item.get("ativo"), {})
        item.setdefault("liquidity_class", availability_item.get("liquidity_class"))
        item.setdefault("execution_warning", availability_item.get("execution_warning"))
    summary = summarize_real_opportunities(opportunities)
    conditional_summary = summarize_conditional_entries(opportunities)
    funnel = summarize_real_eod_funnel(opportunities)
    metrics = st.columns(4)
    metrics[0].metric("Ativos analisados", summary["assets_analyzed"])
    metrics[1].metric("Com opções", summary["assets_with_options"])
    metrics[2].metric("Sem opções", summary["assets_without_options"])
    metrics[3].metric("Candidatas", summary["candidates"])
    status_metrics = st.columns(4)
    status_metrics[0].metric("Entrada condicional", conditional_summary["entrada_condicional"])
    status_metrics[1].metric("Acompanhar na abertura", conditional_summary["acompanhar_na_abertura"])
    status_metrics[2].metric("Evitar", conditional_summary["evitar"])
    status_metrics[3].metric("Inconclusivas", conditional_summary["inconclusivo"])
    if conditional_summary["entrada_condicional"] == 0 and conditional_summary["acompanhar_na_abertura"] > 0:
        st.info("Nenhuma entrada condicional plena hoje, mas há estruturas para acompanhar na abertura.")
    elif conditional_summary["entrada_condicional"] == 0 and conditional_summary["acompanhar_na_abertura"] == 0:
        st.warning("Nenhuma estrutura está próxima o suficiente hoje.")
    st.markdown("## Diagnóstico do Funil Real EOD")
    st.caption(
        f"Vencimentos analisados: {', '.join(funnel['expirations_analyzed']) or 'nenhum'} · "
        f"Ativos com opções: {', '.join(funnel['assets_with_options']) or 'nenhum'} · "
        f"Ativos sem acesso: {', '.join(funnel['assets_without_access']) or 'nenhum'}"
    )
    diagnostic_metrics = st.columns(4)
    diagnostic_metrics[0].metric("Matemática completa", funnel["complete_math_count"])
    diagnostic_metrics[1].metric("Preço utilizável", funnel["usable_price_count"])
    diagnostic_metrics[2].metric("Zero hard blockers", funnel["zero_hard_blockers_count"])
    diagnostic_metrics[3].metric("Somente soft warnings", funnel["soft_warnings_only_count"])
    if funnel["hard_blockers"]:
        st.markdown("### Hard blockers mais comuns")
        st.dataframe(pd.DataFrame([{"Hard blocker": key, "Ocorrências": value} for key, value in funnel["hard_blockers"].items()]), width="stretch", hide_index=True)
    if funnel["soft_warnings"]:
        st.markdown("### Soft warnings mais comuns")
        st.dataframe(pd.DataFrame([{"Soft warning": key, "Ocorrências": value} for key, value in funnel["soft_warnings"].items()]), width="stretch", hide_index=True)
    reasons_rows = [{"Motivo": reason, "Ocorrências": count} for reason, count in funnel["rejection_reasons"].items()]
    if reasons_rows:
        st.dataframe(pd.DataFrame(reasons_rows), width="stretch", hide_index=True)
    missing_rows = [{"Campo ausente": field, "Ocorrências": count} for field, count in funnel["missing_fields"].items()]
    if missing_rows:
        st.markdown("### Campos ausentes mais comuns")
        st.dataframe(pd.DataFrame(missing_rows), width="stretch", hide_index=True)
    st.markdown("### Quase Entradas")
    if funnel["near_misses"]:
        near_rows = [
            {
                "Ativo": item.get("ativo"), "Estratégia": item.get("estrategia"), "Vencimento": item.get("vencimento"),
                "Score": item.get("score"), "Motivo": item.get("motivo_principal"),
                "O que precisa mudar": "; ".join(item.get("what_needs_to_change", [])),
                "Custo EOD": item.get("custo_liquido"), "Débito máximo": item.get("max_debit_allowed"),
                "Crédito mínimo": item.get("min_credit_required"), "Status": item.get("conditional_status"),
            }
            for item in funnel["near_misses"]
        ]
        st.dataframe(pd.DataFrame(near_rows), width="stretch", hide_index=True)
    else:
        st.info("Nenhuma candidata ficou próxima o suficiente para entrada condicional.")
    st.markdown("## Auditoria dos Dados de Opções")
    if st.button("Atualizar auditoria dos snapshots de opções", key="audit_saved_options"):
        st.session_state["options_data_audit"] = build_options_audit_report()
    audit = st.session_state.get("options_data_audit") or build_options_audit_report()
    audit_summary = audit["summary"]
    audit_metrics = st.columns(4)
    audit_metrics[0].metric("Séries auditadas", audit_summary["series_total"])
    audit_metrics[1].metric("Preço utilizável", audit_summary["with_usable_price"])
    audit_metrics[2].metric("Sem preço", audit_summary["without_usable_price"])
    audit_metrics[3].metric("Bid/ask", audit_summary["with_bid_ask"])
    st.caption(
        f"Close presente: {audit_summary['with_close']} · Average presente: {audit_summary['with_average']} · "
        f"Trades presente: {audit_summary['with_trades']} · Volume presente: {audit_summary['with_volume']} · "
        f"Campos zerados: {audit_summary['zero_price_series']}"
    )
    st.markdown("**Principais campos raw:** " + (", ".join(list(audit_summary["raw_field_inventory"])[:20]) or "raw ainda não preservado; atualize os snapshots"))
    st.markdown("**Possíveis aliases detectados:** " + (", ".join(audit_summary["possible_aliases"]) or "nenhum"))
    if audit_summary["math_incomplete_causes"]:
        st.dataframe(
            pd.DataFrame([{"Causa": key, "Séries": value} for key, value in audit_summary["math_incomplete_causes"].items()]),
            width="stretch", hide_index=True,
        )
    ranked = rank_conditional_entries(opportunities, top_n=len(opportunities))
    groups = {status: [item for item in ranked if item.get("conditional_status") == status] for status in ("entrada_condicional", "acompanhar_na_abertura", "evitar", "inconclusivo")}
    labels = {"entrada_condicional": "Entrada condicional", "acompanhar_na_abertura": "Acompanhar na abertura", "evitar": "Evitar", "inconclusivo": "Inconclusivo"}
    for status in ("entrada_condicional", "acompanhar_na_abertura", "evitar", "inconclusivo"):
        st.markdown(f"## {labels[status]} ({len(groups[status])})")
        for index, item in enumerate(groups[status]):
            action = render_real_opportunity_card(item)
            if action == "simulate":
                st.session_state["manual_simulation_seed"] = {"candidate": item, "thesis": {}}
                st.info("Simulador preparado com os dados atuais da candidata EOD.")
            elif action == "follow" and status in {"entrada_condicional", "acompanhar_na_abertura"}:
                result = add_to_opening_watchlist(item)
                if result["added"]:
                    add_history_event(history_event("acompanhar_abertura", result["item"], "Candidata EOD adicionada à lista da abertura."))
                    st.success("Candidata salva para validação na abertura. Nenhuma entrada ou ordem foi registrada.")
                else:
                    st.info("Esta candidata já está na lista da abertura.")
            with st.expander(f"Detalhes técnicos · {item.get('ativo')} · {item.get('estrategia')}", expanded=False):
                st.write(
                    {
                        "Healthbox": {
                            "score": item.get("healthbox_score"),
                            "status": item.get("healthbox_status"),
                        },
                        "Bulkowski": "não aplicável nesta camada EOD",
                        "Strategy Screener": "não aplicável nesta camada EOD",
                        "capital": {
                            "perda_maxima": item.get("perda_maxima"),
                            "ganho_maximo": item.get("ganho_maximo"),
                            "risco_retorno": item.get("risco_retorno"),
                        },
                        "plano_manual": {
                            "confirmation_rules": item.get("confirmation_rules", []),
                            "invalidation_rules": item.get("invalidation_rules", []),
                            "entry_price_condition": item.get("entry_price_condition"),
                        },
                        "checklist_book": item.get("confirmation_rules", []),
                        "motivos_rejeicao": item.get("hard_blockers", []),
                        "campos_ausentes": item.get("campos_ausentes", []),
                    }
                )


def opening_watchlist_page() -> None:
    st.header("Watchlist de Abertura")
    st.warning(EOD_NOTICE + " Esta lista não envia ordens e não conecta corretora.")
    items = load_opening_watchlist()
    if not items:
        st.info("Nenhuma candidata salva para a abertura.")
        return
    for item in items:
        evaluated = evaluate_watchlist_item(item)
        st.markdown(f"### {evaluated.get('ativo') or 'Ativo indisponível'} · {evaluated.get('estrategia') or 'Estratégia indisponível'}")
        st.caption(f"Status: {evaluated.get('status')} · Vencimento: {evaluated.get('vencimento') or 'indisponível'} · Frequência: EOD")
        c1, c2, c3 = st.columns(3)
        c1.metric("Preço EOD de referência", money(evaluated.get("preco_eod_referencia") or evaluated.get("custo_eod") or evaluated.get("credito_eod")))
        c2.metric("Custo máximo", money(evaluated.get("max_debit_allowed")))
        c3.metric("Crédito mínimo", money(evaluated.get("min_credit_required")))
        st.markdown(
            f"**Strikes:** `{evaluated.get('strikes')}`  \n"
            f"**Perda máxima:** {money(evaluated.get('perda_maxima'))} · **Ganho máximo:** {money(evaluated.get('ganho_maximo'))} · "
            f"**Break-even:** {money(evaluated.get('break_even'))} · **Risco/retorno:** {evaluated.get('risk_reward') or 'indisponível'}"
        )
        for label, key in (
            ("Regras de confirmação", "confirmation_rules"), ("Regras de invalidação", "invalidation_rules"),
            ("Hard blockers", "hard_blockers"), ("Soft warnings", "soft_warnings"),
            ("O que precisa mudar", "what_needs_to_change"),
        ):
            values = evaluated.get(key) or []
            st.markdown(f"**{label}:** {'; '.join(map(str, values)) if values else 'nenhum registrado'}")
        st.error(EOD_NOTICE)
        if evaluated.get("converted_to_position"):
            st.success("Entrada manual já registrada; este item foi convertido em posição acompanhada.")
        elif st.button("Registrar entrada manual", key=f"start_manual_entry_{evaluated['id']}"):
            st.session_state["manual_opening_entry_id"] = evaluated["id"]
        if st.session_state.get("manual_opening_entry_id") == evaluated["id"] and not evaluated.get("converted_to_position"):
            st.markdown("#### Registrar entrada manual")
            st.write({
                "ativo": evaluated.get("ativo"), "estratégia": evaluated.get("estrategia"),
                "vencimento": evaluated.get("vencimento"), "strikes": evaluated.get("strikes"),
                "preço EOD de referência": evaluated.get("preco_eod_referencia"),
            })
            with st.form(f"manual_entry_form_{evaluated['id']}"):
                real_price = st.number_input("Preço real de entrada", min_value=0.0, step=0.01, format="%.4f")
                quantity = st.number_input("Quantidade", min_value=1, step=1, value=1)
                entry_date = st.date_input("Data de entrada", value=date.today())
                entry_time = st.time_input("Hora de entrada", value=datetime.now().time().replace(microsecond=0))
                note = st.text_area("Observação")
                confirmed = st.checkbox("Confirmo que conferi o preço no pregão/book e que esta entrada é manual.")
                submitted = st.form_submit_button("Salvar como posição acompanhada")
            if submitted:
                if real_price <= 0:
                    st.error("Informe um preço real de entrada maior que zero.")
                elif not confirmed:
                    st.error("A confirmação de conferência no pregão/book é obrigatória.")
                else:
                    entry_at = datetime.combine(entry_date, entry_time).astimezone().isoformat(timespec="seconds")
                    position = build_manual_position(evaluated, float(real_price), int(quantity), entry_at, note)
                    if add_position(position):
                        mark_as_converted(evaluated["id"], position["id"], entry_at)
                        add_history_event(history_event("entrada_manual_abertura", evaluated, "Entrada manual registrada após confirmação do usuário no pregão/book."))
                        st.session_state.pop("manual_opening_entry_id", None)
                        st.success("Entrada manual salva como posição acompanhada. Nenhuma ordem foi enviada.")
                        st.rerun()
                    else:
                        st.warning("Esta candidata já foi convertida em posição acompanhada.")
        if st.button("Remover da Abertura", key=f"remove_opening_{evaluated['id']}"):
            if remove_from_opening_watchlist(evaluated["id"]):
                add_history_event(history_event("removido_watchlist", evaluated, "Candidata removida da lista da abertura."))
                st.success("Item removido da lista da abertura.")
                st.rerun()
        st.divider()


def positions_page() -> None:
    st.header("Posições")
    mock_badge("REGISTROS LOCAIS — MOCK E ENTRADAS MANUAIS EOD IDENTIFICADOS")
    positions = load_positions()
    if positions:
        positions_table(positions)
        st.markdown("## Monitor de Posições")
        real_snapshots = {item.get("ativo"): item for item in load_market_snapshots() if item.get("ativo")}
        monitor_rows = []
        for position in positions:
            if position.get("origem") == "opening_watchlist":
                snapshot = real_snapshots.get(position.get("ativo"))
                if snapshot:
                    healthbox = snapshot_to_healthbox(snapshot)
                    healthbox["confirmation"] = healthbox_confirms_strategy(healthbox, position.get("tipo_estrutura", ""))
                    context = {
                        "asset_snapshot": snapshot, "healthbox": healthbox,
                        "current_mark": None, "tipo_dado": snapshot.get("tipo_dado"),
                        "fonte": snapshot.get("fonte") or snapshot.get("fonte_base") or "brapi",
                    }
                else:
                    context = None
            else:
                context = MOCK_MARKET_CONTEXT.get(position.get("ativo"))
            result = build_position_status(position, context)
            pnl = result["pnl"]
            capture = result["gain_capture"]
            monitor_rows.append(
                {
                    "Ativo": position.get("ativo"),
                    "Origem": "Abertura" if position.get("origem") == "opening_watchlist" else "MOCK / EXEMPLO",
                    "Preço real de entrada": money(position.get("preco_real_entrada")),
                    "Preço EOD de referência": money(position.get("preco_eod_referencia")),
                    "Status": result["status"],
                    "Severidade": result["severity"],
                    "Motivo": result["reason"],
                    "P/L da opção": money(pnl["pnl_per_unit"]) if pnl["calculated"] else "indisponível",
                    "Motivo do P/L": pnl.get("reason"),
                    "P/L total": money(pnl["pnl_total"]) if pnl["calculated"] else "não calculado por falta de dados",
                    "P/L %": f"{pnl['pnl_percent']:.2f}%" if pnl["calculated"] and pnl["pnl_percent"] is not None else "indisponível",
                    "Captura do ganho máximo": f"{capture['capture_percent']:.2f}%" if capture["calculated"] else "não calculado por falta de dados",
                    "Alerta principal": result["reason"],
                    "Tipo do dado": result["tipo_dado"],
                }
            )
            if position.get("origem") == "opening_watchlist" and result["status"] == "tese invalidada":
                st.error(f"{position.get('ativo')} · tese invalidada: {result['reason']}")
        st.dataframe(pd.DataFrame(monitor_rows), width="stretch", hide_index=True)
        st.info("Posições da Abertura são acompanhadas pelo ativo e pelas regras; o preço atual da opção precisa de fonte intraday. Preço EOD não é usado como marcação atual.")
        st.markdown("### Detalhes das posições")
        for position in positions:
            if st.button(f"Ver detalhes da posição · {position.get('ativo')} · {position.get('id', '')[:8]}", key=f"position-detail-{position.get('id')}"):
                st.session_state["position_detail_id"] = position.get("id")
        selected_position = next((item for item in positions if item.get("id") == st.session_state.get("position_detail_id")), None)
        if selected_position:
            if selected_position.get("origem") == "opening_watchlist":
                snapshot = real_snapshots.get(selected_position.get("ativo"))
                healthbox = snapshot_to_healthbox(snapshot) if snapshot else {}
                if healthbox:
                    healthbox["confirmation"] = healthbox_confirms_strategy(healthbox, selected_position.get("tipo_estrutura", ""))
                context = {"asset_snapshot": snapshot, "healthbox": healthbox, "current_mark": None, "tipo_dado": snapshot.get("tipo_dado"), "fonte": snapshot.get("fonte") or "brapi"} if snapshot else None
            else:
                context = MOCK_MARKET_CONTEXT.get(selected_position.get("ativo"))
            result = build_position_status(selected_position, context)
            st.markdown(f"#### {selected_position.get('ativo')} · {selected_position.get('estrategia')}")
            if selected_position.get("origem") == "opening_watchlist":
                st.write({"origem": "Abertura", "preço real de entrada": selected_position.get("preco_real_entrada"), "preço EOD de referência": selected_position.get("preco_eod_referencia"), "regras de invalidação": selected_position.get("invalidation_rules", [])})
            st.write({"posição": selected_position, "status_exit_engine": result})
    else:
        st.info("Você ainda não marcou nenhuma posição como entrada.")

    confirm = st.checkbox("Confirmo que desejo limpar as posições mockadas")
    if st.button("Limpar posições mockadas", disabled=not confirm):
        save_positions([])
        add_history_event(
            {
                "id": str(uuid4()),
                "tipo": "posicoes_mock_limpas",
                "ativo": "—",
                "estrategia": "—",
                "data_hora": now_iso(),
                "mensagem": "As posições MOCK / EXEMPLO foram removidas.",
                "tipo_dado": "MOCK / EXEMPLO",
            }
        )
        st.success("Posições mockadas removidas.")
        st.rerun()


def history_page() -> None:
    st.header("Histórico de Decisões")
    history = load_history()
    if history:
        f1, f2, f3 = st.columns(3)
        selected_type = f1.selectbox("Tipo de decisão", ["todos", *sorted({str(event.get('tipo', 'indisponível')) for event in history})])
        selected_asset = f2.selectbox("Ativo do histórico", ["todos", *sorted({str(event.get('ativo', 'indisponível')) for event in history})])
        selected_strategy = f3.selectbox("Estratégia do histórico", ["todas", *sorted({str(event.get('estrategia', 'indisponível')) for event in history})])
        filtered_history = [
            event
            for event in history
            if (selected_type == "todos" or event.get("tipo") == selected_type)
            and (selected_asset == "todos" or event.get("ativo") == selected_asset)
            and (selected_strategy == "todas" or event.get("estrategia") == selected_strategy)
        ]
        rows = [
            {
                "Tipo": event.get("tipo"),
                "Ativo": event.get("ativo"),
                "Estratégia": event.get("estrategia"),
                "Data/hora": event.get("data_hora"),
                "Mensagem": event.get("mensagem"),
            }
            for event in reversed(filtered_history)
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Nenhuma decisão registrada ainda.")

    confirm = st.checkbox("Confirmo que desejo limpar o histórico mockado")
    if st.button("Limpar histórico mockado", disabled=not confirm):
        save_history([])
        st.success("Histórico mockado removido.")
        st.rerun()


def alerts_page() -> None:
    st.header("Alertas")
    st.warning(
        "Alertas desta etapa usam contexto MOCK / EXEMPLO. Não há dados reais de mercado, conexão com corretora ou envio de ordens."
    )
    positions = load_positions()
    if not positions:
        st.info("Nenhuma posição real/mockada foi registrada ainda. Abaixo estão apenas alertas visuais antigos de exemplo.")
        alerts_section(MOCK_ALERTS)
        return
    generated = generate_exit_alerts(positions, MOCK_MARKET_CONTEXT)
    groups = {
        "Alertas críticos": [item for item in generated if item["severity"] == "vermelho"],
        "Alertas de atenção": [item for item in generated if item["severity"] == "amarelo"],
        "Alertas de realização": [item for item in generated if item["status"].startswith("realizar")],
        "Inconclusivos por falta de dados": [item for item in generated if item["severity"] == "cinza"],
    }
    for title, alerts in groups.items():
        st.markdown(f"## {title} ({len(alerts)})")
        if not alerts:
            st.caption("Nenhum alerta nesta categoria.")
        for alert in alerts:
            render_alert_card(alert)


def sources_configuration_page() -> None:
    st.header("Dados/Config")
    status = provider_status()
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Provider ativo", status.get("provider", "indisponível"))
    p2.metric("Status", status.get("status", "indisponível"))
    p3.metric("Token detectado", "sim" if status.get("token_detected") else "não")
    p4.metric("Cache ativo", f"sim · {status.get('cached_files', 0)} arquivo(s)")
    st.caption(
        f"Última coleta: {status.get('last_collection') or 'nenhuma'} · "
        f"fallback permitido: {'sim' if status.get('fallback_allowed') else 'não'}"
    )
    render_data_notice(
        "Nesta etapa, a brapi ainda não alimenta o Opportunity Engine. Ela apenas valida a coleta automática de preços e histórico."
    )
    latest_result = st.session_state.get("brapi_history_test") or st.session_state.get("brapi_quote_test")
    st.caption(
        f"Status da última chamada: {latest_result.get('status_dado', 'nenhuma chamada nesta sessão') if latest_result else 'nenhuma chamada nesta sessão'} · "
        f"fallback mock ativo: {'sim' if status.get('fallback_allowed') else 'não'}"
    )
    quote_test_status = st.session_state.get("brapi_quote_test", {}).get("status_dado", "não testado nesta sessão")
    history_test_status = st.session_state.get("brapi_history_test", {}).get("status_dado", "não testado nesta sessão")
    st.markdown(
        f'<div class="section-card"><div class="small-label">Status brapi</div><p><b>Configurada:</b> {"sim" if status.get("configured") else "não"}<br><b>Último teste de cotação:</b> {quote_test_status}<br><b>Último teste de histórico:</b> {history_test_status}<br><b>Cache:</b> ativo · <b>Fallback mock:</b> {"ativo" if status.get("fallback_allowed") else "inativo"}</p></div>',
        unsafe_allow_html=True,
    )
    test_quotes, test_history = st.columns(2)
    if test_quotes.button("Testar brapi: PETR4, VALE3, ITUB4, BOVA11"):
        st.session_state["brapi_quote_test"] = fetch_quotes(["PETR4", "VALE3", "ITUB4", "BOVA11"], use_cache=False)
    if test_history.button("Testar histórico brapi"):
        st.session_state["brapi_history_test"] = fetch_historical(["PETR4"], range="3mo", interval="1d", use_cache=False)

    quote_result = st.session_state.get("brapi_quote_test")
    if quote_result:
        if quote_result.get("success"):
            st.success(f"Cotação respondida por {quote_result.get('provider')} · {quote_result.get('status_dado')}")
            quote_rows = []
            expected = ["ticker", "preco", "abertura", "maxima", "minima", "fechamento_anterior", "volume", "variacao_percentual", "market_time"]
            for record in quote_result.get("data", []):
                row = {key: record.get(key) for key in expected}
                row.update(
                    campos_ausentes=", ".join(key for key in expected if record.get(key) is None) or "nenhum",
                    coleta=record.get("coleta", quote_result.get("coleta", "indisponível")),
                    fonte=record.get("fonte", quote_result.get("provider", "indisponível")),
                    tipo_dado=record.get("tipo_dado", quote_result.get("tipo_dado", "indisponível")),
                    status_dado=record.get("status_dado", quote_result.get("status_dado", "indisponível")),
                )
                quote_rows.append(row)
            st.dataframe(pd.DataFrame(quote_rows), width="stretch", hide_index=True)
        else:
            st.error(f"Falha no teste de cotação: {quote_result.get('error', 'erro desconhecido')}")

    historical_result = st.session_state.get("brapi_history_test")
    if historical_result:
        if historical_result.get("success"):
            assets = historical_result.get("data", [])
            candle_count = sum(len(item.get("candles", [])) for item in assets)
            st.success(
                f"Histórico normalizado: {candle_count} candle(s) · fonte {historical_result.get('provider')} · "
                f"tipo {historical_result.get('tipo_dado')} · status {historical_result.get('status_dado')} · "
                f"coleta {historical_result.get('coleta', 'indisponível')}"
            )
            candles = assets[0].get("candles", [])[-10:] if assets else []
            candle_rows = [
                {
                    **candle,
                    "campos_ausentes": ", ".join(key for key in ("date", "open", "high", "low", "close", "volume", "adjusted_close") if candle.get(key) is None) or "nenhum",
                }
                for candle in candles
            ]
            st.dataframe(pd.DataFrame(candle_rows), width="stretch", hide_index=True)
        else:
            st.error(f"Falha no teste histórico: {historical_result.get('error', 'erro desconhecido')}")

    st.markdown("## Teste brapi Opções — EOD")
    st.warning(
        "Esta seção testa dados de opções da brapi. Esses dados são EOD/fim de pregão quando disponíveis. "
        "Não são usados ainda para gerar oportunidades reais."
    )
    options_underlying = st.text_input("Ativo subjacente", value="PETR4", key="brapi_options_underlying").strip().upper()
    expiration_column, chain_column = st.columns(2)
    if expiration_column.button("Testar vencimentos", key="test_options_expirations"):
        st.session_state["brapi_options_expirations"] = fetch_options_expirations(options_underlying)
    if chain_column.button("Testar cadeia do próximo vencimento", key="test_options_chain"):
        snapshot = build_options_snapshot(options_underlying)
        st.session_state["brapi_options_snapshot"] = snapshot
        st.session_state["brapi_options_expirations"] = {
            "success": bool(snapshot.get("expirations")), "underlying": snapshot.get("underlying"),
            "expirations": snapshot.get("expirations", []), "count": len(snapshot.get("expirations", [])),
            "access_status": snapshot.get("access_status"), "error": snapshot.get("error"),
            "fonte": snapshot.get("fonte"), "coleta": snapshot.get("coleta"),
            "status_dado": snapshot.get("status_dado"), "observacao": snapshot.get("observacao"),
        }

    expiration_result = st.session_state.get("brapi_options_expirations")
    options_snapshot = st.session_state.get("brapi_options_snapshot") or load_options_snapshot()
    options_summary = summarize_options_snapshot(options_snapshot)
    if expiration_result:
        if expiration_result.get("access_status") == "sem_acesso":
            st.error("Opções indisponíveis na fonte atual. Verifique se seu plano brapi inclui opções.")
        elif not expiration_result.get("success"):
            st.error(f"Opções indisponíveis na fonte atual. Motivo: {expiration_result.get('error', 'erro de API')}")
        else:
            st.success(f"{expiration_result.get('count', 0)} vencimento(s) encontrado(s) para {options_underlying}.")
    render_options_status_card(options_summary)
    st.caption(options_summary.get("observacao", "Dados de opções EOD/fim de pregão quando disponíveis."))
    option_metrics = st.columns(4)
    option_metrics[0].metric("Vencimentos", options_summary.get("expiration_count", 0))
    option_metrics[1].metric("Séries", options_summary.get("series_count", 0))
    option_metrics[2].metric("Calls", options_summary.get("calls", 0))
    option_metrics[3].metric("Puts", options_summary.get("puts", 0))
    missing_options = options_summary.get("campos_ausentes_comuns", {})
    st.caption(
        f"Status de acesso: {options_summary.get('access_status', 'indisponível')} · "
        f"Fonte: {options_summary.get('fonte', 'brapi_options')} · Coleta: {options_summary.get('coleta') or 'nenhuma'} · "
        f"Campos ausentes comuns: {', '.join(f'{key} ({value})' for key, value in missing_options.items()) or 'nenhum registrado'}"
    )
    if options_summary.get("error"):
        st.error(f"Motivo registrado: {options_summary['error']}")
    series = options_snapshot.get("series", []) if isinstance(options_snapshot, dict) else []
    if series:
        st.dataframe(pd.DataFrame(series), width="stretch", hide_index=True)

    st.markdown("## Atualização de Opções EOD — brapi")
    st.warning(
        "Dados de opções da brapi são EOD/fim de pregão. Eles ainda não alimentam recomendações reais nesta etapa."
    )
    multiasset_text = st.text_input(
        "Ativos para atualização EOD",
        value="PETR4, VALE3, ITUB4, BOVA11",
        key="options_eod_underlyings",
    )
    update_options_column, load_options_column = st.columns(2)
    if update_options_column.button("Atualizar opções EOD agora", key="update_options_eod"):
        symbols = [item.strip().upper() for item in multiasset_text.split(",") if item.strip()]
        with st.spinner("Atualizando cadeias EOD de opções..."):
            st.session_state["options_eod_result"] = run_options_update(symbols, mode="close", max_expirations=4, min_dte=7, max_dte=60)
    if load_options_column.button("Usar último snapshot de opções", key="load_options_eod"):
        st.session_state["options_eod_result"] = get_last_options_update_summary().get("last_update") or {}

    eod_status = get_last_options_update_summary()
    render_options_eod_status_card(eod_status)
    eod_result = st.session_state.get("options_eod_result") or eod_status.get("last_update") or {}
    if eod_result:
        eod_metrics = st.columns(4)
        eod_metrics[0].metric("Consultados", eod_result.get("total_underlyings", 0))
        eod_metrics[1].metric("Disponíveis", eod_result.get("available_count", 0))
        eod_metrics[2].metric("Indisponíveis", eod_result.get("unavailable_count", 0))
        eod_metrics[3].metric("Erros", eod_result.get("error_count", 0))
        st.caption(
            f"Séries: {eod_result.get('total_series', 0)} · Calls: {eod_result.get('total_calls', 0)} · "
            f"Puts: {eod_result.get('total_puts', 0)} · Fonte: {eod_result.get('source', 'brapi_options')} · "
            f"Frequência: {eod_result.get('data_frequency', 'EOD')} · Coleta: {eod_result.get('finished_at', 'indisponível')}"
        )
        if eod_result.get("errors"):
            st.error("Falhas registradas: " + " | ".join(map(str, eod_result["errors"])))
    saved_options = load_all_options_snapshots()
    if saved_options:
        saved_rows = [
            {
                "Ativo": symbol, "Status": item.get("status_dado"), "Acesso": item.get("access_status"),
                "Vencimento": item.get("expiration_used"), "Séries": item.get("series_count", 0),
                "Calls": item.get("calls_count", 0), "Puts": item.get("puts_count", 0),
                "Erro": item.get("error") or "nenhum", "Coleta": item.get("coleta"),
            }
            for symbol, item in saved_options.items()
        ]
        st.dataframe(pd.DataFrame(saved_rows), width="stretch", hide_index=True)

    st.markdown("## Universo Real de Ativos com Opções")
    availability = load_options_universe_availability()
    availability_summary = summarize_options_availability(availability)
    candidate_tickers = load_option_candidate_tickers()
    tested_tickers = set(availability.get("tickers_tested", []))
    pending_tickers = [ticker for ticker in candidate_tickers if ticker not in tested_tickers]
    source_denied = sum(item.get("status") == "sem_acesso_fonte" for item in availability.get("assets", []))
    technical_errors = sum(item.get("status") == "erro" for item in availability.get("assets", []))
    universe_metrics = st.columns(6)
    universe_metrics[0].metric("Total de candidatos", len(candidate_tickers))
    universe_metrics[1].metric("Ativos testados", availability_summary["tickers_tested"])
    universe_metrics[2].metric("Pendentes", len(pending_tickers))
    universe_metrics[3].metric("Acessíveis", availability_summary["available_count"])
    universe_metrics[4].metric("Sem acesso pela fonte", source_denied)
    universe_metrics[5].metric("Erros", technical_errors)
    st.caption(f"Última descoberta: {availability.get('generated_at', 'nunca')}")
    st.warning("Sem acesso pela fonte atual não significa ausência de opções na B3.")
    st.caption("Cache real EOD; o pipeline reutiliza apenas resultados com até 72 horas e não executa discovery automaticamente.")
    if availability.get("available"):
        st.success("Disponíveis: " + ", ".join(availability["available"]))
    if availability.get("errors"):
        st.error("Principais erros: " + " | ".join(map(str, availability["errors"][:5])))
    liquidity_classes = availability_summary.get("liquidity_classes", {})
    st.caption("Classes de liquidez: " + " · ".join(f"{key}: {value}" for key, value in liquidity_classes.items()))
    if any(liquidity_classes.get(key, 0) for key in ("baixa", "muito baixa", "sem negócio")):
        st.warning("Liquidez baixa no mercado brasileiro. Validar book, spread e execução manualmente.")
    if st.button("Atualizar universo de opções", key="discover_options_universe"):
        candidate_tickers = load_option_candidate_tickers()[:20]
        with st.spinner("Testando disponibilidade real de opções EOD..."):
            st.session_state["options_universe_discovery"] = discover_options_availability(candidate_tickers, limit=20)
        st.success("Descoberta concluída e cache salvo. Falhas permanecem registradas por ativo.")
        st.rerun()

    st.markdown("## Rotinas de Atualização")
    st.markdown(
        "- **Pré-pregão:** 1x antes da abertura;\n"
        "- **Intraday radar:** a cada 15 minutos;\n"
        "- **Posições abertas:** a cada 5 a 15 minutos, se houver dados confiáveis;\n"
        "- **Pós-fechamento:** 1x após o fechamento."
    )
    routine_status = get_last_update_summary()
    routine_rows = []
    for mode in ("premarket", "intraday", "close"):
        execution = routine_status.get("last_updates", {}).get(mode, {})
        success = execution.get("success")
        routine_rows.append(
            {
                "Modo": mode,
                "Última execução": execution.get("finished_at", "nunca"),
                "Runner": execution.get("runner", "indisponível"),
                "Sucesso": "sim" if success is True else "não" if success is False else "indisponível",
                "Incompletos": execution.get("incomplete_count", 0),
                "Erros": execution.get("error_count", 0),
            }
        )
    st.dataframe(pd.DataFrame(routine_rows), width="stretch", hide_index=True)
    if routine_status.get("last_error"):
        st.error(f"Erro recente: {routine_status['last_error']}")
    st.info(
        "Quando o projeto estiver no GitHub e o secret BRAPI_TOKEN estiver configurado, "
        "o GitHub Actions atualizará estes arquivos automaticamente."
    )

    st.markdown("## Healthbox Real — brapi experimental")
    render_data_notice(
        "Esta seção usa dados reais da brapi quando disponíveis. O Opportunity Engine ainda permanece em MOCK / EXEMPLO."
    )
    ticker_text = st.text_input("Tickers para o Healthbox real", value="PETR4, VALE3, ITUB4, BOVA11")
    if st.button("Atualizar Healthbox com brapi"):
        tickers = [ticker.strip().upper() for ticker in ticker_text.split(",") if ticker.strip()]
        st.session_state["real_healthbox_snapshots"] = build_many_asset_snapshots(tickers, range="3mo", interval="1d")

    real_snapshots = st.session_state.get("real_healthbox_snapshots")
    if real_snapshots:
        updated = sum(item.get("status_dado") == "atualizado" for item in real_snapshots)
        incomplete = sum(item.get("status_dado") == "incompleto" for item in real_snapshots)
        errors = sum(item.get("status_dado") == "erro" for item in real_snapshots)
        for column, (value, label, color) in zip(
            st.columns(4),
            [
                (updated, "Ativos atualizados", "approved"),
                (incomplete, "Ativos incompletos", "warning"),
                (errors, "Ativos com erro", "rejected"),
                ("brapi", "Fonte", "teal"),
            ],
        ):
            with column:
                metric_card(value, label, "Healthbox real experimental", color)
        rows = []
        for snapshot in real_snapshots:
            healthbox = snapshot_to_healthbox(snapshot)
            score_result = healthbox.get("score_result", {})
            rows.append(
                {
                    "Ativo": snapshot.get("ativo"),
                    "Preço atual": snapshot.get("preco_atual"),
                    "Variação diária %": snapshot.get("variacao_diaria_percent"),
                    "Range diário %": snapshot.get("range_diario_percent"),
                    "ADR %": snapshot.get("adr_percent"),
                    "ATR %": snapshot.get("atr_percent"),
                    "rVol": snapshot.get("rvol"),
                    "RSI": snapshot.get("rsi"),
                    "RSI 200": snapshot.get("rsi_200") if snapshot.get("rsi_200") is not None else "indisponível",
                    "Tendência": snapshot.get("tendencia"),
                    "Suporte simples": snapshot.get("suporte"),
                    "Resistência simples": snapshot.get("resistencia"),
                    "Distância suporte %": snapshot.get("distancia_suporte_percent"),
                    "Distância resistência %": snapshot.get("distancia_resistencia_percent"),
                    "Score Healthbox": score_result.get("score") if score_result.get("score") is not None else "score não calculado",
                    "Status": snapshot.get("status_dado"),
                    "Campos ausentes": ", ".join(snapshot.get("campos_ausentes", [])) or "nenhum",
                    "Fonte": snapshot.get("fonte"),
                    "Tipo do dado": snapshot.get("tipo_dado"),
                    "Coleta": snapshot.get("coleta"),
                }
            )
        st.dataframe(pd.DataFrame(rows).astype(str), width="stretch", hide_index=True)

    st.header("Fontes de Dados")
    st.warning(
        "Nenhuma coleta real está implementada nesta versão. Esta tela apenas registra fontes futuras e controle de confiabilidade."
    )
    sources = load_source_registry()
    source_rows = [
        {
            "Fonte": source["nome"],
            "Categoria": source["categoria"],
            "Uso previsto": source["uso_previsto"],
            "Status": source["status"],
            "Custo": source["custo"],
            "Frequência esperada": source["frequencia_esperada"],
            "Confiabilidade": source["confiabilidade"],
            "Última coleta": source["ultima_coleta"] or "nunca coletado",
            "Observação": source["observacao"],
        }
        for source in sources
    ]
    st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)

    st.markdown("## Contratos de Dados")
    contract_rows = [
        {
            "Contrato": name,
            "Campos obrigatórios": ", ".join(contract["required"]),
            "Campos desejáveis": ", ".join(contract["optional"]) or "nenhum nesta etapa",
        }
        for name, contract in CONTRACTS.items()
    ]
    st.dataframe(pd.DataFrame(contract_rows), width="stretch", hide_index=True)

    st.markdown("## Qualidade dos Dados")
    summary = build_source_summary()
    labels = [
        (summary["sources_registered"], "Fontes registradas"),
        (summary["sources_implemented"], "Fontes implementadas"),
        (summary["mock_sources"], "Fontes mockadas"),
        (summary["missing_metadata"], "Metadados incompletos"),
    ]
    for column, (value, label) in zip(st.columns(4), labels):
        with column:
            metric_card(value, label)
    st.info(
        f"Status geral: **{summary['status']}** · coleta real habilitada: **não** · campos ausentes em fontes: **{summary['missing_metadata']}**"
    )
    st.markdown(
        '<div class="section-card"><div class="small-label">Status do Projeto</div><h3>Ambiente demonstrativo protegido</h3><p>Opportunity Engine, Healthbox, Bulkowski e Exit Engine ativos sobre dados MOCK / EXEMPLO. Coleta real, corretora e envio de ordens permanecem desativados.</p></div>',
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown('<div class="sidebar-title">Radar de Opções Brasil</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-group">Painel</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-group">Acompanhamento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-group">Ferramentas</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navegação",
        [
            "Visão geral",
            "Radar EOD",
            "Teses",
            "Eventos",
            "Posições",
            "Alertas",
            "Simulador",
            "Histórico",
            "Configurações",
        ],
        label_visibility="collapsed",
    )

st.markdown('<div class="eyebrow">Radar de Opções Brasil</div>', unsafe_allow_html=True)
if page != "Visão geral":
    st.title(page)
if page in {"Visão geral", "Radar EOD", "Eventos", "Teses", "Posições", "Alertas"}:
    mock_badge("DADOS REAIS EOD / EXPERIMENTAL")
else:
    mock_badge()

render_global_risk_notice()

if page == "Visão geral":
    decision_panel_page()
elif page == "Radar EOD":
    real_eod_opportunities_page()
elif page == "Eventos":
    opening_watchlist_page()
elif page == "Teses":
    graphical_watchlist_page()
elif page == "Simulador":
    manual_simulations_page()
elif page == "Posições":
    positions_page()
elif page == "Alertas":
    alerts_page()
elif page == "Histórico":
    history_page()
else:
    sources_configuration_page()
    show_data_control()

st.caption(
    "Radar de Opções Brasil • apoio à decisão • nenhuma ordem é enviada • motor mock e análise real EOD experimental permanecem separados"
)
