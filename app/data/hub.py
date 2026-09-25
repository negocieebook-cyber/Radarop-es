from __future__ import annotations

from datetime import date, datetime
from typing import Any

import streamlit as st

from app.bulkowski_engine import analyze_pattern_for_asset
from app.graphical_thesis_engine import build_graphical_thesis
from app.market_snapshot_engine import snapshot_to_healthbox
from app.position_monitor import build_position_status, current_context
from app.pipeline_orchestrator import REAL_OPPORTUNITIES_FILE
from app.real_opportunity_engine import build_real_candidates_for_asset
from app.storage import POSITIONS_PATH, load_json
from app.update_orchestrator import SNAPSHOTS_FILE


@st.cache_data
def get_unified_data() -> dict[str, Any]:
    return {
        "market_snapshots": load_json(SNAPSHOTS_FILE, []),
        "real_opportunities_snapshot": load_json(REAL_OPPORTUNITIES_FILE, {}),
        "positions": load_json(POSITIONS_PATH, []),
    }


def _normalize_ticker(value: str) -> str:
    return str(value or "").strip().upper()


def _asset_base_snapshot(ticker: str) -> dict[str, Any]:
    return {
        "ativo": ticker,
        "fonte": "indisponível",
        "tipo_dado": "indisponível",
        "status_dado": "não coletado",
    }


def _find_market_snapshot(unified: dict[str, Any], ticker: str) -> dict[str, Any] | None:
    snapshots = unified.get("market_snapshots", [])
    return next((item for item in snapshots if str(item.get("ativo", "")).upper() == ticker), None)


def _find_positions(unified: dict[str, Any], ticker: str) -> list[dict[str, Any]]:
    return [
        item for item in unified.get("positions", [])
        if str(item.get("ativo", "")).upper() == ticker
    ]


def _find_snapshot_opportunities(unified: dict[str, Any], ticker: str) -> list[dict[str, Any]]:
    snapshot = unified.get("real_opportunities_snapshot", {})
    opportunities = snapshot.get("opportunities", []) if isinstance(snapshot, dict) else []
    return [
        item for item in opportunities
        if str(item.get("ativo", "")).upper() == ticker
    ]


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}, ()):
            return value
    return None


def _parse_iso_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _label_event_impact(days: int | None) -> str:
    if days is None:
        return "indisponível"
    if days <= 2:
        return "atenção imediata"
    if days <= 5:
        return "monitorar"
    return "informativo"


def _match_preferred_opportunity(
    preferred_strategy: dict[str, Any] | None,
    opportunities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not preferred_strategy:
        return opportunities[0] if opportunities else None
    strategy_id = str(preferred_strategy.get("strategy_id") or "").strip().lower()
    strategy_name = str(preferred_strategy.get("strategy_name") or "").strip().lower()
    for item in opportunities:
        kind = str(item.get("tipo_estrutura") or "").strip().lower()
        name = str(item.get("estrategia") or "").strip().lower()
        if strategy_id and strategy_id == kind:
            return item
        if strategy_name and strategy_name == name:
            return item
    return opportunities[0] if opportunities else None


def _build_operation_values(
    thesis: dict[str, Any],
    preferred_strategy: dict[str, Any] | None,
    matched_opportunity: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "entrada": {
            "valor": _first_non_empty(
                (matched_opportunity or {}).get("entry_reference_price"),
                (matched_opportunity or {}).get("custo_liquido"),
                (matched_opportunity or {}).get("credito_liquido"),
            ),
            "condicao": _first_non_empty(
                (matched_opportunity or {}).get("entry_price_condition"),
                "Indisponível",
            ),
            "notas": _first_non_empty((matched_opportunity or {}).get("entry_notes"), []),
        },
        "stop_invalidation": {
            "valor": thesis.get("invalidacao"),
            "regras": _first_non_empty((matched_opportunity or {}).get("invalidation_rules"), []),
        },
        "alvo": thesis.get("alvo"),
        "break_even": _first_non_empty((matched_opportunity or {}).get("break_even"), "Indisponível"),
        "capital": {
            "estimativa": _first_non_empty(
                (preferred_strategy or {}).get("capital_required_estimate"),
                (preferred_strategy or {}).get("recommended_capital"),
            ),
            "minimo_tecnico": (preferred_strategy or {}).get("minimum_technical_capital"),
            "margem_proxy": (preferred_strategy or {}).get("margin_proxy"),
            "capital_fit_status": _first_non_empty(
                (preferred_strategy or {}).get("capital_fit_status"),
                "pendente_dados",
            ),
        },
        "risco": {
            "risco_retorno": (matched_opportunity or {}).get("risco_retorno"),
            "perda_maxima": _first_non_empty(
                (matched_opportunity or {}).get("perda_maxima"),
                (preferred_strategy or {}).get("max_loss_estimate"),
            ),
        },
        "ganho": _first_non_empty(
            (matched_opportunity or {}).get("ganho_maximo"),
            "Indisponível",
        ),
        "perda": _first_non_empty(
            (matched_opportunity or {}).get("perda_maxima"),
            (preferred_strategy or {}).get("max_loss_estimate"),
            "Indisponível",
        ),
        "premio_debito_credito": {
            "premio_pago": (matched_opportunity or {}).get("premio_pago"),
            "premio_recebido": (matched_opportunity or {}).get("premio_recebido"),
            "debito_liquido": (matched_opportunity or {}).get("custo_liquido"),
            "credito_liquido": (matched_opportunity or {}).get("credito_liquido"),
        },
        "delta": _first_non_empty(
            (matched_opportunity or {}).get("delta"),
            (matched_opportunity or {}).get("delta_comprado"),
            (matched_opportunity or {}).get("delta_vendido"),
            "Indisponível",
        ),
        "strike": {
            "comprado": (matched_opportunity or {}).get("strike_comprado"),
            "vendido": (matched_opportunity or {}).get("strike_vendido"),
            "regiao_sugerida": "Indisponível",
        },
        "vencimento": {
            "data": (matched_opportunity or {}).get("vencimento"),
            "dias": (matched_opportunity or {}).get("vencimento_dias"),
            "janela_ideal": "Indisponível",
        },
    }


def _build_calendar(
    ticker: str,
    stored_opportunities: list[dict[str, Any]],
) -> dict[str, Any]:
    today = datetime.now().date()
    items: list[dict[str, Any]] = []
    for item in stored_opportunities:
        event_date = _parse_iso_date(item.get("vencimento"))
        days = (event_date - today).days if event_date else None
        if event_date is None:
            continue
        items.append(
            {
                "ativo": ticker,
                "tipo": "vencimento_oportunidade",
                "data": item.get("vencimento"),
                "dias": days,
                "origem": item.get("fonte"),
                "estrutura": item.get("tipo_estrutura"),
                "impacto_operacional": _label_event_impact(days),
            }
        )
    ranked = sorted(
        items,
        key=lambda item: item["dias"] if isinstance(item.get("dias"), int) else 999999,
    )
    return {
        "status": "disponível" if ranked else "sem_dados_eventos",
        "fonte": "data/runtime/real_opportunities_snapshot.json",
        "items": ranked,
        "proximo_evento": ranked[0] if ranked else None,
        "mensagem": None if ranked else "Sem dados de eventos",
    }


def _build_position_monitoring(
    asset_snapshot: dict[str, Any],
    healthbox: dict[str, Any],
    bulkowski: dict[str, Any],
    positions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    monitoring: list[dict[str, Any]] = []
    for position in positions:
        context = current_context(
            asset_snapshot=asset_snapshot,
            healthbox=healthbox,
            bulkowski=bulkowski,
            current_mark=None,
            tipo_dado=asset_snapshot.get("tipo_dado", "indisponível"),
            fonte=asset_snapshot.get("fonte", "indisponível"),
        )
        context["vencimento_dias"] = position.get("vencimento_dias")
        monitoring.append(build_position_status(position, context))
    return monitoring


def _build_alerts(
    thesis: dict[str, Any],
    preferred_strategy: dict[str, Any] | None,
    matched_opportunity: dict[str, Any] | None,
    monitoring: list[dict[str, Any]],
) -> dict[str, Any]:
    alerts: list[dict[str, Any]] = []
    for message in thesis.get("hard_technical_blockers", []):
        alerts.append({"origem": "tese_grafica", "tipo": "bloqueio", "mensagem": message})
    for message in thesis.get("soft_technical_warnings", []):
        alerts.append({"origem": "tese_grafica", "tipo": "alerta", "mensagem": message})
    for message in (matched_opportunity or {}).get("hard_blockers", []):
        alerts.append({"origem": "oportunidade_real", "tipo": "bloqueio", "mensagem": message})
    for message in (matched_opportunity or {}).get("soft_warnings", []):
        alerts.append({"origem": "oportunidade_real", "tipo": "alerta", "mensagem": message})
    for message in (preferred_strategy or {}).get("motivos_contra", []):
        alerts.append({"origem": "screener", "tipo": "atenção", "mensagem": message})
    for item in monitoring:
        alerts.append(
            {
                "origem": "monitoramento",
                "tipo": item.get("severity"),
                "mensagem": item.get("reason"),
            }
        )
    unique = []
    seen: set[tuple[str, str, str]] = set()
    for item in alerts:
        key = (
            str(item.get("origem")),
            str(item.get("tipo")),
            str(item.get("mensagem")),
        )
        if key not in seen and item.get("mensagem"):
            seen.add(key)
            unique.append(item)
    return {
        "items": unique,
        "pontos_de_atencao": [item["mensagem"] for item in unique],
    }


def _collect_unavailable_fields(
    asset_snapshot: dict[str, Any],
    healthbox: dict[str, Any],
    thesis: dict[str, Any],
    preferred_strategy: dict[str, Any] | None,
    matched_opportunity: dict[str, Any] | None,
    calendar: dict[str, Any],
) -> list[str]:
    unavailable: list[str] = []
    if asset_snapshot.get("status_dado") in {None, "erro", "não coletado"}:
        unavailable.append("contexto do ativo")
    if (healthbox.get("score_result") or {}).get("score") is None:
        unavailable.append("healthbox_score")
    if healthbox.get("tendencia") in {None, "indisponível"}:
        unavailable.append("tendência")
    unavailable.append("força") if "força" not in unavailable else None
    if _first_non_empty(
        (matched_opportunity or {}).get("liquidez"),
        asset_snapshot.get("volume"),
    ) is None:
        unavailable.append("liquidez")
    if not (matched_opportunity or {}).get("vencimento"):
        unavailable.append("vencimento da operação")
    if _first_non_empty(
        (matched_opportunity or {}).get("delta"),
        (matched_opportunity or {}).get("delta_comprado"),
        (matched_opportunity or {}).get("delta_vendido"),
    ) in {None, ""}:
        unavailable.append("delta")
    if calendar.get("status") != "disponível":
        unavailable.append("eventos e calendário")
    return unavailable


@st.cache_data
def build_terminal_decision_payload(ticker: str) -> dict[str, Any]:
    symbol = _normalize_ticker(ticker)
    if not symbol:
        return {
            "ticker": "",
            "modo_atual": "análise",
            "contexto_ativo": _asset_base_snapshot(""),
            "healthbox": {},
            "diagnostico_grafico": {},
            "tese_grafica": {},
            "oportunidades_reais": [],
            "estrategia_principal": {"status": "vazio", "motivo": "ticker não informado"},
            "estrategias_alternativas": [],
            "oportunidade_principal": {"status": "vazio", "motivo": "ticker não informado"},
            "operacao": {},
            "eventos_calendario": {"status": "sem_dados_eventos", "items": [], "proximo_evento": None, "mensagem": "Sem dados de eventos"},
            "impacto_eventos": [],
            "alertas": [],
            "pontos_de_atencao": ["ticker não informado"],
            "monitoramento": [],
            "fontes_utilizadas": {"unified_data": True},
            "campos_indisponiveis": ["ticker", "contexto do ativo", "eventos e calendário"],
        }
    unified = get_unified_data()
    asset_snapshot = _find_market_snapshot(unified, symbol) or _asset_base_snapshot(symbol)
    positions = _find_positions(unified, symbol)
    stored_opportunities = _find_snapshot_opportunities(unified, symbol)
    opportunities = stored_opportunities or build_real_candidates_for_asset(symbol)
    healthbox = snapshot_to_healthbox(asset_snapshot)
    bulkowski = analyze_pattern_for_asset(asset_snapshot)
    thesis = build_graphical_thesis(asset_snapshot, healthbox, bulkowski)
    preferred_strategy = (thesis.get("top_3_strategies") or [None])[0]
    alternative_strategies = (thesis.get("top_3_strategies") or [])[1:]
    matched_opportunity = _match_preferred_opportunity(preferred_strategy, opportunities)
    monitoring = _build_position_monitoring(asset_snapshot, healthbox, bulkowski, positions)
    calendar = _build_calendar(symbol, stored_opportunities)
    alerts = _build_alerts(thesis, preferred_strategy, matched_opportunity, monitoring)
    unavailable = _collect_unavailable_fields(
        asset_snapshot,
        healthbox,
        thesis,
        preferred_strategy,
        matched_opportunity,
        calendar,
    )

    return {
        "ticker": symbol,
        "modo_atual": "monitoramento" if positions else "análise",
        "contexto_ativo": asset_snapshot,
        "healthbox": {
            **healthbox,
            "saude": healthbox.get("status_geral", "indisponível"),
            "tendencia": healthbox.get("tendencia", "indisponível"),
            "forca": "Indisponível",
            "volatilidade": _first_non_empty(
                healthbox.get("atr_classificacao"),
                healthbox.get("volatilidade_implicita"),
                "Indisponível",
            ),
            "liquidez": _first_non_empty(
                (matched_opportunity or {}).get("liquidez"),
                asset_snapshot.get("volume"),
                "Indisponível",
            ),
        },
        "diagnostico_grafico": {
            "bulkowski": bulkowski,
            "thesis": {
                "status": thesis.get("status"),
                "direcao_tese": thesis.get("direcao_tese"),
                "market_regime": thesis.get("market_regime"),
                "gatilho_confirmacao": thesis.get("gatilho_confirmacao"),
                "distancia_ate_gatilho": thesis.get("distancia_ate_gatilho"),
                "hard_technical_blockers": thesis.get("hard_technical_blockers", []),
                "soft_technical_warnings": thesis.get("soft_technical_warnings", []),
                "missing_confirmations": thesis.get("missing_confirmations", []),
                "what_needs_to_happen": thesis.get("what_needs_to_happen", []),
                "motivo_status": thesis.get("motivo_status"),
            },
        },
        "tese_grafica": thesis,
        "oportunidades_reais": opportunities,
        "estrategia_principal": preferred_strategy
        or {
            "status": "indisponível",
            "motivo": "screener sem estratégia priorizada",
        },
        "estrategias_alternativas": alternative_strategies,
        "oportunidade_principal": matched_opportunity
        or {
            "status": "vazio",
            "motivo": "nenhuma oportunidade real disponível para o ticker",
        },
        "operacao": _build_operation_values(thesis, preferred_strategy, matched_opportunity),
        "eventos_calendario": calendar,
        "impacto_eventos": [item["impacto_operacional"] for item in calendar.get("items", [])],
        "alertas": alerts["items"],
        "pontos_de_atencao": alerts["pontos_de_atencao"],
        "monitoramento": monitoring,
        "fontes_utilizadas": {
            "unified_data": True,
            "market_snapshot_source": asset_snapshot.get("fonte"),
            "real_opportunities_source": (
                opportunities[0].get("fonte") if opportunities else "indisponível"
            ),
            "positions_source": "data/positions.json" if positions else "vazio",
        },
        "campos_indisponiveis": unavailable,
    }
