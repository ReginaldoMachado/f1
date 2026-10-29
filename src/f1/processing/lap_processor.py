"""Pure helpers for filtering and ranking lap records."""

from __future__ import annotations

from f1.domain.models import Driver, FastestLapEntry, Lap


def filter_valid_laps(laps: list[Lap]) -> list[Lap]:
    """Keep timed laps that are not pit-out laps."""
    return [
        lap for lap in laps if lap.lap_duration is not None and not lap.is_pit_out_lap
    ]


def build_driver_index(drivers: list[Driver]) -> dict[int, Driver]:
    """Index drivers by their car number."""
    return {driver.driver_number: driver for driver in drivers}


def compute_top_n_laps(
    laps: list[Lap],
    drivers_index: dict[int, Driver],
    n: int,
) -> list[FastestLapEntry]:
    """Return the fastest valid laps, ordered by lap time."""
    if n < 0:
        raise ValueError("n cannot be negative")
    valid_laps = filter_valid_laps(laps)
    ranked_laps = sorted(
        valid_laps,
        key=lambda lap: (
            lap.lap_duration if lap.lap_duration is not None else float("inf")
        ),
    )
    return [
        FastestLapEntry(
            driver_number=lap.driver_number,
            driver=drivers_index.get(lap.driver_number),
            lap=lap,
        )
        for lap in ranked_laps[:n]
    ]
