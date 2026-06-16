# Clinical Trial Data Pipeline

ETL pipeline for the DE technical challenge — parse ClinicalTrials.gov XML, clean/validate, load into SQLite, run 5 analytics queries.

**Data:** [Kaggle — All Clinical Trials](https://www.kaggle.com/datasets/skylord/all-clinical-trials)  
Put the zip at `sample_data/archive.zip.download/archive.zip` (~103k XML files, not in git).  
Without the zip you can use `--fixtures` (2 sample studies).

XML ingest is done. CSV/API/SQL connectors are not built yet.

---

## What it does

1. Read XML from zip or test fixtures
2. Clean dates/phases, validate required fields
3. Load into 4 SQLite tables
4. Bad rows → `data/quarantine/rejected_studies.csv`
5. Run 5 SQL queries from `src/analytics/queries.sql`

```
XML → parse → clean → validate → load → trials.db → report
                      ↓
              rejected_studies.csv
```

**Tables:** `studies`, `study_conditions`, `study_interventions`, `study_locations`  
One study can have many conditions/interventions/locations so they're separate tables, not one flat row.

---

## Setup

**Need:** Python 3.10+, pip

```bash
git clone <repo-url>
cd test_Coding_Challenge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: download the Kaggle zip to `sample_data/archive.zip.download/archive.zip`

```bash
# init db
python -m src.init_db

# quick run (no zip needed)
python -m src.run_pipeline --fixtures --report

# from zip, capped at 500 by default
python -m src.run_pipeline --max-studies 500 --report

pytest -q
```

Explore script if you want to poke at the raw XML first:
```bash
python src/explore_data.py --sample-size 300
```

---

## Docker

```bash
docker compose up --build
```

Runs tests, loads data (fixtures if no zip mounted), prints report.  
`MAX_STUDIES` (default 500) and `RUN_TESTS` (default 1) in `docker-compose.yml`.

Mount the zip in compose if you have it:
```yaml
volumes:
  - ./data:/app/data
  - ./sample_data/archive.zip.download:/app/sample_data/archive.zip.download:ro
```

---

## Validation rules

| Rule | What happens |
|------|--------------|
| Missing nct_id or title | Rejected |
| Bad nct_id format | Rejected |
| start_date after completion_date | Rejected |
| Bad XML | Rejected |
| Empty phase | → `Unknown` |
| Bad date | → NULL |
| Duplicate nct_id | Keep latest |

---

## Analytics

| # | Query |
|---|-------|
| 1 | Trials by type and phase |
| 2 | Top 10 conditions |
| 3 | Interventions with best completion rate |
| 4 | Geographic distribution |
| 5 | Avg duration by phase |

Completion rate = completed studies with intervention X / all studies with intervention X

---

## Design notes

- Sampled ~300 XML files before designing schema — lots of trials have multiple conditions
- Read from zip directly instead of extracting 103k files
- SQLite + plain Python CLI — easy to run locally, not meant for production scale
- Quarantine CSV so you can see what failed
- `MAX_STUDIES=500` by default so dev runs stay fast

**Limitations:** XML only, 2020 snapshot data, basic validation, no scheduler. Tests run on small fixtures not the full archive.

**Time:** ~3 days — day 1 explore + schema, day 2 ETL + validation, day 3 SQL + Docker + docs.

**Next steps if I had more time:** CSV/API/SQL ingest, Postgres, incremental loads, Airflow.

---

## Follow-up questions (short answers)

**Scale 100x?** S3 for raw files, parallel parsing, Postgres/Snowflake, incremental API sync instead of full reload.

**More data quality?** Stricter enums on status/phase, reject incomplete studies, range checks on enrollment, Great Expectations-style checks.

**GxP?** Audit logs, validated deployments, schema change control. This data is public registry stuff — no PHI here.

**Monitoring?** Row counts per stage, alert if quarantine rate spikes, track data freshness vs source.

**Security?** Encryption, secrets in a vault, RBAC. Again — public data in this project.

More detail in [STORY.md](STORY.md) and [IMPLEMENTATION.md](IMPLEMENTATION.md).

---

## Project layout

```
src/
  config.py, pipeline.py, run_pipeline.py
  ingest/       xml read + parse
  transform/    clean + validate
  load/         loader.py
  db/           schema.sql, connection.py
  analytics/    queries.sql, report.py
tests/          pytest (22 tests), fixtures/
data/           trials.db + quarantine (generated)
docker/         entrypoint.sh
```

---

## Links

- https://www.kaggle.com/datasets/skylord/all-clinical-trials
- https://clinicaltrials.gov
- https://clinicaltrials.gov/data-api/api
