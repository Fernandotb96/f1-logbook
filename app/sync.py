from datetime import date
from typing import Any, Callable, Optional

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .season_history import recalculate_season_history


JOLPICA_BASE_URL = "https://api.jolpi.ca/ergast/f1"
JOLPICA_USER_AGENT = "F1LogbookAPI/1.0"
PAGE_SIZE = 100
REQUEST_TIMEOUT_SECONDS = 20


class JolpicaSyncError(Exception):
    """Raised when Jolpica cannot provide a valid season response."""


def _empty_counts() -> dict[str, dict[str, int]]:
    return {
        entity: {"created": 0, "updated": 0}
        for entity in (
            "seasons",
            "circuits",
            "drivers",
            "constructors",
            "races",
            "race_results",
            "sprint_results",
        )
    }


def _update_values(instance: Any, values: dict[str, Any]) -> bool:
    changed = False
    for field, value in values.items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed = True
    return changed


def _required(data: dict[str, Any], field: str, context: str) -> Any:
    value = data.get(field)
    if value is None or value == "":
        raise JolpicaSyncError(f"Jolpica response is missing {field} for {context}")
    return value


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, "", "\\N"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise JolpicaSyncError(f"Expected an integer value, received {value!r}") from error


def _required_float(value: Any, context: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise JolpicaSyncError(f"Expected points for {context}") from error


def _fetch_races(
    year: int,
    endpoint: str,
    request_get: Callable[..., requests.Response],
) -> list[dict[str, Any]]:
    """Fetch every page for one Jolpica race-based endpoint."""
    races: list[dict[str, Any]] = []
    offset = 0

    while True:
        url = f"{JOLPICA_BASE_URL}/{year}/{endpoint}.json"
        try:
            response = request_get(
                url,
                params={"limit": PAGE_SIZE, "offset": offset},
                headers={"User-Agent": JOLPICA_USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise JolpicaSyncError(
                f"Could not fetch Jolpica {endpoint} data for {year}"
            ) from error

        try:
            mr_data = payload["MRData"]
            total = int(mr_data["total"])
            page_races = mr_data["RaceTable"]["Races"]
        except (KeyError, TypeError, ValueError) as error:
            raise JolpicaSyncError(
                f"Jolpica returned an invalid {endpoint} response for {year}"
            ) from error

        if not isinstance(page_races, list):
            raise JolpicaSyncError(
                f"Jolpica returned invalid races for {endpoint} in {year}"
            )

        races.extend(page_races)
        if offset + PAGE_SIZE >= total:
            return races
        if not page_races:
            raise JolpicaSyncError(
                f"Jolpica pagination stopped early for {endpoint} in {year}"
            )
        offset += PAGE_SIZE


def _upsert_circuit(
    circuit_data: dict[str, Any],
    db: Session,
    counts: dict[str, dict[str, int]],
) -> models.Circuit:
    jolpica_id = str(_required(circuit_data, "circuitId", "circuit"))
    location_data = circuit_data.get("Location") or {}
    if not isinstance(location_data, dict):
        raise JolpicaSyncError(f"Invalid location for circuit {jolpica_id}")

    values = {
        "jolpica_id": jolpica_id,
        "name": str(_required(circuit_data, "circuitName", f"circuit {jolpica_id}")),
        "location": location_data.get("locality"),
        "country": location_data.get("country"),
    }
    circuit = db.scalar(
        select(models.Circuit).where(models.Circuit.jolpica_id == jolpica_id)
    )
    if not circuit:
        circuit = models.Circuit(**values)
        db.add(circuit)
        db.flush()
        counts["circuits"]["created"] += 1
    elif _update_values(circuit, values):
        counts["circuits"]["updated"] += 1
    return circuit


def _upsert_driver(
    driver_data: dict[str, Any],
    db: Session,
    counts: dict[str, dict[str, int]],
) -> models.Driver:
    jolpica_id = str(_required(driver_data, "driverId", "driver"))
    name = " ".join(
        str(value)
        for value in (driver_data.get("givenName"), driver_data.get("familyName"))
        if value
    )
    values = {
        "jolpica_id": jolpica_id,
        "name": name or jolpica_id,
        "nationality": driver_data.get("nationality"),
    }
    driver = db.scalar(
        select(models.Driver).where(models.Driver.jolpica_id == jolpica_id)
    )
    if not driver:
        driver = models.Driver(**values)
        db.add(driver)
        db.flush()
        counts["drivers"]["created"] += 1
    elif _update_values(driver, values):
        counts["drivers"]["updated"] += 1
    return driver


def _upsert_constructor(
    constructor_data: Optional[dict[str, Any]],
    db: Session,
    counts: dict[str, dict[str, int]],
) -> Optional[models.Constructor]:
    if constructor_data is None:
        return None
    if not isinstance(constructor_data, dict):
        raise JolpicaSyncError("Invalid constructor response")

    jolpica_id = str(_required(constructor_data, "constructorId", "constructor"))
    values = {
        "jolpica_id": jolpica_id,
        "name": str(_required(constructor_data, "name", f"constructor {jolpica_id}")),
        "nationality": constructor_data.get("nationality"),
    }
    constructor = db.scalar(
        select(models.Constructor).where(
            models.Constructor.jolpica_id == jolpica_id
        )
    )
    if not constructor:
        constructor = models.Constructor(**values)
        db.add(constructor)
        db.flush()
        counts["constructors"]["created"] += 1
    elif _update_values(constructor, values):
        counts["constructors"]["updated"] += 1
    return constructor


def _upsert_race(
    race_data: dict[str, Any],
    year: int,
    db: Session,
    counts: dict[str, dict[str, int]],
) -> models.Race:
    source_year = _optional_int(_required(race_data, "season", "race"))
    if source_year != year:
        raise JolpicaSyncError(f"Jolpica returned a race outside season {year}")

    round_number = _optional_int(_required(race_data, "round", "race"))
    if round_number is None:
        raise JolpicaSyncError("Jolpica returned a race without a round")

    circuit_data = _required(race_data, "Circuit", f"race round {round_number}")
    if not isinstance(circuit_data, dict):
        raise JolpicaSyncError(f"Invalid circuit for race round {round_number}")
    circuit = _upsert_circuit(circuit_data, db, counts)

    try:
        race_date = date.fromisoformat(str(_required(race_data, "date", "race")))
    except ValueError as error:
        raise JolpicaSyncError(f"Invalid date for race round {round_number}") from error

    values = {
        "name": str(_required(race_data, "raceName", f"race round {round_number}")),
        "season": year,
        "round": round_number,
        "race_date": race_date,
        "circuit_id": circuit.id,
    }
    race = db.scalar(
        select(models.Race).where(
            models.Race.season == year,
            models.Race.round == round_number,
        )
    )
    if not race:
        race = models.Race(**values)
        db.add(race)
        db.flush()
        counts["races"]["created"] += 1
    elif _update_values(race, values):
        counts["races"]["updated"] += 1
    return race


def _fastest_lap_time_ms(result_data: dict[str, Any]) -> Optional[int]:
    fastest_lap = result_data.get("FastestLap")
    if fastest_lap is None:
        return None
    if not isinstance(fastest_lap, dict):
        raise JolpicaSyncError("Invalid fastest lap response")
    lap_time = fastest_lap.get("Time")
    if not isinstance(lap_time, dict):
        return None
    return _optional_int(lap_time.get("millis"))


def _upsert_race_results(
    race_data: dict[str, Any],
    year: int,
    db: Session,
    counts: dict[str, dict[str, int]],
) -> None:
    race = _upsert_race(race_data, year, db, counts)
    results = _required(race_data, "Results", f"race round {race.round}")
    if not isinstance(results, list):
        raise JolpicaSyncError(f"Invalid results for race round {race.round}")

    for result_data in results:
        if not isinstance(result_data, dict):
            raise JolpicaSyncError(f"Invalid race result for race round {race.round}")
        driver_data = _required(result_data, "Driver", "race result")
        if not isinstance(driver_data, dict):
            raise JolpicaSyncError("Invalid driver in race result")
        driver = _upsert_driver(driver_data, db, counts)
        constructor = _upsert_constructor(result_data.get("Constructor"), db, counts)

        values = {
            "constructor_id": constructor.id if constructor else None,
            "grid_position": _optional_int(result_data.get("grid")),
            "position": _optional_int(result_data.get("position")),
            "points": _required_float(
                _required(result_data, "points", "race result"), "race result"
            ),
            "status": result_data.get("status"),
            "fastest_lap_time_ms": _fastest_lap_time_ms(result_data),
        }
        result = db.scalar(
            select(models.RaceResult).where(
                models.RaceResult.race_id == race.id,
                models.RaceResult.driver_id == driver.id,
            )
        )
        if not result:
            db.add(models.RaceResult(race_id=race.id, driver_id=driver.id, **values))
            counts["race_results"]["created"] += 1
        elif _update_values(result, values):
            counts["race_results"]["updated"] += 1


def _upsert_sprint_results(
    race_data: dict[str, Any],
    year: int,
    db: Session,
    counts: dict[str, dict[str, int]],
) -> None:
    race = _upsert_race(race_data, year, db, counts)
    results = _required(race_data, "SprintResults", f"sprint round {race.round}")
    if not isinstance(results, list):
        raise JolpicaSyncError(f"Invalid sprint results for race round {race.round}")

    for result_data in results:
        if not isinstance(result_data, dict):
            raise JolpicaSyncError(f"Invalid sprint result for race round {race.round}")
        driver_data = _required(result_data, "Driver", "sprint result")
        if not isinstance(driver_data, dict):
            raise JolpicaSyncError("Invalid driver in sprint result")
        driver = _upsert_driver(driver_data, db, counts)
        constructor = _upsert_constructor(result_data.get("Constructor"), db, counts)

        values = {
            "constructor_id": constructor.id if constructor else None,
            "grid_position": _optional_int(result_data.get("grid")),
            "position": _optional_int(result_data.get("position")),
            "points": _required_float(
                _required(result_data, "points", "sprint result"), "sprint result"
            ),
            "status": result_data.get("status"),
        }
        result = db.scalar(
            select(models.SprintResult).where(
                models.SprintResult.race_id == race.id,
                models.SprintResult.driver_id == driver.id,
            )
        )
        if not result:
            db.add(models.SprintResult(race_id=race.id, driver_id=driver.id, **values))
            counts["sprint_results"]["created"] += 1
        elif _update_values(result, values):
            counts["sprint_results"]["updated"] += 1


def sync_season(
    year: int,
    db: Session,
    completed: Optional[bool] = None,
    request_get: Callable[..., requests.Response] = requests.get,
    current_year: Optional[int] = None,
) -> dict[str, Any]:
    """Synchronize one season without committing the database transaction."""
    calendar_races = _fetch_races(year, "races", request_get)
    race_results = _fetch_races(year, "results", request_get)
    sprint_results = _fetch_races(year, "sprint", request_get)

    counts = _empty_counts()
    target_completed = (
        completed
        if completed is not None
        else year < (current_year if current_year is not None else date.today().year)
    )

    season = db.scalar(select(models.Season).where(models.Season.year == year))
    if not season:
        season = models.Season(year=year, is_completed=target_completed)
        db.add(season)
        counts["seasons"]["created"] += 1
    elif _update_values(season, {"is_completed": target_completed}):
        counts["seasons"]["updated"] += 1

    # The session used by the API disables autoflush. Insert the parent season
    # before creating races that reference it with a foreign key.
    db.flush()

    for race_data in calendar_races:
        if not isinstance(race_data, dict):
            raise JolpicaSyncError(f"Invalid calendar race for {year}")
        _upsert_race(race_data, year, db, counts)

    for race_data in race_results:
        if not isinstance(race_data, dict):
            raise JolpicaSyncError(f"Invalid result race for {year}")
        _upsert_race_results(race_data, year, db, counts)

    for race_data in sprint_results:
        if not isinstance(race_data, dict):
            raise JolpicaSyncError(f"Invalid sprint race for {year}")
        _upsert_sprint_results(race_data, year, db, counts)

    db.flush()
    recalculate_season_history(year, db)
    db.flush()
    return {
        "season": year,
        "is_completed": target_completed,
        **counts,
    }
