"""Páginas de configuração e fontes de dados, organizadas em abas internas."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components import (
    metric_card,
    render_data_notice,
    render_options_eod_status_card,
    render_options_status_card,
)
from app.data_contracts import CONTRACTS
from app.market_snapshot_engine import build_many_asset_snapshots, snapshot_to_healthbox
from app.options_snapshot_engine import (
    build_options_snapshot,
    fetch_options_expirations,
    load_options_snapshot,
    summarize_options_snapshot,
)
from app.options_update_orchestrator import (
    get_last_options_update_summary,
    load_all_options_snapshots,
    run_options_update,
)
from app.options_universe_discovery import (
    discover_options_availability,
    load_option_candidate_tickers,
    load_options_universe_availability,
    summarize_options_availability,
)
from app.providers.provider_manager import fetch_historical, fetch_quotes, provider_status
from app.notify_engine import (
    build_daily_digest,
    clear_telegram_config,
    save_telegram_config,
    send_daily_digest,
    telegram_status,
)
from app.source_registry import build_source_summary, load_source_registry
from app.ui.pages.mock_page import show_data_control
from app.update_orchestrator import get_last_update_summary


def _render_provider_overview() -> None:
    status = provider_status()
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Provider ativo", status.get("provider", "indisponível"))
    p2.metric("Status", status.get("status", "indisponível"))
    p3.metric("Token detectado", "sim" if status.get("token_detected") else "não")
    p4.metric("Cache ativo", f"sim · {status.get('cached_files', 0)} arquivo(s)")
    st.caption(
        f"Última coleta: {status.get('last_collection') or 'nenhuma'} · "
        f"fallback permitido: {'sim' if status.get('fallback_allowed') else 'não'}"
    )
    render_data_notice(
        "Nesta etapa, a brapi ainda não alimenta o Opportunity Engine. Ela apenas valida a coleta automática de preços e histórico."
    )
    latest_result = st.session_state.get("brapi_history_test") or st.session_state.get("brapi_quote_test")
    st.caption(
        f"Status da última chamada: {latest_result.get('status_dado', 'nenhuma chamada nesta sessão') if latest_result else 'nenhuma chamada nesta sessão'} · "
        f"fallback mock ativo: {'sim' if status.get('fallback_allowed') else 'não'}"
    )
    quote_test_status = st.session_state.get("brapi_quote_test", {}).get("status_dado", "não testado nesta sessão")
    history_test_status = st.session_state.get("brapi_history_test", {}).get("status_dado", "não testado nesta sessão")
    st.markdown(
        f'<div class="section-card"><div class="small-label">Status brapi</div><p><b>Configurada:</b> {"sim" if status.get("configured") else "não"}<br><b>Último teste de cotação:</b> {quote_test_status}<br><b>Último teste de histórico:</b> {history_test_status}<br><b>Cache:</b> ativo · <b>Fallback mock:</b> {"ativo" if status.get("fallback_allowed") else "inativo"}</p></div>',
        unsafe_allow_html=True,
    )
    test_quotes, test_history = st.columns(2)
    if test_quotes.button("Testar brapi: PETR4, VALE3, ITUB4, BOVA11"):
        st.session_state["brapi_quote_test"] = fetch_quotes(["PETR4", "VALE3", "ITUB4", "BOVA11"], use_cache=False)
    if test_history.button("Testar histórico brapi"):
        st.session_state["brapi_history_test"] = fetch_historical(["PETR4"], range="3mo", interval="1d", use_cache=False)

    quote_result = st.session_state.get("brapi_quote_test")
    if quote_result:
        if quote_result.get("success"):
            st.success(f"Cotação respondida por {quote_result.get('provider')} · {quote_result.get('status_dado')}")
            quote_rows = []
            expected = ["ticker", "preco", "abertura", "maxima", "minima", "fechamento_anterior", "volume", "variacao_percentual", "market_time"]
            for record in quote_result.get("data", []):
                row = {key: record.get(key) for key in expected}
                row.update(
                    campos_ausentes=", ".join(key for key in expected if record.get(key) is None) or "nenhum",
                    coleta=record.get("coleta", quote_result.get("coleta", "indisponível")),
                    fonte=record.get("fonte", quote_result.get("provider", "indisponível")),
                    tipo_dado=record.get("tipo_dado", quote_result.get("tipo_dado", "indisponível")),
                    status_dado=record.get("status_dado", quote_result.get("status_dado", "indisponível")),
                )
                quote_rows.append(row)
            st.dataframe(pd.DataFrame(quote_rows), width="stretch", hide_index=True)
        else:
            st.error(f"Falha no teste de cotação: {quote_result.get('error', 'erro desconhecido')}")

    historical_result = st.session_state.get("brapi_history_test")
    if historical_result:
        if historical_result.get("success"):
            assets = historical_result.get("data", [])
            candle_count = sum(len(item.get("candles", [])) for item in assets)
            st.success(
                f"Histórico normalizado: {candle_count} candle(s) · fonte {historical_result.get('provider')} · "
                f"tipo {historical_result.get('tipo_dado')} · status {historical_result.get('status_dado')} · "
                f"coleta {historical_result.get('coleta', 'indisponível')}"
            )
            candles = assets[0].get("candles", [])[-10:] if assets else []
            candle_rows = [
                {
                    **candle,
                    "campos_ausentes": ", ".join(key for key in ("date", "open", "high", "low", "close", "volume", "adjusted_close") if candle.get(key) is None) or "nenhum",
                }
                for candle in candles
            ]
            st.dataframe(pd.DataFrame(candle_rows), width="stretch", hide_index=True)
        else:
            st.error(f"Falha no teste histórico: {historical_result.get('error', 'erro desconhecido')}")


def _render_options_test() -> None:
    st.warning(
        "Esta seção testa dados de opções da brapi. Esses dados são EOD/fim de pregão quando disponíveis. "
        "Não são usados ainda para gerar oportunidades reais."
    )
    options_underlying = st.text_input("Ativo subjacente", value="PETR4", key="brapi_options_underlying").strip().upper()
    expiration_column, chain_column = st.columns(2)
    if expiration_column.button("Testar vencimentos", key="test_options_expirations"):
        st.session_state["brapi_options_expirations"] = fetch_options_expirations(options_underlying)
    if chain_column.button("Testar cadeia do próximo vencimento", key="test_options_chain"):
        snapshot = build_options_snapshot(options_underlying)
        st.session_state["brapi_options_snapshot"] = snapshot
        st.session_state["brapi_options_expirations"] = {
            "success": bool(snapshot.get("expirations")), "underlying": snapshot.get("underlying"),
            "expirations": snapshot.get("expirations", []), "count": len(snapshot.get("expirations", [])),
            "access_status": snapshot.get("access_status"), "error": snapshot.get("error"),
            "fonte": snapshot.get("fonte"), "coleta": snapshot.get("coleta"),
            "status_dado": snapshot.get("status_dado"), "observacao": snapshot.get("observacao"),
        }

    expiration_result = st.session_state.get("brapi_options_expirations")
    options_snapshot = st.session_state.get("brapi_options_snapshot") or load_options_snapshot()
    options_summary = summarize_options_snapshot(options_snapshot)
    if expiration_result:
        if expiration_result.get("access_status") == "sem_acesso":
            st.error("Opções indisponíveis na fonte atual. Verifique se seu plano brapi inclui opções.")
        elif not expiration_result.get("success"):
            st.error(f"Opções indisponíveis na fonte atual. Motivo: {expiration_result.get('error', 'erro de API')}")
        else:
            st.success(f"{expiration_result.get('count', 0)} vencimento(s) encontrado(s) para {options_underlying}.")
    render_options_status_card(options_summary)
    st.caption(options_summary.get("observacao", "Dados de opções EOD/fim de pregão quando disponíveis."))
    option_metrics = st.columns(4)
    option_metrics[0].metric("Vencimentos", options_summary.get("expiration_count", 0))
    option_metrics[1].metric("Séries", options_summary.get("series_count", 0))
    option_metrics[2].metric("Calls", options_summary.get("calls", 0))
    option_metrics[3].metric("Puts", options_summary.get("puts", 0))
    missing_options = options_summary.get("campos_ausentes_comuns", {})
    st.caption(
        f"Status de acesso: {options_summary.get('access_status', 'indisponível')} · "
        f"Fonte: {options_summary.get('fonte', 'brapi_options')} · Coleta: {options_summary.get('coleta') or 'nenhuma'} · "
        f"Campos ausentes comuns: {', '.join(f'{key} ({value})' for key, value in missing_options.items()) or 'nenhum registrado'}"
    )
    if options_summary.get("error"):
        st.error(f"Motivo registrado: {options_summary['error']}")
    series = options_snapshot.get("series", []) if isinstance(options_snapshot, dict) else []
    if series:
        st.dataframe(pd.DataFrame(series), width="stretch", hide_index=True)


def _render_options_eod_update() -> None:
    st.warning(
        "Dados de opções da brapi são EOD/fim de pregão. Eles ainda não alimentam recomendações reais nesta etapa."
    )
    multiasset_text = st.text_input(
        "Ativos para atualização EOD",
        value="PETR4, VALE3, ITUB4, BOVA11",
        key="options_eod_underlyings",
    )
    update_options_column, load_options_column = st.columns(2)
    if update_options_column.button("Atualizar opções EOD agora", key="update_options_eod"):
        symbols = [item.strip().upper() for item in multiasset_text.split(",") if item.strip()]
        with st.spinner("Atualizando cadeias EOD de opções..."):
            st.session_state["options_eod_result"] = run_options_update(symbols, mode="close", max_expirations=4, min_dte=7, max_dte=60)
    if load_options_column.button("Usar último snapshot de opções", key="load_options_eod"):
        st.session_state["options_eod_result"] = get_last_options_update_summary().get("last_update") or {}

    eod_status = get_last_options_update_summary()
    render_options_eod_status_card(eod_status)
    eod_result = st.session_state.get("options_eod_result") or eod_status.get("last_update") or {}
    if eod_result:
        eod_metrics = st.columns(4)
        eod_metrics[0].metric("Consultados", eod_result.get("total_underlyings", 0))
        eod_metrics[1].metric("Disponíveis", eod_result.get("available_count", 0))
        eod_metrics[2].metric("Indisponíveis", eod_result.get("unavailable_count", 0))
        eod_metrics[3].metric("Erros", eod_result.get("error_count", 0))
        st.caption(
            f"Séries: {eod_result.get('total_series', 0)} · Calls: {eod_result.get('total_calls', 0)} · "
            f"Puts: {eod_result.get('total_puts', 0)} · Fonte: {eod_result.get('source', 'brapi_options')} · "
            f"Frequência: {eod_result.get('data_frequency', 'EOD')} · Coleta: {eod_result.get('finished_at', 'indisponível')}"
        )
        if eod_result.get("errors"):
            st.error("Falhas registradas: " + " | ".join(map(str, eod_result["errors"])))
    saved_options = load_all_options_snapshots()
    if saved_options:
        saved_rows = [
            {
                "Ativo": symbol, "Status": item.get("status_dado"), "Acesso": item.get("access_status"),
                "Vencimento": item.get("expiration_used"), "Séries": item.get("series_count", 0),
                "Calls": item.get("calls_count", 0), "Puts": item.get("puts_count", 0),
                "Erro": item.get("error") or "nenhum", "Coleta": item.get("coleta"),
            }
            for symbol, item in saved_options.items()
        ]
        st.dataframe(pd.DataFrame(saved_rows), width="stretch", hide_index=True)


def _render_universe() -> None:
    availability = load_options_universe_availability()
    availability_summary = summarize_options_availability(availability)
    candidate_tickers = load_option_candidate_tickers()
    tested_tickers = set(availability.get("tickers_tested", []))
    pending_tickers = [ticker for ticker in candidate_tickers if ticker not in tested_tickers]
    source_denied = sum(item.get("status") == "sem_acesso_fonte" for item in availability.get("assets", []))
    technical_errors = sum(item.get("status") == "erro" for item in availability.get("assets", []))
    universe_metrics = st.columns(6)
    universe_metrics[0].metric("Total de candidatos", len(candidate_tickers))
    universe_metrics[1].metric("Ativos testados", availability_summary["tickers_tested"])
    universe_metrics[2].metric("Pendentes", len(pending_tickers))
    universe_metrics[3].metric("Acessíveis", availability_summary["available_count"])
    universe_metrics[4].metric("Sem acesso pela fonte", source_denied)
    universe_metrics[5].metric("Erros", technical_errors)
    st.caption(f"Última descoberta: {availability.get('generated_at', 'nunca')}")
    st.warning("Sem acesso pela fonte atual não significa ausência de opções na B3.")
    st.caption("Cache real EOD; o pipeline reutiliza apenas resultados com até 72 horas e não executa discovery automaticamente.")
    if availability.get("available"):
        st.success("Disponíveis: " + ", ".join(availability["available"]))
    if availability.get("errors"):
        st.error("Principais erros: " + " | ".join(map(str, availability["errors"][:5])))
    liquidity_classes = availability_summary.get("liquidity_classes", {})
    st.caption("Classes de liquidez: " + " · ".join(f"{key}: {value}" for key, value in liquidity_classes.items()))
    if any(liquidity_classes.get(key, 0) for key in ("baixa", "muito baixa", "sem negócio")):
        st.warning("Liquidez baixa no mercado brasileiro. Validar book, spread e execução manualmente.")
    if st.button("Atualizar universo de opções", key="discover_options_universe"):
        candidate_tickers = load_option_candidate_tickers()[:20]
        with st.spinner("Testando disponibilidade real de opções EOD..."):
            st.session_state["options_universe_discovery"] = discover_options_availability(candidate_tickers, limit=20)
        st.success("Descoberta concluída e cache salvo. Falhas permanecem registradas por ativo.")
        st.rerun()


def _render_telegram_section() -> None:
    st.markdown("### Notificações externas (Telegram)")
    status = telegram_status()
    columns = st.columns(3)
    columns[0].metric("Configurado", "sim" if status["configured"] else "não")
    columns[1].metric("Ativado", "sim" if status["enabled"] else "não")
    columns[2].metric("Origem", status["source"])
    if status["configured"]:
        st.caption(f"Token: `{status['bot_token_masked']}` · chat_id: `{status['chat_id']}`")
    st.caption(status["observacao"])
    with st.form("telegram_config_form"):
        bot_token = st.text_input("Token do bot (obrigatório)", type="password", value="", help="Criado no @BotFather. Fica salvo apenas localmente.")
        chat_id = st.text_input("chat_id de destino (obrigatório)", value="", help="ID do chat, grupo ou canal. Consulte @userinfobot.")
        enabled = st.checkbox("Notificações ativadas", value=True)
        saved = st.form_submit_button("Salvar configuração")
    if saved:
        try:
            save_telegram_config(bot_token, chat_id, enabled)
            st.success("Configuração salva localmente. Nenhum dado foi enviado.")
        except ValueError as error:
            st.error(str(error))
    c1, c2 = st.columns(2)
    if c1.button("Enviar digest de teste"):
        result = send_daily_digest()
        if result.get("success"):
            st.success("Digest enviado. Confira o chat de destino.")
        else:
            st.error(f"Falha no envio: {result.get('error')}")
    if c2.button("Apagar configuração salva"):
        clear_telegram_config()
        st.info("Configuração local apagada. Variáveis de ambiente continuam sendo usadas se existirem.")
    text, meta = build_daily_digest()
    with st.expander("Pré-visualizar digest diário", expanded=False):
        st.code(text)
        st.caption(f"Gerado às {meta.get('built_at')} (UTC) · status pipeline: {meta.get('pipeline_status') or 'indisponível'}")
    st.info(
        "O digest é informativo: resumo das rotinas e números do radar. Nenhuma recomendação, nenhuma ordem. "
        "Para automação diária, use scripts/send_daily_digest.py no GitHub Actions."
    )


def _render_routines() -> None:
    st.markdown(
        "- **Pré-pregão:** 1x antes da abertura;\n"
        "- **Intraday radar:** a cada 15 minutos;\n"
        "- **Posições abertas:** a cada 5 a 15 minutos, se houver dados confiáveis;\n"
        "- **Pós-fechamento:** 1x após o fechamento."
    )
    routine_status = get_last_update_summary()
    routine_rows = []
    for mode in ("premarket", "intraday", "close"):
        execution = routine_status.get("last_updates", {}).get(mode, {})
        success = execution.get("success")
        routine_rows.append(
            {
                "Modo": mode,
                "Última execução": execution.get("finished_at", "nunca"),
                "Runner": execution.get("runner", "indisponível"),
                "Sucesso": "sim" if success is True else "não" if success is False else "indisponível",
                "Incompletos": execution.get("incomplete_count", 0),
                "Erros": execution.get("error_count", 0),
            }
        )
    st.dataframe(pd.DataFrame(routine_rows), width="stretch", hide_index=True)
    if routine_status.get("last_error"):
        st.error(f"Erro recente: {routine_status['last_error']}")
    st.info(
        "Quando o projeto estiver no GitHub e o secret BRAPI_TOKEN estiver configurado, "
        "o GitHub Actions atualizará estes arquivos automaticamente."
    )
    _render_telegram_section()


def _render_real_healthbox() -> None:
    render_data_notice(
        "Esta seção usa dados reais da brapi quando disponíveis. O Opportunity Engine ainda permanece em MOCK / EXEMPLO."
    )
    ticker_text = st.text_input("Tickers para o Healthbox real", value="PETR4, VALE3, ITUB4, BOVA11")
    if st.button("Atualizar Healthbox com brapi"):
        tickers = [ticker.strip().upper() for ticker in ticker_text.split(",") if ticker.strip()]
        st.session_state["real_healthbox_snapshots"] = build_many_asset_snapshots(tickers, range="3mo", interval="1d")

    real_snapshots = st.session_state.get("real_healthbox_snapshots")
    if real_snapshots:
        updated = sum(item.get("status_dado") == "atualizado" for item in real_snapshots)
        incomplete = sum(item.get("status_dado") == "incompleto" for item in real_snapshots)
        errors = sum(item.get("status_dado") == "erro" for item in real_snapshots)
        for column, (value, label, color) in zip(
            st.columns(4),
            [
                (updated, "Ativos atualizados", "approved"),
                (incomplete, "Ativos incompletos", "warning"),
                (errors, "Ativos com erro", "rejected"),
                ("brapi", "Fonte", "teal"),
            ],
        ):
            with column:
                metric_card(value, label, "Healthbox real experimental", color)
        rows = []
        for snapshot in real_snapshots:
            healthbox = snapshot_to_healthbox(snapshot)
            score_result = healthbox.get("score_result", {})
            rows.append(
                {
                    "Ativo": snapshot.get("ativo"),
                    "Preço atual": snapshot.get("preco_atual"),
                    "Variação diária %": snapshot.get("variacao_diaria_percent"),
                    "Range diário %": snapshot.get("range_diario_percent"),
                    "ADR %": snapshot.get("adr_percent"),
                    "ATR %": snapshot.get("atr_percent"),
                    "rVol": snapshot.get("rvol"),
                    "RSI": snapshot.get("rsi"),
                    "RSI 200": snapshot.get("rsi_200") if snapshot.get("rsi_200") is not None else "indisponível",
                    "Tendência": snapshot.get("tendencia"),
                    "Suporte simples": snapshot.get("suporte"),
                    "Resistência simples": snapshot.get("resistencia"),
                    "Distância suporte %": snapshot.get("distancia_suporte_percent"),
                    "Distância resistência %": snapshot.get("distancia_resistencia_percent"),
                    "Score Healthbox": score_result.get("score") if score_result.get("score") is not None else "score não calculado",
                    "Status": snapshot.get("status_dado"),
                    "Campos ausentes": ", ".join(snapshot.get("campos_ausentes", [])) or "nenhum",
                    "Fonte": snapshot.get("fonte"),
                    "Tipo do dado": snapshot.get("tipo_dado"),
                    "Coleta": snapshot.get("coleta"),
                }
            )
        st.dataframe(pd.DataFrame(rows).astype(str), width="stretch", hide_index=True)


def _render_sources_registry() -> None:
    st.warning(
        "Nenhuma coleta real está implementada nesta versão. Esta tela apenas registra fontes futuras e controle de confiabilidade."
    )
    sources = load_source_registry()
    source_rows = [
        {
            "Fonte": source["nome"],
            "Categoria": source["categoria"],
            "Uso previsto": source["uso_previsto"],
            "Status": source["status"],
            "Custo": source["custo"],
            "Frequência esperada": source["frequencia_esperada"],
            "Confiabilidade": source["confiabilidade"],
            "Última coleta": source["ultima_coleta"] or "nunca coletado",
            "Observação": source["observacao"],
        }
        for source in sources
    ]
    st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)


def _render_contracts_and_quality() -> None:
    st.markdown("## Contratos de Dados")
    contract_rows = [
        {
            "Contrato": name,
            "Campos obrigatórios": ", ".join(contract["required"]),
            "Campos desejáveis": ", ".join(contract["optional"]) or "nenhum nesta etapa",
        }
        for name, contract in CONTRACTS.items()
    ]
    st.dataframe(pd.DataFrame(contract_rows), width="stretch", hide_index=True)

    summary = build_source_summary()
    labels = [
        (summary["sources_registered"], "Fontes registradas"),
        (summary["sources_implemented"], "Fontes implementadas"),
        (summary["mock_sources"], "Fontes mockadas"),
        (summary["missing_metadata"], "Metadados incompletos"),
    ]
    for column, (value, label) in zip(st.columns(4), labels):
        with column:
            metric_card(value, label)
    st.info(
        f"Status geral: **{summary['status']}** · coleta real habilitada: **não** · campos ausentes em fontes: **{summary['missing_metadata']}**"
    )
    st.markdown(
        '<div class="section-card"><div class="small-label">Status do Projeto</div><h3>Ambiente demonstrativo protegido</h3><p>Opportunity Engine, Healthbox, Bulkowski e Exit Engine ativos sobre dados MOCK / EXEMPLO. Coleta real, corretora e envio de ordens permanecem desativados.</p></div>',
        unsafe_allow_html=True,
    )


def configuration_page() -> None:
    tabs = st.tabs(["Fontes e brapi", "Opções EOD", "Universo de opções", "Rotinas", "Saúde dos dados"])
    with tabs[0]:
        _render_provider_overview()
        _render_sources_registry()
    with tabs[1]:
        _render_options_test()
        _render_options_eod_update()
    with tabs[2]:
        _render_universe()
    with tabs[3]:
        _render_routines()
        _render_real_healthbox()
    with tabs[4]:
        _render_contracts_and_quality()
        show_data_control()
