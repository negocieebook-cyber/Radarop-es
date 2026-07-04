"""Watchlist persistente de teses gráficas, sem execução automática."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.healthbox_engine import build_healthbox, healthbox_score
from app.storage import load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRAPHICAL_WATCHLIST_PATH = PROJECT_ROOT / "data" / "runtime" / "graphical_watchlist.json"
ELIGIBLE_STATUSES = {
    "compra_operavel",
    "interesse_compra",
    "venda_operavel",
    "interesse_venda",
}
WATCHLIST_STATUSES = (
    "aguardando gatilho",
    "perto do gatilho",
    "gatilho acionado",
    "invalidada",
    "inconclusiva por falta de dados",
)
MANUAL_NOTICE = (
    "tese gráfica não é ordem; validar preço, liquidez e opção antes de qualquer entrada."
)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_graphical_watchlist() -> list[dict[str, Any]]:
    data = load_json(GRAPHICAL_WATCHLIST_PATH, [])
    return data if isinstance(data, list) else []


def save_graphical_watchlist(items: list[dict[str, Any]]) -> None:
    save_json(GRAPHICAL_WATCHLIST_PATH, items)


def _thesis_id(thesis: dict[str, Any]) -> str:
    existing = thesis.get("thesis_id")
    if existing:
        return str(existing)
    identity = "|".join(
        str(value if value is not None else "")
        for value in (
            thesis.get("ativo"),
            thesis.get("direcao_tese") or thesis.get("direcao_provavel"),
            thesis.get("gatilho_confirmacao"),
            thesis.get("invalidacao"),
            thesis.get("alvo"),
        )
    )
    return sha256(identity.encode("utf-8")).hexdigest()[:20]


def _trigger_price(thesis: dict[str, Any]) -> float | None:
    direction = thesis.get("direcao_provavel") or thesis.get("direcao_tese")
    if direction == "altista":
        return _number(thesis.get("resistencia"))
    if direction == "baixista":
        return _number(thesis.get("suporte"))
    return _number(thesis.get("gatilho_preco"))


def build_graphical_watchlist_item(thesis: dict[str, Any]) -> dict[str, Any]:
    thesis_id = _thesis_id(thesis)
    direction = thesis.get("direcao_provavel") or thesis.get("direcao_tese")
    return {
        "id": f"graphical-{thesis_id}",
        "thesis_id": thesis_id,
        "ativo": thesis.get("ativo"),
        "status_original": thesis.get("status"),
        "near_setup_score": thesis.get("near_setup_score"),
        "direcao_provavel": direction,
        "preco_referencia": thesis.get("preco_atual"),
        "regiao_entrada": thesis.get("regiao_entrada_grafica"),
        "gatilho_confirmacao": thesis.get("gatilho_confirmacao"),
        "gatilho_preco": _trigger_price(thesis),
        "invalidacao": thesis.get("invalidacao"),
        "alvo": thesis.get("alvo"),
        "relacao_alvo_risco": thesis.get("relacao_alvo_risco"),
        "distancia_ate_gatilho": thesis.get("distancia_ate_gatilho"),
        "healthbox": deepcopy(thesis.get("healthbox_usado")),
        "bulkowski": deepcopy(thesis.get("bulkowski_usado")),
        "estrutura_opcao_sugerida": thesis.get("tipo_estrutura_sugerida"),
        "delta_alvo": thesis.get("delta_alvo"),
        "vencimento_ideal": thesis.get("vencimento_ideal"),
        "cadeia_opcoes_status": thesis.get("cadeia_opcoes_status"),
        "what_needs_to_happen": list(thesis.get("what_needs_to_happen") or []),
        "primary_reason": thesis.get("primary_reason"),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status_atual": "aguardando gatilho",
        "aviso": MANUAL_NOTICE,
    }


def item_exists(thesis_id: str) -> bool:
    return any(
        str(item.get("thesis_id")) == str(thesis_id)
        for item in load_graphical_watchlist()
    )


def add_to_graphical_watchlist(thesis: dict[str, Any]) -> dict[str, Any]:
    item = build_graphical_watchlist_item(thesis)
    is_near_setup = thesis.get("near_setup_score") is not None
    if thesis.get("status") not in ELIGIBLE_STATUSES and not is_near_setup:
        return {"added": False, "item": item, "reason": "status não elegível"}
    if item_exists(item["thesis_id"]):
        return {"added": False, "item": item, "reason": "duplicado"}
    items = load_graphical_watchlist()
    items.append(item)
    save_graphical_watchlist(items)
    return {"added": True, "item": item, "reason": None}


def remove_from_graphical_watchlist(item_id: str) -> bool:
    items = load_graphical_watchlist()
    filtered = [item for item in items if str(item.get("id")) != str(item_id)]
    if len(filtered) == len(items):
        return False
    save_graphical_watchlist(filtered)
    return True


def evaluate_graphical_watchlist_item(
    item: dict[str, Any], market_snapshot: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Reavalia níveis gráficos sem presumir entrada ou disponibilidade de opção."""
    evaluated = deepcopy(item)
    if not market_snapshot or market_snapshot.get("status_dado") == "erro":
        evaluated["status_atual"] = "inconclusiva por falta de dados"
        evaluated["evaluation_reason"] = "Snapshot de mercado ausente ou com erro."
        return evaluated

    price = _number(market_snapshot.get("preco_atual"))
    trigger = _number(evaluated.get("gatilho_preco"))
    invalidation = _number(evaluated.get("invalidacao"))
    direction = evaluated.get("direcao_provavel")
    if price is None or trigger is None or invalidation is None or direction not in {"altista", "baixista"}:
        evaluated["status_atual"] = "inconclusiva por falta de dados"
        evaluated["evaluation_reason"] = "Preço, gatilho, invalidação ou direção não disponível."
        return evaluated

    if (direction == "altista" and price < invalidation) or (
        direction == "baixista" and price > invalidation
    ):
        evaluated["status_atual"] = "invalidada"
        evaluated["evaluation_reason"] = "Preço perdeu o nível de invalidação registrado."
        return evaluated

    current_healthbox = build_healthbox(market_snapshot)
    current_health_score = healthbox_score(current_healthbox).get("score")
    healthbox_invalidates = isinstance(current_health_score, (int, float)) and current_health_score < 45
    triggered = (direction == "altista" and price >= trigger) or (
        direction == "baixista" and price <= trigger
    )
    distance_percent = abs(price - trigger) / price * 100 if price else None
    evaluated["preco_atual_avaliado"] = price
    evaluated["distancia_percentual_ate_gatilho"] = (
        round(distance_percent, 4) if distance_percent is not None else None
    )
    evaluated["healthbox_atual"] = current_healthbox

    if triggered and not healthbox_invalidates:
        evaluated["status_atual"] = "gatilho acionado"
        evaluated["evaluation_reason"] = "Preço atingiu o gatilho e o Healthbox não invalidou a tese."
    elif distance_percent is not None and distance_percent <= 2:
        evaluated["status_atual"] = "perto do gatilho"
        evaluated["evaluation_reason"] = "Preço está a até 2% do gatilho registrado."
    else:
        evaluated["status_atual"] = "aguardando gatilho"
        evaluated["evaluation_reason"] = (
            "Gatilho ainda não confirmado."
            if not healthbox_invalidates
            else "Gatilho sem confirmação porque o Healthbox atual está abaixo do mínimo."
        )
    return evaluated


def summarize_graphical_watchlist(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(item.get("status_atual") for item in items)
    return {
        "total": len(items),
        **{status: counts[status] for status in WATCHLIST_STATUSES},
    }
