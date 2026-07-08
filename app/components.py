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
        :root{
          --bg:#f4f0e8;
          --panel:#fffaf2;
          --panel-2:#f8f3ea;
          --line:#d7cfc2;
          --text:#1b1c18;
          --muted:#6b6b63;
          --green:#2f8f5b;
          --yellow:#d6a125;
          --blue:#2f78c4;
          --red:#c24d47;
          --gray:#7d858e;
        }
        #MainMenu,footer,[data-testid="stHeader"]{visibility:hidden}
        .stApp{
          background:
            radial-gradient(circle at 0% 0%, #efe5d1 0, transparent 26%),
            radial-gradient(circle at 100% 0%, #dce8dd 0, transparent 24%),
            linear-gradient(180deg,#f5efe4 0%,#f1ece3 100%);
          color:var(--text);
        }
        .block-container{padding-top:1.35rem;padding-bottom:3rem;max-width:1380px}
        h1,h2,h3{font-weight:800!important;color:var(--text)}
        h1{letter-spacing:-0.04em}
        .stCaption,.muted-copy{color:var(--muted)!important}
        [data-testid="stSidebar"]{
          background:linear-gradient(180deg,#efe4d0 0%,#efe9df 100%);
          border-right:1px solid var(--line);
        }
        [data-testid="stSidebar"] .block-container{padding-top:1.2rem}
        div.stButton>button{
          border-radius:12px;
          width:100%;
          min-height:2.5rem;
          border:1px solid #c9bfaf;
          background:#fff8ef;
          color:var(--text);
          font-weight:700;
        }
        div.stButton>button:hover{
          border-color:#8ca584;
          background:#f9f3e8;
        }
        [data-testid="stDataFrame"]{
          border:1px solid var(--line);
          border-radius:16px;
          overflow:hidden;
          background:var(--panel);
        }
        [data-testid="stExpander"]{
          border:1px solid var(--line);
          border-radius:14px;
          background:rgba(255,250,242,.75);
        }
        [data-testid="stForm"]{
          border:1px solid var(--line);
          border-radius:16px;
          background:rgba(255,250,242,.88);
          padding:1rem;
        }
        [data-baseweb="select"]>div,[data-baseweb="input"]>div{
          background:#fffaf2!important;
          border-color:#cfc3b0!important;
        }
        .eyebrow,.small-label{
          color:#7f735f;
          font-size:.72rem;
          font-weight:800;
          letter-spacing:.13em;
          text-transform:uppercase;
        }
        .mock-badge,.status-badge,.mini-badge{
          display:inline-flex;
          align-items:center;
          gap:.3rem;
          padding:.32rem .7rem;
          border-radius:999px;
          font-size:.72rem;
          font-weight:800;
          letter-spacing:.04em;
          text-transform:uppercase;
          border:1px solid transparent;
        }
        .mock-badge{background:#e7decb;color:#6f664f;border-color:#d2c6b0}
        .status-approved{background:#e5f3ea;color:var(--green);border-color:#b7d6c4}
        .status-warning{background:#fff4d6;color:#9a6d00;border-color:#edd39b}
        .status-info{background:#e5f0fb;color:var(--blue);border-color:#bfd3ec}
        .status-rejected{background:#fae5e2;color:var(--red);border-color:#e4beb9}
        .status-neutral{background:#eceff2;color:#616972;border-color:#d1d7dd}
        .sidebar-note,.section-card,.notice-banner,.decision-card,.metric-card,.strip-card{
          border:1px solid var(--line);
          border-radius:18px;
          background:rgba(255,250,242,.88);
          box-shadow:0 10px 30px rgba(92,82,58,.08);
        }
        .sidebar-note,.section-card,.strip-card{padding:1rem 1.1rem}
        .notice-banner{
          padding:.95rem 1rem;
          background:linear-gradient(90deg,#fff8ea 0%,#f3efe8 100%);
        }
        .section-title{
          display:flex;
          align-items:flex-end;
          justify-content:space-between;
          gap:1rem;
          margin:1.4rem 0 .8rem;
        }
        .section-title h2{margin:0!important}
        .section-title p{margin:0;color:var(--muted)}
        .metric-card{
          padding:1rem 1.05rem;
          min-height:112px;
          position:relative;
          overflow:hidden;
        }
        .metric-card:before{
          content:"";
          position:absolute;
          left:0;top:0;bottom:0;width:5px;
          background:var(--gray);
        }
        .metric-card.approved:before{background:var(--green)}
        .metric-card.warning:before{background:var(--yellow)}
        .metric-card.rejected:before{background:var(--red)}
        .metric-card.teal:before,.metric-card.info:before{background:var(--blue)}
        .metric-card .value{font-size:2rem;font-weight:850;line-height:1.05}
        .metric-card .label{font-size:.88rem;color:#373730;margin-top:.35rem}
        .metric-card .subtitle{font-size:.74rem;color:var(--muted);margin-top:.42rem}
        .decision-card{padding:1rem 1.05rem;margin:.65rem 0}
        .decision-card .top{
          display:flex;
          justify-content:space-between;
          gap:.8rem;
          align-items:flex-start;
          margin-bottom:.75rem;
        }
        .decision-card .asset{font-size:1.38rem;font-weight:850;letter-spacing:-.03em}
        .decision-card .summary{
          color:var(--muted);
          font-size:.9rem;
          margin:.45rem 0 .7rem;
        }
        .decision-grid{
          display:grid;
          grid-template-columns:repeat(3,minmax(0,1fr));
          gap:.55rem;
          margin:.65rem 0 .85rem;
        }
        .mini-panel{
          padding:.62rem .68rem;
          border-radius:12px;
          background:#f8f2e8;
          border:1px solid #dfd4c4;
        }
        .mini-panel b{
          display:block;
          font-size:.67rem;
          color:var(--muted);
          text-transform:uppercase;
          letter-spacing:.08em;
          margin-bottom:.18rem;
        }
        .mini-panel span{font-size:.82rem;font-weight:700}
        .compact-row{
          display:grid;
          grid-template-columns:repeat(2,minmax(0,1fr));
          gap:.55rem;
          margin:.5rem 0;
        }
        .compact-line{
          padding:.5rem .62rem;
          border-radius:11px;
          background:#fbf6ee;
          border:1px solid #e0d7c8;
          font-size:.82rem;
        }
        .compact-line b{
          display:block;
          color:var(--muted);
          font-size:.67rem;
          text-transform:uppercase;
          letter-spacing:.08em;
        }
        .detail-list{
          display:grid;
          grid-template-columns:repeat(2,minmax(0,1fr));
          gap:.5rem;
        }
        .detail-box{
          background:#fbf6ee;
          border:1px solid #e0d7c8;
          border-radius:12px;
          padding:.7rem .75rem;
        }
        .detail-box b{
          display:block;
          margin-bottom:.2rem;
          color:#3f433b;
          font-size:.78rem;
        }
        .strip-grid{
          display:grid;
          grid-template-columns:repeat(4,minmax(0,1fr));
          gap:.7rem;
        }
        .strip-label{font-size:.68rem;color:var(--muted);text-transform:uppercase;font-weight:800;letter-spacing:.08em}
        .strip-value{font-size:.92rem;font-weight:750;color:var(--text);margin-top:.15rem}
        .alert-card{
          border:1px solid var(--line);
          border-radius:14px;
          padding:.85rem 1rem;
          margin:.45rem 0;
          background:#fffaf2;
        }
        .alert-card.red{border-left:4px solid var(--red)}
        .alert-card.yellow{border-left:4px solid var(--yellow)}
        .alert-card.green{border-left:4px solid var(--green)}
        .alert-card.gray{border-left:4px solid var(--gray)}
        @media(max-width:920px){
          .decision-grid,.strip-grid,.detail-list,.compact-row{grid-template-columns:1fr}
          .block-container{padding-left:1rem;padding-right:1rem}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _escape(value: object, fallback: str = "indisponível") -> str:
    if value is None or value == "":
        return fallback
    return html.escape(str(value))


def _status_css(status: str) -> str:
    normalized = str(status or "").lower()
    if normalized in {
        "aprovada",
        "validado",
        "validada",
        "ok",
        "entrada_condicional",
        "compra_operavel",
        "venda_operavel",
        "gatilho acionado",
        "realizar parcial",
        "realizar total",
        "manter",
    }:
        return "status-approved"
    if normalized in {
        "atenção",
        "acompanhar",
        "acompanhar_na_abertura",
        "aguardar_gatilho",
        "aguardando gatilho",
        "perto do gatilho",
        "vencimento próximo",
        "interesse_compra",
        "interesse_venda",
        "neutra_observar",
        "parcial",
        "atualizado com dados parciais",
    }:
        return "status-warning"
    if normalized in {"estudo", "informação", "info", "gerado"}:
        return "status-info"
    if normalized in {
        "reprovada",
        "evitar",
        "evitar_por_enquanto",
        "invalidada",
        "tese invalidada",
        "sair agora",
        "falha na fonte",
        "erro",
    }:
        return "status-rejected"
    return "status-neutral"


def render_mock_badge(text: str = "DADOS MOCK / EXEMPLO") -> None:
    st.markdown(f'<span class="mock-badge">{_escape(text)}</span>', unsafe_allow_html=True)


def render_metric_card(value: str | int, label: str, subtitle: str = "Leitura protegida", status: str = "neutral") -> None:
    st.markdown(
        f'<div class="metric-card {html.escape(status)}">'
        f'<div class="value">{_escape(value, "0")}</div>'
        f'<div class="label">{_escape(label)}</div>'
        f'<div class="subtitle">{_escape(subtitle)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> None:
    st.markdown(
        f'<span class="status-badge {_status_css(status)}">{_escape(status)}</span>',
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-title"><h2>{_escape(title)}</h2><p>{_escape(subtitle, "")}</p></div>',
        unsafe_allow_html=True,
    )


def render_data_notice(text: str) -> None:
    st.markdown(f'<div class="notice-banner">⚠ {_escape(text)}</div>', unsafe_allow_html=True)


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
        ("Última atualização", latest.get("finished_at") or "indisponível"),
        ("Ativos atualizados", latest.get("updated_count", summary.get("completos", 0))),
        ("Incompletos / erros", f'{latest.get("incomplete_count", summary.get("incompletos", 0))} / {latest.get("error_count", summary.get("erros", 0))}'),
    ]
    body = "".join(
        f'<div><div class="strip-label">{_escape(label)}</div><div class="strip-value">{_escape(value)}</div></div>'
        for label, value in strip
    )
    st.markdown(f'<div class="strip-card"><div class="strip-grid">{body}</div></div>', unsafe_allow_html=True)


def render_action_summary(summary: dict) -> None:
    metrics = [
        (summary.get("validated", 0), "Oportunidades validadas", "approved"),
        (summary.get("near_entries", 0), "Quase entradas", "warning"),
        (summary.get("watching", 0), "Em acompanhamento", "info"),
        (summary.get("avoid", 0), "Para evitar", "rejected"),
        (summary.get("inconclusive", 0), "Inconclusivo", "neutral"),
        (summary.get("top_asset", "nenhum"), "Olhar primeiro", "teal"),
    ]
    columns = st.columns(6)
    for column, (value, label, status) in zip(columns, metrics):
        with column:
            render_metric_card(value, label, "Painel de decisão", status)


def _detail_box(label: str, value: object) -> str:
    return f'<div class="detail-box"><b>{_escape(label)}</b><span>{_escape(value)}</span></div>'


def _line_box(label: str, value: object) -> str:
    return f'<div class="compact-line"><b>{_escape(label)}</b><span>{_escape(value)}</span></div>'


def render_decision_card(item: dict) -> str | None:
    card_key = str(item.get("card_key") or item.get("id") or item.get("ativo") or "item")
    status = str(item.get("action_status") or item.get("practical_action") or item.get("conditional_status") or item.get("status") or "inconclusivo")
    badges = (
        f'<span class="status-badge {_status_css(status)}">{_escape(status)}</span> '
        f'<span class="status-badge status-neutral">NÃO É ORDEM</span>'
    )
    headline = _escape(item.get("action_label") or item.get("acao_pratica") or item.get("conditional_decision") or "acompanhar")
    strategy = _escape(item.get("strategy_name") or item.get("estrategia") or item.get("preferred_strategy") or "indisponível")
    score = _escape(item.get("score") or item.get("near_setup_score") or (item.get("best_strategy") or {}).get("score") or "indisponível")
    reason = _escape(item.get("reason") or item.get("motivo") or item.get("evaluation_reason") or "indisponível")
    body = (
        f'<div class="decision-card"><div class="top"><div><div class="small-label">{_escape(item.get("source_label", "PAINEL DE DECISÃO"))}</div>'
        f'<div class="asset">{_escape(item.get("ativo"))}</div></div><div>{badges}</div></div>'
        f'<div class="summary"><b>{headline}</b> · estratégia sugerida {_escape(strategy)} · score {_escape(score)}</div>'
        f'<div class="decision-grid">'
        f'<div class="mini-panel"><b>Ação prática</b><span>{headline}</span></div>'
        f'<div class="mini-panel"><b>Estratégia</b><span>{strategy}</span></div>'
        f'<div class="mini-panel"><b>Score</b><span>{score}</span></div>'
        f'<div class="mini-panel"><b>Gatilho</b><span>{_escape(item.get("gatilho_confirmacao") or item.get("entry_price_condition") or item.get("conditional_trigger"))}</span></div>'
        f'<div class="mini-panel"><b>Invalidação</b><span>{_escape(item.get("invalidacao") or item.get("invalidation_rules_short") or item.get("motivo"))}</span></div>'
        f'<div class="mini-panel"><b>Status da cadeia</b><span>{_escape(item.get("cadeia_opcoes_status") or item.get("chain_status") or "pendente")}</span></div>'
        f"</div>"
        f'<div class="summary"><b>Motivo principal:</b> {reason}</div></div>'
    )
    st.markdown(body, unsafe_allow_html=True)
    details, simulate, follow = st.columns(3)
    action = None
    if details.button("Ver detalhes", key=f"decision_detail_{card_key}"):
        action = "details"
    if simulate.button("Simular manualmente", key=f"decision_simulate_{card_key}"):
        action = "simulate"
    if follow.button("Acompanhar tese", key=f"decision_follow_{card_key}"):
        action = "follow"
    return action


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
    score = (healthbox.get("score_result") or {}).get("score", "não calculado")
    st.markdown(
        f'<div class="section-card"><div class="top"><div><div class="small-label">MERCADO REAL</div><div class="asset">{_escape(snapshot.get("ativo"))}</div></div>'
        f'<div><span class="status-badge {_status_css(snapshot.get("status_dado", "indisponível"))}">{_escape(snapshot.get("status_dado", "indisponível"))}</span></div></div>'
        f'<div class="compact-row">'
        f'{_line_box("Preço", snapshot.get("preco_atual"))}'
        f'{_line_box("Variação diária %", change)}'
        f'{_line_box("Tendência", snapshot.get("tendencia"))}'
        f'{_line_box("Healthbox", score)}'
        f'{_line_box("RSI", snapshot.get("rsi"))}'
        f'{_line_box("rVol", snapshot.get("rvol"))}'
        f"</div>"
        f'<div class="summary">Fonte {_escape(snapshot.get("fonte"))} · coleta {_escape(snapshot.get("coleta"))} · campos ausentes {_escape(", ".join(snapshot.get("campos_ausentes", [])) or "nenhum")}</div></div>',
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
        f'<p><span class="status-badge {_status_css(general)}">{_escape(general)}</span> '
        f'<span class="status-badge status-neutral">snapshot {_escape(status.get("snapshot_age_status", "indisponível"))}</span></p>'
        f'<p><b>Última atualização:</b> {_escape(latest.get("finished_at"))}<br>'
        f'<b>Modo:</b> {_escape(latest.get("mode"))} · <b>Origem:</b> {_escape(latest.get("runner"))} · <b>Fonte:</b> {_escape(latest.get("source") or summary.get("fonte"))}</p>'
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
        f'<b>Status:</b> {_escape(summary.get("status_dado", "indisponível"))} · <b>Coleta:</b> {_escape(summary.get("coleta") or "nenhuma")}</p></div>',
        unsafe_allow_html=True,
    )


def render_options_eod_status_card(status: dict) -> None:
    last = status.get("last_update") or {}
    summary = status.get("snapshot_summary") or {}
    general = str(last.get("status") or summary.get("status") or "não atualizado")
    st.markdown(
        f'<div class="section-card"><div class="small-label">STATUS OPÇÕES EOD</div>'
        f'<p><span class="status-badge {_status_css(general)}">{_escape(general)}</span></p>'
        f'<p><b>Última atualização:</b> {_escape(last.get("finished_at") or summary.get("latest_collection") or "não atualizada")}<br>'
        f'<b>Ativos disponíveis:</b> {last.get("available_count", summary.get("available_count", 0))} · <b>Séries:</b> {last.get("total_series", summary.get("total_series", 0))} · '
        f'<b>Erros:</b> {last.get("error_count", summary.get("error_count", 0))}</p></div>',
        unsafe_allow_html=True,
    )


def render_real_opportunity_card(item: dict) -> str | None:
    action_item = {
        "card_key": f'{item.get("ativo")}_{item.get("estrategia")}_{item.get("vencimento")}',
        "source_label": "RADAR EOD",
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
                    "Estratégia": candidate.get("strategy_name"),
                    "Score": candidate.get("suitability_score"),
                    "Status": candidate.get("status"),
                    "Objetivo": candidate.get("objective_label"),
                    "Complexidade": candidate.get("complexidade"),
                    "Motivos contra": "; ".join(candidate.get("motivos_contra", [])),
                    "Dados necessários": "; ".join(candidate.get("dados_necessarios", [])),
                    "Delta-alvo": plan.get("delta_target"),
                    "Vencimento": plan.get("expiration_window"),
                    "Encaixe capital": candidate.get("capital_fit_status"),
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.caption("Nenhum screening disponível.")


def render_daily_priority_item(item: dict) -> None:
    render_decision_card(
        {
            "card_key": f'priority_{item.get("ativo")}_{item.get("strategy_name")}',
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
        f'<h3>{_escape(simulation.get("ticker"))} · {_escape(simulation.get("strategy_name"))}</h3>'
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
            f"**{_escape(item.get('ativo', '—'))} · {_escape(item.get('estrategia', 'indisponível'))}** — "
            f"`{_escape(item.get('conditional_status', 'inconclusivo'))}` · score {_escape(item.get('score') if item.get('score') is not None else 'indisponível')}"
        )


def render_real_engine_status_card(options_snapshots: dict, last_summary: dict | None = None) -> None:
    summary = last_summary or {}
    unavailable = [
        symbol for symbol, snapshot in options_snapshots.items() if not snapshot.get("success") or not snapshot.get("series")
    ]
    st.markdown(
        f'<div class="section-card"><div class="small-label">RADAR EOD</div>'
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
        getattr(st, alert["nivel"])(f"**{alert['titulo']}:** {alert['mensagem']} — MOCK / EXEMPLO")


mock_badge = render_mock_badge
metric_card = render_metric_card
render_opportunity_card = opportunity_card
