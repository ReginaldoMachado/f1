"""HTTP transport with bounded retries for OpenF1 requests."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from f1.utils.logger import get_logger

logger = get_logger(__name__)
QueryValue = str | int | float | bool


class HttpClientError(Exception):
    """Raised when an HTTP request fails or returns an invalid payload."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class HttpClient:
    """Small HTTP client that retries transient server and timeout failures."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        max_attempts: int = 3,
        backoff_seconds: float = 0.25,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")

        self._client = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/",
            timeout=timeout,
            transport=transport,
        )
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    def get(
        self,
        endpoint: str,
        params: Mapping[str, QueryValue] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch a list of JSON records from an endpoint."""
        normalized_endpoint = endpoint.lstrip("/")
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._client.get(normalized_endpoint, params=params)
            except httpx.TimeoutException as error:
                if attempt == self._max_attempts:
                    logger.error(
                        "OpenF1 request timed out",
                        extra={"endpoint": normalized_endpoint, "attempt": attempt},
                    )
                    raise HttpClientError(
                        f"Request to /{normalized_endpoint} timed out."
                    ) from error
                self._wait_before_retry(normalized_endpoint, attempt, "timeout")
                continue
            except httpx.TransportError as error:
                logger.error(
                    "OpenF1 transport request failed",
                    extra={"endpoint": normalized_endpoint, "error": str(error)},
                )
                raise HttpClientError(
                    f"Request to /{normalized_endpoint} failed: {error}"
                ) from error

            if response.status_code == 429:
                if attempt < self._max_attempts:
                    retry_after = self._retry_after_seconds(
                        response.headers.get("Retry-After")
                    )
                    self._wait_before_retry(
                        normalized_endpoint,
                        attempt,
                        "429",
                        delay=retry_after,
                    )
                    continue
                logger.error(
                    "OpenF1 rate limit persisted after retries",
                    extra={
                        "endpoint": normalized_endpoint,
                        "status_code": response.status_code,
                    },
                )
                raise HttpClientError(
                    f"OpenF1 returned HTTP {response.status_code} "
                    f"for /{normalized_endpoint}.",
                    status_code=response.status_code,
                )

            if response.status_code >= 500:
                if attempt < self._max_attempts:
                    self._wait_before_retry(
                        normalized_endpoint, attempt, str(response.status_code)
                    )
                    continue
                logger.error(
                    "OpenF1 server returned an error",
                    extra={
                        "endpoint": normalized_endpoint,
                        "status_code": response.status_code,
                    },
                )
                raise HttpClientError(
                    f"OpenF1 returned HTTP {response.status_code} "
                    f"for /{normalized_endpoint}.",
                    status_code=response.status_code,
                )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                logger.error(
                    "OpenF1 request returned an unsuccessful status",
                    extra={
                        "endpoint": normalized_endpoint,
                        "status_code": response.status_code,
                    },
                )
                raise HttpClientError(
                    f"OpenF1 returned HTTP {response.status_code} "
                    f"for /{normalized_endpoint}.",
                    status_code=response.status_code,
                ) from error

            try:
                payload = response.json()
            except ValueError as error:
                logger.error(
                    "OpenF1 returned invalid JSON",
                    extra={"endpoint": normalized_endpoint},
                )
                raise HttpClientError(
                    f"OpenF1 returned invalid JSON for /{normalized_endpoint}."
                ) from error

            if not isinstance(payload, list) or not all(
                isinstance(record, dict) for record in payload
            ):
                logger.error(
                    "OpenF1 returned an invalid record collection",
                    extra={"endpoint": normalized_endpoint},
                )
                raise HttpClientError(
                    f"Response from /{normalized_endpoint} must be a list of records."
                )
            return payload

        raise RuntimeError("HTTP retry loop exited unexpectedly")

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _wait_before_retry(
        self,
        endpoint: str,
        attempt: int,
        reason: str,
        delay: float | None = None,
    ) -> None:
        if delay is None:
            base_delay = self._backoff_seconds
            if reason == "429":
                base_delay = max(base_delay, 1.0)
            delay = base_delay * (2 ** (attempt - 1))
        logger.warning(
            "Retrying OpenF1 request",
            extra={"endpoint": endpoint, "attempt": attempt, "reason": reason},
        )
        time.sleep(delay)

    @staticmethod
    def _retry_after_seconds(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
            except (TypeError, ValueError, OverflowError):
                return None
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)
            return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
