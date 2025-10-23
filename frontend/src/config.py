"""Configuration primitives for the frontend application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

_DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_FEATURE_FLAG_ENV = "FRONTEND_FEATURE_FLAGS"


def _parse_feature_flags(raw_value: str | None) -> Mapping[str, bool]:
    """Parse a comma-separated feature flag string into an immutable mapping."""
    if not raw_value:
        return MappingProxyType({})

    entries: dict[str, bool] = {}
    for item in raw_value.split(","):
        key_value = item.strip()
        if not key_value:
            continue
        if "=" in key_value:
            key, raw_flag = key_value.split("=", maxsplit=1)
            entries[key.strip()] = raw_flag.strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        else:
            entries[key_value] = True
    return MappingProxyType(entries)


def _resolve_backend_url(raw_url: str | None) -> str:
    """Resolve the backend base URL, providing an explicit default when unset."""
    if not raw_url:
        return _DEFAULT_BACKEND_URL
    return raw_url.rstrip("/")


@dataclass(frozen=True, slots=True)
class FrontendConfig:
    """Immutable configuration for the frontend service layer."""

    backend_base_url: str = field(default=_DEFAULT_BACKEND_URL)
    request_timeout_seconds: float = field(default=_DEFAULT_TIMEOUT_SECONDS)
    feature_flags: Mapping[str, bool] = field(
        default_factory=lambda: MappingProxyType({})
    )
    debug: bool = field(default=False)

    @classmethod
    def from_env(cls) -> FrontendConfig:
        """Build a configuration object from environment variables."""
        backend_url = _resolve_backend_url(os.getenv("FRONTEND_BACKEND_URL"))
        timeout_raw = os.getenv("FRONTEND_REQUEST_TIMEOUT", "")
        flags_raw = os.getenv(_FEATURE_FLAG_ENV)
        debug_raw = os.getenv("FRONTEND_DEBUG", "false")

        timeout = cls._safe_float(timeout_raw, fallback=_DEFAULT_TIMEOUT_SECONDS)
        debug_enabled = debug_raw.lower() in {"1", "true", "yes", "on"}

        return cls(
            backend_base_url=backend_url,
            request_timeout_seconds=timeout,
            feature_flags=_parse_feature_flags(flags_raw),
            debug=debug_enabled,
        )

    @staticmethod
    def _safe_float(value: str, fallback: float) -> float:
        """Convert strings to floats with fallback on invalid input."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def is_feature_enabled(self, name: str) -> bool:
        """Return True when the named feature flag is active."""
        return self.feature_flags.get(name, False)
