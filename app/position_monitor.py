"""Monitor de posições e alertas de saída, sem ordens ou coleta de mercado."""

from __future__ import annotations

from typing import Any

from app.data_quality import is_missing


MOCK_TYPE = "MOCK / EXEMPLO"
UNAVAILABLE_REASON = "inconclusivo por falta de dados"
SUPPORTED_STRATEGIES = {
    "call_debit_spread",
    "put_debit_spread",
    "bull_put_spread",
    "bear_call_spread",
    "covered_call",
    "long_call",
    "long_put",
}
BULLISH_STRATEGIES = {"call_debit_spread", "bull_put_spread", "covered_call", "long_call"}
BEARISH_STRATEGIES = {"put_debit_spread", "bear_call_spread", "long_put"}
OPENING_ORIGIN = "opening_watchlist"
OPTION_MARK_UNAVAILABLE = "sem preço intraday da estrutura"


def _number(value: Any) -> float | None:
    if is_missing(value) or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _result(status: str, severity: str, reason: str, details: Any, source: str = "mock interno") -> dict[str, Any]:
    return {
        "status": status,
        "severity": severity,
        "reason": reason,
        "details": details,
        "tipo_dado": MOCK_TYPE,
        "fonte": source,
    }


def calculate_position_pnl(position: dict[str, Any], current_mark: Any) -> dict[str, Any]:
    entry = _number(position.get("preco_real_entrada"))
    quantity = _number(position.get("quantidade"))
    mark = _number(current_mark)
    missing = []
    if entry is None:
        missing.append("preco_real_entrada")
    if quantity is None:
        missing.append("quantidade")
    if mark is None:
        missing.append("current_mark")
    if missing:
        return {"calculated": False, "pnl_per_unit": None, "pnl_total": None, "pnl_percent": None, "missing_fields": missing, "reason": "não calculado por falta de dados"}
    pnl_unit = mark - entry
    return {
        "calculated": True,
        "pnl_per_unit": round(pnl_unit, 4),
        "pnl_total": round(pnl_unit * quantity, 2),
        "pnl_percent": round((pnl_unit / entry) * 100, 2) if entry != 0 else None,
        "missing_fields": [],
        "reason": "calculado sobre marcação MOCK / EXEMPLO",
    }


def _opening_option_pnl() -> dict[str, Any]:
    return {
        "calculated": False,
        "pnl_per_unit": None,
        "pnl_total": None,
        "pnl_percent": None,
        "missing_fields": ["preco_intraday_estrutura"],
        "reason": OPTION_MARK_UNAVAILABLE,
        "eod_used_as_current_mark": False,
    }


def is_opening_watchlist_position(position: dict[str, Any]) -> bool:
    return position.get("origem") == OPENING_ORIGIN and position.get("data_frequency") == "EOD"


def build_opening_position_status(
    position: dict[str, Any], context: dict[str, Any] | None
) -> dict[str, Any]:
    """Monitora a tese pelo ativo real sem transformar EOD em marca intraday da opção."""
    pnl = _opening_option_pnl()
    capture = {
        "calculated": False, "capture_ratio": None, "capture_percent": None,
        "missing_fields": ["preco_intraday_estrutura"], "reason": OPTION_MARK_UNAVAILABLE,
    }
    base = {
        "pnl": pnl,
        "gain_capture": capture,
        "option_pnl_label": "P/L da opção: indisponível",
        "option_pnl_reason": OPTION_MARK_UNAVAILABLE,
        "eod_used_as_current_mark": False,
        "invalidation_rules": list(position.get("invalidation_rules") or []),
        "confirmation_rules": list(position.get("confirmation_rules") or []),
        "tipo_dado": (context or {}).get("tipo_dado") or position.get("tipo_dado") or "DADOS REAIS EOD / EXPERIMENTAL",
        "fonte": (context or {}).get("fonte") or position.get("fonte") or "indisponível",
    }
    snapshot = (context or {}).get("asset_snapshot") or {}
    if not context or not snapshot:
        return {**_result(UNAVAILABLE_REASON, "cinza", "snapshot real do ativo ausente", {"missing_fields": ["market_snapshot"]}, base["fonte"]), **base, "pnl": pnl, "gain_capture": capture, "alerts": []}
    if snapshot.get("status_dado") == "erro" or _number(snapshot.get("preco_atual")) is None:
        return {**_result(UNAVAILABLE_REASON, "cinza", "snapshot de mercado indisponível ou sem preço atual do ativo", {"snapshot_status": snapshot.get("status_dado"), "missing_fields": ["preco_atual"]}, base["fonte"]), **base, "pnl": pnl, "gain_capture": capture, "alerts": []}

    graph = graph_invalidation_status(position, snapshot, context.get("healthbox"), context.get("bulkowski"))
    triggered_rules = list(context.get("triggered_invalidation_rules") or [])
    if graph["status"] == "tese invalidada" or triggered_rules:
        reason = graph["reason"] if graph["status"] == "tese invalidada" else "regra de invalidação acionada"
        details = {**graph.get("details", {}), "triggered_invalidation_rules": triggered_rules}
        alert = _result("tese invalidada", "vermelho", reason, details, base["fonte"])
        return {**alert, **base, "status": alert["status"], "severity": alert["severity"], "reason": alert["reason"], "details": alert["details"], "pnl": pnl, "gain_capture": capture, "alerts": [alert]}

    expiry = days_to_expiration_status((context or {}).get("vencimento_dias", position.get("vencimento_dias")))
    if expiry["status"] == "vencimento próximo":
        alert = _result("vencimento próximo", expiry["severity"], expiry["reason"], expiry["details"], base["fonte"])
        return {**alert, **base, "status": alert["status"], "severity": alert["severity"], "reason": alert["reason"], "details": alert["details"], "pnl": pnl, "gain_capture": capture, "alerts": [alert]}

    healthbox = context.get("healthbox") or {}
    confirmation = str(healthbox.get("confirmation", healthbox.get("confirmacao", ""))).lower()
    rvol = _number(healthbox.get("rvol"))
    if not confirmation or "indisponível" in confirmation or "indisponivel" in confirmation:
        alert = _result(UNAVAILABLE_REASON, "cinza", "Healthbox real insuficiente para avaliar a tese", {"healthbox": confirmation or "ausente"}, base["fonte"])
        return {**alert, **base, "status": alert["status"], "severity": alert["severity"], "reason": alert["reason"], "details": alert["details"], "pnl": pnl, "gain_capture": capture, "alerts": [alert]}
    if confirmation in {"não confirma", "nao confirma", "atenção", "atencao", "neutro", "neutral"} or (rvol is not None and rvol < 1):
        reasons = []
        if confirmation:
            reasons.append(f"Healthbox: {confirmation}")
        if rvol is not None and rvol < 1:
            reasons.append("rVol baixo")
        alert = _result("atenção", "amarelo", "; ".join(reasons) or "Healthbox neutro", {"healthbox": confirmation or "indisponível", "rvol": rvol}, base["fonte"])
        return {**alert, **base, "status": alert["status"], "severity": alert["severity"], "reason": alert["reason"], "details": alert["details"], "pnl": pnl, "gain_capture": capture, "alerts": [alert]}

    alert = _result("manter em acompanhamento", "verde", "tese não invalidada pelo snapshot real disponível", {"snapshot_status": snapshot.get("status_dado"), "coleta": snapshot.get("coleta")}, base["fonte"])
    return {**alert, **base, "status": alert["status"], "severity": alert["severity"], "reason": alert["reason"], "details": alert["details"], "pnl": pnl, "gain_capture": capture, "alerts": [alert]}


def _maximum_per_unit(position: dict[str, Any], field: str) -> float | None:
    explicit = _number(position.get(f"{field}_por_unidade"))
    if explicit is not None:
        return explicit
    value = _number(position.get(field))
    quantity = _number(position.get("quantidade"))
    if value is None:
        return None
    if position.get(f"{field}_escopo") == "lote" or position.get("valores_maximos_escopo") == "lote":
        return value / quantity if quantity not in (None, 0) else None
    return value


def calculate_gain_capture(position: dict[str, Any], current_mark: Any) -> dict[str, Any]:
    pnl = calculate_position_pnl(position, current_mark)
    maximum = _maximum_per_unit(position, "ganho_maximo")
    missing = list(pnl["missing_fields"])
    if maximum is None:
        missing.append("ganho_maximo_por_unidade")
    if missing or not pnl["calculated"]:
        return {"calculated": False, "capture_ratio": None, "capture_percent": None, "missing_fields": list(dict.fromkeys(missing)), "reason": "não calculado por falta de dados"}
    if maximum <= 0:
        return {"calculated": False, "capture_ratio": None, "capture_percent": None, "missing_fields": [], "reason": "ganho máximo deve ser maior que zero"}
    ratio = pnl["pnl_per_unit"] / maximum
    return {"calculated": True, "capture_ratio": round(ratio, 4), "capture_percent": round(ratio * 100, 2), "missing_fields": [], "reason": "captura aproximada calculada sobre dados MOCK / EXEMPLO"}


def days_to_expiration_status(vencimento_dias: Any) -> dict[str, Any]:
    days = _number(vencimento_dias)
    if days is None:
        return _result(UNAVAILABLE_REASON, "cinza", "dias até o vencimento ausentes", {"missing_fields": ["vencimento_dias"]})
    if days <= 5:
        return _result("vencimento próximo", "vermelho", "faltam 5 dias ou menos", {"vencimento_dias": days})
    if days <= 10:
        return _result("vencimento próximo", "amarelo", "faltam 10 dias ou menos", {"vencimento_dias": days})
    return _result("manter", "verde", "vencimento ainda confortável", {"vencimento_dias": days})


def distance_to_strike_status(position: dict[str, Any], asset_snapshot: dict[str, Any]) -> dict[str, Any]:
    strikes = position.get("strikes") if isinstance(position.get("strikes"), dict) else {}
    sold_strike = _number(position.get("strike_vendido", strikes.get("vendido")))
    price = _number(asset_snapshot.get("preco_atual"))
    missing = []
    if sold_strike is None:
        missing.append("strike_vendido")
    if price is None:
        missing.append("preco_atual")
    if missing:
        return _result(UNAVAILABLE_REASON, "cinza", "distância ao strike não calculada", {"missing_fields": missing})
    distance = ((price - sold_strike) / sold_strike) * 100
    near = abs(distance) <= 2
    return _result("atenção" if near else "manter", "amarelo" if near else "verde", "ativo perto do strike vendido" if near else "ativo longe do strike vendido", {"distance_percent": round(distance, 2), "strike_vendido": sold_strike, "preco_atual": price})


def graph_invalidation_status(
    position: dict[str, Any],
    asset_snapshot: dict[str, Any],
    healthbox: dict[str, Any] | None = None,
    bulkowski: dict[str, Any] | None = None,
) -> dict[str, Any]:
    strategy = position.get("tipo_estrutura") or position.get("strategy_type")
    if strategy not in SUPPORTED_STRATEGIES:
        return _result(UNAVAILABLE_REASON, "cinza", "estratégia não reconhecida", {"strategy": strategy})
    price = _number(asset_snapshot.get("preco_atual"))
    support = _number(asset_snapshot.get("suporte"))
    resistance = _number(asset_snapshot.get("resistencia"))
    if price is None:
        return _result(UNAVAILABLE_REASON, "cinza", "preço atual ausente", {"missing_fields": ["preco_atual"]})
    if strategy in BULLISH_STRATEGIES:
        if support is None:
            return _result(UNAVAILABLE_REASON, "cinza", "suporte ausente para tese altista", {"missing_fields": ["suporte"]})
        if price < support:
            return _result("tese invalidada", "vermelho", "suporte perdido em operação altista", {"preco_atual": price, "suporte": support})
    if strategy in BEARISH_STRATEGIES:
        if resistance is None:
            return _result(UNAVAILABLE_REASON, "cinza", "resistência ausente para tese baixista", {"missing_fields": ["resistencia"]})
        if price > resistance:
            return _result("tese invalidada", "vermelho", "resistência rompida contra operação baixista", {"preco_atual": price, "resistencia": resistance})
    health_confirmation = str((healthbox or {}).get("confirmation", (healthbox or {}).get("confirmacao", ""))).lower()
    if health_confirmation in {"não confirma", "nao confirma"}:
        return _result("atenção", "amarelo", "Healthbox não confirma mais a estratégia", {"healthbox": health_confirmation})
    bulk_status = str((bulkowski or {}).get("status", "")).lower()
    if bulk_status in {"falhado", "tese invalidada"}:
        return _result("tese invalidada", "vermelho", "padrão Bulkowski invalidado", {"bulkowski_status": bulk_status})
    return _result("manter", "verde", "tese gráfica não invalidada pelos dados disponíveis", {})


def current_context(
    asset_snapshot: dict[str, Any] | None = None,
    healthbox: dict[str, Any] | None = None,
    bulkowski: dict[str, Any] | None = None,
    current_mark: Any = None,
    tipo_dado: str = MOCK_TYPE,
    fonte: str = "mock interno",
) -> dict[str, Any]:
    return {"asset_snapshot": asset_snapshot or {}, "healthbox": healthbox or {}, "bulkowski": bulkowski or {}, "current_mark": current_mark, "tipo_dado": tipo_dado, "fonte": fonte}


def evaluate_exit_rules(position: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    strategy = position.get("tipo_estrutura") or position.get("strategy_type")
    source = context.get("fonte") or "mock interno"
    if strategy not in SUPPORTED_STRATEGIES:
        return [_result(UNAVAILABLE_REASON, "cinza", "estratégia não reconhecida", {"strategy": strategy}, source)]
    pnl = calculate_position_pnl(position, context.get("current_mark"))
    capture = calculate_gain_capture(position, context.get("current_mark"))
    expiration_days = context.get("vencimento_dias", position.get("vencimento_dias"))
    expiry = days_to_expiration_status(expiration_days)
    strike = distance_to_strike_status(position, context.get("asset_snapshot", {}))
    graph = graph_invalidation_status(position, context.get("asset_snapshot", {}), context.get("healthbox"), context.get("bulkowski"))
    rules: list[dict[str, Any]] = []

    if graph["status"] == "tese invalidada":
        rules.append(graph)
    max_loss = _maximum_per_unit(position, "perda_maxima")
    if pnl["calculated"] and max_loss is not None and pnl["pnl_per_unit"] <= -abs(max_loss):
        rules.append(_result("sair agora", "vermelho", "perda atual atingiu o limite de risco definido", {"pnl_per_unit": pnl["pnl_per_unit"], "max_loss_per_unit": max_loss}, source))
    if expiry["severity"] == "vermelho" and pnl["calculated"] and pnl["pnl_per_unit"] <= 0:
        rules.append(_result("sair agora", "vermelho", "faltam 5 dias ou menos e a operação não evoluiu", {"vencimento_dias": expiration_days, "pnl_per_unit": pnl["pnl_per_unit"]}, source))
    if capture["calculated"] and capture["capture_ratio"] >= 0.75:
        rules.append(_result("realizar total", "verde", "captura do ganho máximo igual ou superior a 75%", capture, source))
    elif capture["calculated"] and capture["capture_ratio"] >= 0.50:
        rules.append(_result("realizar parcial", "verde", "captura do ganho máximo entre 50% e 75%", capture, source))

    if expiry["severity"] == "amarelo":
        rules.append(expiry)
    if strike["status"] == "atenção":
        rules.append(strike)
    health_confirmation = str(context.get("healthbox", {}).get("confirmation", context.get("healthbox", {}).get("confirmacao", ""))).lower()
    if health_confirmation in {"não confirma", "nao confirma", "atenção"}:
        rules.append(_result("atenção", "amarelo", "Healthbox não confirma plenamente a estratégia", {"healthbox": health_confirmation}, source))
    bulk_status = str(context.get("bulkowski", {}).get("status", "")).lower()
    if bulk_status in {"inconclusivo", "padrão não detectado"}:
        rules.append(_result("atenção", "amarelo", "Bulkowski inconclusivo", {"bulkowski_status": bulk_status}, source))
    if not rules and (not pnl["calculated"] or graph["status"] == UNAVAILABLE_REASON):
        missing = list(pnl["missing_fields"])
        missing.extend(graph.get("details", {}).get("missing_fields", []))
        rules.append(_result(UNAVAILABLE_REASON, "cinza", "dados insuficientes para avaliar saída", {"missing_fields": list(dict.fromkeys(missing))}, source))
    if not rules:
        rules.append(_result("manter", "verde", "nenhuma regra crítica foi acionada", {"pnl": pnl, "capture": capture}, source))
    return rules


def build_position_status(position: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    if is_opening_watchlist_position(position):
        return build_opening_position_status(position, context)
    if not context:
        base = _result(UNAVAILABLE_REASON, "cinza", "contexto de mercado ausente", {"missing_fields": ["current_context"]})
        base.update(pnl=calculate_position_pnl(position, None), gain_capture=calculate_gain_capture(position, None), alerts=[])
        return base
    alerts = evaluate_exit_rules(position, context)
    priority = {"tese invalidada": 8, "sair agora": 7, "realizar total": 6, "realizar parcial": 5, "ajustar": 4, "vencimento próximo": 3, "atenção": 2, "manter": 1, UNAVAILABLE_REASON: 0}
    primary = max(alerts, key=lambda alert: priority.get(alert["status"], 0))
    result = dict(primary)
    result.update(
        pnl=calculate_position_pnl(position, context.get("current_mark")),
        gain_capture=calculate_gain_capture(position, context.get("current_mark")),
        alerts=alerts,
        tipo_dado=context.get("tipo_dado") or MOCK_TYPE,
        fonte=context.get("fonte") or "mock interno",
    )
    return result


def generate_exit_alerts(positions: list[dict[str, Any]], market_context: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    alerts = []
    for position in positions:
        status = build_position_status(position, market_context.get(position.get("ativo")))
        alerts.append({"position_id": position.get("id"), "ativo": position.get("ativo", "indisponível"), "estrategia": position.get("estrategia", "indisponível"), **status})
    return alerts
