from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal


class ProviderNotConfigured(RuntimeError):
    """Raised when a provider is called without the credentials/config it needs."""


class MarketDataProvider(ABC):
    name: str
    requires_api_key: bool = False

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def latest_price(self, symbol: str) -> tuple[date, Decimal]:
        """Return (as_of_date, price). Must raise ProviderNotConfigured instead of guessing."""
