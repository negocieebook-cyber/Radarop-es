"""Persistência JSON local para registros da versão MOCK / EXEMPLO."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
POSITIONS_PATH = DATA_DIR / "positions.json"
HISTORY_PATH = DATA_DIR / "history.json"


def load_json(path: str | Path, default: Any) -> Any:
    file_path = Path(path)
    try:
        if not file_path.exists() or file_path.stat().st_size == 0:
            return default
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def save_json(path: str | Path, data: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_path.replace(file_path)


def load_positions() -> list[dict[str, Any]]:
    data = load_json(POSITIONS_PATH, [])
    return data if isinstance(data, list) else []


def save_positions(positions: list[dict[str, Any]]) -> None:
    save_json(POSITIONS_PATH, positions)


def add_position(position: dict[str, Any]) -> bool:
    positions = load_positions()
    watchlist_item_id = position.get("watchlist_item_id")
    if watchlist_item_id and any(
        str(item.get("watchlist_item_id")) == str(watchlist_item_id) for item in positions
    ):
        return False
    positions.append(position)
    save_positions(positions)
    return True


def load_history() -> list[dict[str, Any]]:
    data = load_json(HISTORY_PATH, [])
    return data if isinstance(data, list) else []


def save_history(history: list[dict[str, Any]]) -> None:
    save_json(HISTORY_PATH, history)


def add_history_event(event: dict[str, Any]) -> None:
    history = load_history()
    history.append(event)
    save_history(history)
