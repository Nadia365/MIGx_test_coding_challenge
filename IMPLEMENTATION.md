# Implementation Guide & Interview Notes

This document explains **what we built**, **why we chose each approach**, and **how to talk about it in an interview**. Written at a junior data-engineering level — clear reasoning without over-engineering.

---

## Project context

**Challenge:** Build a clinical trial data pipeline (DE Technical Challenge).

**Dataset chosen:** Option 2 — [All Clinical Trials (Kaggle)](https://www.kaggle.com/datasets/skylord/all-clinical-trials)

**Local file:** `sample_data/archive.zip.download/archive.zip`
- ~103,509 XML files (one file per study)
- ClinicalTrials.gov bulk export, May 2020 snapshot
- ~2.8 GB total size

**Why Option 2?**
- Single comprehensive registry — good for schema design and analytics
- Same domain as the challenge examples (trials, phases, conditions, interventions)
- Easier to explain than multi-file Kaggle bundles (Option 1)

---

## Implementation phases (roadmap)

| Phase | Status | What we did |
|-------|--------|-------------|
| **0 — Data exploration** | Done | Profile XML sample, document quality issues |
| **1 — Schema design** | Done | `schema.sql`, `init_db`, tests |
| **2 — ETL core** | Done | XML → clean → validate → load |
| **3 — Multi-source** | Next | CSV, API, SQL connectors |
| **4 — Tests** | Planned | pytest with fixtures |
| **5 — Analytics** | Planned | 5 SQL queries |
| **6 — Docker & docs** | Planned | Container + final README |

---

## Phase 0: Data exploration (DONE)

### What we implemented

- **Script:** `src/explore_data.py`
- **Fixtures:** `tests/fixtures/NCT00000102.xml`, `NCT00000125.xml` (2 sample files for future tests)
- **Run command:**
  ```bash
  python src/explore_data.py --sample-size 300
  ```

### What the script does (simple flow)

1. Opens the zip file **without extracting all 103k files** (saves disk space and time)
2. Reads the first N XML files (default 200, we used 300)
3. Parses each file with Python's built-in `xml.etree.ElementTree`
4. Counts missing fields, multi-value cases, phases, statuses
5. Prints a readable report to the console

### Observations from our sample (300 studies)

| Finding | Count / detail | Impact on pipeline |
|---------|----------------|-------------------|
| Total files in zip | 103,509 | Use `MAX_STUDIES` cap for dev/demo |
| Parse errors | 0 in sample | Still handle errors in production path |
| Missing title | 0 | `title` is reliable as required field |
| Missing phase | 13 (~4%) | Map empty → `Unknown`; common for observational studies |
| Missing start_date | 40 (~13%) | Date parsing must allow NULL |
| Missing completion_date | 93 (~31%) | Duration analytics need NULL handling |
| Multi-condition studies | 111 (~37%) | **Need separate `study_conditions` table** |
| Multi-intervention studies | 90 (~30%) | **Need separate `study_interventions` table** |
| Multi-location studies | 42 (~14%) | **Need separate `study_locations` table** |
| Study types | 287 Interventional, 13 Observational | Supports "trials by study type" analytics |
| Top phases | Phase 2 (131), Phase 3 (77), Phase 1 (33) | Phase normalization needed (`Phase 1/Phase 2` exists) |
| Top statuses | Completed (247), Unknown (25), Withdrawn (15) | Completion-rate analytics use `status` |
| Date formats | `December 1990`, `March 2012`, etc. | Not ISO format — need date cleaning step |

### Data quality issues to handle (documented for README)

1. **Inconsistent date formats** — text like "February 1994" instead of `YYYY-MM-DD`
2. **Missing completion dates** — ~31% in our sample; timeline analysis must skip or partial-fill
3. **Multi-valued fields** — one study can have many conditions, interventions, and sites
4. **Phase inconsistencies** — `Phase 1/Phase 2`, `N/A`, or blank
5. **Large volume** — 103k files; full load is optional, subset for prototype

---

## Interview Q&A: Phase 0 (Data exploration)

### "Why did you explore the data before designing the schema?"

**Answer:** In data engineering you design the schema around the data, not the other way around. This XML archive has repeatable tags like `<condition>` and `<intervention>` — if I used one flat CSV-style table, I'd duplicate study info or lose multi-value relationships. Exploration showed ~37% of studies have multiple conditions, which directly led to the decision to normalize into child tables.

### "Why parse from the zip instead of extracting everything?"

**Answer:** The archive is ~2.8 GB with 103k files. Extracting everything is slow and uses a lot of disk. For exploration and development, reading directly from the zip with Python's `zipfile` module is enough. In production you'd likely use object storage and batch processing, but for a take-home prototype this is a practical trade-off.

### "Why use ElementTree instead of pandas read_csv?"

**Answer:** Our download is XML, not CSV. Each study is a separate XML file with nested and repeatable elements. ElementTree is built into Python — no extra dependency — and is fine for a junior-level prototype. For 103k files at scale you'd consider parallel parsing or a streaming XML library, but that would be over-engineering for this step.

### "How did you decide what fields to extract?"

**Answer:** I mapped XML tags to the analytics questions in the challenge:
- **Trials by type and phase** → `study_type`, `phase`
- **Common conditions** → `<condition>` tags
- **Intervention completion rates** → `<intervention>` + `overall_status`
- **Geographic distribution** → `<location>` / country
- **Timeline analysis** → `start_date`, `completion_date`

### "What would you do differently with more time?"

**Answer:** Profile the full 103k dataset (not just 300), build a data dictionary, and add Great Expectations or similar for automated quality checks. I'd also export a 500-row CSV subset for faster test runs.

---

## Phase 1: Schema design (DONE)

### What we implemented

| File | Purpose |
|------|---------|
| `src/db/schema.sql` | 4 tables + foreign keys + indexes |
| `src/db/connection.py` | Open DB, run schema, list tables |
| `src/config.py` | Paths (`ZIP_PATH`, `DB_PATH`) and `MAX_STUDIES` |
| `src/init_db.py` | CLI to create `data/processed/trials.db` |
| `tests/test_schema.py` | Tests that tables are created and accept inserts |

### Run Phase 1

```bash
python -m src.init_db
pytest tests/test_schema.py -q
```

### Tables created

| Table | Purpose |
|-------|---------|
| `studies` | One row per trial (`nct_id` primary key) |
| `study_conditions` | One row per disease/condition |
| `study_interventions` | One row per drug/treatment |
| `study_locations` | One row per trial site (city, country) |

### Interview Q&A: Phase 1

**"Why four tables instead of one?"**  
Exploration showed ~37% of trials have multiple conditions. One flat table would duplicate study info or use comma-separated strings that break analytics counts.

**"Why TEXT for dates instead of DATE type?"**  
Raw XML has messy text dates (`February 1994`). We store as TEXT during load and clean in the transform step (Phase 2). Keeps the schema simple for now.

**"Why indexes on phase, status, country, condition_name?"**  
Those columns appear in the five required analytics queries. Indexes speed up `GROUP BY` and `JOIN` filters on a larger dataset.

**"Why foreign keys with ON DELETE CASCADE?"**  
If we reload a study, deleting the parent row automatically removes old child rows — avoids orphan records.

---

## Phase 2: ETL core (DONE)

### What we implemented

| File | Purpose |
|------|---------|
| `src/ingest/xml_parser.py` | Parse XML → study + child rows |
| `src/ingest/xml_ingest.py` | Read from zip or fixtures |
| `src/transform/clean.py` | Dates, phases, enrollment |
| `src/transform/validate.py` | Valid/invalid split + quarantine CSV |
| `src/load/loader.py` | Insert into SQLite |
| `src/pipeline.py` | Orchestrates E-T-L |
| `src/run_pipeline.py` | CLI entry point |

### Run

```bash
python -m src.run_pipeline --fixtures          # quick: 2 studies
python -m src.run_pipeline --max-studies 500     # from zip
pytest -q
```

### Interview Q&A: Phase 2

**"Walk me through your ETL."**  
Extract: read XML from zip with `zipfile`, parse with `ElementTree`. Transform: clean dates/phases, validate required fields, quarantine rejects. Load: upsert into `studies`, replace child rows per trial.

**"Why delete child rows before re-insert?"**  
When reloading a study, conditions/interventions may change. Delete + insert keeps child data in sync with the parent.

---

## Phase 3: Multi-source (NEXT)

| Phase | Key files | Junior-level approach |
|-------|-----------|----------------------|
| ETL core | `xml_ingest.py`, `clean.py`, `validate.py`, `loader.py` | Simple functions, pandas DataFrames, bulk insert |
| Multi-source | `csv_ingest.py`, `api_ingest.py`, `sql_ingest.py` | Same output shape from each connector |
| Tests | `tests/test_*.py` | Use 2 XML fixtures, small CSV sample |
| Analytics | `queries.sql`, `report.py` | Plain SQL files, print results |
| Docker | `Dockerfile`, `docker-compose.yml` | One command to run pipeline |

### "Why three connectors but one dataset?" (interview answer)

The challenge says **choose one dataset** but also **support CSV, API, and SQL ingestion**. That means three **connector types**, not three different datasets. I'll use the same clinical trial data loaded different ways:
- **XML/CSV** — from the Kaggle download
- **API** — small live sample from ClinicalTrials.gov v2
- **SQL** — staging copy in a second SQLite file

All three feed the same normalized schema (ELT pattern).

---

## Design principles for this project

1. **Start simple, document trade-offs** — junior-level code that works beats advanced code that's half-finished
2. **Explore before building** — schema follows data
3. **Subset for dev, full load optional** — 103k files is real; cap with `MAX_STUDIES`
4. **Separate concerns lightly** — ingest / transform / load as folders, not one giant script
5. **Explain decisions in README and this doc** — interviewers care about *why*

---

## Files added in Phase 0

| File | Purpose |
|------|---------|
| `src/explore_data.py` | Data profiling script |
| `tests/fixtures/NCT00000102.xml` | Sample study for tests |
| `tests/fixtures/NCT00000125.xml` | Sample study with dates/enrollment |
| `.gitignore` | Ignore zip, db files, extracted data |
| `IMPLEMENTATION.md` | This document |
| `PLAN.md` | Full project roadmap |

---

## Files added in Phase 1

| File | Purpose |
|------|---------|
| `src/db/schema.sql` | Table DDL and indexes |
| `src/db/connection.py` | Database init helpers |
| `src/config.py` | Central paths and settings |
| `src/init_db.py` | Create database from CLI |
| `tests/test_schema.py` | Schema unit tests |
| `pytest.ini` | pytest pythonpath config |

---

## Next step

Run Phase 3: add CSV, API, and SQL connectors that feed the same pipeline.

```bash
python -m src.run_pipeline --max-studies 500
pytest -q
```
