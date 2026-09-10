"""AI helpers for summarizing and discussing the latest standings snapshot."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import requests

DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "bdl.db"
DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


def get_latest_snapshot(season: int) -> list[dict[str, Any]]:
	"""Return the latest non-legacy standings rows with team and conference names."""
	if not DATABASE_PATH.exists():
		raise RuntimeError(f"Database not found at {DATABASE_PATH}.")

	with sqlite3.connect(DATABASE_PATH) as connection:
		connection.row_factory = sqlite3.Row
		rows = connection.execute(
			"""
			SELECT
				s.season,
				s.snapshot_date,
				c.name AS conference,
				t.city,
				t.name AS mascot,
				t.abbreviation,
				s.wins,
				s.losses,
				s.win_percentage,
				s.games_behind,
				s.home_record,
				s.away_record,
				s.conference_record
			FROM standings AS s
			JOIN teams AS t ON t.id = s.team_id
			JOIN conferences AS c ON c.id = s.conference_id
			WHERE s.season = ?
			  AND s.snapshot_date <> 'legacy'
			  AND s.snapshot_date = (
				  SELECT MAX(snapshot_date)
				  FROM standings
				  WHERE season = ? AND snapshot_date <> 'legacy'
			  )
			ORDER BY c.name, s.wins DESC, s.losses ASC, t.city ASC
			""",
			(season, season),
		).fetchall()
	return [dict(row) for row in rows]


def build_snapshot_context(season: int) -> str:
	"""Serialize the latest season snapshot for use as model context."""
	rows = get_latest_snapshot(season)
	if not rows:
		return f"No non-legacy standings snapshot exists for the {season} season."
	return json.dumps(rows, indent=2, default=str)


def call_ai(user_prompt: str, season: int, history: list[dict[str, str]] | None = None) -> str:
	"""Send a user prompt and latest database snapshot to an OpenAI-compatible API."""
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("Missing OPENAI_API_KEY. Set it before using the AI features.")

	messages: list[dict[str, str]] = [
		{
			"role": "system",
			"content": (
				"You are an assistant for a college football standings app. "
				"Use only the supplied database snapshot when answering questions "
				"about standings. Say when the snapshot does not contain the answer. "
				"Keep answers concise and readable."
			),
		},
		{
			"role": "system",
			"content": f"Latest database snapshot for season {season}:\n{build_snapshot_context(season)}",
		},
	]
	messages.extend(history or [])
	messages.append({"role": "user", "content": user_prompt})

	try:
		response = requests.post(
			os.getenv("OPENAI_API_URL", DEFAULT_API_URL),
			headers={"Authorization": f"Bearer {api_key}"},
			json={
				"model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
				"messages": messages,
				"temperature": 0.2,
			},
			timeout=60,
		)
	except requests.RequestException as error:
		raise RuntimeError(f"Unable to reach the AI API: {error}") from error
	if not response.ok:
		raise RuntimeError(
			f"AI API request failed with HTTP {response.status_code}: {response.text}"
		)

	try:
		return response.json()["choices"][0]["message"]["content"].strip()
	except (KeyError, IndexError, TypeError, ValueError) as error:
		raise RuntimeError("AI API returned an unexpected response format.") from error
