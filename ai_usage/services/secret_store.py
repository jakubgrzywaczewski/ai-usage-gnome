from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_SCHEMA_NAME = "ai-usage"

try:
    import secretstorage

    _HAS_SECRETSTORAGE = True
except ImportError:
    _HAS_SECRETSTORAGE = False


class SecretStore:
    """Wraps GNOME Keyring / libsecret via secretstorage."""

    def __init__(self, service: str = "com.jakubgrzywaczewski.ai-usage"):
        self._service = service
        self._cache: dict[str, str] = {}
        self._connection = None

    def _get_connection(self):
        if not _HAS_SECRETSTORAGE:
            return None
        if self._connection is None:
            try:
                self._connection = secretstorage.dbus_init()
            except Exception as e:
                logger.warning("Could not connect to Secret Service: %s", e)
                return None
        return self._connection

    def _get_collection(self):
        conn = self._get_connection()
        if conn is None:
            return None
        try:
            return secretstorage.get_default_collection(conn)
        except Exception as e:
            logger.warning("Could not access default keyring collection: %s", e)
            return None

    def save(self, account: str, value: str) -> None:
        self._cache[account] = value
        collection = self._get_collection()
        if collection is None:
            return
        try:
            if collection.is_locked():
                collection.unlock()
            attrs = {"service": self._service, "account": account}
            items = list(collection.search_items(attrs))
            if items:
                items[0].set_secret(value.encode("utf-8"))
            else:
                collection.create_item(
                    f"{self._service} - {account}",
                    attrs,
                    value.encode("utf-8"),
                    replace=True,
                )
        except Exception as e:
            logger.error("Failed to save secret for %s: %s", account, e)

    def load(self, account: str) -> str | None:
        if account in self._cache:
            return self._cache[account]

        collection = self._get_collection()
        if collection is None:
            return None
        try:
            if collection.is_locked():
                collection.unlock()
            attrs = {"service": self._service, "account": account}
            items = list(collection.search_items(attrs))
            if items:
                value = items[0].get_secret().decode("utf-8")
                self._cache[account] = value
                return value
        except Exception as e:
            logger.warning("Failed to load secret for %s: %s", account, e)
        return None

    def delete(self, account: str) -> None:
        self._cache.pop(account, None)
        collection = self._get_collection()
        if collection is None:
            return
        try:
            if collection.is_locked():
                collection.unlock()
            attrs = {"service": self._service, "account": account}
            for item in collection.search_items(attrs):
                item.delete()
        except Exception as e:
            logger.warning("Failed to delete secret for %s: %s", account, e)
