from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ai_usage.domain.models import ProviderAuthState, ProviderID, ProviderSnapshot


class UsageProvider(ABC):
    @property
    @abstractmethod
    def id(self) -> ProviderID: ...

    @property
    @abstractmethod
    def source_description(self) -> str: ...

    @abstractmethod
    def current_auth_state(self) -> ProviderAuthState: ...

    @abstractmethod
    def refresh(self, now: datetime) -> ProviderSnapshot: ...

    @abstractmethod
    def clear_auth(self) -> None: ...
