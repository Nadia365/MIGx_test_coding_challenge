# Clinical Trial Data Pipeline

Junior-level prototype for the **DE Technical Challenge**.

**Status:** Phases 0–1 complete (data exploration + schema design). ETL and analytics are next.

**Primary dataset:** [Option 2 — All Clinical Trials (Kaggle)](https://www.kaggle.com/datasets/skylord/all-clinical-trials)

**Local data:** `sample_data/archive.zip.download/archive.zip` (~103,509 ClinicalTrials.gov XML files)

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Phase 0: explore a sample of the XML data
python src/explore_data.py --sample-size 300

# Phase 1: create empty database tables
python -m src.init_db
# or
python -m src.run_pipeline

# Run tests
pytest -q
```

---

## Project status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Data exploration | **Done** |
| 1 | Schema design | **Done** |
| 2 | ETL (parse, clean, load) | Planned |
| 3 | Multi-source (CSV, API, SQL) | Planned |
| 4 | Validation & tests | Planned |
| 5 | Analytics SQL | Planned |
| 6 | Docker & submission | Planned |

See [PLAN.md](PLAN.md), [IMPLEMENTATION.md](IMPLEMENTATION.md), and [ppt.md](ppt.md) for details.

---

## Phase 0: Data exploration

- Script: `src/explore_data.py`
- Sample fixtures: `tests/fixtures/NCT00000102.xml`, `NCT00000125.xml`

Key findings (300-study sample): multi-condition trials (~37%), missing completion dates (~31%), text date formats, 103k XML files total.

---

## Phase 1: Schema design

- DDL: `src/db/schema.sql`
- DB helpers: `src/db/connection.py`
- Config: `src/config.py`
- Init CLI: `python -m src.init_db`
- Database file: `data/processed/trials.db` (created locally, gitignored)

### Tables

| Table | Purpose |
|-------|---------|
| `studies` | One row per trial (`nct_id` primary key) |
| `study_conditions` | Diseases/conditions per trial |
| `study_interventions` | Drugs/treatments per trial |
| `study_locations` | Cities/countries per trial |

### Verify tables

```bash
python -m src.init_db
sqlite3 data/processed/trials.db ".tables"
pytest tests/test_schema.py -q
```

---

## Repository structure

```
src/
  explore_data.py       # Phase 0
  config.py
  init_db.py            # Phase 1
  run_pipeline.py       # runs init_db
  db/
    schema.sql
    connection.py
tests/
  fixtures/
  test_schema.py
PLAN.md
IMPLEMENTATION.md
ppt.md
```

---

## Design decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Dataset | Option 2 — All Clinical Trials | Comprehensive registry |
| Raw format | XML bulk archive | Actual Kaggle download |
| Schema | 4 normalized tables | Multi-value fields in exploration |
| Database | SQLite | Simple local setup for reviewers |

---

## References

- Dataset: https://www.kaggle.com/datasets/skylord/all-clinical-trials
- Reviewer GitHub (if private): `MIGx-user`
