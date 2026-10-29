from __future__ import annotations

from typing import Any

import pytest

import f1.dashboard as dashboard
from f1.domain.models import (
    Driver,
    FastestLapEntry,
    Meeting,
    Session,
    SessionOverview,
    SessionStatistics,
)
from f1.ingestion.http_client import HttpClientError


class FakeColumn:
    def __init__(self, metrics: list[tuple[str, Any]]) -> None:
        self._metrics = metrics

    def __enter__(self) -> FakeColumn:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def metric(self, label: str, value: Any) -> None:
        self._metrics.append((label, value))


class FakeStreamlit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.metrics: list[tuple[str, Any]] = []
        self.markdown_calls: list[str] = []
        self.tables: list[list[dict[str, Any]]] = []

    def set_page_config(self, **kwargs: Any) -> None:
        pass

    def title(self, value: str) -> None:
        pass

    def caption(self, value: str) -> None:
        pass

    def selectbox(
        self,
        label: str,
        options: list[Any],
        format_func: Any = None,
        **kwargs: Any,
    ) -> Any:
        return options[0]

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def subheader(self, value: str) -> None:
        pass

    def columns(self, count: int) -> list[FakeColumn]:
        return [FakeColumn(self.metrics) for _ in range(count)]

    def markdown(self, value: str, **kwargs: Any) -> None:
        self.markdown_calls.append(value)

    def dataframe(self, data: list[dict[str, Any]], **kwargs: Any) -> None:
        self.tables.append(data)

    def info(self, message: str) -> None:
        pass


def test_main_renders_session_metrics_cards_and_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)
    monkeypatch.setattr(
        dashboard,
        "load_meetings",
        lambda year: [Meeting(meeting_key=100, meeting_name="Grand Prix")],
    )
    monkeypatch.setattr(
        dashboard,
        "load_sessions",
        lambda meeting_key: [Session(session_key=200, session_name="Race")],
    )
    driver = Driver(
        driver_number=44,
        name_acronym="HAM",
        team_name="Mercedes",
        team_colour="00D2BE",
    )
    fastest_lap = FastestLapEntry(
        driver_number=44,
        driver=driver,
        lap={"driver_number": 44, "lap_number": 1, "lap_duration": 90.5},
    )
    overview = SessionOverview(
        drivers=[driver],
        fastest_laps=[fastest_lap],
        statistics=SessionStatistics(
            total_laps=1,
            valid_laps=1,
            driver_count=1,
            fastest_lap_seconds=90.5,
            average_lap_seconds=90.5,
        ),
    )
    monkeypatch.setattr(
        dashboard, "load_session_overview", lambda session_key: overview
    )

    dashboard.main()

    assert fake_st.errors == []
    assert fake_st.metrics == [
        ("Voltas válidas", 1),
        ("Melhor volta", "90.500 s"),
        ("Média das voltas", "90.500 s"),
    ]
    assert "#00D2BE" in fake_st.markdown_calls[0]
    assert fake_st.tables[0][0]["piloto"] == "HAM"
    assert fake_st.tables[0][0]["tempo (s)"] == 90.5


def test_main_reports_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    def fail_to_load(year: int) -> list[Meeting]:
        raise HttpClientError("service unavailable")

    monkeypatch.setattr(dashboard, "load_meetings", fail_to_load)

    dashboard.main()

    assert fake_st.errors == [
        "Não foi possível carregar os eventos: service unavailable"
    ]


def test_main_explains_rate_limit_and_suggests_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    def fail_to_load(year: int) -> list[Meeting]:
        raise HttpClientError("OpenF1 returned HTTP 429", status_code=429)

    monkeypatch.setattr(dashboard, "load_meetings", fail_to_load)

    dashboard.main()

    assert fake_st.errors == [
        "Não foi possível carregar os eventos: a OpenF1 limitou "
        "temporariamente as consultas. Aguarde um pouco e tente novamente."
    ]


def test_main_warns_when_season_has_no_meetings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)
    monkeypatch.setattr(dashboard, "load_meetings", lambda year: [])

    dashboard.main()

    assert fake_st.warnings == ["Nenhum evento disponível para esta temporada."]
