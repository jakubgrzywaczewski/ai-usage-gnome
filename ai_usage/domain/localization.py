from __future__ import annotations

import enum
from typing import Any

from ai_usage.domain.models import (
    AppLanguage,
    ClaudeMenuBarMetric,
    CodexMenuBarMetric,
    ProviderID,
    UsageMetricKind,
)


class L10nKey(str, enum.Enum):
    MENU_BAR_APP_NAME = "menuBarAppName"
    NOT_CONFIGURED = "notConfigured"
    UNAVAILABLE = "unavailable"
    NO_USAGE_DATA = "noUsageData"
    USAGE_PANEL_TITLE = "usagePanelTitle"
    SETTINGS_TITLE = "settingsTitle"
    LAST_UPDATE = "lastUpdate"
    REFRESH_NOW = "refreshNow"
    OPEN_SETTINGS = "openSettings"
    STALE_DATA = "staleData"
    AUTHENTICATION_REQUIRED = "authenticationRequired"
    AUTHENTICATE_IN_SETTINGS = "authenticateInSettings"
    GENERAL_SECTION = "generalSection"
    APPEARANCE_SECTION = "appearanceSection"
    MENU_BAR_SECTION = "menuBarSection"
    MAIN_PANEL_SECTION = "mainPanelSection"
    NOTIFICATIONS_SECTION = "notificationsSection"
    USAGE_NOTIFICATIONS_SECTION = "usageNotificationsSection"
    EARLY_RESET_NOTIFICATIONS_SECTION = "earlyResetNotificationsSection"
    LANGUAGE = "language"
    REFRESH_INTERVAL = "refreshInterval"
    CODEX_MENU_BAR_METRIC = "codexMenuBarMetric"
    CLAUDE_MENU_BAR_METRIC = "claudeMenuBarMetric"
    SHOW_CODEX_SPARK_USAGE = "showCodexSparkUsage"
    MENU_BAR_METRIC_WEEKLY = "menuBarMetricWeekly"
    MENU_BAR_METRIC_FIVE_HOUR = "menuBarMetricFiveHour"
    MENU_BAR_ICONS = "menuBarIcons"
    USAGE_PANEL_PROVIDERS = "usagePanelProviders"
    NOTIFICATIONS_AHEAD = "notificationsAhead"
    NOTIFICATIONS_BEHIND = "notificationsBehind"
    NOTIFICATIONS_CODEX_RESET = "notificationsCodexReset"
    NOTIFICATIONS_CLAUDE_RESET = "notificationsClaudeReset"
    PROVIDER_CODEX = "providerCodex"
    PROVIDER_CLAUDE = "providerClaude"
    PROVIDER_COPILOT = "providerCopilot"
    ENABLED = "enabled"
    PERCENTAGE_SHOWN = "percentageShown"
    USAGE_LIMIT_FIVE_HOUR_CODEX_SPARK = "usageLimitFiveHourCodexSpark"
    USAGE_LIMIT_WEEKLY_CODEX_SPARK = "usageLimitWeeklyCodexSpark"
    USAGE_LIMIT_FIVE_HOUR = "usageLimitFiveHour"
    USAGE_LIMIT_WEEKLY = "usageLimitWeekly"
    USAGE_LIMIT_SEVEN_DAY = "usageLimitSevenDay"
    USAGE_LIMIT_MONTHLY = "usageLimitMonthly"
    USAGE_METRIC_CREDITS = "usageMetricCredits"
    RESET_AT = "resetAt"
    SAVE = "save"
    CANCEL = "cancel"
    SIGN_IN_TO_CODEX = "signInToCodex"
    SIGN_IN_TO_GITHUB_COPILOT = "signInToGitHubCopilot"
    COPILOT_TOKEN = "copilotToken"
    FETCH_FAILED = "fetchFailed"
    SIGNED_OUT = "signedOut"
    CONNECTED = "connected"
    ACCOUNTS_SECTION = "accountsSection"
    CODEX_SESSION_HELP = "codexSessionHelp"
    CODEX_CLI_CONNECTED = "codexCliConnected"
    CLAUDE_SESSION_HELP = "claudeSessionHelp"
    CLAUDE_CLI_CONNECTED = "claudeCliConnected"
    COPILOT_PAT_HELP = "copilotPatHelp"
    COPILOT_DEVICE_FLOW_WAITING = "copilotDeviceFlowWaiting"
    COPILOT_DEVICE_FLOW_CONNECTED = "copilotDeviceFlowConnected"
    SAVE_AND_REFRESH = "saveAndRefresh"
    RELOAD = "reload"
    TOKEN_SAVED = "tokenSaved"
    SETTINGS_TAB_ACCOUNTS = "settingsTabAccounts"
    SETTINGS_TAB_DISPLAY = "settingsTabDisplay"
    SETTINGS_TAB_NOTIFICATIONS = "settingsTabNotifications"
    SETTINGS_TAB_LOGS = "settingsTabLogs"
    SETTINGS_TAB_ABOUT = "settingsTabAbout"
    PROVIDER_STATUS_OK = "providerStatusOk"
    PROVIDER_STATUS_NEEDS_ATTENTION = "providerStatusNeedsAttention"
    COPILOT_PLAN_HELP = "copilotPlanHelp"
    COPILOT_CONNECTED_HELP = "copilotConnectedHelp"
    NOTIFICATIONS_AHEAD_DESCRIPTION = "notificationsAheadDescription"
    NOTIFICATIONS_BEHIND_DESCRIPTION = "notificationsBehindDescription"
    NOTIFICATIONS_CODEX_RESET_DESCRIPTION = "notificationsCodexResetDescription"
    NOTIFICATIONS_CLAUDE_RESET_DESCRIPTION = "notificationsClaudeResetDescription"
    NOTIFICATION_TITLE_AHEAD_FORMAT = "notificationTitleAheadFormat"
    NOTIFICATION_TITLE_BEHIND_FORMAT = "notificationTitleBehindFormat"
    NOTIFICATION_BODY_SCHEDULE_FORMAT = "notificationBodyScheduleFormat"
    NOTIFICATION_TITLE_CODEX_RESET = "notificationTitleCodexReset"
    NOTIFICATION_TITLE_CLAUDE_RESET = "notificationTitleClaudeReset"
    NOTIFICATION_BODY_RESET_FORMAT = "notificationBodyResetFormat"
    NOTIFICATION_METRIC_FIVE_HOUR_FORMAT = "notificationMetricFiveHourFormat"
    NOTIFICATION_METRIC_WEEKLY_FORMAT = "notificationMetricWeeklyFormat"
    NOTIFICATION_METRIC_MONTHLY_FORMAT = "notificationMetricMonthlyFormat"
    NOTIFICATION_METRIC_CREDITS_FORMAT = "notificationMetricCreditsFormat"
    COPY_LOGS = "copyLogs"
    CLEAR_LOGS = "clearLogs"
    NO_LOGS = "noLogs"
    LOGS_COPIED = "logsCopied"
    APP_VERSION = "appVersion"
    LEGAL_SECTION = "legalSection"
    LOGO_DISCLAIMER = "logoDisclaimer"
    QUIT_APP = "quitApp"
    MENU_ACTION_REFRESH = "menuActionRefresh"
    MENU_ACTION_SETTINGS = "menuActionSettings"
    SIGN_OUT = "signOut"


_ENGLISH: dict[L10nKey, str] = {
    L10nKey.MENU_BAR_APP_NAME: "AI Usage",
    L10nKey.NOT_CONFIGURED: "Not configured",
    L10nKey.UNAVAILABLE: "Unavailable",
    L10nKey.NO_USAGE_DATA: "No data for this plan",
    L10nKey.USAGE_PANEL_TITLE: "AI Usage",
    L10nKey.SETTINGS_TITLE: "Settings",
    L10nKey.LAST_UPDATE: "Last update",
    L10nKey.REFRESH_NOW: "Refresh now",
    L10nKey.OPEN_SETTINGS: "Settings",
    L10nKey.STALE_DATA: "Stale data",
    L10nKey.AUTHENTICATION_REQUIRED: "Authentication required",
    L10nKey.AUTHENTICATE_IN_SETTINGS: "Open Settings to authenticate providers.",
    L10nKey.GENERAL_SECTION: "General",
    L10nKey.APPEARANCE_SECTION: "Appearance",
    L10nKey.MENU_BAR_SECTION: "Tray icon",
    L10nKey.MAIN_PANEL_SECTION: "Main panel",
    L10nKey.NOTIFICATIONS_SECTION: "Notifications",
    L10nKey.USAGE_NOTIFICATIONS_SECTION: "Usage notifications",
    L10nKey.EARLY_RESET_NOTIFICATIONS_SECTION: "Early reset notifications",
    L10nKey.LANGUAGE: "Language",
    L10nKey.REFRESH_INTERVAL: "Refresh interval",
    L10nKey.CODEX_MENU_BAR_METRIC: "Codex tray percentage",
    L10nKey.CLAUDE_MENU_BAR_METRIC: "Claude Code tray percentage",
    L10nKey.SHOW_CODEX_SPARK_USAGE: "Show GPT-5.3-Codex-Spark usage",
    L10nKey.MENU_BAR_METRIC_WEEKLY: "Weekly usage",
    L10nKey.MENU_BAR_METRIC_FIVE_HOUR: "5-hour usage",
    L10nKey.MENU_BAR_ICONS: "Tray icons",
    L10nKey.USAGE_PANEL_PROVIDERS: "Usage panel providers",
    L10nKey.NOTIFICATIONS_AHEAD: "Ahead-of-schedule alerts",
    L10nKey.NOTIFICATIONS_BEHIND: "Behind-schedule alerts",
    L10nKey.NOTIFICATIONS_CODEX_RESET: "Codex early reset alerts",
    L10nKey.NOTIFICATIONS_CLAUDE_RESET: "Claude Code early reset alerts",
    L10nKey.PROVIDER_CODEX: "Codex",
    L10nKey.PROVIDER_CLAUDE: "Claude Code",
    L10nKey.PROVIDER_COPILOT: "GitHub Copilot",
    L10nKey.ENABLED: "Enabled",
    L10nKey.PERCENTAGE_SHOWN: "Percentage shown",
    L10nKey.USAGE_LIMIT_FIVE_HOUR_CODEX_SPARK: "GPT-5.3-Codex-Spark 5-hour usage limit",
    L10nKey.USAGE_LIMIT_WEEKLY_CODEX_SPARK: "GPT-5.3-Codex-Spark weekly usage limit",
    L10nKey.USAGE_LIMIT_FIVE_HOUR: "5-hour usage limit",
    L10nKey.USAGE_LIMIT_WEEKLY: "Weekly usage limit",
    L10nKey.USAGE_LIMIT_SEVEN_DAY: "7-day usage limit",
    L10nKey.USAGE_LIMIT_MONTHLY: "Monthly usage limit",
    L10nKey.USAGE_METRIC_CREDITS: "Credits",
    L10nKey.RESET_AT: "Reset",
    L10nKey.SAVE: "Save",
    L10nKey.CANCEL: "Cancel",
    L10nKey.SIGN_IN_TO_CODEX: "Sign in to Codex",
    L10nKey.SIGN_IN_TO_GITHUB_COPILOT: "Sign in to GitHub",
    L10nKey.COPILOT_TOKEN: "GitHub Copilot token",
    L10nKey.FETCH_FAILED: "Unable to fetch",
    L10nKey.SIGNED_OUT: "Signed out",
    L10nKey.CONNECTED: "Connected",
    L10nKey.ACCOUNTS_SECTION: "Accounts",
    L10nKey.CODEX_SESSION_HELP: "Codex uses the local Codex CLI login from ~/.codex/auth.json. Run `codex login` in Terminal, then refresh.",
    L10nKey.CODEX_CLI_CONNECTED: "Detected local Codex CLI auth. Sign out through the Codex CLI if you want to disconnect it.",
    L10nKey.CLAUDE_SESSION_HELP: "Claude Code uses the local Claude Code login from ~/.claude/.credentials.json. Run `claude` in Terminal, then refresh.",
    L10nKey.CLAUDE_CLI_CONNECTED: "Detected local Claude Code auth. Sign out through Claude Code if you want to disconnect it.",
    L10nKey.COPILOT_PAT_HELP: "GitHub Copilot signs in with GitHub device flow and loads usage from GitHub's Copilot API.",
    L10nKey.COPILOT_DEVICE_FLOW_WAITING: "Continue in your browser and enter this GitHub code: %s",
    L10nKey.COPILOT_DEVICE_FLOW_CONNECTED: "GitHub Copilot is connected.",
    L10nKey.SAVE_AND_REFRESH: "Save and refresh",
    L10nKey.RELOAD: "Reload",
    L10nKey.TOKEN_SAVED: "Token saved to keyring.",
    L10nKey.SETTINGS_TAB_ACCOUNTS: "Accounts",
    L10nKey.SETTINGS_TAB_DISPLAY: "Appearance",
    L10nKey.SETTINGS_TAB_NOTIFICATIONS: "Notifications",
    L10nKey.SETTINGS_TAB_LOGS: "Logs",
    L10nKey.SETTINGS_TAB_ABOUT: "About",
    L10nKey.PROVIDER_STATUS_OK: "Connected",
    L10nKey.PROVIDER_STATUS_NEEDS_ATTENTION: "Needs attention",
    L10nKey.COPILOT_PLAN_HELP: "Sign in with GitHub to load your GitHub Copilot usage.",
    L10nKey.COPILOT_CONNECTED_HELP: "GitHub Copilot is connected. Sign out to remove the saved GitHub token.",
    L10nKey.NOTIFICATIONS_AHEAD_DESCRIPTION: "Warn when a quota is being consumed faster than the time window suggests.",
    L10nKey.NOTIFICATIONS_BEHIND_DESCRIPTION: "Warn when remaining quota is materially higher than expected for the current point in the window.",
    L10nKey.NOTIFICATIONS_CODEX_RESET_DESCRIPTION: "Warn when the Codex 5-hour or weekly window appears to reset earlier than previously observed.",
    L10nKey.NOTIFICATIONS_CLAUDE_RESET_DESCRIPTION: "Warn when the Claude Code 5-hour or weekly window appears to reset earlier than previously observed.",
    L10nKey.NOTIFICATION_TITLE_AHEAD_FORMAT: "Ahead of schedule: %s",
    L10nKey.NOTIFICATION_TITLE_BEHIND_FORMAT: "Behind schedule: %s",
    L10nKey.NOTIFICATION_BODY_SCHEDULE_FORMAT: "Remaining usage is %d%% while the schedule suggests about %d%% should remain.",
    L10nKey.NOTIFICATION_TITLE_CODEX_RESET: "Codex reset detected early",
    L10nKey.NOTIFICATION_TITLE_CLAUDE_RESET: "Claude Code reset detected early",
    L10nKey.NOTIFICATION_BODY_RESET_FORMAT: "%s appears to have reset earlier than expected.",
    L10nKey.NOTIFICATION_METRIC_FIVE_HOUR_FORMAT: "%s 5-hour window",
    L10nKey.NOTIFICATION_METRIC_WEEKLY_FORMAT: "%s weekly window",
    L10nKey.NOTIFICATION_METRIC_MONTHLY_FORMAT: "%s monthly quota",
    L10nKey.NOTIFICATION_METRIC_CREDITS_FORMAT: "%s credits",
    L10nKey.COPY_LOGS: "Copy logs",
    L10nKey.CLEAR_LOGS: "Clear logs",
    L10nKey.NO_LOGS: "No logs yet",
    L10nKey.LOGS_COPIED: "Logs copied to the clipboard.",
    L10nKey.APP_VERSION: "Version",
    L10nKey.LEGAL_SECTION: "Legal",
    L10nKey.LOGO_DISCLAIMER: "The OpenAI logo, Claude logo, and GitHub Copilot logo are used only to identify their respective services. All trademarks, service marks, and logos are the property of their respective owners. This app is independent and is not affiliated with, endorsed by, or sponsored by OpenAI, Anthropic, or GitHub.",
    L10nKey.QUIT_APP: "Quit",
    L10nKey.MENU_ACTION_REFRESH: "Refresh",
    L10nKey.MENU_ACTION_SETTINGS: "Settings",
    L10nKey.SIGN_OUT: "Sign out",
}

_POLISH: dict[L10nKey, str] = {
    L10nKey.MENU_BAR_APP_NAME: "Użycie AI",
    L10nKey.NOT_CONFIGURED: "Nie skonfigurowano",
    L10nKey.UNAVAILABLE: "Niedostępne",
    L10nKey.NO_USAGE_DATA: "Brak danych dla tego planu",
    L10nKey.USAGE_PANEL_TITLE: "Użycie AI",
    L10nKey.SETTINGS_TITLE: "Ustawienia",
    L10nKey.LAST_UPDATE: "Ostatnia aktualizacja",
    L10nKey.REFRESH_NOW: "Odśwież teraz",
    L10nKey.OPEN_SETTINGS: "Ustawienia",
    L10nKey.STALE_DATA: "Nieaktualne dane",
    L10nKey.AUTHENTICATION_REQUIRED: "Wymagana autoryzacja",
    L10nKey.AUTHENTICATE_IN_SETTINGS: "Otwórz Ustawienia, aby skonfigurować dostęp do usług.",
    L10nKey.GENERAL_SECTION: "Ogólne",
    L10nKey.APPEARANCE_SECTION: "Wygląd",
    L10nKey.MENU_BAR_SECTION: "Ikona w trayu",
    L10nKey.MAIN_PANEL_SECTION: "Panel główny",
    L10nKey.NOTIFICATIONS_SECTION: "Powiadomienia",
    L10nKey.USAGE_NOTIFICATIONS_SECTION: "Powiadomienia o użyciu",
    L10nKey.EARLY_RESET_NOTIFICATIONS_SECTION: "Powiadomienia o wczesnym resecie",
    L10nKey.LANGUAGE: "Język",
    L10nKey.REFRESH_INTERVAL: "Częstotliwość odświeżania",
    L10nKey.CODEX_MENU_BAR_METRIC: "Procent Codex w trayu",
    L10nKey.CLAUDE_MENU_BAR_METRIC: "Procent Claude Code w trayu",
    L10nKey.SHOW_CODEX_SPARK_USAGE: "Pokaż użycie GPT-5.3-Codex-Spark",
    L10nKey.MENU_BAR_METRIC_WEEKLY: "Użycie tygodniowe",
    L10nKey.MENU_BAR_METRIC_FIVE_HOUR: "Użycie 5-godzinne",
    L10nKey.MENU_BAR_ICONS: "Ikony w trayu",
    L10nKey.USAGE_PANEL_PROVIDERS: "Usługi w panelu",
    L10nKey.NOTIFICATIONS_AHEAD: "Alerty: za szybkie zużycie",
    L10nKey.NOTIFICATIONS_BEHIND: "Alerty: zbyt wolne zużycie",
    L10nKey.NOTIFICATIONS_CODEX_RESET: "Alerty o wczesnym resecie Codex",
    L10nKey.NOTIFICATIONS_CLAUDE_RESET: "Alerty o wczesnym resecie Claude Code",
    L10nKey.PROVIDER_CODEX: "Codex",
    L10nKey.PROVIDER_CLAUDE: "Claude Code",
    L10nKey.PROVIDER_COPILOT: "GitHub Copilot",
    L10nKey.ENABLED: "Włączone",
    L10nKey.PERCENTAGE_SHOWN: "Pokazywany procent",
    L10nKey.USAGE_LIMIT_FIVE_HOUR_CODEX_SPARK: "5-godzinny limit GPT-5.3-Codex-Spark",
    L10nKey.USAGE_LIMIT_WEEKLY_CODEX_SPARK: "Tygodniowy limit GPT-5.3-Codex-Spark",
    L10nKey.USAGE_LIMIT_FIVE_HOUR: "5-godzinny limit wykorzystania",
    L10nKey.USAGE_LIMIT_WEEKLY: "Tygodniowy limit wykorzystania",
    L10nKey.USAGE_LIMIT_SEVEN_DAY: "7-dniowy limit wykorzystania",
    L10nKey.USAGE_LIMIT_MONTHLY: "Miesięczny limit wykorzystania",
    L10nKey.USAGE_METRIC_CREDITS: "Kredyty",
    L10nKey.RESET_AT: "Reset",
    L10nKey.SAVE: "Zapisz",
    L10nKey.CANCEL: "Anuluj",
    L10nKey.SIGN_IN_TO_CODEX: "Zaloguj do Codex",
    L10nKey.SIGN_IN_TO_GITHUB_COPILOT: "Zaloguj do GitHub",
    L10nKey.COPILOT_TOKEN: "Token GitHub Copilot",
    L10nKey.FETCH_FAILED: "Nie udało się pobrać danych",
    L10nKey.SIGNED_OUT: "Wylogowano",
    L10nKey.CONNECTED: "Połączono",
    L10nKey.ACCOUNTS_SECTION: "Konta",
    L10nKey.CODEX_SESSION_HELP: "Codex korzysta z lokalnego logowania CLI z ~/.codex/auth.json. Uruchom `codex login` w terminalu, a potem odśwież.",
    L10nKey.CODEX_CLI_CONNECTED: "Wykryto lokalne uwierzytelnienie Codex CLI. Wyloguj się z poziomu Codex CLI, jeśli chcesz je odłączyć.",
    L10nKey.CLAUDE_SESSION_HELP: "Claude Code korzysta z lokalnego logowania z ~/.claude/.credentials.json. Uruchom `claude` w terminalu, a potem odśwież.",
    L10nKey.CLAUDE_CLI_CONNECTED: "Wykryto lokalne uwierzytelnienie Claude Code. Wyloguj się z poziomu Claude Code, jeśli chcesz je odłączyć.",
    L10nKey.COPILOT_PAT_HELP: "GitHub Copilot loguje się przez GitHub device flow i pobiera użycie z API Copilot.",
    L10nKey.COPILOT_DEVICE_FLOW_WAITING: "Kontynuuj w przeglądarce i wpisz ten kod GitHub: %s",
    L10nKey.COPILOT_DEVICE_FLOW_CONNECTED: "GitHub Copilot jest połączony.",
    L10nKey.SAVE_AND_REFRESH: "Zapisz i odśwież",
    L10nKey.RELOAD: "Przeładuj",
    L10nKey.TOKEN_SAVED: "Token zapisany w keyring.",
    L10nKey.SETTINGS_TAB_ACCOUNTS: "Konta",
    L10nKey.SETTINGS_TAB_DISPLAY: "Wygląd",
    L10nKey.SETTINGS_TAB_NOTIFICATIONS: "Powiadomienia",
    L10nKey.SETTINGS_TAB_LOGS: "Logi",
    L10nKey.SETTINGS_TAB_ABOUT: "Informacje",
    L10nKey.PROVIDER_STATUS_OK: "Połączono",
    L10nKey.PROVIDER_STATUS_NEEDS_ATTENTION: "Wymaga uwagi",
    L10nKey.COPILOT_PLAN_HELP: "Zaloguj się do GitHub, aby wczytać użycie GitHub Copilot.",
    L10nKey.COPILOT_CONNECTED_HELP: "GitHub Copilot jest połączony. Wyloguj się, aby usunąć zapisany token.",
    L10nKey.NOTIFICATIONS_AHEAD_DESCRIPTION: "Ostrzegaj, gdy limit jest zużywany szybciej, niż wynikałoby z upływu okna czasowego.",
    L10nKey.NOTIFICATIONS_BEHIND_DESCRIPTION: "Ostrzegaj, gdy pozostały limit jest wyraźnie wyższy niż oczekiwany.",
    L10nKey.NOTIFICATIONS_CODEX_RESET_DESCRIPTION: "Ostrzegaj, gdy okno 5-godzinne lub tygodniowe Codex wygląda na zresetowane wcześniej niż poprzednio.",
    L10nKey.NOTIFICATIONS_CLAUDE_RESET_DESCRIPTION: "Ostrzegaj, gdy okno 5-godzinne lub tygodniowe Claude Code wygląda na zresetowane wcześniej niż poprzednio.",
    L10nKey.NOTIFICATION_TITLE_AHEAD_FORMAT: "Zużycie powyżej tempa: %s",
    L10nKey.NOTIFICATION_TITLE_BEHIND_FORMAT: "Zużycie poniżej tempa: %s",
    L10nKey.NOTIFICATION_BODY_SCHEDULE_FORMAT: "Pozostałe użycie to %d%%, a harmonogram sugeruje około %d%%.",
    L10nKey.NOTIFICATION_TITLE_CODEX_RESET: "Wykryto wcześniejszy reset Codex",
    L10nKey.NOTIFICATION_TITLE_CLAUDE_RESET: "Wykryto wcześniejszy reset Claude Code",
    L10nKey.NOTIFICATION_BODY_RESET_FORMAT: "%s wygląda na zresetowane wcześniej niż oczekiwano.",
    L10nKey.NOTIFICATION_METRIC_FIVE_HOUR_FORMAT: "5-godzinne okno %s",
    L10nKey.NOTIFICATION_METRIC_WEEKLY_FORMAT: "Tygodniowe okno %s",
    L10nKey.NOTIFICATION_METRIC_MONTHLY_FORMAT: "Miesięczny limit %s",
    L10nKey.NOTIFICATION_METRIC_CREDITS_FORMAT: "Kredyty %s",
    L10nKey.COPY_LOGS: "Kopiuj logi",
    L10nKey.CLEAR_LOGS: "Wyczyść logi",
    L10nKey.NO_LOGS: "Brak logów",
    L10nKey.LOGS_COPIED: "Logi skopiowano do schowka.",
    L10nKey.APP_VERSION: "Wersja",
    L10nKey.LEGAL_SECTION: "Informacje prawne",
    L10nKey.LOGO_DISCLAIMER: "Logo OpenAI, logo Claude i logo GitHub Copilot są używane wyłącznie w celu identyfikacji odpowiednich usług. Wszystkie znaki towarowe należą do ich właścicieli. Ta aplikacja jest niezależna i nie jest powiązana z OpenAI, Anthropic ani GitHub.",
    L10nKey.QUIT_APP: "Zakończ",
    L10nKey.MENU_ACTION_REFRESH: "Odśwież",
    L10nKey.MENU_ACTION_SETTINGS: "Ustawienia",
    L10nKey.SIGN_OUT: "Wyloguj się",
}


class Localizer:
    def __init__(self, language: AppLanguage = AppLanguage.ENGLISH_US):
        self._language = language

    def text(self, key: L10nKey) -> str:
        if self._language == AppLanguage.POLISH:
            return _POLISH.get(key, _ENGLISH.get(key, key.value))
        return _ENGLISH.get(key, key.value)

    def formatted(self, key: L10nKey, *args: Any) -> str:
        template = self.text(key)
        try:
            return template % args
        except (TypeError, ValueError):
            return template

    def provider_display_name(self, provider: ProviderID) -> str:
        mapping = {
            ProviderID.CODEX: L10nKey.PROVIDER_CODEX,
            ProviderID.CLAUDE: L10nKey.PROVIDER_CLAUDE,
            ProviderID.COPILOT: L10nKey.PROVIDER_COPILOT,
        }
        return self.text(mapping[provider])

    def metric_title(self, kind: UsageMetricKind) -> str:
        mapping = {
            UsageMetricKind.CODEX_FIVE_HOUR: L10nKey.USAGE_LIMIT_FIVE_HOUR,
            UsageMetricKind.CODEX_WEEKLY: L10nKey.USAGE_LIMIT_WEEKLY,
            UsageMetricKind.CODEX_SPARK_FIVE_HOUR: L10nKey.USAGE_LIMIT_FIVE_HOUR_CODEX_SPARK,
            UsageMetricKind.CODEX_SPARK_WEEKLY: L10nKey.USAGE_LIMIT_WEEKLY_CODEX_SPARK,
            UsageMetricKind.CODEX_CREDITS: L10nKey.USAGE_METRIC_CREDITS,
            UsageMetricKind.CLAUDE_FIVE_HOUR: L10nKey.USAGE_LIMIT_FIVE_HOUR,
            UsageMetricKind.CLAUDE_WEEKLY: L10nKey.USAGE_LIMIT_SEVEN_DAY,
            UsageMetricKind.COPILOT_MONTHLY: L10nKey.USAGE_LIMIT_MONTHLY,
        }
        return self.text(mapping[kind])

    def codex_menu_bar_metric_label(self, metric: CodexMenuBarMetric) -> str:
        mapping = {
            CodexMenuBarMetric.WEEKLY: L10nKey.MENU_BAR_METRIC_WEEKLY,
            CodexMenuBarMetric.FIVE_HOUR: L10nKey.MENU_BAR_METRIC_FIVE_HOUR,
        }
        return self.text(mapping[metric])

    def claude_menu_bar_metric_label(self, metric: ClaudeMenuBarMetric) -> str:
        mapping = {
            ClaudeMenuBarMetric.WEEKLY: L10nKey.MENU_BAR_METRIC_WEEKLY,
            ClaudeMenuBarMetric.FIVE_HOUR: L10nKey.MENU_BAR_METRIC_FIVE_HOUR,
        }
        return self.text(mapping[metric])

    def notification_metric_name(self, kind: UsageMetricKind) -> str:
        provider_name = self.provider_display_name(kind.provider)
        mapping = {
            UsageMetricKind.CODEX_FIVE_HOUR: L10nKey.NOTIFICATION_METRIC_FIVE_HOUR_FORMAT,
            UsageMetricKind.CODEX_WEEKLY: L10nKey.NOTIFICATION_METRIC_WEEKLY_FORMAT,
            UsageMetricKind.CODEX_SPARK_FIVE_HOUR: L10nKey.USAGE_LIMIT_FIVE_HOUR_CODEX_SPARK,
            UsageMetricKind.CODEX_SPARK_WEEKLY: L10nKey.USAGE_LIMIT_WEEKLY_CODEX_SPARK,
            UsageMetricKind.CODEX_CREDITS: L10nKey.NOTIFICATION_METRIC_CREDITS_FORMAT,
            UsageMetricKind.CLAUDE_FIVE_HOUR: L10nKey.NOTIFICATION_METRIC_FIVE_HOUR_FORMAT,
            UsageMetricKind.CLAUDE_WEEKLY: L10nKey.NOTIFICATION_METRIC_WEEKLY_FORMAT,
            UsageMetricKind.COPILOT_MONTHLY: L10nKey.NOTIFICATION_METRIC_MONTHLY_FORMAT,
        }
        key = mapping[kind]
        if kind in {UsageMetricKind.CODEX_SPARK_FIVE_HOUR, UsageMetricKind.CODEX_SPARK_WEEKLY}:
            return self.text(key)
        return self.formatted(key, provider_name)
