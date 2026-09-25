"""Páginas do Radar de Mercado e do Radar EOD real."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.conditional_entry_engine import rank_conditional_entries, summarize_conditional_entries
from app.components import (
    render_market_card,
    render_real_opportunity_card,
    render_update_status_card,
    status_label,
    strategy_label,
)
from app.formatting import format_dt
from app.funnel_diagnostics import summarize_real_eod_funnel
from app.market_snapshot_engine import snapshot_to_healthbox
from app.opening_watchlist import add_to_opening_watchlist
from app.notices import EOD_OPTIONS_NOTICE
from app.options_data_audit import build_options_audit_report
from app.options_universe_discovery import load_options_universe_availability
from app.pipeline_orchestrator import load_real_opportunities_snapshot, run_pipeline
from app.real_opportunity_engine import summarize_real_opportunities
from app.storage import add_history_event
from app.update_orchestrator import default_watchlist, get_last_update_summary, load_market_snapshots, run_market_update
from app.ui.shared import history_event


def show_real_market_radar() -> None:
    st.caption("Snapshots reais coletados da brapi. Oportunidades de opções permanecem MOCK / EXEMPLO.")
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
        f"Fonte: {latest.get('source', 'indisponível')} · Coleta: {format_dt(latest.get('finished_at'))} · "
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
    elif complete == 0:
        st.warning(
            f"Radar consultado: {len(snapshots)} ativo(s), {incomplete} incompleto(s) e {errors} com erro. "
            "Nenhum snapshot completo nesta rodada; verifique a fonte em Configurações."
        )
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
                "Fonte": snapshot.get("fonte"), "Tipo do dado": snapshot.get("tipo_dado"), "Status": snapshot.get("status_dado"), "Coleta": format_dt(snapshot.get("coleta"), "nenhuma"),
            }
        )
    st.markdown("### Tabela Healthbox real")
    st.dataframe(pd.DataFrame(rows).astype(str), width="stretch", hide_index=True)

def real_eod_opportunities_page() -> None:
    st.warning(EOD_OPTIONS_NOTICE)
    automatic_snapshot = load_real_opportunities_snapshot()
    if automatic_snapshot:
        st.info(f"Última geração automática: {format_dt(automatic_snapshot.get('generated_at'))} · modo {automatic_snapshot.get('mode', 'indisponível')} · frequência EOD")
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
    ranked = rank_conditional_entries(opportunities, top_n=len(opportunities))
    groups = {status: [item for item in ranked if item.get("conditional_status") == status] for status in ("entrada_condicional", "acompanhar_na_abertura", "evitar", "inconclusivo")}
    labels = {"entrada_condicional": "Entrada condicional", "acompanhar_na_abertura": "Acompanhar na abertura", "evitar": "Evitar", "inconclusivo": "Inconclusivo"}
    for status in ("entrada_condicional", "acompanhar_na_abertura", "evitar", "inconclusivo"):
        st.markdown(f"## {labels[status]} ({len(groups[status])})")
        for index, item in enumerate(groups[status]):
            action = render_real_opportunity_card(item, key_suffix=f"_{status}_{index}")
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
            with st.expander(f"Detalhes técnicos · {item.get('ativo')} · {strategy_label(item.get('estrategia'))}", expanded=False):
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
    with st.expander("Diagnóstico do funil real EOD", expanded=False):
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
            st.markdown("#### Hard blockers mais comuns")
            st.dataframe(pd.DataFrame([{"Hard blocker": key, "Ocorrências": value} for key, value in funnel["hard_blockers"].items()]), width="stretch", hide_index=True)
        if funnel["soft_warnings"]:
            st.markdown("#### Soft warnings mais comuns")
            st.dataframe(pd.DataFrame([{"Soft warning": key, "Ocorrências": value} for key, value in funnel["soft_warnings"].items()]), width="stretch", hide_index=True)
        reasons_rows = [{"Motivo": reason, "Ocorrências": count} for reason, count in funnel["rejection_reasons"].items()]
        if reasons_rows:
            st.markdown("#### Motivos de rejeição")
            st.dataframe(pd.DataFrame(reasons_rows), width="stretch", hide_index=True)
        missing_rows = [{"Campo ausente": field, "Ocorrências": count} for field, count in funnel["missing_fields"].items()]
        if missing_rows:
            st.markdown("#### Campos ausentes mais comuns")
            st.dataframe(pd.DataFrame(missing_rows), width="stretch", hide_index=True)
        st.markdown("#### Quase entradas")
        if funnel["near_misses"]:
            near_rows = [
                {
                    "Ativo": item.get("ativo"), "Estratégia": strategy_label(item.get("estrategia")), "Vencimento": item.get("vencimento"),
                    "Score": item.get("score"), "Motivo": item.get("motivo_principal"),
                    "O que precisa mudar": "; ".join(item.get("what_needs_to_change", [])),
                    "Custo EOD": item.get("custo_liquido"), "Débito máximo": item.get("max_debit_allowed"),
                    "Crédito mínimo": item.get("min_credit_required"), "Status": status_label(item.get("conditional_status")),
                }
                for item in funnel["near_misses"]
            ]
            st.dataframe(pd.DataFrame(near_rows), width="stretch", hide_index=True)
        else:
            st.info("Nenhuma candidata ficou próxima o suficiente para entrada condicional.")
    with st.expander("Auditoria dos dados de opções", expanded=False):
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
