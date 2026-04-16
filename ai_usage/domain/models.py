from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ProviderID(str, enum.Enum):
    CODEX = "codex"
    CLAUDE = "claude"
    COPILOT = "copilot"

    @property
    def usage_settings_url(self) -> str:
        return {
            ProviderID.CODEX: "https://chatgpt.com/codex/cloud/settings/usage",
            ProviderID.CLAUDE: "https://claude.ai/settings/usage",
            ProviderID.COPILOT: "https://github.com/settings/copilot/features",
        }[self]

    @property
    def icon_resource_name(self) -> str:
        return {
            ProviderID.CODEX: "openai-icon",
            ProviderID.CLAUDE: "claude-icon",
            ProviderID.COPILOT: "copilot-icon",
        }[self]


class UsageMetricKind(str, enum.Enum):
    CODEX_FIVE_HOUR = "codexFiveHour"
    CODEX_WEEKLY = "codexWeekly"
    CODEX_SPARK_FIVE_HOUR = "codexSparkFiveHour"
    CODEX_SPARK_WEEKLY = "codexSparkWeekly"
    CODEX_CREDITS = "codexCredits"
    CLAUDE_FIVE_HOUR = "claudeFiveHour"
    CLAUDE_WEEKLY = "claudeWeekly"
    COPILOT_MONTHLY = "copilotMonthly"

    @property
    def provider(self) -> ProviderID:
        mapping = {
            UsageMetricKind.CODEX_FIVE_HOUR: ProviderID.CODEX,
            UsageMetricKind.CODEX_WEEKLY: ProviderID.CODEX,
            UsageMetricKind.CODEX_SPARK_FIVE_HOUR: ProviderID.CODEX,
            UsageMetricKind.CODEX_SPARK_WEEKLY: ProviderID.CODEX,
            UsageMetricKind.CODEX_CREDITS: ProviderID.CODEX,
            UsageMetricKind.CLAUDE_FIVE_HOUR: ProviderID.CLAUDE,
            UsageMetricKind.CLAUDE_WEEKLY: ProviderID.CLAUDE,
            UsageMetricKind.COPILOT_MONTHLY: ProviderID.COPILOT,
        }
        return mapping[self]

    @property
    def participates_in_menu_bar(self) -> bool:
        return self in {
            UsageMetricKind.CODEX_FIVE_HOUR,
            UsageMetricKind.CODEX_WEEKLY,
            UsageMetricKind.CLAUDE_FIVE_HOUR,
            UsageMetricKind.CLAUDE_WEEKLY,
            UsageMetricKind.COPILOT_MONTHLY,
        }

    @property
    def supports_ahead_notifications(self) -> bool:
        return self in {
            UsageMetricKind.CODEX_FIVE_HOUR,
            UsageMetricKind.CODEX_WEEKLY,
            UsageMetricKind.CLAUDE_FIVE_HOUR,
            UsageMetricKind.CLAUDE_WEEKLY,
            UsageMetricKind.COPILOT_MONTHLY,
        }

    @property
    def supports_behind_notifications(self) -> bool:
        return self in {
            UsageMetricKind.CODEX_WEEKLY,
            UsageMetricKind.CLAUDE_WEEKLY,
            UsageMetricKind.COPILOT_MONTHLY,
        }


class MetricUnit(str, enum.Enum):
    PERCENTAGE = "percentage"
    REQUESTS = "requests"
    CREDITS = "credits"


class ProviderAuthState(str, enum.Enum):
    SIGNED_OUT = "signedOut"
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"


class ProviderFetchState(str, enum.Enum):
    OK = "ok"
    MISSING_AUTH = "missingAuth"
    FAILED = "failed"


class UsageAlertDirection(str, enum.Enum):
    AHEAD = "ahead"
    BEHIND = "behind"


@dataclass
class UsageMetric:
    kind: UsageMetricKind
    remaining_fraction: Optional[float] = None
    remaining_value: Optional[float] = None
    total_value: Optional[float] = None
    unit: MetricUnit = MetricUnit.PERCENTAGE
    reset_at_utc: Optional[datetime] = None
    last_updated_at_utc: Optional[datetime] = None
    detail_text: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "remaining_fraction": self.remaining_fraction,
            "remaining_value": self.remaining_value,
            "total_value": self.total_value,
            "unit": self.unit.value,
            "reset_at_utc": self.reset_at_utc.isoformat() if self.reset_at_utc else None,
            "last_updated_at_utc": self.last_updated_at_utc.isoformat() if self.last_updated_at_utc else None,
            "detail_text": self.detail_text,
        }

    @classmethod
    def from_dict(cls, d: dict) -> UsageMetric:
        return cls(
            kind=UsageMetricKind(d["kind"]),
            remaining_fraction=d.get("remaining_fraction"),
            remaining_value=d.get("remaining_value"),
            total_value=d.get("total_value"),
            unit=MetricUnit(d.get("unit", "percentage")),
            reset_at_utc=datetime.fromisoformat(d["reset_at_utc"]) if d.get("reset_at_utc") else None,
            last_updated_at_utc=datetime.fromisoformat(d["last_updated_at_utc"]) if d.get("last_updated_at_utc") else None,
            detail_text=d.get("detail_text"),
        )


@dataclass
class ProviderSnapshot:
    provider: ProviderID
    auth_state: ProviderAuthState = ProviderAuthState.SIGNED_OUT
    fetch_state: ProviderFetchState = ProviderFetchState.MISSING_AUTH
    fetched_at_utc: Optional[datetime] = None
    metrics: list[UsageMetric] = field(default_factory=list)
    error_description: Optional[str] = None
    source_description: Optional[str] = None

    def metric(self, kind: UsageMetricKind) -> Optional[UsageMetric]:
        return next((m for m in self.metrics if m.kind == kind), None)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider.value,
            "auth_state": self.auth_state.value,
            "fetch_state": self.fetch_state.value,
            "fetched_at_utc": self.fetched_at_utc.isoformat() if self.fetched_at_utc else None,
            "metrics": [m.to_dict() for m in self.metrics],
            "error_description": self.error_description,
            "source_description": self.source_description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ProviderSnapshot:
        return cls(
            provider=ProviderID(d["provider"]),
            auth_state=ProviderAuthState(d.get("auth_state", "signedOut")),
            fetch_state=ProviderFetchState(d.get("fetch_state", "missingAuth")),
            fetched_at_utc=datetime.fromisoformat(d["fetched_at_utc"]) if d.get("fetched_at_utc") else None,
            metrics=[UsageMetric.from_dict(m) for m in d.get("metrics", [])],
            error_description=d.get("error_description"),
            source_description=d.get("source_description"),
        )


@dataclass
class UsageAlertState:
    direction: UsageAlertDirection
    metric_kind: UsageMetricKind
    last_triggered_at_utc: Optional[datetime] = None
    last_extreme_delta: float = 0.0
    last_reset_at_utc: Optional[datetime] = None
    is_armed: bool = True

    def to_dict(self) -> dict:
        return {
            "direction": self.direction.value,
            "metric_kind": self.metric_kind.value,
            "last_triggered_at_utc": self.last_triggered_at_utc.isoformat() if self.last_triggered_at_utc else None,
            "last_extreme_delta": self.last_extreme_delta,
            "last_reset_at_utc": self.last_reset_at_utc.isoformat() if self.last_reset_at_utc else None,
            "is_armed": self.is_armed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> UsageAlertState:
        return cls(
            direction=UsageAlertDirection(d["direction"]),
            metric_kind=UsageMetricKind(d["metric_kind"]),
            last_triggered_at_utc=datetime.fromisoformat(d["last_triggered_at_utc"]) if d.get("last_triggered_at_utc") else None,
            last_extreme_delta=d.get("last_extreme_delta", 0.0),
            last_reset_at_utc=datetime.fromisoformat(d["last_reset_at_utc"]) if d.get("last_reset_at_utc") else None,
            is_armed=d.get("is_armed", True),
        )


@dataclass
class MenuBarSummaryItem:
    provider: ProviderID
    remaining_fraction: Optional[float] = None


class AppLanguage(str, enum.Enum):
    ENGLISH_US = "englishUS"
    POLISH = "polish"


class CodexMenuBarMetric(str, enum.Enum):
    WEEKLY = "weekly"
    FIVE_HOUR = "fiveHour"

    @property
    def usage_metric_kind(self) -> UsageMetricKind:
        return {
            CodexMenuBarMetric.WEEKLY: UsageMetricKind.CODEX_WEEKLY,
            CodexMenuBarMetric.FIVE_HOUR: UsageMetricKind.CODEX_FIVE_HOUR,
        }[self]


class ClaudeMenuBarMetric(str, enum.Enum):
    WEEKLY = "weekly"
    FIVE_HOUR = "fiveHour"

    @property
    def usage_metric_kind(self) -> UsageMetricKind:
        return {
            ClaudeMenuBarMetric.WEEKLY: UsageMetricKind.CLAUDE_WEEKLY,
            ClaudeMenuBarMetric.FIVE_HOUR: UsageMetricKind.CLAUDE_FIVE_HOUR,
        }[self]


@dataclass
class DisplayPreferences:
    hidden_providers: set[ProviderID] = field(default_factory=set)
    hidden_panel_providers: set[ProviderID] = field(default_factory=set)
    show_ahead_notifications: bool = True
    show_behind_notifications: bool = True
    show_codex_reset_notifications: bool = True
    show_claude_reset_notifications: bool = True
    show_codex_spark_usage: bool = False
    refresh_interval_minutes: int = 5
    language: AppLanguage = AppLanguage.ENGLISH_US
    codex_menu_bar_metric: CodexMenuBarMetric = CodexMenuBarMetric.WEEKLY
    claude_menu_bar_metric: ClaudeMenuBarMetric = ClaudeMenuBarMetric.WEEKLY

    @property
    def visible_providers(self) -> set[ProviderID]:
        return {p for p in ProviderID if p not in self.hidden_providers}

    @visible_providers.setter
    def visible_providers(self, value: set[ProviderID]):
        self.hidden_providers = {p for p in ProviderID if p not in value}

    @property
    def visible_panel_providers(self) -> set[ProviderID]:
        return {p for p in ProviderID if p not in self.hidden_panel_providers}

    @visible_panel_providers.setter
    def visible_panel_providers(self, value: set[ProviderID]):
        self.hidden_panel_providers = {p for p in ProviderID if p not in value}

    def should_reschedule_refresh(self, previous: DisplayPreferences) -> bool:
        return self.refresh_interval_minutes != previous.refresh_interval_minutes

    def to_dict(self) -> dict:
        return {
            "hidden_providers": [p.value for p in self.hidden_providers],
            "hidden_panel_providers": [p.value for p in self.hidden_panel_providers],
            "show_ahead_notifications": self.show_ahead_notifications,
            "show_behind_notifications": self.show_behind_notifications,
            "show_codex_reset_notifications": self.show_codex_reset_notifications,
            "show_claude_reset_notifications": self.show_claude_reset_notifications,
            "show_codex_spark_usage": self.show_codex_spark_usage,
            "refresh_interval_minutes": self.refresh_interval_minutes,
            "language": self.language.value,
            "codex_menu_bar_metric": self.codex_menu_bar_metric.value,
            "claude_menu_bar_metric": self.claude_menu_bar_metric.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DisplayPreferences:
        return cls(
            hidden_providers={ProviderID(p) for p in d.get("hidden_providers", [])},
            hidden_panel_providers={ProviderID(p) for p in d.get("hidden_panel_providers", [])},
            show_ahead_notifications=d.get("show_ahead_notifications", True),
            show_behind_notifications=d.get("show_behind_notifications", True),
            show_codex_reset_notifications=d.get("show_codex_reset_notifications", True),
            show_claude_reset_notifications=d.get("show_claude_reset_notifications", True),
            show_codex_spark_usage=d.get("show_codex_spark_usage", False),
            refresh_interval_minutes=d.get("refresh_interval_minutes", 5),
            language=AppLanguage(d.get("language", "englishUS")),
            codex_menu_bar_metric=CodexMenuBarMetric(d.get("codex_menu_bar_metric", "weekly")),
            claude_menu_bar_metric=ClaudeMenuBarMetric(d.get("claude_menu_bar_metric", "weekly")),
        )
