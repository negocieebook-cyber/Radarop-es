"""Componentes visuais reutilizáveis da dashboard."""

from __future__ import annotations

import html
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from app.formatting import format_dt
from app.statuses import status_css_class, status_label
from app.theme import get_theme_css


def inject_styles() -> None:
    st.markdown(get_theme_css(), unsafe_allow_html=True)


def _escape(value: object, fallback: str = "indisponível") -> str:
    if value is None or value == "":
        return fallback
    return html.escape(str(value))


def _status_css(status: str) -> str:
    return status_css_class(status)


def render_mock_badge(text: str = "DADOS MOCK / EXEMPLO") -> None:
    st.markdown(f'<span class="mock-badge">{_escape(text)}</span>', unsafe_allow_html=True)


def _metric_value_css(status: str) -> str:
    mapping = {
        "status-approved": "v-approved",
        "status-warning": "v-warning",
        "status-rejected": "v-rejected",
        "status-info": "v-info",
    }
    return mapping.get(_status_css(status), "v-neutral")


def _fmt_num(value: object, digits: int = 2) -> str:
    if value in (None, ""):
        return "—"
    try:
        return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(value)


def _money_br(value: object) -> str:
    if not isinstance(value, (int, float)):
        return _escape(value)
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_metric_card(value: str | int, label: str, subtitle: str = "", status: str = "neutral") -> None:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">{_escape(label)}</div>'
        f'<div class="metric-value {_metric_value_css(status)}">{_escape(value, "0")}</div>'
        + (f'<div class="metric-note">{_escape(subtitle)}</div>' if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> None:
    st.markdown(
        f'<span class="status-badge {_status_css(status)}">{_escape(status_label(status))}</span>',
        unsafe_allow_html=True,
    )


def render_page_header(title: str, badge_text: str, description: str = "", how_to: list[str] | None = None) -> None:
    description_html = f'<p class="page-desc">{_escape(description, "")}</p>' if description else ""
    st.markdown(
        f'<div class="page-header"><div><div class="eyebrow">Radar de Opções Brasil</div>'
        f'<h1 class="page-title">{_escape(title)}</h1>{description_html}</div>'
        f'<span class="mock-badge page-header-badge">{_escape(badge_text)}</span></div>',
        unsafe_allow_html=True,
    )
    if how_to:
        parts = [
            f'<span class="howto-step"><span class="howto-num">{index}</span>{_escape(step, "")}</span>'
            for index, step in enumerate(how_to, start=1)
        ]
        steps = '<span class="howto-sep">›</span>'.join(parts)
        st.markdown(
            f'<div class="howto-box"><span class="howto-label">Como usar</span>{steps}</div>',
            unsafe_allow_html=True,
        )


def render_section_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-title"><h2>{_escape(title)}</h2><p>{_escape(subtitle, "")}</p></div>',
        unsafe_allow_html=True,
    )


def render_data_notice(text: str) -> None:
    st.markdown(f'<div class="compact-banner">⚠ {_escape(text)}</div>', unsafe_allow_html=True)


def render_alert_card(alert: dict) -> None:
    severity = str(alert.get("severity", "cinza"))
    css = {"vermelho": "red", "amarelo": "yellow", "verde": "green"}.get(severity, "gray")
    st.markdown(
        f'<div class="alert-card {css}"><b>{_escape(alert.get("ativo", "—"))} · {_escape(alert.get("status", "—"))}</b><br>'
        f'<span>{_escape(alert.get("reason", alert.get("motivo", "indisponível")))}</span><br>'
        f'<small>{_escape(alert.get("tipo_dado", "MOCK / EXEMPLO"))} · {_escape(alert.get("fonte", "fonte ausente"))}</small></div>',
        unsafe_allow_html=True,
    )


def render_checklist_item(question: str, status: str, detail: str) -> None:
    icon = "🟢" if status == "ok" else "🟡" if status in {"atenção", "não calculado"} else "⚪" if status == "indisponível" else "🔴"
    st.markdown(f"{icon} **{question}** — {detail}")


def classify_data_age(collected_at: str | None, fresh_minutes: int = 30) -> str:
    if not collected_at:
        return "indisponível"
    try:
        collected = datetime.fromisoformat(str(collected_at).replace("Z", "+00:00"))
        if collected.tzinfo is None:
            collected = collected.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - collected.astimezone(timezone.utc)).total_seconds() / 60
        return "atualizado" if age_minutes <= fresh_minutes else "atrasado"
    except (TypeError, ValueError):
        return "indisponível"


def render_data_status_strip(status: dict) -> None:
    latest = status.get("latest_update") or {}
    summary = status.get("snapshot_summary") or {}
    strip = [
        ("Status dos dados", "falha na fonte" if not latest.get("success", True) and latest else "atualizado" if latest else "sem leitura"),
        ("Última atualização", format_dt(latest.get("finished_at"))),
        ("Ativos atualizados", latest.get("updated_count", summary.get("completos", 0))),
    ]
    body = "".join(
        f'<div class="status-item"><b>{_escape(label)}</b><span>{_escape(value)}</span></div>'
        for label, value in strip
    )
    st.markdown(f'<div class="surface-card"><div class="status-strip">{body}</div></div>', unsafe_allow_html=True)


def render_action_summary(summary: dict) -> None:
    metrics = [
        (summary.get("validated", 0), "Operáveis", "Prontas para validar no book", "approved"),
        (summary.get("near_entries", 0), "Aguardando gatilho", "Gatilho e invalidação definidos", "warning"),
        (summary.get("events", 0), "Eventos próximos", "Resultados em até 5 dias", "info"),
        (summary.get("avoid", 0), "Evitar", "Sem setup ou bloqueadas hoje", "rejected"),
    ]
    columns = st.columns(4)
    for column, (value, label, subtitle, status) in zip(columns, metrics):
        with column:
            render_metric_card(value, label, subtitle, status)


def _detail_box(label: str, value: object) -> str:
    return f'<div class="detail-box"><b>{_escape(label)}</b><span>{_escape(value)}</span></div>'


def _line_box(label: str, value: object) -> str:
    return f'<div class="compact-line"><b>{_escape(label)}</b><span>{_escape(value)}</span></div>'


_PILL_CLASS = {
    "status-approved": "pill-approved",
    "status-warning": "pill-warning",
    "status-rejected": "pill-rejected",
    "status-info": "pill-info",
    "status-neutral": "pill-neutral",
}


def _render_op_actions(card_key: str) -> str | None:
    row = st.columns([0.15, 0.12, 0.73], gap="small")
    action = None
    if row[0].button("Detalhes", key=f"decision_detail_{card_key}", type="primary"):
        action = "details"
    if row[1].button("Simular", key=f"decision_simulate_{card_key}"):
        action = "simulate"
    return action


RUNNER_LABELS = {
    "local_script": "Script local",
    "streamlit_app": "App Streamlit",
    "github_actions": "GitHub Actions",
}


def runner_label(value: object) -> str:
    raw = str(value or "").strip()
    return RUNNER_LABELS.get(raw.lower(), raw.replace("_", " ") if raw else "indisponível")


STRATEGY_LABELS = {
    "call_debit_spread": "Spread debitável de call",
    "put_debit_spread": "Spread debitável de put",
    "bull_put_spread": "Bull put spread",
    "bear_call_spread": "Bear call spread",
    "covered_call": "Call coberta",
    "iron_condor": "Iron condor",
    "iron_butterfly": "Iron butterfly",
    "cash_secured_put": "Put coberta de caixa (cash secured)",
    "protective_put": "Put protetiva",
    "calendar_spread": "Spread de calendário",
    "collar": "Colar (collar)",
    "diagonal_spread": "Spread diagonal",
    "long_straddle": "Straddle comprado",
    "long_strangle": "Strangle comprado",
    "short_straddle_travado": "Straddle vendido travado",
    "short_strangle_travado": "Strangle vendido travado",
    "ratio_spread_travado": "Ratio spread travado",
    "backspread_call": "Backspread de call",
    "backspread_put": "Backspread de put",
    "spread": "Spread",
    "spread_disponivel": "Spread disponível",
}


def strategy_label(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "Estratégia indisponível"
    if raw in STRATEGY_LABELS:
        return STRATEGY_LABELS[raw]
    parts = [part.strip() for part in raw.split(" ou ")]
    if len(parts) > 1:
        return " ou ".join(STRATEGY_LABELS.get(part, part.replace("_", " ")) for part in parts)
    return raw.replace("_", " ")


def render_decision_card(item: dict) -> str | None:
    card_key = str(item.get("card_key") or item.get("id") or item.get("ativo") or "item")
    status = str(item.get("action_status") or item.get("practical_action") or item.get("conditional_status") or item.get("status") or "inconclusivo")
    badge_css = _status_css(status)
    accent = {"status-approved": "c-approved", "status-warning": "c-warning", "status-rejected": "c-rejected", "status-info": "c-info"}.get(badge_css, "c-neutral")
    headline = status_label(status)
    strategy = item.get("strategy_name") or item.get("estrategia") or item.get("preferred_strategy")
    score = item.get("score") or item.get("near_setup_score") or (item.get("best_strategy") or {}).get("score")
    gatilho = item.get("gatilho_confirmacao") or item.get("entry_price_condition") or item.get("conditional_trigger")
    invalidacao = item.get("invalidacao") or item.get("invalidation_rules_short") or item.get("motivo")
    evento = item.get("event_label") or item.get("evento_proximo")
    cadeia = item.get("cadeia_opcoes_status") or item.get("chain_status")
    motivo = item.get("reason") or item.get("motivo") or item.get("evaluation_reason")

    score_text = str(score) if score is not None and str(score) != "" else None
    score_chip = f'<span class="op-score">Score {html.escape(score_text)}</span>' if score_text else ""
    head = (
        f'<div class="op-head"><div>'
        f'<div class="op-eyebrow">{_escape(item.get("source_label", "PAINEL"))}</div>'
        f'<div class="op-ticker">{_escape(item.get("ativo"))}</div></div>'
        f'<div class="op-badges"><span class="pill {_PILL_CLASS.get(badge_css, "pill-neutral")}">{_escape(headline)}</span>'
        f'<span class="pill pill-ghost">Não é ordem</span></div></div>'
    )
    line = f'<div class="op-line"><span class="op-strategy">{_escape(strategy_label(strategy) if strategy else "Estratégia indisponível")}</span>{score_chip}</div>'
    fields: list[tuple[str, object]] = []
    if gatilho:
        fields.append(("Gatilho", gatilho))
    if invalidacao:
        fields.append(("Invalidação", invalidacao))
    if cadeia:
        fields.append(("Cadeia de opções", status_label(cadeia)))
    if evento:
        fields.append(("Evento próximo", evento))
    field_html = "".join(f'<div class="op-field"><dt>{_escape(label)}</dt><dd>{_escape(value)}</dd></div>' for label, value in fields)
    fields_block = f'<dl class="op-fields">{field_html}</dl>' if field_html else ""
    reason_block = f'<div class="op-reason">{_escape(motivo)}</div>' if motivo else ""
    st.markdown(f'<div class="op-card {accent}">{head}{line}{fields_block}{reason_block}</div>', unsafe_allow_html=True)
    return _render_op_actions(card_key)


def render_empty_state(title: str, text: str) -> None:
    st.markdown(
        f'<div class="empty-state"><div class="empty-title">{_escape(title)}</div><div class="empty-copy">{_escape(text)}</div></div>',
        unsafe_allow_html=True,
    )


def render_info_panel(title: str, rows: list[tuple[str, object]]) -> None:
    body = "".join(
        f'<div class="info-box"><b>{_escape(label)}</b><span>{_escape(value)}</span></div>'
        for label, value in rows
    )
    st.markdown(
        f'<div class="surface-card"><div class="small-label">{_escape(title)}</div><div class="info-row">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_compact_thesis_card(item: dict) -> str | None:
    action_item = {
        "card_key": item.get("id") or item.get("ativo"),
        "source_label": "TESE GRÁFICA",
        "ativo": item.get("ativo"),
        "action_status": item.get("practical_action") or item.get("status"),
        "action_label": item.get("practical_action_label") or item.get("status"),
        "strategy_name": (item.get("best_strategy") or {}).get("strategy_name") or item.get("preferred_strategy"),
        "score": (item.get("best_strategy") or {}).get("score") or item.get("near_setup_score"),
        "gatilho_confirmacao": item.get("gatilho_confirmacao"),
        "invalidacao": item.get("invalidacao"),
        "cadeia_opcoes_status": item.get("cadeia_opcoes_status"),
        "reason": (item.get("best_strategy") or {}).get("reason") or item.get("evaluation_reason"),
    }
    return render_decision_card(action_item)


def render_market_card(snapshot: dict, healthbox: dict) -> None:
    change = snapshot.get("variacao_diaria_percent")
    score = (healthbox.get("score_result") or {}).get("score")
    status_dado = str(snapshot.get("status_dado", "indisponível"))
    badge_css = _status_css(status_dado)
    change_html = ""
    if isinstance(change, (int, float)):
        direction = "up" if change > 0 else "down" if change < 0 else "flat"
        arrow = "▲" if change > 0 else "▼" if change < 0 else ""
        change_html = f'<span class="chg {direction}">{arrow} {abs(change):.2f}%</span>'.replace(".", ",")
    stats = [
        ("Tendência", status_label(snapshot.get("tendencia"))),
        ("Healthbox", score if score is not None else "—"),
        ("RSI", _fmt_num(snapshot.get("rsi"))),
        ("rVol", _fmt_num(snapshot.get("rvol"))),
    ]
    stats_html = "".join(f'<div class="mkt-stat"><dt>{_escape(label)}</dt><dd>{_escape(value)}</dd></div>' for label, value in stats)
    campos = ", ".join(snapshot.get("campos_ausentes", [])) or "nenhum"
    st.markdown(
        f'<div class="mkt-card {badge_css.replace("status-", "c-")}">'
        f'<div class="op-head"><div><div class="op-eyebrow">Mercado real</div>'
        f'<div class="op-ticker">{_escape(snapshot.get("ativo"))}</div></div>'
        f'<span class="pill {_PILL_CLASS.get(badge_css, "pill-neutral")}">{_escape(status_label(status_dado))}</span></div>'
        f'<div class="mkt-price">{_money_br(snapshot.get("preco_atual"))} {change_html}</div>'
        f'<dl class="mkt-stats">{stats_html}</dl>'
        f'<div class="mkt-foot">Fonte {_escape(snapshot.get("fonte"))} · coleta {format_dt(snapshot.get("coleta"))} · campos ausentes: {_escape(campos)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_update_status_card(status: dict, summary: dict) -> None:
    latest = status.get("latest_update")
    if not latest:
        st.info("Nenhuma atualização registrada ainda.")
        return
    if not latest.get("success") or latest.get("error_count", 0):
        general = "falha na fonte"
    elif latest.get("incomplete_count", 0):
        general = "atualizado com dados parciais"
    else:
        general = "atualizado"
    st.markdown(
        f'<div class="section-card"><div class="small-label">STATUS DOS DADOS</div>'
        f'<p><span class="status-badge {_status_css(general)}">{_escape(status_label(general))}</span> '
        f'<span class="status-badge status-neutral">snapshot {_escape(status_label(status.get("snapshot_age_status", "indisponível")))}</span></p>'
        f'<p><b>Última atualização:</b> {format_dt(latest.get("finished_at"))}<br>'
        f'<b>Modo:</b> {_escape(latest.get("mode"))} · <b>Origem:</b> {_escape(runner_label(latest.get("runner")))} · <b>Fonte:</b> {_escape(latest.get("source") or summary.get("fonte"))}</p>'
        f'<p><b>Ativos consultados:</b> {latest.get("total_tickers", 0)} · <b>Atualizados:</b> {latest.get("updated_count", 0)} · '
        f'<b>Incompletos:</b> {latest.get("incomplete_count", 0)} · <b>Erros:</b> {latest.get("error_count", 0)}</p></div>',
        unsafe_allow_html=True,
    )


def render_options_status_card(summary: dict) -> None:
    access = str(summary.get("access_status", "indisponível"))
    label = "último snapshot salvo" if summary.get("series_count", 0) else "sem acesso" if access == "sem_acesso" else "teste disponível"
    st.markdown(
        f'<div class="section-card"><div class="small-label">OPÇÕES EOD</div>'
        f'<p><span class="status-badge {_status_css(label)}">{_escape(label)}</span></p>'
        f'<p><b>Fonte:</b> {_escape(summary.get("fonte", "brapi_options"))} · <b>Séries salvas:</b> {summary.get("series_count", 0)} · '
        f'<b>Status:</b> {_escape(summary.get("status_dado", "indisponível"))} · <b>Coleta:</b> {_escape(format_dt(summary.get("coleta"), "nenhuma"))}</p></div>',
        unsafe_allow_html=True,
    )


def render_options_eod_status_card(status: dict) -> None:
    last = status.get("last_update") or {}
    summary = status.get("snapshot_summary") or {}
    general = str(last.get("status") or summary.get("status") or "não atualizado")
    st.markdown(
        f'<div class="section-card"><div class="small-label">STATUS OPÇÕES EOD</div>'
        f'<p><span class="status-badge {_status_css(general)}">{_escape(status_label(general))}</span></p>'
        f'<p><b>Última atualização:</b> {format_dt(last.get("finished_at") or summary.get("latest_collection") or None, "não atualizada")}<br>'
        f'<b>Ativos disponíveis:</b> {last.get("available_count", summary.get("available_count", 0))} · <b>Séries:</b> {last.get("total_series", summary.get("total_series", 0))} · '
        f'<b>Erros:</b> {last.get("error_count", summary.get("error_count", 0))}</p></div>',
        unsafe_allow_html=True,
    )


def render_real_opportunity_card(item: dict, key_suffix: str = "") -> str | None:
    action_item = {
        "card_key": f'{item.get("ativo")}_{item.get("estrategia")}_{item.get("vencimento")}{key_suffix}',
        "source_label": "RADAR DE FECHAMENTO",
        "ativo": item.get("ativo"),
        "action_status": item.get("conditional_status") or item.get("status"),
        "action_label": item.get("conditional_decision") or item.get("conditional_status"),
        "strategy_name": item.get("estrategia"),
        "score": item.get("score"),
        "gatilho_confirmacao": item.get("entry_price_condition") or "; ".join((item.get("confirmation_rules") or [])[:2]),
        "invalidacao": "; ".join((item.get("invalidation_rules") or [])[:2]) or item.get("motivo"),
        "cadeia_opcoes_status": item.get("liquidity_class") or item.get("liquidez"),
        "reason": item.get("motivo"),
    }
    return render_decision_card(action_item)


def render_graphical_thesis_card(item: dict) -> str | None:
    return render_compact_thesis_card(item)


def render_practical_strategy_card(item: dict) -> str | None:
    return render_compact_thesis_card(item)


def render_full_strategy_screening(item: dict) -> None:
    with st.expander(f"Ver screening completo · {item.get('ativo')}", expanded=False):
        rows = []
        for candidate in item.get("strategy_screening", []):
            plan = candidate.get("manual_validation_plan") or {}
            rows.append(
                {
                    "Estratégia": strategy_label(candidate.get("strategy_name")),
                    "Score": _display(candidate.get("suitability_score")),
                    "Status": status_label(candidate.get("status")),
                    "Objetivo": _display(candidate.get("objective_label")),
                    "Complexidade": _display(candidate.get("complexidade")),
                    "Motivos contra": "; ".join(candidate.get("motivos_contra", [])) or "—",
                    "Dados necessários": "; ".join(candidate.get("dados_necessarios", [])) or "—",
                    "Delta-alvo": _display(plan.get("delta_target")),
                    "Vencimento": _display(plan.get("expiration_window")),
                    "Encaixe capital": _display(candidate.get("capital_fit_status")),
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.caption("Nenhum screening disponível.")


def render_daily_priority_item(item: dict, key_suffix: str = "") -> None:
    render_decision_card(
        {
            "card_key": f'priority_{item.get("ativo")}_{item.get("strategy_name")}{key_suffix}',
            "source_label": "PRIORIDADE DIÁRIA",
            "ativo": item.get("ativo"),
            "action_status": item.get("practical_action"),
            "action_label": item.get("practical_action"),
            "strategy_name": item.get("strategy_name"),
            "score": item.get("suitability_score"),
            "gatilho_confirmacao": item.get("gatilho"),
            "invalidacao": item.get("invalidacao"),
            "cadeia_opcoes_status": item.get("cadeia_opcoes_status"),
            "reason": item.get("capital_fit_reason") or item.get("objective_description"),
        }
    )


def render_daily_priority_plan(item: dict, key: str) -> None:
    plan = item.get("manual_validation_plan") or {}
    with st.expander("Detalhes técnicos", expanded=False):
        st.write(
            {
                "delta_alvo": plan.get("delta_target"),
                "regiao_strike": plan.get("strike_region"),
                "vencimento": plan.get("expiration_window"),
                "checklist_book": plan.get("book_checklist", []),
                "rejeitar_se": plan.get("rejection_rules", []),
                "aviso": plan.get("warning"),
            }
        )


def render_manual_simulation(simulation: dict) -> None:
    break_evens = "; ".join(str(value) for value in simulation.get("break_even_points", [])) or "indisponível"
    st.markdown(
        f'<div class="section-card"><div class="small-label">SIMULADOR · NÃO É ORDEM</div>'
        f'<h3>{_escape(simulation.get("ticker"))} · {_escape(strategy_label(simulation.get("strategy_name")))}</h3>'
        f'<div class="compact-row">{_line_box("Fonte", simulation.get("source"))}{_line_box("Vencimento", simulation.get("expiration"))}'
        f'{_line_box("Quantidade", simulation.get("quantity"))}{_line_box("Multiplicador", simulation.get("contract_multiplier"))}'
        f'{_line_box("Capital mínimo", simulation.get("capital_required"))}{_line_box("Perda máxima", simulation.get("max_loss"))}'
        f'{_line_box("Ganho máximo", simulation.get("max_gain"))}{_line_box("Break-even", break_evens)}</div>'
        f'<div class="summary">{_escape(simulation.get("warning"))}</div></div>',
        unsafe_allow_html=True,
    )


def render_graphical_watchlist_card(item: dict) -> str | None:
    action_item = {
        "card_key": item.get("id") or item.get("ativo"),
        "source_label": "WATCHLIST DE ABERTURA",
        "ativo": item.get("ativo"),
        "action_status": item.get("status_atual"),
        "action_label": item.get("status_atual"),
        "strategy_name": item.get("estrutura_opcao_sugerida"),
        "score": item.get("near_setup_score"),
        "gatilho_confirmacao": item.get("gatilho_confirmacao"),
        "invalidacao": item.get("invalidacao"),
        "cadeia_opcoes_status": item.get("cadeia_opcoes_status"),
        "reason": item.get("evaluation_reason"),
    }
    return render_decision_card(action_item)


def render_top_conditional_entries(entries: list[dict], diagnostics: dict | None = None) -> None:
    st.markdown("## Top Entradas Condicionais EOD")
    if not entries:
        st.info("Nenhuma estrutura real EOD está em condição aceitável hoje.")
        return
    reasons = (diagnostics or {}).get("rejection_reasons", {})
    if reasons:
        principal = next(iter(reasons.items()))
        st.caption(f"Principal motivo agregado: {principal[0]} ({principal[1]})")
    for item in entries[:5]:
        st.markdown(
            f"**{_escape(item.get('ativo', '—'))} · {_escape(strategy_label(item.get('estrategia')))}** — "
            f"`{_escape(item.get('conditional_status', 'inconclusivo'))}` · score {_escape(item.get('score') if item.get('score') is not None else 'indisponível')}"
        )


def render_real_engine_status_card(options_snapshots: dict, last_summary: dict | None = None) -> None:
    summary = last_summary or {}
    unavailable = [
        symbol for symbol, snapshot in options_snapshots.items() if not snapshot.get("success") or not snapshot.get("series")
    ]
    st.markdown(
        f'<div class="section-card"><div class="small-label">RADAR DE FECHAMENTO</div>'
        f'<p><span class="status-badge status-info">gerado</span></p>'
        f'<p><b>Candidatas na última geração:</b> {summary.get("candidates", 0)} · <b>Evitar:</b> {summary.get("evitar", 0)} · '
        f'<b>Inconclusivas:</b> {summary.get("inconclusivo", 0)}<br><b>Ativos sem acesso/dados:</b> {_escape(", ".join(unavailable) or "nenhum")}</p></div>',
        unsafe_allow_html=True,
    )


def opportunity_card(item: dict) -> str | None:
    action_item = {
        "card_key": item.get("id") or item.get("ativo"),
        "source_label": "MOCK / EXEMPLO",
        "ativo": item.get("ativo"),
        "action_status": item.get("status"),
        "action_label": item.get("decisao"),
        "strategy_name": item.get("estrategia"),
        "score": item.get("score"),
        "gatilho_confirmacao": item.get("tese"),
        "invalidacao": item.get("motivo"),
        "cadeia_opcoes_status": item.get("liquidez_status"),
        "reason": item.get("motivo"),
    }
    action = render_decision_card(action_item)
    if action == "simulate":
        return "enter"
    if action == "details":
        return "detail"
    if action == "follow":
        return "watch"
    return None


def _display(value: object, fallback: str = "—") -> str:
    if value is None or str(value).strip() == "":
        return fallback
    return str(value)


def positions_table(positions: list[dict]) -> None:
    rows = [
        {
            "Ativo": _display(p.get("ativo")),
            "Origem": "Abertura" if p.get("origem") == "opening_watchlist" else "Mock / Exemplo",
            "Estratégia": strategy_label(p.get("estrategia")),
            "Preço real de entrada": _money_br(p.get("preco_real_entrada")),
            "Preço EOD de referência": _money_br(p.get("preco_eod_referencia")),
            "Quantidade": _display(p.get("quantidade")),
            "Data de entrada": format_dt(p.get("data_entrada")) if p.get("data_entrada") else "—",
            "Vencimento": f"{p.get('vencimento_dias')} dias" if p.get("vencimento_dias") is not None else "—",
            "Ganho máximo": _money_br(p.get("ganho_maximo")),
            "Perda máxima": _money_br(p.get("perda_maxima")),
            "Break-even": _money_br(p.get("break_even")),
            "Status": status_label(p.get("status")),
            "Tipo do dado": _display(p.get("tipo_dado")),
        }
        for p in positions
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def sources_table(sources: list[dict]) -> None:
    st.dataframe(pd.DataFrame(sources), width="stretch", hide_index=True)


def alerts_section(alerts: list[dict]) -> None:
    for alert in alerts:
        getattr(st, alert["nivel"])(f"**{alert['titulo']}:** {alert['mensagem']} — MOCK / EXEMPLO")


mock_badge = render_mock_badge
metric_card = render_metric_card
render_opportunity_card = opportunity_card
