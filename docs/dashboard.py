"""Interface Streamlit para explorar dados históricos da OpenF1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

import streamlit as st

from f1.api import OpenF1APIError, OpenF1Client, Record


class OpenF1Gateway(Protocol):
    """Interface das consultas necessárias à apresentação do dashboard."""

    def get_meetings(self, year: int) -> list[Record]: ...

    def get_sessions(self, meeting_key: str | int) -> list[Record]: ...

    def get_drivers(self, session_key: str | int) -> list[Record]: ...

    def get_session_results(self, session_key: str | int) -> list[Record]: ...

    def get_laps(self, session_key: str | int) -> list[Record]: ...


def build_driver_rows(
    drivers: list[Record],
    results: list[Record],
) -> list[dict[str, Any]]:
    """Combina resultados com nomes e equipes dos pilotos."""
    drivers_by_number = {
        str(driver["driver_number"]): driver
        for driver in drivers
        if driver.get("driver_number") is not None
    }
    rows = []
    for result in results:
        driver_number = result.get("driver_number")
        driver = drivers_by_number.get(str(driver_number), {})
        rows.append(
            {
                "posição": result.get("position"),
                "piloto": driver.get("name_acronym")
                or driver.get("full_name")
                or (str(driver_number) if driver_number is not None else "—"),
                "equipe": driver.get("team_name", "—"),
                "pontos": result.get("points"),
            }
        )
    return rows


def build_lap_rows(
    laps: list[Record],
    drivers: list[Record],
) -> list[dict[str, Any]]:
    """Prepara tempos de volta com a identificação do piloto."""
    drivers_by_number = {
        str(driver["driver_number"]): driver
        for driver in drivers
        if driver.get("driver_number") is not None
    }
    rows = []
    for lap in laps:
        driver_number = lap.get("driver_number")
        driver = drivers_by_number.get(str(driver_number), {})
        rows.append(
            {
                "piloto": driver.get("name_acronym")
                or (str(driver_number) if driver_number is not None else "—"),
                "volta": lap.get("lap_number"),
                "tempo (s)": lap.get("lap_duration"),
                "setor 1 (s)": lap.get("duration_sector_1"),
                "setor 2 (s)": lap.get("duration_sector_2"),
                "setor 3 (s)": lap.get("duration_sector_3"),
            }
        )
    return rows


def _meeting_label(meeting: Record) -> str:
    name = meeting.get("meeting_name") or "Evento sem nome"
    location = meeting.get("location")
    return f"{name} — {location}" if location else str(name)


def _session_label(session: Record) -> str:
    name = session.get("session_name") or "Sessão sem nome"
    date_start = session.get("date_start")
    if date_start:
        try:
            date_label = datetime.fromisoformat(
                str(date_start).replace("Z", "+00:00")
            ).strftime("%d/%m/%Y %H:%M UTC")
        except ValueError:
            date_label = str(date_start)
        return f"{name} — {date_label}"
    return str(name)


def main(client: OpenF1Gateway | None = None) -> None:
    """Renderiza o dashboard e consulta os dados selecionados."""
    st.set_page_config(page_title="F1 Explorer", page_icon="🏎️", layout="wide")
    st.title("F1 Explorer")
    st.caption("Explore resultados históricos da Fórmula 1 com dados da OpenF1.")

    seasons = list(range(2023, datetime.now(UTC).year + 1))
    season = st.selectbox("Temporada", seasons, index=len(seasons) - 1)
    api = client or OpenF1Client()

    try:
        with st.spinner("Carregando eventos..."):
            meetings = api.get_meetings(season)
    except OpenF1APIError as error:
        st.error(f"Não foi possível carregar os eventos: {error}")
        return

    meeting_options = {
        meeting["meeting_key"]: meeting
        for meeting in meetings
        if meeting.get("meeting_key") is not None
    }
    if not meeting_options:
        st.warning("Nenhum evento disponível para esta temporada.")
        return

    meeting_key = st.selectbox(
        "Grande Prêmio",
        list(meeting_options),
        format_func=lambda key: _meeting_label(meeting_options[key]),
    )

    try:
        with st.spinner("Carregando sessões..."):
            sessions = api.get_sessions(meeting_key)
    except OpenF1APIError as error:
        st.error(f"Não foi possível carregar as sessões: {error}")
        return

    session_options = {
        session["session_key"]: session
        for session in sessions
        if session.get("session_key") is not None
    }
    if not session_options:
        st.warning("Nenhuma sessão disponível para este evento.")
        return

    session_key = st.selectbox(
        "Sessão",
        list(session_options),
        format_func=lambda key: _session_label(session_options[key]),
    )

    try:
        with st.spinner("Carregando resultados e voltas..."):
            drivers = api.get_drivers(session_key)
            results = api.get_session_results(session_key)
            laps = api.get_laps(session_key)
    except OpenF1APIError as error:
        st.error(f"Não foi possível carregar os dados da sessão: {error}")
        return

    st.subheader("Resultado")
    driver_rows = build_driver_rows(drivers, results)
    if driver_rows:
        st.dataframe(driver_rows, hide_index=True, width="stretch")
    else:
        st.info("O resultado final ainda não está disponível para esta sessão.")

    st.subheader("Voltas")
    lap_rows = build_lap_rows(laps, drivers)
    if lap_rows:
        st.dataframe(lap_rows, hide_index=True, width="stretch")
    else:
        st.info("Não há tempos de volta disponíveis para esta sessão.")


if __name__ == "__main__":
    main()
