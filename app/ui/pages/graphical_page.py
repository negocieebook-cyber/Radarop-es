"""Páginas do Radar Gráfico e da watchlist de teses."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.capital_requirements import classify_capital_fit, explain_capital_requirement
from app.components import (
    render_compact_thesis_card,
    render_daily_priority_item,
    render_daily_priority_plan,
    render_graphical_watchlist_card,
)
from app.daily_priority_engine import build_daily_priority_list
from app.graphical_watchlist import (
    add_to_graphical_watchlist,
    load_graphical_watchlist,
    remove_from_graphical_watchlist,
    summarize_graphical_watchlist,
)
from app.pipeline_orchestrator import load_graphical_theses_snapshot
from app.practical_strategy_view import build_practical_strategy_summary, matches_quick_objective_filter
from app.storage import add_history_event
from app.user_trading_profile import load_user_trading_profile, save_user_trading_profile
from app.ui.pages.panel_page import handle_thesis_card_action
from app.ui.pages.simulator_page import manual_simulator_form
from app.ui.shared import history_event


def show_graphical_radar() -> None:
    graphical_snapshot = load_graphical_theses_snapshot()
    theses = graphical_snapshot.get("theses", [])
    summary = graphical_snapshot.get("summary", {})
    st.caption("Teses de regiões gráficas por ativo, com prioridades por objetivo. Nenhuma tese é ordem.")
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
                render_daily_priority_item(priority, key_suffix=f"_{group}_{priority_index}")
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


def radar_grafico_page() -> None:
    tabs = st.tabs(["Prioridades de hoje", "Teses acompanhadas"])
    with tabs[0]:
        show_graphical_radar()
    with tabs[1]:
        graphical_watchlist_page()
