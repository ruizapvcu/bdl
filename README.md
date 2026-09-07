**Architecture & File Responsibilities**

**SPRINT 1: DATA PIPELINE**

* **`src/fetch.py`**
  * Runs on a GitHub Actions schedule.
  * Fetches live NCAAF data from the balldontlie endpoints (conferences, teams, standings).
  * Writes output to a dated snapshot (e.g., `data/2026-09-10.json`).
  * **STATUS:** SOURCE data. Must be committed to git.

* **`src/build_db.py`**
  * Runs automatically every time the Streamlit app starts.
  * Reads the committed JSON snapshots and builds a fresh SQLite database (`project.db`).
  * **STATUS:** DERIVED data. `project.db` MUST be in `.gitignore`.

* **`src/analyze.py`**
  * Houses all SQLite database logic.
  * Contains functions to query and JOIN the tables (e.g., matching teams to their conference standings).
  * Keeps the frontend clean of raw SQL.

---

**SPRINT 3: AI LAYER**

* **`src/summarize.py`**
  * Runs on a schedule after `fetch.py` finishes.
  * Passes current database state to the LLM (Gemini/Groq) to write a text overview of the FBS.
  * Outputs to `data/summary.md`.
  * **STATUS:** SOURCE data. Must be committed to git.

---

**SPRINT 2 & 3: DASHBOARD & CHAT**

* **`src/app.py`**
  * The Streamlit frontend and the only program running live during the showcase.
  * Calls `build_db.py` at startup to load the latest snapshot.
  * Uses `analyze.py` to display tables and multi-month trend charts of FBS records.
  * Reads and displays `data/summary.md`.
  * Hosts the live LLM chat interface strictly for answering user questions.
