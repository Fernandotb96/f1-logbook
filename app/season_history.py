from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def recalculate_season_history(season: int, db: Session) -> None:
    """Rebuild the calculated season history from the race results in the database."""
    season_record = db.scalar(
        select(models.Season).where(models.Season.year == season)
    )
    if not season_record:
        return

    rows = db.execute(
        select(
            models.RaceResult.driver_id,
            models.RaceResult.position,
            models.RaceResult.points,
        )
        .join(models.Race, models.RaceResult.race_id == models.Race.id)
        .where(models.Race.season == season)
    ).all()

    driver_stats = defaultdict(
        lambda: {
            "races_entered": 0,
            "wins": 0,
            "podiums": 0,
            "points": 0.0,
            "position_counts": defaultdict(int),
        }
    )
    highest_position = 0

    for driver_id, position, points in rows:
        stats = driver_stats[driver_id]
        stats["races_entered"] += 1
        stats["points"] += float(points)

        if position is not None:
            stats["position_counts"][position] += 1
            highest_position = max(highest_position, position)

            if position == 1:
                stats["wins"] += 1
            if position <= 3:
                stats["podiums"] += 1

    ordered_drivers = sorted(
        driver_stats.items(),
        key=lambda item: (
            -item[1]["points"],
            *(
                -item[1]["position_counts"][position]
                for position in range(1, highest_position + 1)
            ),
            item[0],
        ),
    )

    existing_histories = db.scalars(
        select(models.DriverSeasonHistory).where(
            models.DriverSeasonHistory.season == season
        )
    ).all()
    histories_by_driver = {history.driver_id: history for history in existing_histories}

    for championship_position, (driver_id, stats) in enumerate(ordered_drivers, start=1):
        history = histories_by_driver.pop(driver_id, None)
        if not history:
            history = models.DriverSeasonHistory(driver_id=driver_id, season=season)
            db.add(history)

        history.races_entered = stats["races_entered"]
        history.wins = stats["wins"]
        history.podiums = stats["podiums"]
        history.points = stats["points"]
        history.championship_position = championship_position
        history.is_champion = (
            season_record.is_completed and championship_position == 1
        )

    for history in histories_by_driver.values():
        db.delete(history)
