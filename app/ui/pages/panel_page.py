"""Página Painel de decisão e seus auxiliares."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.capital_requirements import classify_capital_fit, explain_capital_requirement
from app.components import (
    render_action_summary,
    render_decision_card,
    render_empty_state,
    render_info_panel,
    render_section_title,
    runner_label,
)
from app.formatting import format_dt
from app.graphical_watchlist import add_to_graphical_watchlist
from app.pipeline_orchestrator import load_graphical_theses_snapshot, load_real_opportunities_snapshot
from app.practical_strategy_view import build_practical_strategy_summary
from app.storage import add_history_event
from app.update_orchestrator import default_watchlist, get_last_update_summary, run_market_update
from app.user_trading_profile import load_user_trading_profile
from app.ui.navigation import go_to
from app.ui.pages.simulator_page import manual_simulator_form
from app.ui.shared import history_event


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
        st.caption("O que merece atenção hoje")
    with title_right:
        header_bits = [
            '<span class="status-badge status-info">Dados EOD</span>',
            f'<span class="status-badge {"status-approved" if latest.get("success", False) else "status-warning" if latest else "status-neutral"}">{("Atualizado" if latest.get("success", False) else "Parcial" if latest else "Sem leitura")}</span>',
            f'<span class="status-badge status-neutral">{format_dt(latest.get("finished_at"), "sem horário")}</span>',
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

    render_action_summary(summary)

    has_any_data = any(summary[key] for key in ("validated", "near_entries", "events", "avoid"))
    if not has_any_data:
        render_empty_state("Nenhuma leitura disponível", "Nenhuma leitura disponível. Atualize os dados ou execute o pipeline.")
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
            go_to("Configurações")
        return

    left_col, right_col = st.columns([0.65, 0.35], gap="large")

    with left_col:
        render_section_title("Leitura operacional", "Uma lista única para decidir o que validar, acompanhar ou evitar.")
        ordered_groups = (
            ("Operável agora", groups["olhar_primeiro"], "operavel"),
            ("Aguardando gatilho", groups["aguardar_gatilho"], "aguardar"),
            ("Evitar por enquanto", groups["evitar"], "evitar"),
        )
        decision_items: list[tuple[dict, str, int]] = []
        for label, items, group_key in ordered_groups:
            for thesis in items[:6]:
                decision_items.append((thesis, label, len(decision_items)))
        if not decision_items:
            render_empty_state("Nenhuma leitura disponível", "Nenhuma leitura disponível. Atualize os dados ou execute o pipeline.")
        else:
            st.markdown('<div class="integrated-panel">', unsafe_allow_html=True)
            for thesis, source_label, index in decision_items:
                event_label = (
                    f'{events_summary["next_asset"]} · {events_summary["next_date"]}'
                    if events_summary["next_asset"] == thesis.get("ativo") and events_summary["next_date"]
                    else "sem evento próximo"
                )
                action = render_decision_card(
                    {
                        "card_key": f"decision_panel_{source_label}_{index}_{thesis.get('ativo')}",
                        "source_label": source_label,
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
                handle_thesis_card_action(thesis, action, f"decision_{index}")
            st.markdown("</div>", unsafe_allow_html=True)

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
                ("Horário", format_dt(latest.get("finished_at"))),
                ("Modo", latest.get("mode") or "indisponível"),
                ("Origem", runner_label(latest.get("runner"))),
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
