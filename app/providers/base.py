"""Contrato base para provedores de dados."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    @abstractmethod
    def get_provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_quotes(self, tickers: list[str]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_historical(self, tickers: list[str], range: str = "3mo", interval: str = "1d") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_provider_status(self) -> dict[str, Any]:
        raise NotImplementedError
