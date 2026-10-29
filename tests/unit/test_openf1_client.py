from unittest.mock import MagicMock

from f1.domain.models import Driver
from f1.ingestion.http_client import HttpClient
from f1.ingestion.openf1_client import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
)


def test_driver_repository_skips_invalid_records_and_logs(
    caplog,
) -> None:
    http_client = MagicMock(spec=HttpClient)
    http_client.get.return_value = [
        {"driver_number": 44, "name_acronym": "HAM"},
        {"name_acronym": "INVALID"},
    ]

    with caplog.at_level("WARNING"):
        drivers = OpenF1DriverRepository(http_client).list(123)

    assert drivers == [Driver(driver_number=44, name_acronym="HAM")]
    assert "Ignoring invalid OpenF1 record" in caplog.text
    http_client.get.assert_called_once_with("drivers", {"session_key": 123})


def test_meeting_repository_applies_optional_country_filter() -> None:
    http_client = MagicMock(spec=HttpClient)
    http_client.get.return_value = [
        {"meeting_key": 10, "meeting_name": "Singapore Grand Prix"}
    ]

    meetings = OpenF1MeetingRepository(http_client).list(2024, "Singapore")

    assert meetings[0].meeting_key == 10
    http_client.get.assert_called_once_with(
        "meetings",
        {"year": 2024, "country_name": "Singapore"},
    )


def test_lap_repository_includes_driver_filter_only_when_provided() -> None:
    http_client = MagicMock(spec=HttpClient)
    http_client.get.return_value = []
    repository = OpenF1LapRepository(http_client)

    repository.list("latest")
    repository.list(123, driver_number=44)

    assert http_client.get.call_args_list[0].args == (
        "laps",
        {"session_key": "latest"},
    )
    assert http_client.get.call_args_list[1].args == (
        "laps",
        {"session_key": 123, "driver_number": 44},
    )
