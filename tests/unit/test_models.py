from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from f1.domain.models import Driver, Lap, Meeting, Session


def test_openf1_models_parse_payload_fields_and_ignore_extra_data() -> None:
    meeting = Meeting.model_validate(
        {
            "meeting_key": 1234,
            "meeting_name": "Grand Prix",
            "date_start": "2024-03-01T10:00:00Z",
            "extra_field": "ignored",
        }
    )
    session = Session.model_validate(
        {
            "session_key": 5678,
            "session_name": "Race",
            "date_start": "2024-03-03T10:00:00Z",
        }
    )
    driver = Driver.model_validate(
        {
            "driver_number": 44,
            "full_name": "Lewis Hamilton",
            "team_name": "Mercedes",
        }
    )
    lap = Lap.model_validate(
        {
            "driver_number": 44,
            "lap_number": 8,
            "lap_duration": 91.25,
            "is_pit_out_lap": False,
        }
    )

    assert meeting.date_start == datetime(2024, 3, 1, 10, tzinfo=UTC)
    assert session.session_key == 5678
    assert driver.driver_number == 44
    assert lap.lap_duration == 91.25


def test_model_rejects_missing_required_identity_fields() -> None:
    with pytest.raises(ValidationError):
        Lap.model_validate({"lap_number": 1})
