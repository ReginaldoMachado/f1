"""Application services coordinating repositories and domain processing."""

from __future__ import annotations

from f1.domain.models import (
    FastestLapEntry,
    Meeting,
    Session,
    SessionOverview,
    SessionStatistics,
)
from f1.domain.repositories import (
    DriverRepository,
    LapRepository,
    MeetingRepository,
    SessionRepository,
)
from f1.processing.lap_processor import (
    build_driver_index,
    compute_top_n_laps,
    filter_valid_laps,
)


class F1DashboardService:
    """Provide dashboard-ready data using injected domain repositories."""

    def __init__(
        self,
        meeting_repository: MeetingRepository,
        session_repository: SessionRepository,
        driver_repository: DriverRepository,
        lap_repository: LapRepository,
    ) -> None:
        self._meeting_repository = meeting_repository
        self._session_repository = session_repository
        self._driver_repository = driver_repository
        self._lap_repository = lap_repository

    def list_meetings(self, year: int) -> list[Meeting]:
        """List meetings in the requested season."""
        return self._meeting_repository.list(year)

    def list_sessions(self, meeting_key: int | str) -> list[Session]:
        """List sessions for a meeting."""
        return self._session_repository.list(meeting_key)

    def get_top_n_fastest_laps(
        self,
        session_key: int | str,
        n: int = 10,
    ) -> list[FastestLapEntry]:
        """Return the fastest valid laps from a session."""
        laps = self._lap_repository.list(session_key)
        drivers = self._driver_repository.list(session_key)
        return compute_top_n_laps(laps, build_driver_index(drivers), n)

    def get_session_overview(
        self,
        session_key: int | str,
        n: int = 10,
    ) -> SessionOverview:
        """Load session drivers, ranked laps, and summary statistics."""
        drivers = self._driver_repository.list(session_key)
        laps = self._lap_repository.list(session_key)
        valid_laps = filter_valid_laps(laps)
        fastest_laps = compute_top_n_laps(
            valid_laps,
            build_driver_index(drivers),
            n,
        )
        times = [lap.lap_duration for lap in valid_laps if lap.lap_duration is not None]
        statistics = SessionStatistics(
            total_laps=len(laps),
            valid_laps=len(valid_laps),
            driver_count=len(drivers),
            fastest_lap_seconds=min(times) if times else None,
            average_lap_seconds=sum(times) / len(times) if times else None,
        )
        return SessionOverview(
            drivers=drivers,
            fastest_laps=fastest_laps,
            statistics=statistics,
        )
