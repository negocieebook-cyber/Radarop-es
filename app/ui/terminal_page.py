from __future__ import annotations

from typing import Any

import streamlit as st

from app.data.hub import build_terminal_decision_payload
from app.ui.components import (
    render_data_notice,
    render_empty_state,
    render_info_panel,
    render_market_card,
    render_section_title,
)


def _normalize_ticker(value: str) -> str:
    return str(value or "").strip().upper()


def _format_value(value: Any, fallback: str = "indisponível") -> str:
    if value in (None, "", [], {}, ()):
        return fallback
    return str(value)


def _metric_delta(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _event_style(impact: str) -> tuple[str, str]:
    normalized = str(impact or "").lower()
    if any(token in normalized for token in ("favor", "positivo", "verde")):
        return "#163127", "#7ef0a7"
    if any(token in normalized for token in ("atenção", "atencao", "negativo", "vermelho", "imediata")):
        return "#341616", "#ff8f8f"
    return "#1c2634", "#9fc4ff"


def _alert_icon(text: str) -> str:
    normalized = str(text or "").lower()
    if any(token in normalized for token in ("bloqueio", "invalid", "evitar", "atenção", "atencao", "ruim", "ausente")):
        return "🔴"
    if any(token in normalized for token in ("pendente", "monitor", "confirm", "baixo", "neutro")):
        return "🟡"
    return "🟢"


def _render_strategy_card(payload: dict[str, Any]) -> None:
    strategy = payload.get("estrategia_principal") or {}
    operation = payload.get("operacao") or {}
    capital = operation.get("capital") or {}
    strike = operation.get("strike") or {}
    expiration = operation.get("vencimento") or {}
    risk = operation.get("risco") or {}

    if not strategy or strategy.get("status") in {"vazio", "indisponível"}:
        render_empty_state(
            "Ativo sem oportunidades ou dados de opções disponíveis no momento",
            "O Terminal não encontrou estratégia principal validável para este ativo.",
        )
        return

    with st.container(border=True):
        delta_value = _format_value(operation.get("delta"))
        if "0,25" in delta_value or "0,30" in delta_value or "0,35" in delta_value or "0,40" in delta_value:
            delta_value = f"{delta_value} 🟢"

        st.markdown(
            """
            <div style="font-size:12px;letter-spacing:.12em;color:#8da2bd;margin-bottom:6px;">ESTRATÉGIA RECOMENDADA</div>
            <div style="font-size:24px;font-weight:700;color:#f5f7fb;">%s</div>
            <div style="font-size:14px;color:#b8c3d6;margin-top:4px;margin-bottom:14px;">%s</div>
            """
            % (
                _format_value(strategy.get("strategy_name") or strategy.get("preferred_strategy")),
                _format_value(strategy.get("explicacao_curta") or strategy.get("motivo") or strategy.get("status")),
            ),
            unsafe_allow_html=True,
        )

        detail_left, detail_right = st.columns(2, gap="medium")
        with detail_left:
            render_info_panel(
                "Parâmetros da estrutura",
                [
                    ("Delta", delta_value),
                    ("Strike", _format_value(strike.get("regiao_sugerida") or strike.get("comprado") or strike.get("vendido"))),
                    ("Vencimento", _format_value(expiration.get("data") or expiration.get("janela_ideal"))),
                    ("Capital recomendado", _format_value(capital.get("estimativa"))),
                    ("Capital mínimo", _format_value(capital.get("minimo_tecnico"))),
                ],
            )
        with detail_right:
            st.markdown(
                """
                <div style="font-size:12px;letter-spacing:.08em;color:#8da2bd;margin-bottom:10px;">PLANO DE RISCO</div>
                <div style="display:grid;gap:10px;">
                <div style="padding:10px 12px;border-radius:12px;background:#173022;color:#87f0aa;"><b>Lucro Máximo</b><br>%s</div>
                <div style="padding:10px 12px;border-radius:12px;background:#341818;color:#ff9a9a;"><b>Perda Máxima</b><br>%s</div>
                <div style="padding:10px 12px;border-radius:12px;background:#17283b;color:#8fc5ff;"><b>Capital</b><br>%s</div>
                <div style="padding:10px 12px;border-radius:12px;background:#1f2632;color:#d5dbe7;"><b>Break-even</b><br>%s</div>
                <div style="padding:10px 12px;border-radius:12px;background:#1f2632;color:#d5dbe7;"><b>Risco/retorno</b><br>%s</div>
                </div>
                """
                % (
                    _format_value(operation.get("ganho")),
                    _format_value(operation.get("perda")),
                    _format_value(capital.get("estimativa") or capital.get("minimo_tecnico")),
                    _format_value(operation.get("break_even")),
                    _format_value(risk.get("risco_retorno")),
                ),
                unsafe_allow_html=True,
            )


def _render_calendar(payload: dict[str, Any]) -> None:
    calendar = payload.get("eventos_calendario") or {}
    items = calendar.get("items") or []

    with st.container(border=True):
        render_section_title("CALENDÁRIO E IMPACTO", "Eventos próximos que podem afetar a decisão")
        if not items:
            st.markdown("📅 Nenhum evento relevante nos próximos 15 dias")
            return

        for item in items[:5]:
            impact = _format_value(item.get("impacto_operacional"), "indisponível")
            background, color = _event_style(impact)
            st.markdown(
                """
                <div style="border-radius:14px;padding:12px 14px;margin-bottom:10px;background:%s;border:1px solid rgba(255,255,255,.06);">
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                <div>
                <div style="font-size:14px;font-weight:600;color:#f4f7fb;">%s</div>
                <div style="font-size:12px;color:#c2cbda;">%s</div>
                </div>
                <div style="font-size:12px;font-weight:700;color:%s;">%s</div>
                </div>
                </div>
                """
                % (
                    background,
                    _format_value(item.get("estrutura") or item.get("tipo")),
                    f"Data: {_format_value(item.get('data'))} · Dias: {_format_value(item.get('dias'))}",
                    color,
                    impact,
                ),
                unsafe_allow_html=True,
            )


def _render_alerts(payload: dict[str, Any]) -> None:
    points = payload.get("pontos_de_atencao") or []

    with st.container(border=True):
        render_section_title("ALERTAS", "Leitura rápida dos pontos que exigem atenção")
        if not points:
            render_data_notice("Sem alertas relevantes no payload atual.")
            return

        for item in points:
            st.markdown(f"{_alert_icon(item)} {_format_value(item)}")


def render_terminal_page() -> None:
    st.sidebar.markdown("## Terminal")
    ticker = _normalize_ticker(st.sidebar.text_input("Ticker", value="", placeholder="Ex: PETR4"))

    if not ticker:
        render_data_notice("Digite um ticker para consolidar contexto, estratégia, risco, eventos e alertas em uma única tela.")
        return

    payload = build_terminal_decision_payload(ticker)
    contexto = payload.get("contexto_ativo") or {}
    healthbox = payload.get("healthbox") or {}
    diagnostico = payload.get("diagnostico_grafico") or {}
    thesis = diagnostico.get("thesis") or {}
    has_options_data = bool(payload.get("oportunidades_reais")) or payload.get("estrategia_principal", {}).get("status") not in {"vazio", "indisponível"}

    if not contexto or (contexto.get("status_dado") == "não coletado" and not has_options_data):
        render_empty_state(
            "Ativo sem oportunidades ou dados de opções disponíveis no momento",
            "Não há contexto salvo nem estrutura de opções aproveitável para este ticker.",
        )
        return

    st.markdown("## Terminal")
    metric_cols = st.columns(4, gap="medium")
    metric_cols[0].metric("Preço Atual", _format_value(contexto.get("preco_atual")))
    metric_cols[1].metric("Variação %", _format_value(contexto.get("variacao_diaria_percent"), "indisponível"), _metric_delta(contexto.get("variacao_diaria_percent")))
    metric_cols[2].metric("Saúde", _format_value(healthbox.get("saude")))
    metric_cols[3].metric("Tendência", _format_value(healthbox.get("tendencia")))

    left_col, right_col = st.columns([0.48, 0.52], gap="large")

    with left_col:
        with st.container(border=True):
            render_section_title("Healthbox e Diagnóstico", f"Leitura rápida para {ticker}")
            if contexto and contexto.get("status_dado") != "não coletado":
                render_market_card(contexto, healthbox)
            else:
                render_data_notice("Snapshot de mercado indisponível; exibindo apenas o que o payload conseguiu consolidar.")

            render_info_panel(
                "Saúde do ativo",
                [
                    ("Saúde", _format_value(healthbox.get("saude"))),
                    ("Tendência", _format_value(healthbox.get("tendencia"))),
                    ("Liquidez", _format_value(healthbox.get("liquidez"))),
                ],
            )

        with st.container(border=True):
            render_info_panel(
                "Diagnóstico Gráfico com Tese",
                [
                    ("Status", _format_value(thesis.get("status"))),
                    ("Direção", _format_value(thesis.get("direcao_tese"))),
                    ("Regime", _format_value(thesis.get("market_regime"))),
                    ("Gatilho", _format_value(thesis.get("gatilho_confirmacao"))),
                    ("Motivo", _format_value(thesis.get("motivo_status"))),
                ],
            )

    with right_col:
        render_section_title("Decisão", f"Motor unificado para {ticker}")
        if has_options_data:
            _render_strategy_card(payload)
        else:
            render_empty_state(
                "Ativo sem oportunidades ou dados de opções disponíveis no momento",
                "O payload não trouxe oportunidade real nem estratégia principal para este ticker.",
            )

        _render_calendar(payload)
        _render_alerts(payload)
