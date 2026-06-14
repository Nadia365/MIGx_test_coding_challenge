# Clinical Trial Data Pipeline

Junior-level prototype for the **DE Technical Challenge**.

**Status:** Phases 0–2 complete (exploration, schema, ETL). Phase 3 (multi-source) is next.

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

# Phase 2: load XML data into database
python -m src.run_pipeline --max-studies 500
python -m src.run_pipeline --fixtures   # quick demo: 2 studies

# Run tests
pytest -q
```

---

## Project status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Data exploration | **Done** |
| 1 | Schema design | **Done** |
| 2 | ETL (parse, clean, load) | **Done** |
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

## Phase 2: ETL pipeline (completed)

Loads XML trial data into the normalized SQLite tables.

```
XML (zip or fixtures)  →  Extract  →  Clean  →  Validate  →  Load  →  trials.db
                                              ↓
                                    data/quarantine/ (rejected rows)
```

| Step | File | What it does |
|------|------|--------------|
| Extract | `src/ingest/xml_parser.py` | Parse one XML file |
| Extract | `src/ingest/xml_ingest.py` | Read from zip or fixtures |
| Transform | `src/transform/clean.py` | Normalize dates, phases |
| Transform | `src/transform/validate.py` | Reject bad rows; quarantine CSV |
| Load | `src/load/loader.py` | Insert into 4 tables |
| Orchestrate | `src/pipeline.py` | Runs all steps |
| CLI | `src/run_pipeline.py` | Entry point |

### Validation rules

| Rule | Action |
|------|--------|
| Missing `nct_id` or `title` | Reject → quarantine |
| Invalid `nct_id` format | Reject |
| Empty phase | Map to `Unknown` |
| Bad/missing dates | Set NULL |
| Duplicate `nct_id` | Keep latest |

---

## Repository structure

```
src/
  explore_data.py       # Phase 0
  config.py
  init_db.py            # Phase 1
  pipeline.py           # Phase 2 orchestrator
  run_pipeline.py       # Phase 2 CLI
  ingest/
    xml_parser.py
    xml_ingest.py
  transform/
    clean.py
    validate.py
  load/
    loader.py
  db/
    schema.sql
    connection.py
tests/
  fixtures/
  test_schema.py
  test_xml_parser.py
  test_clean.py
  test_validate.py
  test_pipeline.py
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
