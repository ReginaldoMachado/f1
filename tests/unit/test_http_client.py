import httpx
import pytest

from f1.ingestion.http_client import HttpClient, HttpClientError


def test_http_client_retries_server_errors_and_encodes_filters() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        assert request.url.params["speed>="] == "300"
        return httpx.Response(200, json=[{"speed": 310}])

    with HttpClient(
        "https://api.openf1.org/v1",
        transport=httpx.MockTransport(handler),
        backoff_seconds=0,
    ) as client:
        result = client.get("car_data", {"speed>=": 300})

    assert result == [{"speed": 310}]
    assert attempts == 2


def test_http_client_retries_rate_limit_after_retry_after(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json=[{"lap_number": 1}])

    monkeypatch.setattr("f1.ingestion.http_client.time.sleep", delays.append)
    with HttpClient(
        "https://api.openf1.org/v1",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = client.get("laps")

    assert result == [{"lap_number": 1}]
    assert attempts == 2
    assert delays == [2.0]


def test_http_client_reports_rate_limit_after_max_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429)

    monkeypatch.setattr("f1.ingestion.http_client.time.sleep", delays.append)
    with HttpClient(
        "https://api.openf1.org/v1",
        transport=httpx.MockTransport(handler),
        backoff_seconds=0,
    ) as client:
        with pytest.raises(HttpClientError, match="HTTP 429") as error:
            client.get("laps")

    assert error.value.status_code == 429
    assert attempts == 3
    assert delays == [1.0, 2.0]


def test_http_client_retries_timeouts_three_times() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("slow response", request=request)

    client = HttpClient(
        "https://api.openf1.org/v1",
        transport=httpx.MockTransport(handler),
        backoff_seconds=0,
    )
    with pytest.raises(HttpClientError, match="timed out"):
        client.get("laps")
    client.close()

    assert attempts == 3


def test_http_client_does_not_retry_client_errors() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(404)

    client = HttpClient(
        "https://api.openf1.org/v1",
        transport=httpx.MockTransport(handler),
        backoff_seconds=0,
    )
    with pytest.raises(HttpClientError, match="HTTP 404") as error:
        client.get("laps")
    client.close()

    assert attempts == 1
    assert error.value.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [b"invalid", b'{"detail":"not a list"}', b"[null]"],
)
def test_http_client_rejects_invalid_json_shapes(payload: bytes) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=payload)
    )
    client = HttpClient("https://api.openf1.org/v1", transport=transport)

    with pytest.raises(HttpClientError):
        client.get("drivers")
    client.close()


def test_http_client_validates_configuration() -> None:
    with pytest.raises(ValueError, match="timeout"):
        HttpClient("https://api.openf1.org/v1", timeout=0)
    with pytest.raises(ValueError, match="max_attempts"):
        HttpClient("https://api.openf1.org/v1", max_attempts=0)
