"""Páginas de acompanhamento: abertura, posições, histórico e alertas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from app.components import alerts_section, mock_badge, positions_table, render_alert_card
from app.healthbox_engine import healthbox_confirms_strategy
from app.market_snapshot_engine import snapshot_to_healthbox
from app.mock_data import MOCK_ALERTS, MOCK_MARKET_CONTEXT
from app.notices import NO_BROKER_NOTICE
from app.opening_watchlist import (
    EOD_NOTICE,
    build_manual_position,
    evaluate_watchlist_item,
    load_opening_watchlist,
    mark_as_converted,
    remove_from_opening_watchlist,
)
from app.position_marking import build_option_mark_context
from app.position_monitor import build_position_status, generate_exit_alerts
from app.storage import add_history_event, add_position, load_history, load_positions, save_history, save_positions
from app.update_orchestrator import load_market_snapshots
from app.ui.shared import history_event, money, now_iso


def opening_watchlist_page() -> None:
    st.warning(f"{EOD_NOTICE} {NO_BROKER_NOTICE}")
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

def _context_for_position(position: dict, real_snapshots: dict) -> dict | None:
    """Contexto do monitor: real para posições da Abertura (com marcação EOD), mock para o resto."""
    if position.get("origem") != "opening_watchlist":
        return MOCK_MARKET_CONTEXT.get(position.get("ativo"))
    snapshot = real_snapshots.get(position.get("ativo"))
    if not snapshot:
        return None
    healthbox = snapshot_to_healthbox(snapshot)
    healthbox["confirmation"] = healthbox_confirms_strategy(healthbox, position.get("tipo_estrutura", ""))
    context = {
        "asset_snapshot": snapshot,
        "healthbox": healthbox,
        "current_mark": None,
        "tipo_dado": snapshot.get("tipo_dado"),
        "fonte": snapshot.get("fonte") or snapshot.get("fonte_base") or "brapi",
    }
    context.update(build_option_mark_context(position))
    return context


def positions_page() -> None:
    mock_badge("REGISTROS LOCAIS — MOCK E ENTRADAS MANUAIS EOD IDENTIFICADOS")
    positions = load_positions()
    if positions:
        positions_table(positions)
        st.markdown("## Monitor de Posições")
        real_snapshots = {item.get("ativo"): item for item in load_market_snapshots() if item.get("ativo")}
        monitor_rows = []
        for position in positions:
            context = _context_for_position(position, real_snapshots)
            result = build_position_status(position, context)
            pnl = result["pnl"]
            capture = result["gain_capture"]
            option_mark = result.get("option_mark") or {}
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
                    "Marcação da estrutura": money(option_mark.get("current_mark")) if option_mark.get("calculated") else "indisponível",
                    "Base da marcação": (option_mark.get("mark_basis") or "indisponível") if option_mark.get("calculated") else "—",
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
        st.info(
            "Posições da Abertura são acompanhadas pelo ativo e pelas regras; o P/L da opção usa a marcação do último "
            "preço da última sessão (EOD) via opcoes.net.br. Marcação EOD não é cotação intraday e não considera bid/ask."
        )
        st.markdown("### Detalhes das posições")
        for position in positions:
            if st.button(f"Ver detalhes da posição · {position.get('ativo')} · {position.get('id', '')[:8]}", key=f"position-detail-{position.get('id')}"):
                st.session_state["position_detail_id"] = position.get("id")
        selected_position = next((item for item in positions if item.get("id") == st.session_state.get("position_detail_id")), None)
        if selected_position:
            context = _context_for_position(selected_position, real_snapshots)
            result = build_position_status(selected_position, context)
            st.markdown(f"#### {selected_position.get('ativo')} · {selected_position.get('estrategia')}")
            if selected_position.get("origem") == "opening_watchlist":
                st.write({"origem": "Abertura", "preço real de entrada": selected_position.get("preco_real_entrada"), "preço EOD de referência": selected_position.get("preco_eod_referencia"), "regras de invalidação": selected_position.get("invalidation_rules", [])})
            option_mark = result.get("option_mark") or {}
            if option_mark.get("calculated") and option_mark.get("legs"):
                st.markdown("#### Marcação da estrutura (EOD, última sessão)")
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Perna": leg.get("papel"),
                            "Lado": leg.get("lado"),
                            "Símbolo": leg.get("simbolo"),
                            "Strike": leg.get("strike"),
                            "Prêmio última sessão": money(leg.get("premio_ultima_sessao")),
                            "Negócios": leg.get("negocios"),
                            "Data da cotação": leg.get("quote_date"),
                            "IV": leg.get("iv"),
                            "Delta": leg.get("delta"),
                        }
                        for leg in option_mark.get("legs")
                    ]),
                    width="stretch",
                    hide_index=True,
                )
                st.caption(f"Vencimento usado: {option_mark.get('expiration_used')} · Fonte: {option_mark.get('fonte')} · {option_mark.get('observacao')}")
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


def positions_hub_page() -> None:
    tabs = st.tabs(["Posições", "Alertas"])
    with tabs[0]:
        positions_page()
    with tabs[1]:
        alerts_page()
