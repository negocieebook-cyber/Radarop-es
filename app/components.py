"""Componentes visuais reutilizáveis da dashboard."""

from __future__ import annotations

import html
from datetime import datetime, timezone

import pandas as pd
import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root{--bg:#07101c;--panel:#0d1928;--panel2:#101f31;--line:#22364c;--text:#edf5ff;--muted:#92a6bb;--green:#38d996;--teal:#2dd4bf;--yellow:#f5c451;--red:#ff6577;--gray:#8494a7}
        #MainMenu,footer,[data-testid="stHeader"]{visibility:hidden}.stApp{background:radial-gradient(circle at 86% -8%,#12343d 0,#091522 31%,var(--bg) 68%);color:var(--text)}
        .block-container{padding-top:1.7rem;padding-bottom:4rem;max-width:1480px}h1{font-size:2.25rem!important;letter-spacing:-.035em}h2{margin-top:1.7rem!important}h1,h2,h3{font-weight:750!important}.stCaption{color:var(--muted)!important}
        [data-testid="stSidebar"]{background:linear-gradient(180deg,#091727,#07111d);border-right:1px solid var(--line);box-shadow:8px 0 30px #02071055}[data-testid="stSidebar"] .block-container{padding-top:1.5rem}
        .mock-badge,.status-badge{display:inline-flex;align-items:center;padding:.34rem .68rem;border-radius:999px;font-size:.72rem;font-weight:850;letter-spacing:.065em;text-transform:uppercase}.mock-badge{background:#3b2d0c;border:1px solid #a87b19;color:#ffe08a}.status-approved{background:#0d382b;color:#7ff0bd;border:1px solid #266d55}.status-warning{background:#3a2d0d;color:#ffe08a;border:1px solid #8c6b20}.status-rejected{background:#401b25;color:#ff9caa;border:1px solid #873545}.status-neutral{background:#202d3c;color:#b7c5d4;border:1px solid #41546a}
        .eyebrow,.small-label{color:#5eead4;font-size:.72rem;font-weight:850;letter-spacing:.13em;text-transform:uppercase}.section-title{display:flex;align-items:end;justify-content:space-between;margin:1.9rem 0 .75rem}.section-title h2{margin:0!important}.section-title p{margin:0;color:var(--muted)}
        .metric-card,.section-card,.data-warning,.sidebar-note{border:1px solid var(--line);border-radius:18px;background:linear-gradient(145deg,#122235ee,#0b1727ee);box-shadow:0 12px 34px #02071038}.metric-card{padding:1rem 1.1rem;min-height:118px;position:relative;overflow:hidden}.metric-card:before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:var(--gray)}.metric-card.approved:before{background:var(--green)}.metric-card.warning:before{background:var(--yellow)}.metric-card.rejected:before{background:var(--red)}.metric-card.teal:before{background:var(--teal)}.metric-card .value{font-size:2.15rem;font-weight:850;color:#f8fbff;line-height:1.1}.metric-card .label{color:#c5d2df;font-size:.88rem;margin-top:.32rem}.metric-card .subtitle{color:var(--muted);font-size:.72rem;margin-top:.45rem}
        .section-card{padding:1.15rem 1.25rem;margin:.65rem 0}.data-warning{padding:.85rem 1rem;border-color:#80651f;background:#2b220df2;color:#ffe6a1}.sidebar-note{padding:.85rem;background:#0d1d2d;color:#c6d4e2;font-size:.82rem}
        .opportunity-card{padding:1.15rem;border:1px solid var(--line);border-radius:20px;background:linear-gradient(150deg,#132438,#0b1727);min-height:420px;box-shadow:0 14px 35px #02071040;transition:transform .18s,border-color .18s}.opportunity-card:hover{transform:translateY(-2px)}.opportunity-card.approved{border-color:#286d56}.opportunity-card.warning{border-color:#82651e}.opportunity-card.rejected{border-color:#7c3240}.opportunity-card.neutral{border-color:#405369}.ticker{font-size:1.55rem;font-weight:900;letter-spacing:-.02em}.score{float:right;color:#79ead7;font-weight:850;background:#123831;padding:.24rem .5rem;border-radius:9px}.pill{display:inline-block;padding:.24rem .58rem;border-radius:999px;background:#17364a;color:#a7dff2;font-size:.75rem;margin-top:.35rem}.muted{color:var(--muted);font-size:.86rem;min-height:2.5rem}.detail{display:flex;justify-content:space-between;gap:.8rem;border-bottom:1px solid #1f3247;padding:.35rem 0;font-size:.82rem}.detail span:first-child{color:var(--muted)}.detail span:last-child{font-weight:700;text-align:right}.mini-grid{display:grid;grid-template-columns:1fr 1fr;gap:.45rem;margin-top:.75rem}.mini-box{background:#091522;border:1px solid #1f3347;border-radius:10px;padding:.5rem}.mini-box b{display:block;color:#91a6bb;font-size:.67rem;text-transform:uppercase}.mini-box span{font-size:.78rem}
        .market-card{padding:1rem;border:1px solid var(--line);border-radius:17px;background:linear-gradient(150deg,#112237,#0a1624);min-height:300px;box-shadow:0 10px 28px #02071035;margin-bottom:.7rem}.market-card.up{border-top:3px solid var(--green)}.market-card.sideways{border-top:3px solid var(--yellow)}.market-card.down{border-top:3px solid var(--red)}.market-card.incomplete{border-top:3px solid var(--gray)}.market-price{font-size:1.45rem;font-weight:850;margin:.25rem 0}.market-change.up{color:var(--green)}.market-change.down{color:var(--red)}.market-change.flat{color:var(--yellow)}.market-meta{font-size:.68rem;color:var(--muted);margin-top:.65rem;white-space:normal;word-break:break-word}
        .notice{padding:.8rem;border-radius:12px;border:1px solid #8b6c20;background:#2b210c;color:#fde68a}.alert-card{border:1px solid var(--line);border-radius:14px;padding:.85rem 1rem;margin:.45rem 0;background:#0d1a2a}.alert-card.red{border-left:4px solid var(--red)}.alert-card.yellow{border-left:4px solid var(--yellow)}.alert-card.green{border-left:4px solid var(--green)}.alert-card.gray{border-left:4px solid var(--gray)}
        [data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:15px;overflow:hidden;background:#0b1725}div.stButton>button{border-radius:11px;width:100%;border:1px solid #34516b;background:#102239;color:#eaf3fc;font-weight:700;min-height:2.45rem}div.stButton>button:hover{border-color:var(--teal);color:#7ff5df;transform:translateY(-1px)}[data-testid="stForm"]{border:1px solid var(--line);border-radius:18px;background:#0c1928;padding:1rem}[data-baseweb="select"]>div,[data-baseweb="input"]>div{background:#0d1b2b!important;border-color:#294158!important}
        @media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.opportunity-card{min-height:auto}.mini-grid{grid-template-columns:1fr}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_mock_badge(text: str = "DADOS MOCK / EXEMPLO") -> None:
    st.markdown(f'<span class="mock-badge">{html.escape(text)}</span>', unsafe_allow_html=True)


def render_metric_card(value: str | int, label: str, subtitle: str = "Leitura MOCK", status: str = "neutral") -> None:
    st.markdown(
        f'<div class="metric-card {html.escape(status)}"><div class="value">{html.escape(str(value))}</div><div class="label">{html.escape(label)}</div><div class="subtitle">{html.escape(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> None:
    normalized = status.lower()
    css = "status-approved" if normalized in {"aprovada", "manter", "realizar parcial", "realizar total"} else "status-warning" if normalized in {"atenção", "vencimento próximo", "acompanhar"} else "status-rejected" if normalized in {"reprovada", "sair agora", "tese invalidada", "evitar"} else "status-neutral"
    st.markdown(f'<span class="status-badge {css}">{html.escape(status)}</span>', unsafe_allow_html=True)


def render_section_title(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section-title"><h2>{html.escape(title)}</h2><p>{html.escape(subtitle)}</p></div>', unsafe_allow_html=True)


def render_data_notice(text: str) -> None:
    st.markdown(f'<div class="data-warning">⚠ {html.escape(text)}</div>', unsafe_allow_html=True)


def render_alert_card(alert: dict) -> None:
    severity = str(alert.get("severity", "cinza"))
    css = {"vermelho": "red", "amarelo": "yellow", "verde": "green"}.get(severity, "gray")
    st.markdown(f'<div class="alert-card {css}"><b>{html.escape(str(alert.get("ativo", "—")))} · {html.escape(str(alert.get("status", "—")))}</b><br><span>{html.escape(str(alert.get("reason", alert.get("motivo", "indisponível"))))}</span><br><small>{html.escape(str(alert.get("tipo_dado", "MOCK / EXEMPLO")))} · {html.escape(str(alert.get("fonte", "fonte ausente")))}</small></div>', unsafe_allow_html=True)


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


def render_market_card(snapshot: dict, healthbox: dict) -> None:
    trend = str(snapshot.get("tendencia") or "indefinida")
    status = str(snapshot.get("status_dado") or "indisponível")
    css = "incomplete" if status in {"incompleto", "erro", "indisponível"} else "up" if trend == "alta" else "down" if trend == "baixa" else "sideways"
    change = snapshot.get("variacao_diaria_percent")
    change_css = "up" if isinstance(change, (int, float)) and change > 0 else "down" if isinstance(change, (int, float)) and change < 0 else "flat"

    def value(field: str, suffix: str = "") -> str:
        raw = snapshot.get(field)
        return f"{raw:.2f}{suffix}" if isinstance(raw, (int, float)) else "indisponível"

    score = healthbox.get("score_result", {}).get("score")
    age = classify_data_age(snapshot.get("coleta"))
    missing = ", ".join(map(str, snapshot.get("campos_ausentes") or [])) or "nenhum"
    st.markdown(
        f'<div class="market-card {css}"><span class="ticker">{html.escape(str(snapshot.get("ativo", "—")))}</span><span class="status-badge status-neutral">{html.escape(status)}</span><div class="market-price">R$ {value("preco_atual")}</div><div class="market-change {change_css}">{value("variacao_diaria_percent", "%")} · tendência {html.escape(trend)}</div><div class="mini-grid"><div class="mini-box"><b>RSI</b><span>{value("rsi")}</span></div><div class="mini-box"><b>ATR</b><span>{value("atr_percent", "%")}</span></div><div class="mini-box"><b>rVol</b><span>{value("rvol", "x")}</span></div><div class="mini-box"><b>Healthbox</b><span>{html.escape(str(score if score is not None else "não calculado"))}</span></div><div class="mini-box"><b>Suporte</b><span>{value("suporte")}</span></div><div class="mini-box"><b>Resistência</b><span>{value("resistencia")}</span></div><div class="mini-box"><b>Dist. suporte</b><span>{value("distancia_suporte_percent", "%")}</span></div><div class="mini-box"><b>Dist. resistência</b><span>{value("distancia_resistencia_percent", "%")}</span></div></div><div class="market-meta">fonte: {html.escape(str(snapshot.get("fonte", "indisponível")))} · status: {html.escape(status)} · idade: {age}<br>coleta: {html.escape(str(snapshot.get("coleta") or "indisponível"))}<br>campos ausentes: {html.escape(missing)}</div></div>',
        unsafe_allow_html=True,
    )


def render_update_status_card(status: dict, summary: dict) -> None:
    updates = status.get("last_updates", {})
    latest = status.get("latest_update")
    if not latest:
        st.info("Nenhuma atualização registrada ainda.")
        return
    errors = latest.get("errors") or []
    if not latest.get("success") or latest.get("error_count", 0):
        general = "falha na fonte"
        css = "status-rejected"
    elif latest.get("incomplete_count", 0):
        general = "atualizado com dados parciais"
        css = "status-warning"
    else:
        general = "atualizado"
        css = "status-approved"
    age = str(status.get("snapshot_age_status", "indisponível"))
    error_html = (
        f'<p><b>Erro da fonte:</b> {html.escape(" | ".join(map(str, errors)))}</p>'
        if errors
        else ""
    )
    st.markdown(
        f'<div class="section-card"><div class="small-label">Status da Atualização</div>'
        f'<p><span class="status-badge {css}">{html.escape(general)}</span> '
        f'<span class="status-badge status-neutral">snapshot {html.escape(age)}</span></p>'
        f'<p><b>Última atualização:</b> {html.escape(str(latest.get("finished_at") or "indisponível"))}<br>'
        f'<b>Modo:</b> {html.escape(str(latest.get("mode") or "indisponível"))} · '
        f'<b>Origem:</b> {html.escape(str(latest.get("runner") or "indisponível"))} · '
        f'<b>Fonte:</b> {html.escape(str(latest.get("source") or summary.get("fonte", "indisponível")))}</p>'
        f'<p><b>Ativos consultados:</b> {latest.get("total_tickers", 0)} · '
        f'<b>Atualizados:</b> {latest.get("updated_count", 0)} · '
        f'<b>Incompletos:</b> {latest.get("incomplete_count", 0)} · '
        f'<b>Erros:</b> {latest.get("error_count", 0)}<br>'
        f'<b>Opportunity Engine:</b> {html.escape(str(latest.get("opportunity_engine_status", "MOCK / EXEMPLO")))}</p>'
        f'{error_html}</div>',
        unsafe_allow_html=True,
    )


def render_options_status_card(summary: dict) -> None:
    access = str(summary.get("access_status", "indisponível"))
    if summary.get("series_count", 0):
        label = "último snapshot salvo"
        css = "status-approved"
    elif access == "sem_acesso":
        label = "sem acesso"
        css = "status-rejected"
    else:
        label = "teste disponível"
        css = "status-neutral"
    st.markdown(
        f'<div class="section-card"><div class="small-label">Opções reais — teste EOD</div>'
        f'<p><span class="status-badge {css}">{html.escape(label)}</span></p>'
        f'<p><b>Integração:</b> não integrada ao Opportunity Engine · '
        f'<b>Fonte:</b> {html.escape(str(summary.get("fonte", "brapi_options")))} · '
        f'<b>Séries salvas:</b> {summary.get("series_count", 0)}<br>'
        f'<b>Status:</b> {html.escape(str(summary.get("status_dado", "indisponível")))} · '
        f'<b>Coleta:</b> {html.escape(str(summary.get("coleta") or "nenhuma"))}</p></div>',
        unsafe_allow_html=True,
    )


def render_options_eod_status_card(status: dict) -> None:
    last = status.get("last_update") or {}
    summary = status.get("snapshot_summary") or {}
    general = str(last.get("status") or summary.get("status") or "não atualizado")
    css = "status-approved" if general == "disponível" else "status-warning" if general == "parcial" else "status-rejected" if general == "erro" else "status-neutral"
    st.markdown(
        f'<div class="section-card"><div class="small-label">Status Opções EOD</div>'
        f'<p><span class="status-badge {css}">{html.escape(general)}</span></p>'
        f'<p><b>Última atualização:</b> {html.escape(str(last.get("finished_at") or summary.get("latest_collection") or "não atualizada"))}<br>'
        f'<b>Ativos disponíveis:</b> {last.get("available_count", summary.get("available_count", 0))} · '
        f'<b>Séries:</b> {last.get("total_series", summary.get("total_series", 0))} · '
        f'<b>Calls:</b> {last.get("total_calls", summary.get("total_calls", 0))} · '
        f'<b>Puts:</b> {last.get("total_puts", summary.get("total_puts", 0))} · '
        f'<b>Erros:</b> {last.get("error_count", summary.get("error_count", 0))}</p>'
        f'<p><b>Frequência:</b> EOD/fim de pregão · <b>Opportunity Engine:</b> MOCK / EXEMPLO</p></div>',
        unsafe_allow_html=True,
    )


def render_real_opportunity_card(item: dict) -> None:
    status = str(item.get("conditional_status", item.get("status", "inconclusivo")))
    css = "status-approved" if status == "entrada_condicional" else "status-warning" if status == "acompanhar_na_abertura" else "status-rejected" if status == "evitar" else "status-neutral"
    def shown(value: object) -> str:
        return html.escape(str(value if value is not None else "indisponível"))
    st.markdown(
        f'<div class="section-card"><div class="small-label">DADOS REAIS EOD / EXPERIMENTAL</div>'
        f'<h3>{shown(item.get("ativo"))} · {shown(item.get("estrategia"))}</h3>'
        f'<p><span class="status-badge {css}">{shown(status)}</span> '
        f'<span class="status-badge status-neutral">score {shown(item.get("score"))}</span></p>'
        f'<p><b>Decisão condicional:</b> {shown(item.get("conditional_decision"))}<br><b>Motivo:</b> {shown(item.get("motivo"))}</p>'
        f'<p><b>Vencimento:</b> {shown(item.get("vencimento"))} · '
        f'<b>Qualidade:</b> {shown(item.get("expiration_quality"))} ({shown(item.get("expiration_note"))}) · '
        f'<b>Strikes:</b> compra {shown(item.get("strike_comprado"))} / venda {shown(item.get("strike_vendido"))}<br>'
        f'<b>Base de preço:</b> {shown(item.get("price_basis"))} · {shown(item.get("aviso_preco"))}</p>'
        f'<p><b>Perda máxima:</b> {shown(item.get("perda_maxima"))} · '
        f'<b>Ganho máximo:</b> {shown(item.get("ganho_maximo"))} · '
        f'<b>Break-even:</b> {shown(item.get("break_even"))} · '
        f'<b>Risco/retorno:</b> {shown(item.get("risco_retorno"))}</p>'
        f'<p><b>Referência EOD:</b> {shown(item.get("entry_reference_price"))} · '
        f'<b>Débito máximo:</b> {shown(item.get("max_debit_allowed"))} · '
        f'<b>Faixa débito para acompanhar:</b> {shown(item.get("debit_watch_limit"))} · '
        f'<b>Crédito mínimo:</b> {shown(item.get("min_credit_required"))} · '
        f'<b>Faixa crédito para acompanhar:</b> {shown(item.get("credit_watch_limit"))}<br>'
        f'<b>Condição de preço:</b> {shown(item.get("entry_price_condition"))}<br>'
        f'<b>Aviso:</b> {shown(item.get("eod_warning"))}</p>'
        f'<p><b>Healthbox:</b> {shown(item.get("healthbox_status"))} ({shown(item.get("healthbox_score"))}) · '
        f'<b>Liquidez da candidata:</b> {shown(item.get("liquidez"))} · <b>Classe no universo:</b> {shown(item.get("liquidity_class"))}<br>'
        f'<b>Campos ausentes:</b> {shown(", ".join(map(str, item.get("campos_ausentes", []))) or "nenhum")}<br>'
        f'<b>Fonte:</b> {shown(item.get("fonte"))} · <b>Coleta:</b> {shown(item.get("coleta"))}</p>'
        f'<p><b>Confirmar:</b> {shown("; ".join(item.get("confirmation_rules", [])))}<br>'
        f'<b>Invalidar se:</b> {shown("; ".join(item.get("invalidation_rules", [])))}<br>'
        f'<b>Hard blockers:</b> {shown("; ".join(item.get("hard_blockers", [])) or "nenhum")}<br>'
        f'<b>Soft warnings:</b> {shown("; ".join(item.get("soft_warnings", [])) or "nenhum")}<br>'
        f'<b>O que precisa mudar:</b> {shown("; ".join(item.get("what_needs_to_change", [])))}</p></div>',
        unsafe_allow_html=True,
    )


def render_graphical_thesis_card(item: dict) -> None:
    def shown(value: object) -> str:
        return html.escape(str(value if value is not None else "indisponível"))
    status = str(item.get("status", "inconclusiva"))
    css = "status-approved" if status in {"compra_operavel", "venda_operavel"} else "status-warning" if status in {"interesse_compra", "interesse_venda", "neutra_observar"} else "status-rejected" if status == "evitar" else "status-neutral"
    bulk = item.get("bulkowski_usado") or {}
    strategies = item.get("top_3_strategies") or []
    alternatives = "; ".join(candidate.get("strategy_name", "") for candidate in strategies[1:3])
    validations = "; ".join(dict.fromkeys(
        validation for candidate in strategies[:3] for validation in candidate.get("validacoes_obrigatorias", [])
    ))
    rejected = "; ".join(
        f'{entry.get("strategy_name")}: {entry.get("reason")}'
        for entry in (item.get("rejected_strategies_summary") or [])[:3]
    )
    preferred_screening = strategies[0] if strategies else {}
    strategy_details = "".join(
        f'<p><b>{shown(candidate.get("strategy_name"))}</b> — {shown(candidate.get("explicacao_curta"))}<br>'
        f'<b>Pernas:</b> {shown("; ".join(candidate.get("pernas", [])))}<br>'
        f'<b>Quando usar:</b> {shown(candidate.get("quando_usar"))}<br>'
        f'<b>Principal risco:</b> {shown(candidate.get("principal_risco"))}<br>'
        f'<b>Por que classificada:</b> {shown("; ".join(candidate.get("motivos_favoraveis", []) + candidate.get("motivos_contra", [])))}<br>'
        f'<b>Validar:</b> {shown("; ".join(candidate.get("validacoes_obrigatorias", [])))}</p>'
        for candidate in strategies
    )
    manual_plans = "".join(
        f'<p><b>Como validar no book — {shown(candidate.get("strategy_name"))}</b><br>'
        f'<b>Delta-alvo:</b> {shown((candidate.get("manual_validation_plan") or {}).get("delta_target"))}<br>'
        f'<b>Região de strike:</b> {shown((candidate.get("manual_validation_plan") or {}).get("strike_region"))}<br>'
        f'<b>Vencimento:</b> {shown((candidate.get("manual_validation_plan") or {}).get("expiration_window"))}<br>'
        f'<b>Débito máximo:</b> {shown((candidate.get("manual_validation_plan") or {}).get("max_debit_allowed"))} · '
        f'<b>Crédito mínimo:</b> {shown((candidate.get("manual_validation_plan") or {}).get("min_credit_required"))}<br>'
        f'<b>Pernas:</b> {shown("; ".join((candidate.get("manual_validation_plan") or {}).get("structure_legs_description", [])))}<br>'
        f'<b>Checklist:</b> {shown("; ".join((candidate.get("manual_validation_plan") or {}).get("book_checklist", [])))}<br>'
        f'<b>Rejeitar se:</b> {shown("; ".join((candidate.get("manual_validation_plan") or {}).get("rejection_rules", [])))}</p>'
        for candidate in strategies
    )
    regime_label = "Lateral — estudar estratégia de range" if item.get("market_regime") == "lateral" else item.get("market_regime")
    st.markdown(
        f'<div class="section-card"><div class="small-label">TESE GRÁFICA · NÃO É ORDEM</div>'
        f'<h3>{shown(item.get("ativo"))} · {shown(item.get("direcao_tese"))}</h3>'
        f'<p><span class="status-badge {css}">{shown(status)}</span></p>'
        f'<p><b>Preço:</b> {shown(item.get("preco_atual"))}<br><b>Gatilho:</b> {shown(item.get("gatilho_confirmacao"))} · '
        f'<b>Distância até gatilho:</b> {shown(item.get("distancia_ate_gatilho"))}</p>'
        f'<p><b>Região:</b> {shown(item.get("regiao_entrada_grafica"))}<br>'
        f'<b>Invalidação:</b> {shown(item.get("invalidacao"))} · <b>Alvo:</b> {shown(item.get("alvo"))} · <b>Alvo/risco:</b> {shown(item.get("relacao_alvo_risco"))}</p>'
        f'<p><b>Motivo:</b> {shown(item.get("motivo_status"))}</p>'
        f'<p><b>Blockers:</b> {shown("; ".join(item.get("hard_technical_blockers", [])) or "nenhum")}<br>'
        f'<b>Warnings:</b> {shown("; ".join(item.get("soft_technical_warnings", [])) or "nenhum")}<br>'
        f'<b>Near setup score:</b> {shown(item.get("near_setup_score"))}<br>'
        f'<b>Precisa acontecer:</b> {shown("; ".join(item.get("what_needs_to_happen", [])) or "nenhuma confirmação adicional calculada")}</p>'
        f'<p><b>Healthbox:</b> score {shown(item.get("healthbox_score"))} · <b>Bulkowski:</b> {shown(bulk.get("nome_padrao"))} / {shown(item.get("bulkowski_status"))}</p>'
        f'<p><b>Regime:</b> {shown(regime_label)} · <b>Família:</b> {shown(item.get("preferred_strategy_family"))}<br>'
        f'<b>Estratégia preferida:</b> {shown(item.get("preferred_strategy"))}<br>'
        f'<b>Top 3 candidatas:</b> {shown("; ".join(candidate.get("strategy_name", "") for candidate in strategies) or "nenhuma")}<br>'
        f'<b>Alternativas:</b> {shown(alternatives or "nenhuma")}<br>'
        f'<b>Rejeitadas:</b> {shown(rejected or "nenhuma") }<br>'
        f'<b>Status da estratégia:</b> {shown(item.get("strategy_status"))}<br>'
        f'<b>Validações necessárias:</b> {shown(validations or "dados gráficos completos")}</p>'
        f'{strategy_details}'
        f'{manual_plans}'
        f'<p><b>Delta-alvo:</b> {shown(preferred_screening.get("delta_alvo"))}<br>'
        f'<b>Vencimento:</b> {shown(preferred_screening.get("vencimento_ideal"))}<br><b>Cadeia:</b> {shown(item.get("cadeia_opcoes_status"))}</p>'
        f'<p><b>Aviso:</b> {shown(item.get("strategy_warning") or item.get("aviso"))}</p></div>',
        unsafe_allow_html=True,
    )


def render_practical_strategy_card(item: dict) -> None:
    def shown(value: object) -> str:
        return html.escape(str(value if value is not None else "indisponível"))
    best = item.get("best_strategy") or {}
    top = item.get("top_3_strategies") or []
    action = item.get("practical_action") or "inconclusivo"
    regime = "Lateralidade detectada" if item.get("market_regime") == "lateral" else item.get("market_regime")
    chain = item.get("cadeia_opcoes_status")
    chain_alert = "cadeia disponível; ainda validar preço, spread, liquidez e perda máxima" if chain == "disponivel_fonte" else "cadeia não validada; procurar e conferir manualmente no book"
    rejection_rules = [
        rule for rule in best.get("rejection_rules", [])
        if any(term in rule.lower() for term in ("spread", "liquidez", "suporte", "resistência"))
    ][:2]
    limit_text = (
        f'débito máximo {best.get("max_debit_allowed")}'
        if best.get("max_debit_allowed") is not None else
        f'crédito mínimo {best.get("min_credit_required")}'
        if best.get("min_credit_required") is not None else
        "limite monetário indisponível sem estrutura real"
    )
    st.markdown(
        f'<div class="section-card"><div class="small-label">ESTRATÉGIA PRÁTICA · NÃO É ORDEM</div>'
        f'<h3>{shown(item.get("ativo"))} · {shown(regime)}</h3>'
        f'<p><b>Objetivo:</b> {shown(best.get("objective_label") or item.get("practical_objective_label"))}<br>'
        f'{shown(best.get("objective_description") or item.get("practical_objective_description"))}<br>'
        f'<b>Alerta do objetivo:</b> {shown(best.get("objective_warning") or item.get("practical_objective_warning"))}</p>'
        f'<p><b>Status da tese:</b> {shown(item.get("status"))} · <b>Near setup score:</b> {shown(item.get("near_setup_score"))} · '
        f'<b>Ação:</b> {shown(action)}</p>'
        f'<p><b>Melhor estratégia:</b> {shown(best.get("strategy_name"))} · score {shown(best.get("score"))}<br>'
        f'<b>Motivo:</b> {shown(best.get("reason"))}<br>'
        f'<b>Top 3:</b> {shown("; ".join(candidate.get("strategy_name", "") for candidate in top) or "nenhuma")}</p>'
        f'<p><b>Capital técnico mínimo:</b> {shown(best.get("minimum_technical_capital"))}<br>'
        f'<b>Capital recomendado:</b> {shown(best.get("recommended_capital"))}<br>'
        f'<b>Perda máxima estimada:</b> {shown(best.get("max_loss_estimate"))}<br>'
        f'<b>Encaixe no capital:</b> {shown(best.get("capital_fit_status"))}<br>'
        f'<b>Motivo:</b> {shown(best.get("capital_fit_reason"))}<br>'
        f'<b>Dados ausentes:</b> {shown("; ".join(best.get("missing_capital_fields", [])) or "nenhum")}</p>'
        f'<p><b>Como validar no book</b><br>'
        f'<b>Delta-alvo:</b> {shown(best.get("delta_target"))}<br>'
        f'<b>Strike/região:</b> {shown(best.get("strike_region"))}<br>'
        f'<b>Vencimento:</b> {shown(best.get("expiration_window"))}<br>'
        f'<b>Preço:</b> {shown(limit_text)}<br>'
        f'<b>Olhar:</b> {shown("; ".join(best.get("book_checklist", [])[:4]))}<br>'
        f'<b>Rejeitar:</b> {shown("; ".join(rejection_rules) or "spread ou liquidez ruins; perda dos níveis gráficos")}</p>'
        f'<p><b>Gatilho:</b> {shown(item.get("gatilho_confirmacao"))} · <b>Invalidação:</b> {shown(item.get("invalidacao"))}<br>'
        f'<b>Cadeia:</b> {shown(chain_alert)}</p>'
        f'<p><b>Aviso:</b> {shown(best.get("warning") or item.get("strategy_warning"))}<br>'
        f'{shown(best.get("capital_warning"))}<br>Não operar se a perda máxima for desconfortável.</p></div>',
        unsafe_allow_html=True,
    )


def render_full_strategy_screening(item: dict) -> None:
    with st.expander(f"Ver screening completo · {item.get('ativo')}", expanded=False):
        rows = []
        for candidate in item.get("strategy_screening", []):
            plan = candidate.get("manual_validation_plan") or {}
            rows.append({
                "Estratégia": candidate.get("strategy_name"),
                "Score": candidate.get("suitability_score"),
                "Status": candidate.get("status"),
                "Objetivo": candidate.get("objective_label"),
                "Complexidade": candidate.get("complexidade"),
                "Risco definido": candidate.get("risco_definido"),
                "Motivos favoráveis": "; ".join(candidate.get("motivos_favoraveis", [])),
                "Motivos contra": "; ".join(candidate.get("motivos_contra", [])),
                "Dados necessários": "; ".join(candidate.get("dados_necessarios", [])),
                "Delta-alvo": plan.get("delta_target"),
                "Região de strike": plan.get("strike_region"),
                "Vencimento": plan.get("expiration_window"),
                "Capital mínimo": candidate.get("minimum_technical_capital"),
                "Capital recomendado": candidate.get("recommended_capital"),
                "Perda máxima": candidate.get("max_loss_estimate"),
                "Encaixe capital": candidate.get("capital_fit_status"),
                "Motivo capital": candidate.get("capital_fit_reason"),
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(f"Rejeitadas/não aplicáveis: {item.get('rejected_count', 0)}. Dados completos preservados no snapshot.")


def render_daily_priority_item(item: dict) -> None:
    def shown(value: object) -> str:
        return html.escape(str(value if value is not None else "indisponível"))
    st.markdown(
        f'<div class="section-card"><div class="small-label">PRIORIDADE DIÁRIA · NÃO É ORDEM</div>'
        f'<h3>{shown(item.get("ativo"))} · {shown(item.get("strategy_name"))}</h3>'
        f'<p><b>Objetivo:</b> {shown(item.get("objective_label"))} · <b>Regime:</b> {shown(item.get("regime"))} · '
        f'<b>Score:</b> {shown(item.get("suitability_score"))}<br>'
        f'<b>Delta-alvo:</b> {shown(item.get("delta_target"))}<br>'
        f'<b>Região de strike:</b> {shown(item.get("strike_region"))}<br>'
        f'<b>Vencimento:</b> {shown(item.get("expiration_window"))}</p>'
        f'<p><b>Capital mínimo:</b> {shown(item.get("minimum_technical_capital"))} · '
        f'<b>Recomendado:</b> {shown(item.get("recommended_capital"))}<br>'
        f'<b>Perda máxima:</b> {shown(item.get("max_loss_estimate"))} · '
        f'<b>Encaixe:</b> {shown(item.get("capital_fit_status"))}<br>'
        f'{shown(item.get("capital_fit_reason"))}</p>'
        f'<p><b>Gatilho:</b> {shown(item.get("gatilho"))} · <b>Invalidação:</b> {shown(item.get("invalidacao"))}<br>'
        f'<b>Ação prática:</b> {shown(item.get("practical_action"))}</p>'
        f'<p><b>Aviso:</b> {shown(item.get("objective_warning"))}<br>'
        f'{shown(item.get("capital_warning"))}<br>Não operar se a perda máxima for desconfortável.</p></div>',
        unsafe_allow_html=True,
    )


def render_daily_priority_plan(item: dict, key: str) -> None:
    plan = item.get("manual_validation_plan") or {}
    with st.expander("Ver plano manual", expanded=False):
        st.write({
            "delta_alvo": plan.get("delta_target"),
            "regiao_strike": plan.get("strike_region"),
            "vencimento": plan.get("expiration_window"),
            "debito_maximo": plan.get("max_debit_allowed"),
            "credito_minimo": plan.get("min_credit_required"),
            "checklist_book": plan.get("book_checklist", []),
            "rejeitar_se": plan.get("rejection_rules", []),
            "aviso": plan.get("warning"),
        })


def render_manual_simulation(simulation: dict) -> None:
    def shown(value: object) -> str:
        return html.escape(str(value if value is not None else "indisponível"))
    break_evens = "; ".join(str(value) for value in simulation.get("break_even_points", [])) or "indisponível"
    st.markdown(
        f'<div class="section-card"><div class="small-label">SIMULAÇÃO MANUAL · NÃO É ORDEM</div>'
        f'<h3>{shown(simulation.get("ticker"))} · {shown(simulation.get("strategy_name"))}</h3>'
        f'<p><b>Fonte:</b> {shown(simulation.get("source"))} · <b>Vencimento:</b> {shown(simulation.get("expiration"))}<br>'
        f'<b>Quantidade:</b> {shown(simulation.get("quantity"))} · <b>Multiplicador:</b> {shown(simulation.get("contract_multiplier"))}</p>'
        f'<p><b>Capital mínimo:</b> {shown(simulation.get("capital_required"))}<br>'
        f'<b>Capital recomendado:</b> {shown(simulation.get("recommended_capital"))}<br>'
        f'<b>Perda máxima:</b> {shown(simulation.get("max_loss"))} · <b>Ganho máximo:</b> {shown(simulation.get("max_gain"))}<br>'
        f'<b>Break-even:</b> {shown(break_evens)}<br>'
        f'<b>Débito líquido:</b> {shown(simulation.get("net_debit"))} · <b>Crédito líquido:</b> {shown(simulation.get("net_credit"))}<br>'
        f'<b>Risco/retorno:</b> {shown(simulation.get("risk_reward_ratio"))} · <b>Crédito/largura:</b> {shown(simulation.get("credit_to_width"))}</p>'
        f'<p><b>Encaixe:</b> {shown(simulation.get("capital_fit_status"))}<br>{shown(simulation.get("capital_fit_reason"))}<br>'
        f'<b>Campos ausentes:</b> {shown("; ".join(simulation.get("missing_fields", [])) or "nenhum")}</p>'
        f'<p><b>Aviso:</b> {shown(simulation.get("warning"))}</p></div>',
        unsafe_allow_html=True,
    )


def render_graphical_watchlist_card(item: dict) -> None:
    def shown(value: object) -> str:
        return html.escape(str(value if value is not None else "indisponível"))
    status = str(item.get("status_atual", "inconclusiva por falta de dados"))
    css = "status-approved" if status == "gatilho acionado" else "status-warning" if status in {"aguardando gatilho", "perto do gatilho"} else "status-rejected" if status == "invalidada" else "status-neutral"
    st.markdown(
        f'<div class="section-card"><div class="small-label">TESE GRÁFICA SALVA · NÃO É ORDEM</div>'
        f'<h3>{shown(item.get("ativo"))} · {shown(item.get("direcao_provavel"))}</h3>'
        f'<p><span class="status-badge {css}">{shown(status)}</span> · <b>Score:</b> {shown(item.get("near_setup_score"))}</p>'
        f'<p><b>Preço de referência:</b> {shown(item.get("preco_referencia"))}<br>'
        f'<b>Gatilho:</b> {shown(item.get("gatilho_confirmacao"))}<br>'
        f'<b>Invalidação:</b> {shown(item.get("invalidacao"))} · <b>Alvo:</b> {shown(item.get("alvo"))} · '
        f'<b>Alvo/risco:</b> {shown(item.get("relacao_alvo_risco"))}</p>'
        f'<p><b>Precisa acontecer:</b> {shown("; ".join(item.get("what_needs_to_happen", [])) or "nenhuma confirmação adicional calculada")}<br>'
        f'<b>Estrutura sugerida:</b> {shown(item.get("estrutura_opcao_sugerida"))}<br>'
        f'<b>Delta-alvo:</b> {shown(item.get("delta_alvo"))} · <b>Cadeia:</b> {shown(item.get("cadeia_opcoes_status"))}</p>'
        f'<p><b>Avaliação:</b> {shown(item.get("evaluation_reason"))}<br><b>Aviso:</b> {shown(item.get("aviso"))}</p></div>',
        unsafe_allow_html=True,
    )


def render_top_conditional_entries(entries: list[dict], diagnostics: dict | None = None) -> None:
    st.markdown("## Top Entradas Condicionais EOD")
    conditional = [item for item in entries if item.get("conditional_status") == "entrada_condicional"]
    observable = [item for item in entries if item.get("conditional_status") == "acompanhar_na_abertura"]
    if not conditional:
        st.info("Nenhuma entrada condicional passou nos filtros hoje.")
    if not conditional and not observable:
        st.warning("Nenhuma estrutura real EOD está em condição aceitável hoje.")
    reasons = (diagnostics or {}).get("rejection_reasons", {})
    if reasons:
        principal = next(iter(reasons.items()))
        st.caption(f"Principal motivo agregado: {principal[0]} ({principal[1]})")
    hard = (diagnostics or {}).get("hard_blockers", {})
    soft = (diagnostics or {}).get("soft_warnings", {})
    if hard:
        principal_hard = next(iter(hard.items()))
        st.caption(f"Principal hard blocker: {principal_hard[0]} ({principal_hard[1]})")
    if soft:
        principal_soft = next(iter(soft.items()))
        st.caption(f"Principal soft warning: {principal_soft[0]} ({principal_soft[1]})")
    near_misses = (diagnostics or {}).get("near_misses", [])[:5]
    if near_misses:
        st.markdown("**Quase entradas para observar:**")
        for item in near_misses:
            st.caption(f"{item.get('ativo')} · {item.get('estrategia')} · {item.get('vencimento')} — {item.get('motivo_principal')}")
    for item in entries[:5]:
        st.markdown(
            f"**{html.escape(str(item.get('ativo', '—')))} · {html.escape(str(item.get('estrategia', 'indisponível')))}** — "
            f"`{html.escape(str(item.get('conditional_status', 'inconclusivo')))}` · score {html.escape(str(item.get('score') if item.get('score') is not None else 'indisponível'))}"
        )


def render_real_engine_status_card(options_snapshots: dict, last_summary: dict | None = None) -> None:
    petr = options_snapshots.get("PETR4", {})
    unavailable = [
        symbol for symbol, snapshot in options_snapshots.items()
        if not snapshot.get("success") or not snapshot.get("series")
    ]
    summary = last_summary or {}
    status = "gerado" if summary else "aguardando geração"
    st.markdown(
        f'<div class="section-card"><div class="small-label">Oportunidades Reais EOD</div>'
        f'<p><span class="status-badge status-neutral">{html.escape(status)}</span></p>'
        f'<p><b>PETR4 com opções:</b> {"sim" if petr.get("success") and petr.get("series") else "não"} · '
        f'<b>Ativos sem acesso/dados:</b> {html.escape(", ".join(unavailable) or "nenhum")}<br>'
        f'<b>Candidatas na última geração:</b> {summary.get("candidates", 0)} · '
        f'<b>Estudar:</b> {summary.get("estudar", 0)} · <b>Atenção:</b> {summary.get("atenção", 0)} · '
        f'<b>Evitar:</b> {summary.get("evitar", 0)} · <b>Inconclusivas:</b> {summary.get("inconclusivo", 0)}</p>'
        f'<p>Real experimental ainda não substitui o motor MOCK / EXEMPLO.</p></div>',
        unsafe_allow_html=True,
    )


def opportunity_card(item: dict) -> str | None:
    calculation = item.get("calculation", {})
    score_result = item.get("score_result", {})
    bulkowski = item.get("bulkowski_analysis", {})
    healthbox = item.get("healthbox", {})
    healthbox_score_result = item.get("healthbox_score_result", {})
    score_label = score_result.get("score")
    score_label = score_label if score_label is not None else "—"
    status = str(item.get("status", "score não calculado"))
    status_css = "approved" if status == "aprovada" else "warning" if status == "atenção" else "rejected" if status == "reprovada" else "neutral"
    details = [
        ("Vencimento", f"{item['vencimento_dias']} dias"),
        ("Strike comprado", item["strike_comprado"]),
        ("Strike vendido", item["strike_vendido"]),
        ("Prêmio líquido", item["premio_liquido"]),
        ("Perda máxima", item["perda_maxima"]),
        ("Ganho máximo", item["ganho_maximo"]),
        ("Break-even", item["break_even"]),
        ("Delta", item["delta"]),
        ("Theta", item["theta"]),
        ("Status", item["status"]),
    ]
    rows = "".join(
        f'<div class="detail"><span>{html.escape(str(label))}</span><span>{html.escape(str(value))}</span></div>'
        for label, value in details
    )
    st.markdown(
        f'<div class="opportunity-card {status_css}"><span class="ticker">{html.escape(item["ativo"])}</span><span class="score">{score_label}</span><br><span class="pill">{html.escape(item["estrategia"])}</span> <span class="status-badge status-{"approved" if status_css == "approved" else "warning" if status_css == "warning" else "rejected" if status_css == "rejected" else "neutral"}">{html.escape(status)}</span><p class="muted">{html.escape(item["tese"])}</p>{rows}<div class="mini-grid"><div class="mini-box"><b>Healthbox</b><span>{html.escape(item.get("healthbox_confirmation", "inconclusivo"))}</span></div><div class="mini-box"><b>Bulkowski</b><span>{html.escape(bulkowski.get("confirmacao", "indisponível"))}</span></div><div class="mini-box"><b>Liquidez</b><span>{html.escape(str(item.get("liquidez_status", "indisponível")))}</span></div><div class="mini-box"><b>Decisão</b><span>{html.escape(str(item.get("decisao", "esperar")))}</span></div></div><p><span class="mock-badge">MOCK / EXEMPLO</span></p></div>',
        unsafe_allow_html=True,
    )
    detail, enter, skip, watch = st.columns(4)
    if detail.button("Ver detalhe", key=f"detail-{item['id']}"):
        return "detail"
    if enter.button("Entrei nessa posição", key=f"enter-{item['id']}"):
        return "enter"
    if skip.button("Não entrei", key=f"skip-{item['id']}"):
        return "skip"
    if watch.button("Acompanhar", key=f"watch-{item['id']}"):
        return "watch"
    return None


def positions_table(positions: list[dict]) -> None:
    rows = [
        {
            "Ativo": p.get("ativo"),
            "Origem": "Abertura" if p.get("origem") == "opening_watchlist" else "MOCK / EXEMPLO",
            "Estratégia": p.get("estrategia"),
            "Preço real de entrada": p.get("preco_real_entrada"),
            "Preço EOD de referência": p.get("preco_eod_referencia"),
            "Quantidade": p.get("quantidade"),
            "Data de entrada": p.get("data_entrada"),
            "Vencimento": f"{p.get('vencimento_dias')} dias",
            "Ganho máximo": p.get("ganho_maximo"),
            "Perda máxima": p.get("perda_maxima"),
            "Break-even": p.get("break_even"),
            "Status": p.get("status"),
            "Tipo do dado": p.get("tipo_dado"),
        }
        for p in positions
    ]
    st.dataframe(pd.DataFrame(rows).astype(str), width="stretch", hide_index=True)


def sources_table(sources: list[dict]) -> None:
    st.dataframe(pd.DataFrame(sources), width="stretch", hide_index=True)


def alerts_section(alerts: list[dict]) -> None:
    for alert in alerts:
        getattr(st, alert["nivel"])(
            f"**{alert['titulo']}:** {alert['mensagem']} — MOCK / EXEMPLO"
        )


# Compatibilidade com chamadas existentes e API visual premium.
mock_badge = render_mock_badge
metric_card = render_metric_card
render_opportunity_card = opportunity_card
