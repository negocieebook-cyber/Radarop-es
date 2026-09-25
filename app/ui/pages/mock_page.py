"""Páginas e auxiliares do motor MOCK / EXEMPLO."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pandas as pd
import streamlit as st

from app.bulkowski_engine import analyze_pattern_for_asset
from app.components import mock_badge, opportunity_card, sources_table
from app.healthbox_engine import build_healthbox, healthbox_confirms_strategy, healthbox_score
from app.mock_data import MOCK_ASSET_SNAPSHOTS, MOCK_OPPORTUNITIES
from app.opportunity_engine import generate_daily_opportunities, split_opportunities_by_status
from app.notices import NO_BROKER_NOTICE
from app.options_math import calculate_option_strategy
from app.scoring import score_opportunity
from app.storage import add_history_event, add_position
from app.validators import build_operation_checklist
from app.ui.shared import history_event, money, now_iso


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
        "Este formulário apenas salva um registro local. " + NO_BROKER_NOTICE
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
        st.markdown(f"**{item.get('question')}** — {item.get('detail', 'indisponível')}")

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
