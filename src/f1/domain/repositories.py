"""Domain contracts for OpenF1 data access."""

from __future__ import annotations

from abc import ABC, abstractmethod

from f1.domain.models import Driver, Lap, Meeting, Session


class MeetingRepository(ABC):
    @abstractmethod
    def list(self, year: int, country: str | None = None) -> list[Meeting]:
        """Return meetings for a season, optionally filtered by country."""


class SessionRepository(ABC):
    @abstractmethod
    def list(self, meeting_key: int | str) -> list[Session]:
        """Return sessions belonging to a meeting."""


class DriverRepository(ABC):
    @abstractmethod
    def list(self, session_key: int | str) -> list[Driver]:
        """Return drivers participating in a session."""


class LapRepository(ABC):
    @abstractmethod
    def list(
        self,
        session_key: int | str,
        driver_number: int | None = None,
    ) -> list[Lap]:
        """Return laps for a session, optionally filtered by driver."""
