from unittest.mock import MagicMock

from f1.domain.models import Driver, Lap, Meeting, Session
from f1.domain.repositories import (
    DriverRepository,
    LapRepository,
    MeetingRepository,
    SessionRepository,
)
from f1.domain.services import F1DashboardService


def make_service() -> tuple[
    F1DashboardService,
    MagicMock,
    MagicMock,
    MagicMock,
    MagicMock,
]:
    meetings = MagicMock(spec=MeetingRepository)
    sessions = MagicMock(spec=SessionRepository)
    drivers = MagicMock(spec=DriverRepository)
    laps = MagicMock(spec=LapRepository)
    return (
        F1DashboardService(meetings, sessions, drivers, laps),
        meetings,
        sessions,
        drivers,
        laps,
    )


def test_list_meetings_and_sessions_delegate_to_repositories() -> None:
    service, meeting_repo, session_repo, _, _ = make_service()
    meeting = Meeting(meeting_key=100, meeting_name="Grand Prix")
    session = Session(session_key=200, session_name="Race")
    meeting_repo.list.return_value = [meeting]
    session_repo.list.return_value = [session]

    assert service.list_meetings(2024) == [meeting]
    assert service.list_sessions(100) == [session]
    meeting_repo.list.assert_called_once_with(2024)
    session_repo.list.assert_called_once_with(100)


def test_session_overview_ranks_laps_and_computes_statistics() -> None:
    service, _, _, driver_repo, lap_repo = make_service()
    driver = Driver(driver_number=44, name_acronym="HAM")
    driver_repo.list.return_value = [driver]
    lap_repo.list.return_value = [
        Lap(
            driver_number=44,
            lap_number=1,
            lap_duration=90.0,
            is_pit_out_lap=False,
        ),
        Lap(
            driver_number=44,
            lap_number=2,
            lap_duration=91.0,
            is_pit_out_lap=False,
        ),
        Lap(
            driver_number=44,
            lap_number=3,
            lap_duration=92.0,
            is_pit_out_lap=True,
        ),
    ]

    overview = service.get_session_overview(200, n=1)

    assert overview.fastest_laps[0].lap.lap_number == 1
    assert overview.fastest_laps[0].driver == driver
    assert overview.statistics.total_laps == 3
    assert overview.statistics.valid_laps == 2
    assert overview.statistics.driver_count == 1
    assert overview.statistics.fastest_lap_seconds == 90.0
    assert overview.statistics.average_lap_seconds == 90.5


def test_session_overview_handles_no_valid_laps() -> None:
    service, _, _, driver_repo, lap_repo = make_service()
    driver_repo.list.return_value = []
    lap_repo.list.return_value = []

    overview = service.get_session_overview("latest")

    assert overview.statistics.fastest_lap_seconds is None
    assert overview.statistics.average_lap_seconds is None
    assert overview.fastest_laps == []


def test_get_top_n_fastest_laps_fetches_drivers_and_laps() -> None:
    service, _, _, driver_repo, lap_repo = make_service()
    driver_repo.list.return_value = [Driver(driver_number=16)]
    lap_repo.list.return_value = [
        Lap(driver_number=16, lap_number=1, lap_duration=89.5)
    ]

    fastest = service.get_top_n_fastest_laps(200)

    assert fastest[0].lap.lap_duration == 89.5
    lap_repo.list.assert_called_once_with(200)
    driver_repo.list.assert_called_once_with(200)
