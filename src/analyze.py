"""Build a pandas table of conference standings for one season."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "bdl.db"
LOGO_DIRECTORY = DATABASE_PATH.parent.parent / "465"
LOGO_MANIFEST = LOGO_DIRECTORY / "teams.csv"


def _normalize(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum())


def _attach_local_logos(result: pd.DataFrame) -> pd.DataFrame:
    """Map each database team to its local logo using team identity fields."""
    if result.empty or not LOGO_MANIFEST.exists():
        result["logo_url"] = None
        return result

    manifest = pd.read_csv(LOGO_MANIFEST).fillna("")
    manifest["logo_key"] = manifest["team"].map(_normalize)

    def logo_for_row(row: pd.Series) -> str | None:
        candidates = {
            _normalize(row.get("city", "")),
            _normalize(row.get("abbreviation", "")),
            _normalize(f"{row.get('city', '')}{row.get('name', '')}"),
        }
        matches = manifest[
            manifest["logo_key"].map(
                lambda key: any(key and (key in candidate or candidate in key) for candidate in candidates)
            )
        ]
        if matches.empty:
            return None
        logo_file = matches.iloc[0]["logo_file"]
        logo_path = LOGO_DIRECTORY / str(logo_file)
        return str(logo_path) if logo_path.exists() else None

    result["logo_url"] = result.apply(logo_for_row, axis=1)
    return result


def get_conference_standings(season: int = 2026) -> pd.DataFrame:
    """Join standings, teams, and conferences with pandas."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        standings = pd.read_sql_query(
            """
            SELECT *
            FROM standings
            WHERE season = ?
                            AND snapshot_date <> 'legacy'
              AND snapshot_date = (
                  SELECT MAX(snapshot_date)
                  FROM standings
                  WHERE season = ?
                                        AND snapshot_date <> 'legacy'
              )
            """,
            connection,
            params=(season, season),
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        teams = pd.read_sql_query(
            """
            SELECT id AS team_id, city, name, abbreviation, logo_url
            FROM teams
            """,
            connection,
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        conferences = pd.read_sql_query(
            """
            SELECT id AS conference_id, name AS conference
            FROM conferences
            """,
            connection,
        )

    result = (
        standings.merge(
            teams,
            left_on="team_id",
            right_on="team_id",
            how="inner",
        )
        .merge(
            conferences,
            left_on="conference_id",
            right_on="conference_id",
            how="inner",
        )
        .loc[
            :,
            [
                "team_id",
                "season",
                "snapshot_date",
                "conference",
                "city",
                "name",
                "abbreviation",
                "logo_url",
                "wins",
                "losses",
                "win_percentage",
                "games_behind",
                "home_record",
                "away_record",
                "conference_record",
            ],
        ]
        .sort_values(
            ["conference", "wins", "losses", "city"],
            ascending=[True, False, True, True],
        )
        .reset_index(drop=True)
    )
    result = _attach_local_logos(result)
    return result


def get_standings_history(season: int = 2026) -> pd.DataFrame:
    """Return every non-legacy snapshot for a season, ranked by conference."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        return pd.read_sql_query(
            """
            SELECT
                s.team_id,
                s.snapshot_date,
                c.name AS conference,
                t.city,
                t.name,
                t.abbreviation,
                t.logo_url,
                s.wins,
                s.losses,
                s.win_percentage
            FROM standings AS s
            JOIN teams AS t ON t.id = s.team_id
            JOIN conferences AS c ON c.id = s.conference_id
            WHERE s.season = ? AND s.snapshot_date <> 'legacy'
            ORDER BY s.snapshot_date, c.name, s.wins DESC, s.losses ASC, t.city ASC
            """,
            connection,
            params=(season,),
        )
    return _attach_local_logos(history)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2026)
    args = parser.parse_args()

    standings = get_conference_standings(args.season)
    if standings.empty:
        print(f"No standings found for the {args.season} season.")
        return
    print(standings.to_string(index=False))


if __name__ == "__main__":
    main()
