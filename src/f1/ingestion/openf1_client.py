"""OpenF1 repository implementations."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from f1.domain.models import Driver, Lap, Meeting, Session
from f1.domain.repositories import (
    DriverRepository,
    LapRepository,
    MeetingRepository,
    SessionRepository,
)
from f1.ingestion.http_client import HttpClient
from f1.utils.logger import get_logger

logger = get_logger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)


def _validate_records(
    payload: list[dict[str, object]],
    model: type[ModelT],
    endpoint: str,
) -> list[ModelT]:
    records: list[ModelT] = []
    for index, item in enumerate(payload):
        try:
            records.append(model.model_validate(item))
        except ValidationError as error:
            logger.warning(
                "Ignoring invalid OpenF1 record",
                extra={
                    "endpoint": endpoint,
                    "record_index": index,
                    "validation_error": str(error),
                },
            )
    return records


class OpenF1MeetingRepository(MeetingRepository):
    """Fetch and validate meetings from OpenF1."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def list(self, year: int, country: str | None = None) -> list[Meeting]:
        params: dict[str, str | int] = {"year": year}
        if country:
            params["country_name"] = country
        payload = self._http_client.get("meetings", params)
        return _validate_records(payload, Meeting, "meetings")


class OpenF1SessionRepository(SessionRepository):
    """Fetch and validate sessions from OpenF1."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def list(self, meeting_key: int | str) -> list[Session]:
        payload = self._http_client.get("sessions", {"meeting_key": meeting_key})
        return _validate_records(payload, Session, "sessions")


class OpenF1DriverRepository(DriverRepository):
    """Fetch and validate drivers from OpenF1."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def list(self, session_key: int | str) -> list[Driver]:
        payload = self._http_client.get("drivers", {"session_key": session_key})
        return _validate_records(payload, Driver, "drivers")


class OpenF1LapRepository(LapRepository):
    """Fetch and validate lap records from OpenF1."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def list(
        self,
        session_key: int | str,
        driver_number: int | None = None,
    ) -> list[Lap]:
        params: dict[str, int | str] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        payload = self._http_client.get("laps", params)
        return _validate_records(payload, Lap, "laps")
