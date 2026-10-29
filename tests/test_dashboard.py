from contextlib import nullcontext
from typing import Any

import pytest
from docs import dashboard
from docs.dashboard import build_driver_rows, build_lap_rows

from f1.api import OpenF1APIError


def test_build_driver_rows_joins_result_to_driver() -> None:
    rows = build_driver_rows(
        [
            {
                "driver_number": 44,
                "name_acronym": "HAM",
                "team_name": "Mercedes",
            }
        ],
        [{"driver_number": 44, "position": 1, "points": 25}],
    )

    assert rows == [
        {
            "posição": 1,
            "piloto": "HAM",
            "equipe": "Mercedes",
            "pontos": 25,
        }
    ]


def test_build_driver_rows_handles_missing_driver_data() -> None:
    rows = build_driver_rows([], [{"driver_number": 7, "position": 3}])

    assert rows == [{"posição": 3, "piloto": "7", "equipe": "—", "pontos": None}]


def test_build_lap_rows_adds_driver_and_sector_data() -> None:
    rows = build_lap_rows(
        [{"driver_number": 16, "lap_number": 2, "lap_duration": 91.25}],
        [{"driver_number": "16", "name_acronym": "LEC"}],
    )

    assert rows == [
        {
            "piloto": "LEC",
            "volta": 2,
            "tempo (s)": 91.25,
            "setor 1 (s)": None,
            "setor 2 (s)": None,
            "setor 3 (s)": None,
        }
    ]


def test_empty_api_data_produces_empty_tables() -> None:
    assert build_driver_rows([], []) == []
    assert build_lap_rows([], []) == []


class FakeStreamlit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
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

    def spinner(self, message: str) -> Any:
        return nullcontext()

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def subheader(self, value: str) -> None:
        pass

    def dataframe(self, data: list[dict[str, Any]], **kwargs: Any) -> None:
        self.tables.append(data)

    def info(self, message: str) -> None:
        pass


class FakeClient:
    def get_meetings(self, year: int) -> list[dict[str, Any]]:
        return [{"meeting_key": 1, "meeting_name": "GP Teste"}]

    def get_sessions(self, meeting_key: str | int) -> list[dict[str, Any]]:
        return [{"session_key": 2, "session_name": "Race"}]

    def get_drivers(self, session_key: str | int) -> list[dict[str, Any]]:
        return [{"driver_number": 44, "name_acronym": "HAM"}]

    def get_session_results(self, session_key: str | int) -> list[dict[str, Any]]:
        return [{"driver_number": 44, "position": 1, "points": 25}]

    def get_laps(self, session_key: str | int) -> list[dict[str, Any]]:
        return [{"driver_number": 44, "lap_number": 1, "lap_duration": 91.0}]


def test_main_renders_result_and_lap_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.main(FakeClient())

    assert fake_st.errors == []
    assert len(fake_st.tables) == 2
    assert fake_st.tables[0][0]["piloto"] == "HAM"
    assert fake_st.tables[1][0]["tempo (s)"] == 91.0


def test_main_reports_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailedClient(FakeClient):
        def get_meetings(self, year: int) -> list[dict[str, Any]]:
            raise OpenF1APIError("serviço indisponível")

    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.main(FailedClient())

    assert fake_st.errors == [
        "Não foi possível carregar os eventos: serviço indisponível"
    ]


def test_main_warns_when_no_meetings_are_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class EmptyClient(FakeClient):
        def get_meetings(self, year: int) -> list[dict[str, Any]]:
            return []

    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.main(EmptyClient())

    assert fake_st.warnings == ["Nenhum evento disponível para esta temporada."]
