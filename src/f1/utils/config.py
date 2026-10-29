"""Environment-backed application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv

ALLOWED_ENVIRONMENTS = {"development", "staging", "production"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables or a local .env file."""

    openf1_base_url: str
    openf1_timeout: float
    environment: str
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        """Load and validate application settings."""
        load_dotenv()
        base_url = os.getenv(
            "OPENF1_BASE_URL",
            "https://api.openf1.org/v1",
        ).rstrip("/")
        parsed_url = urlparse(base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("OPENF1_BASE_URL must be an absolute HTTP(S) URL")

        try:
            timeout = float(os.getenv("OPENF1_TIMEOUT", "10"))
        except ValueError as error:
            raise ValueError("OPENF1_TIMEOUT must be a number") from error
        if timeout <= 0:
            raise ValueError("OPENF1_TIMEOUT must be greater than zero")

        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment not in ALLOWED_ENVIRONMENTS:
            allowed = ", ".join(sorted(ALLOWED_ENVIRONMENTS))
            raise ValueError(f"ENVIRONMENT must be one of: {allowed}")

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a standard logging level")

        return cls(
            openf1_base_url=base_url,
            openf1_timeout=timeout,
            environment=environment,
            log_level=log_level,
        )
