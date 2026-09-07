**Architecture & File Responsibilities**

**SPRINT 1: DATA PIPELINE (Sep 10 – Sep 24)**
**Scrum Master:** Aaron | **Tester:** Krish

* **`src/fetch.py`** *(Assignees: Krish, Aaron, Robiel)*
  * Runs on a GitHub Actions schedule.
  * Fetches live NCAAF data from the balldontlie endpoints (conferences, teams, standings).
  * Writes output to a dated snapshot (e.g., `data/2026-09-10.json`).
  * **STATUS:** SOURCE data. Must be committed to git.

* **`src/build_db.py` & `src/analyze.py`** *(Assignee: Wyatt)*
  * Runs automatically every time the Streamlit app starts.
  * Reads the committed JSON snapshots and builds a fresh SQLite database (`project.db`).
  * Houses all SQLite database logic to JOIN tables and keep the frontend clean.
  * **STATUS:** DERIVED data. `project.db` MUST be in `.gitignore`.

---

**SPRINT 2: DASHBOARD & AUTOMATION (Oct 1 – Oct 15)**
**Scrum Master:** Krish | **Tester:** Robiel

* **`src/app.py`** *(Assignees: Aaron, Krish, Robiel)*
  * The Streamlit frontend and the only program running live during the showcase.
  * Calls `build_db.py` at startup to load the latest snapshot.
  * Uses `analyze.py` to display filtered tables and multi-month trend charts of FBS records.

* **`.github/workflows/refresh.yml`** *(Assignee: Wyatt)*
  * Schedules daily automated API fetching using GitHub Actions.
  * Automatically commits new snapshot JSON files to the repository.

---

**BUFFER & LAUNCH PHASE (Oct 22)**
**Scrum Master:** Robiel | **Tester:** Wyatt

* **Deployment & Secrets** *(Assignees: Robiel, Wyatt)*
  * Deploys `src/app.py` to Streamlit Community Cloud.
  * Configures LLM API keys securely in the cloud environment.

---

**SPRINT 3: AI LAYER & INTEGRATION (Oct 29 – Nov 12)**
**Scrum Master:** Wyatt | **Tester:** Aaron

* **`src/summarize.py`** *(Assignee: Krish)*
  * Runs on a schedule after `fetch.py` finishes.
  * Passes current database state to the LLM to write a text overview.
  * Outputs to `data/summary.md`.

* **`src/app.py` (AI Updates)** *(Assignees: Aaron, Robiel)*
  * Reads and displays `data/summary.md`.
  * Hosts the live LLM chat interface, strictly scoped to local SQLite context.

* **`.github/workflows/refresh.yml` (AI Updates)** *(Assignee: Wyatt)*
  * Updates the CI/CD pipeline to execute `src/summarize.py` automatically after data fetch.

---

**WRAP-UP & SHOWCASE (Nov 19 – Dec 10)**
**Scrum Master:** Aaron | **Tester:** Krish

* **`README.md` & Releases** *(Assignees: Aaron, Krish)*
  * Documents architecture and setup instructions.
  * Tags repository release `v1.0.0`.

* **Presentations** *(Assignees: Robiel, Wyatt)*
  * Builds slide deck and conducts live rehearsal walk-through.
  * Delivers final live demonstration on Dec 10.
