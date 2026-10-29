from datetime import UTC, datetime

import pytest

from f1.ingestion.http_client import HttpClient, HttpClientError
from f1.ingestion.openf1_client import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
    OpenF1SessionRepository,
)

pytestmark = pytest.mark.integration


def test_latest_openf1_resources_are_parseable() -> None:
    with HttpClient(
        "https://api.openf1.org/v1",
        timeout=15,
        max_attempts=1,
    ) as http_client:
        meetings = OpenF1MeetingRepository(http_client).list(datetime.now(UTC).year)
        sessions = OpenF1SessionRepository(http_client).list("latest")
        drivers = OpenF1DriverRepository(http_client).list("latest")
        try:
            laps = OpenF1LapRepository(http_client).list(
                "latest",
                driver_number=drivers[0].driver_number if drivers else None,
            )
        except HttpClientError as error:
            if error.status_code == 429:
                pytest.skip("OpenF1 rate-limited the optional integration request")
            raise

    assert isinstance(meetings, list)
    assert isinstance(sessions, list)
    assert isinstance(drivers, list)
    assert isinstance(laps, list)
