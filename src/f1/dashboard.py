"""Streamlit composition root for the F1 Explorer."""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime

import streamlit as st

from f1.domain.models import FastestLapEntry, Meeting, Session, SessionOverview
from f1.domain.services import F1DashboardService
from f1.ingestion.http_client import HttpClient, HttpClientError
from f1.ingestion.openf1_client import (
    OpenF1DriverRepository,
    OpenF1LapRepository,
    OpenF1MeetingRepository,
    OpenF1SessionRepository,
)
from f1.utils.config import Settings


@st.cache_resource
def get_service() -> F1DashboardService:
    """Create the shared service and its HTTP-backed repositories."""
    settings = Settings.from_env()
    client = HttpClient(
        base_url=settings.openf1_base_url,
        timeout=settings.openf1_timeout,
    )
    return F1DashboardService(
        meeting_repository=OpenF1MeetingRepository(client),
        session_repository=OpenF1SessionRepository(client),
        driver_repository=OpenF1DriverRepository(client),
        lap_repository=OpenF1LapRepository(client),
    )


@st.cache_data(ttl=3600)
def load_meetings(year: int) -> list[Meeting]:
    """Cache season meetings for one hour."""
    return get_service().list_meetings(year)


@st.cache_data(ttl=3600)
def load_sessions(meeting_key: int) -> list[Session]:
    """Cache a meeting's sessions for one hour."""
    return get_service().list_sessions(meeting_key)


@st.cache_data(ttl=300)
def load_session_overview(session_key: int) -> SessionOverview:
    """Cache session telemetry summaries for five minutes."""
    return get_service().get_session_overview(session_key)


def _meeting_label(meeting: Meeting) -> str:
    location = f" — {meeting.location}" if meeting.location else ""
    return f"{meeting.meeting_name}{location}"


def _session_label(session: Session) -> str:
    if session.date_start is None:
        return session.session_name
    date_label = session.date_start.strftime("%d/%m/%Y %H:%M UTC")
    return f"{session.session_name} — {date_label}"


def _show_load_error(resource: str, error: HttpClientError) -> None:
    if error.status_code == 429:
        st.error(
            f"Não foi possível carregar {resource}: a OpenF1 limitou "
            "temporariamente as consultas. Aguarde um pouco e tente novamente."
        )
        return
    st.error(f"Não foi possível carregar {resource}: {error}")


def _render_fastest_lap_card(entry: FastestLapEntry, position: int) -> None:
    driver = entry.driver
    driver_name = (
        driver.name_acronym
        if driver and driver.name_acronym
        else f"#{entry.driver_number}"
    )
    team_name = (
        driver.team_name if driver and driver.team_name else "Equipe indisponível"
    )
    raw_colour = driver.team_colour if driver and driver.team_colour else ""
    colour = (
        f"#{raw_colour.lstrip('#')}"
        if re.fullmatch(r"#?[0-9A-Fa-f]{6}", raw_colour)
        else "#808080"
    )
    lap_time = entry.lap.lap_duration
    lap_label = f"{lap_time:.3f} s" if lap_time is not None else "Sem tempo"
    st.markdown(
        (
            '<div style="border-left: 4px solid '
            f'{colour}; padding: 0.5rem 0.75rem; margin-bottom: 0.5rem;">'
            f"<strong>P{position} · {html.escape(driver_name)}</strong><br>"
            f"{html.escape(team_name)}<br>"
            f"<strong>{lap_label}</strong></div>"
        ),
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the season, meeting, session, and fastest-lap explorer."""
    st.set_page_config(page_title="F1 Explorer", page_icon="🏎️", layout="wide")
    st.title("F1 Explorer")
    st.caption("Explore tempos de volta históricos da Fórmula 1 com a OpenF1.")

    years = list(range(2023, datetime.now(UTC).year + 1))
    year = st.selectbox("Temporada", years, index=len(years) - 1)
    try:
        meetings = load_meetings(year)
    except HttpClientError as error:
        _show_load_error("os eventos", error)
        return
    if not meetings:
        st.warning("Nenhum evento disponível para esta temporada.")
        return

    selected_meeting = st.selectbox(
        "Grande Prêmio",
        meetings,
        format_func=_meeting_label,
    )
    try:
        sessions = load_sessions(selected_meeting.meeting_key)
    except HttpClientError as error:
        _show_load_error("as sessões", error)
        return
    if not sessions:
        st.warning("Nenhuma sessão disponível para este evento.")
        return

    selected_session = st.selectbox(
        "Sessão",
        sessions,
        format_func=_session_label,
    )
    try:
        overview = load_session_overview(selected_session.session_key)
    except HttpClientError as error:
        _show_load_error("os dados da sessão", error)
        return

    stats = overview.statistics
    first, second, third = st.columns(3)
    first.metric("Voltas válidas", stats.valid_laps)
    second.metric(
        "Melhor volta",
        f"{stats.fastest_lap_seconds:.3f} s"
        if stats.fastest_lap_seconds is not None
        else "—",
    )
    third.metric(
        "Média das voltas",
        f"{stats.average_lap_seconds:.3f} s"
        if stats.average_lap_seconds is not None
        else "—",
    )

    st.subheader("Top 10 voltas mais rápidas")
    if not overview.fastest_laps:
        st.info("Não há tempos de volta válidos disponíveis para esta sessão.")
        return

    cards = st.columns(2)
    for position, entry in enumerate(overview.fastest_laps, start=1):
        with cards[(position - 1) % len(cards)]:
            _render_fastest_lap_card(entry, position)
    st.dataframe(
        [
            {
                "posição": position,
                "piloto": (
                    entry.driver.name_acronym
                    if entry.driver and entry.driver.name_acronym
                    else f"#{entry.driver_number}"
                ),
                "equipe": (
                    entry.driver.team_name
                    if entry.driver and entry.driver.team_name
                    else "—"
                ),
                "volta": entry.lap.lap_number,
                "tempo (s)": entry.lap.lap_duration,
                "setor 1 (s)": entry.lap.duration_sector_1,
                "setor 2 (s)": entry.lap.duration_sector_2,
                "setor 3 (s)": entry.lap.duration_sector_3,
            }
            for position, entry in enumerate(overview.fastest_laps, start=1)
        ],
        hide_index=True,
        width="stretch",
    )


if __name__ == "__main__":
    main()
