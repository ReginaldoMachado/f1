import pytest

from f1.domain.models import Driver, Lap
from f1.processing.lap_processor import (
    build_driver_index,
    compute_top_n_laps,
    filter_valid_laps,
)


def make_lap(
    lap_number: int,
    duration: float | None,
    driver_number: int = 44,
    is_pit_out_lap: bool = False,
) -> Lap:
    return Lap(
        lap_number=lap_number,
        lap_duration=duration,
        driver_number=driver_number,
        is_pit_out_lap=is_pit_out_lap,
    )


def test_filter_valid_laps_excludes_missing_time_and_pit_out() -> None:
    laps = [
        make_lap(1, 90.5),
        make_lap(2, None),
        make_lap(3, 91.0, is_pit_out_lap=True),
    ]

    assert filter_valid_laps(laps) == [laps[0]]


def test_build_driver_index_uses_driver_number() -> None:
    drivers = [Driver(driver_number=44), Driver(driver_number=16)]

    assert build_driver_index(drivers) == {44: drivers[0], 16: drivers[1]}


def test_compute_top_n_laps_orders_and_enriches_entries() -> None:
    driver = Driver(driver_number=44, name_acronym="HAM")
    laps = [
        make_lap(2, 91.0),
        make_lap(1, 90.5),
        make_lap(3, None),
        make_lap(4, 0.0),
    ]

    result = compute_top_n_laps(laps, {44: driver}, 1)

    assert len(result) == 1
    assert result[0].lap.lap_number == 4
    assert result[0].driver == driver


def test_compute_top_n_laps_handles_unknown_driver_and_zero_limit() -> None:
    laps = [make_lap(1, 90.5, driver_number=99)]

    assert compute_top_n_laps(laps, {}, 1)[0].driver is None
    assert compute_top_n_laps(laps, {}, 0) == []


def test_compute_top_n_laps_rejects_negative_limit() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        compute_top_n_laps([], {}, -1)
