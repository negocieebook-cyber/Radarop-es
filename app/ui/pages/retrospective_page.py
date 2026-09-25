"""Página de Retrospectiva: resultado estimado das candidatas vencidas."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components import mock_badge
from app.retrospective_engine import build_retrospective
from app.ui.shared import money


def retrospective_page() -> None:
    mock_badge("DADOS REAIS EOD / RESULTADO ESTIMADO — NÃO REGISTRA EXECUÇÃO REAL")
    st.caption(
        "Avalia as candidatas da Abertura cujo vencimento já passou, com o fechamento do ativo na data do vencimento "
        "(ou no último pregão anterior disponível) via histórico do opcoes.net.br. O resultado é uma estimativa do "
        "payoff da estrutura por contrato; não registra saída real nem custos."
    )
    retrospective = build_retrospective()
    summary = retrospective.get("summary", {})
    st.markdown("## Resumo das vencidas")
    metrics = st.columns(5)
    metrics[0].metric("Candidatas vencidas", summary.get("vencidas", 0))
    metrics[1].metric("Avaliadas", summary.get("avaliadas", 0))
    metrics[2].metric("Ganhos estimados", summary.get("ganhos", 0))
    metrics[3].metric("Perdas estimadas", summary.get("perdas", 0))
    metrics[4].metric("Inconclusivas", summary.get("inconclusivas", 0))

    by_strategy = summary.get("por_estrategia") or {}
    if by_strategy:
        st.markdown("### Por estratégia")
        rows = [
            {
                "Estrutura": strategy,
                "Vencidas avaliadas": bucket.get("n", 0),
                "Ganhos": bucket.get("ganhos", 0),
                "Perdas": bucket.get("perdas", 0),
                "Zerados": bucket.get("zerados", 0),
                "Taxa de ganho": f"{bucket['taxa_ganho'] * 100:.1f}%" if bucket.get("taxa_ganho") is not None else "indisponível",
                "P/L estimado somado": money(bucket.get("soma_pnl_estimado")),
            }
            for strategy, bucket in sorted(by_strategy.items())
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(
            "Taxa de ganho sobre o payoff no vencimento com preços EOD; amostra pequena não é estatística. "
            "Não substitui registro real de saída."
        )
    else:
        st.info("Nenhuma candidata vencida foi avaliada ainda. Candidatas aparecem aqui quando o vencimento expira.")

    expired = retrospective.get("expired") or []
    if expired:
        st.markdown("## Detalhe das vencidas")
        rows = [
            {
                "Ativo": item.get("ativo"),
                "Estratégia": item.get("estrategia"),
                "Vencimento": item.get("vencimento"),
                "Entrada": money(item.get("entrada_referencia")),
                "Fonte da entrada": item.get("entrada_fonte"),
                "Preço do vencimento": money(item.get("preco_vencimento")) if item.get("preco_vencimento") is not None else "indisponível",
                "Data do preço": item.get("data_preco_vencimento") or "indisponível",
                "Resultado": item.get("resultado"),
                "P/L estimado (contrato)": money(item.get("pnl_por_unidade_estimado")) if item.get("pnl_por_unidade_estimado") is not None else "indisponível",
                "P/L total estimado": money(item.get("pnl_total_estimado")) if item.get("pnl_total_estimado") is not None else "sem quantidade registrada",
                "Status registrado": item.get("status_registrado") or "indisponível",
                "Erro": item.get("error") or "—",
            }
            for item in expired
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        invalidated = [item for item in expired if str(item.get("status_registrado")) == "invalidado"]
        if invalidated:
            st.warning(
                f"{len(invalidated)} candidata(s) vencidas foram marcadas como invalidadas antes do vencimento e não "
                "têm resultado estimado: a saída real não foi registrada no app."
            )
    else:
        st.info("Nenhuma candidata vencida no momento.")

    active = retrospective.get("active") or []
    if active:
        st.markdown("## Em andamento (vencimento futuro)")
        rows = [
            {
                "Ativo": item.get("ativo"),
                "Estratégia": item.get("estrategia"),
                "Vencimento": item.get("vencimento") or "indisponível",
                "Status": item.get("status") or "indisponível",
                "Convertida em posição": "sim" if item.get("convertida") else "não",
            }
            for item in active
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Nenhuma candidata em andamento.")

    st.info(retrospective.get("observacao", ""))
