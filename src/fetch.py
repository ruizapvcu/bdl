"""Fetch NCAAF data from balldontlie and upsert it into local SQLite files."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import requests

from create_databases import (
    DATABASE_DIR,
    DATABASE_PATH,
    create_conferences_database,
    create_standings_database,
    create_teams_database,
)

API_URL = "https://api.balldontlie.io/ncaaf/v1"
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2


def fetch_all(
    endpoint: str,
    api_key: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch every page returned by the API's cursor pagination."""
    request_params = dict(params or {})
    rows: list[dict[str, Any]] = []

    while True:
        url = f"{API_URL}/{endpoint}"
        last_error: Exception | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = None
            try:
                response = requests.get(
                    url,
                    headers={"Authorization": api_key},
                    params=request_params,
                    timeout=30,
                )

                if response.status_code not in {429, *range(500, 600)}:
                    response.raise_for_status()

                response.raise_for_status()
                payload = response.json()
                break
            except (requests.RequestException, ValueError) as error:
                last_error = error
                should_retry = (
                    not isinstance(error, requests.HTTPError)
                    or response is None
                    or response.status_code == 429
                    or response.status_code >= 500
                )
                if not should_retry:
                    raise RuntimeError(
                        f"The API request failed for '{endpoint}' "
                        f"with HTTP {response.status_code}: {response.text}"
                    ) from error
                if attempt < MAX_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS * 2 ** (attempt - 1))
        else:
            raise RuntimeError(
                f"Unable to call the BallDontLie API for '{endpoint}' after "
                f"{MAX_ATTEMPTS} attempts. Check your network connection or "
                "try again later."
            ) from last_error

        rows.extend(payload.get("data", []))

        next_cursor = payload.get("meta", {}).get("next_cursor")
        if not next_cursor:
            return rows
        request_params["cursor"] = next_cursor


def upsert_conferences(rows: list[dict[str, Any]]) -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executemany(
            """
            INSERT INTO conferences (id, name, abbreviation)
            VALUES (:id, :name, :abbreviation)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                abbreviation = excluded.abbreviation
            """,
            rows,
        )


def upsert_teams(rows: list[dict[str, Any]]) -> None:
    normalized_rows = [
        {
            **row,
            "conference_id": int(row["conference"]),
            "city": row["city"],
            "logo_url": row.get("logo_url") or row.get("logo"),
        }
        for row in rows
    ]

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executemany(
            """
            INSERT INTO teams (
                id, conference_id, city, name, full_name, abbreviation, logo_url
            )
            VALUES (
                :id, :conference_id, :city, :name, :full_name, :abbreviation, :logo_url
            )
            ON CONFLICT(id) DO UPDATE SET
                conference_id = excluded.conference_id,
                city = excluded.city,
                name = excluded.name,
                full_name = excluded.full_name,
                abbreviation = excluded.abbreviation,
                logo_url = excluded.logo_url
            """,
            normalized_rows,
        )


def upsert_standings(rows: list[dict[str, Any]], snapshot_date: str) -> None:
    normalized_rows = [
        {
            "team_id": row["team"]["id"],
            "conference_id": row["conference"]["id"],
            "season": row["season"],
            "snapshot_date": snapshot_date,
            "wins": row.get("wins"),
            "losses": row.get("losses"),
            "win_percentage": row.get("win_percentage"),
            "games_behind": row.get("games_behind"),
            "home_record": row.get("home_record"),
            "away_record": row.get("away_record"),
            "conference_record": row.get("conference_record"),
        }
        for row in rows
    ]

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executemany(
            """
            INSERT INTO standings (
                team_id, conference_id, season, snapshot_date, wins, losses, win_percentage,
                games_behind, home_record, away_record, conference_record
            )
            VALUES (
                :team_id, :conference_id, :season, :snapshot_date, :wins, :losses,
                :win_percentage, :games_behind, :home_record, :away_record,
                :conference_record
            )
            ON CONFLICT(team_id, season, snapshot_date) DO UPDATE SET
                conference_id = excluded.conference_id,
                wins = excluded.wins,
                losses = excluded.losses,
                win_percentage = excluded.win_percentage,
                games_behind = excluded.games_behind,
                home_record = excluded.home_record,
                away_record = excluded.away_record,
                conference_record = excluded.conference_record
            """,
            normalized_rows,
        )


def fetch_and_store(season: int, api_key: str) -> None:
    DATABASE_DIR.mkdir(exist_ok=True)
    create_conferences_database()
    create_teams_database()
    create_standings_database()

    conferences = fetch_all("conferences", api_key)
    teams = fetch_all("teams", api_key)
    standings = fetch_all("standings", api_key, {"season": season})
    snapshot_date = datetime.now(timezone.utc).date().isoformat()

    upsert_conferences(conferences)
    upsert_teams(teams)
    upsert_standings(standings, snapshot_date)
    print(
        f"Updated {len(conferences)} conferences, {len(teams)} teams, "
        f"and {len(standings)} standings for {season}."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument(
        "--api-key",
        default=os.getenv("BALLDONTLIE_API_KEY"),
        help="API key; defaults to BALLDONTLIE_API_KEY",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit(
            "Missing API key. Set BALLDONTLIE_API_KEY or pass --api-key."
        )
    try:
        fetch_and_store(args.season, args.api_key)
    except RuntimeError as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
