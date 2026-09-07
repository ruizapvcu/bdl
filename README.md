**Architecture & File Responsibilities**

**SPRINT 1: DATA PIPELINE**
**Scrum Master:** Aaron | **Tester:** Krish

* **`src/fetch.py`** *(Assignees: Krish, Aaron, Robiel)*
  * Runs on a GitHub Actions schedule.
  * Fetches live NCAAF data from the balldontlie endpoints (conferences, teams, standings).
  * Writes output to a dated snapshot (e.g., `data/2026-09-10.json`).
  * **STATUS:** SOURCE data. Must be committed to git.

* **`src/build_db.py`** *(Assignee: Wyatt)*
  * Runs automatically every time the Streamlit app starts.
  * Reads the committed JSON snapshots and builds a fresh SQLite database (`project.db`).
  * **STATUS:** DERIVED data. `project.db` MUST be in `.gitignore`.

* **`src/analyze.py`** *(Assignee: Wyatt)*
  * Houses all SQLite database logic.
  * Contains functions to query and JOIN the tables (e.g., matching teams to their conference standings).
  * Keeps the frontend clean of raw SQL.

---

**SPRINT 2: DASHBOARD & AUTOMATION**
**Scrum Master:** Krish | **Tester:** Robiel

* **`src/app.py`** *(Assignees: Aaron, Krish, Robiel)*
  * The Streamlit frontend and the only program running live during the showcase.
  * Calls `build_db.py` at startup to load the latest snapshot.
  * Uses `analyze.py` to display tables and multi-month trend charts of FBS records.

---

**SPRINT 3: AI LAYER & INTEGRATION**
**Scrum Master:** Wyatt | **Tester:** Aaron

* **`src/summarize.py`** *(Assignee: Krish)*
  * Runs on a schedule after `fetch.py` finishes.
  * Passes current database state to the LLM (Gemini/Groq) to write a text overview of the FBS.
  * Outputs to `data/summary.md`.
  * **STATUS:** SOURCE data. Must be committed to git.

* **`src/app.py` (AI Updates)** *(Assignees: Aaron, Robiel)*
  * Reads and displays `data/summary.md`.
  * Hosts the live LLM chat interface strictly for answering user questions.
