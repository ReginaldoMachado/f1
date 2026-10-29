"""Typed OpenF1 payloads and dashboard projections."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OpenF1Model(BaseModel):
    """Base model that tolerates additional fields added by OpenF1."""

    model_config = ConfigDict(extra="ignore")


class Meeting(OpenF1Model):
    meeting_key: int
    meeting_name: str
    country_name: str | None = None
    circuit_short_name: str | None = None
    location: str | None = None
    year: int | None = None
    date_start: datetime | None = None


class Session(OpenF1Model):
    session_key: int
    session_name: str
    session_type: str | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None
    country_name: str | None = None
    year: int | None = None


class Driver(OpenF1Model):
    driver_number: int
    full_name: str | None = None
    name_acronym: str | None = None
    team_name: str | None = None
    team_colour: str | None = None
    headshot_url: str | None = None


class Lap(OpenF1Model):
    lap_number: int
    lap_duration: float | None = None
    duration_sector_1: float | None = None
    duration_sector_2: float | None = None
    duration_sector_3: float | None = None
    i1_speed: float | None = None
    i2_speed: float | None = None
    st_speed: float | None = None
    is_pit_out_lap: bool | None = None
    driver_number: int


class FastestLapEntry(OpenF1Model):
    driver_number: int
    driver: Driver | None = None
    lap: Lap


class SessionStatistics(OpenF1Model):
    total_laps: int
    valid_laps: int
    driver_count: int
    fastest_lap_seconds: float | None = None
    average_lap_seconds: float | None = None


class SessionOverview(OpenF1Model):
    drivers: list[Driver]
    fastest_laps: list[FastestLapEntry]
    statistics: SessionStatistics
