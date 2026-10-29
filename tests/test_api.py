from __future__ import annotations

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from f1.api import OpenF1APIError, OpenF1Client


def test_get_encodes_query_and_returns_records() -> None:
    response = io.BytesIO(json.dumps([{"meeting_key": 123}]).encode())
    with patch("f1.api.urlopen", return_value=response) as urlopen:
        records = OpenF1Client().get_meetings(2024)

    assert records == [{"meeting_key": 123}]
    assert urlopen.call_args.args[0] == ("https://api.openf1.org/v1/meetings?year=2024")
    assert urlopen.call_args.kwargs == {"timeout": 10.0}


@pytest.mark.parametrize(
    ("method", "parameter"),
    [
        ("get_sessions", "meeting_key"),
        ("get_drivers", "session_key"),
        ("get_laps", "session_key"),
        ("get_session_results", "session_key"),
    ],
)
def test_endpoint_methods_use_the_expected_filter(
    method: str,
    parameter: str,
) -> None:
    response = io.BytesIO(b"[]")
    with patch("f1.api.urlopen", return_value=response) as urlopen:
        getattr(OpenF1Client(), method)(9222)

    assert f"{parameter}=9222" in urlopen.call_args.args[0]


def test_http_error_is_reported() -> None:
    error = HTTPError(
        "https://api.openf1.org/v1/meetings", 503, "Unavailable", {}, None
    )
    with patch("f1.api.urlopen", side_effect=error):
        with pytest.raises(OpenF1APIError, match="HTTP 503"):
            OpenF1Client().get_meetings(2024)


def test_connection_error_is_reported() -> None:
    with patch("f1.api.urlopen", side_effect=URLError("offline")):
        with pytest.raises(OpenF1APIError, match="offline"):
            OpenF1Client().get_meetings(2024)


def test_invalid_json_is_reported() -> None:
    with patch("f1.api.urlopen", return_value=io.BytesIO(b"{")):
        with pytest.raises(OpenF1APIError, match="JSON inválido"):
            OpenF1Client().get_meetings(2024)


@pytest.mark.parametrize("payload", [b'{"error": "bad"}', b"[null]"])
def test_non_record_response_is_reported(payload: bytes) -> None:
    with patch("f1.api.urlopen", return_value=io.BytesIO(payload)):
        with pytest.raises(OpenF1APIError, match="lista de registros"):
            OpenF1Client().get_meetings(2024)
