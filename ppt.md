# Clinical Trial Pipeline — Presentation Notes

Simple notes for each phase: what we did, how we did it, and why.

---

# Phase 0: Data Exploration (Done)

## What is this dataset?

This is a collection of **103,509 clinical trial records** from ClinicalTrials.gov (the U.S. public registry of medical research studies).

Each record describes **one study** — for example: *"We're testing drug X on patients with disease Y, in Phase 2, in Charleston, USA."*

**Why explore first?**  
Before building tables or code, you need to look at the data — what's inside, what's missing, what's messy. It's like opening a few boxes from a shipment before designing the warehouse.

| Item | Detail |
|------|--------|
| Location | `sample_data/archive.zip.download/archive.zip` |
| Format | ZIP of XML files (one file per trial) |
| Size | ~2.8 GB, 103,509 files |

## What we built

- **Script:** `src/explore_data.py`
- **Sample files:** `tests/fixtures/NCT00000102.xml`, `NCT00000125.xml`

## How it works (6 steps)

1. Find the zip file in `sample_data/`
2. Open zip **without** extracting everything (saves time and disk space)
3. Read a **sample** of files (default 200; we used 300)
4. Parse each XML with Python's built-in `ElementTree`
5. Count missing values, multi-condition trials, phases, statuses
6. Print a report to the terminal

**Run it:**
```bash
python src/explore_data.py --sample-size 300
```

## Key findings (300-study sample)

| Finding | Result | Why it matters |
|---------|--------|----------------|
| Total files | 103,509 | Too big for dev — use a subset later |
| Missing completion_date | ~31% | Timeline analytics need NULL handling |
| Multi-condition trials | ~37% | Need separate table for conditions |
| Multi-intervention trials | ~30% | Need separate table for interventions |
| Multi-location trials | ~14% | Need separate table for locations |
| Date formats | Text like "December 1990" | Need cleaning in Phase 2 |

## Interview one-liner (Phase 0)

> "I profiled 300 XML studies from the zip, found multi-value fields and messy dates, and used that to decide how to design the database."

---

# Phase 1: Schema Design (Done)

## What is this phase?

After exploration, we **designed and created the database structure** — the empty "containers" where trial data will live.

Think of it like designing **filing cabinets and folders** before you put papers in them.

**This phase does NOT load data yet.** Tables are created but empty until Phase 2 (ETL).

## What we built

| File | What it does |
|------|--------------|
| `src/db/schema.sql` | SQL that defines the 4 tables and indexes |
| `src/db/connection.py` | Helper functions to open DB and run schema |
| `src/config.py` | Stores paths (where is the zip, where is the DB) |
| `src/init_db.py` | Small script you run to create the database |
| `tests/test_schema.py` | Tests that tables are created correctly |

**Database file created:** `data/processed/trials.db`

## Why 4 tables instead of 1?

Exploration showed that **one trial can have many conditions, drugs, and locations**.

**Bad approach (one big table):**
```
nct_id | title | conditions              | drugs
NCT001 | Trial | Diabetes; Heart Disease | Drug A; Drug B
```
Hard to count, hard to search, easy to get wrong answers.

**Good approach (4 linked tables):**

```
studies              → one row per trial (main info)
study_conditions     → one row per disease
study_interventions  → one row per drug/treatment
study_locations      → one row per city/country
```

They connect through **`nct_id`** — the trial's unique ID (like a student ID linking to their courses).

## The 4 tables explained simply

### 1. `studies` — Main trial record

| Column | Meaning | Example |
|--------|---------|---------|
| nct_id | Unique trial ID (primary key) | NCT00000102 |
| title | Study name | Congenital Adrenal Hyperplasia study |
| study_type | Interventional or Observational | Interventional |
| phase | Research phase | Phase 2 |
| status | Completed, Recruiting, etc. | Completed |
| start_date | When trial started | February 1994 (text for now) |
| completion_date | When trial ended | Often empty |
| enrollment | Number of participants | 1636 |

### 2. `study_conditions` — Diseases studied

| Column | Meaning |
|--------|---------|
| nct_id | Links to the trial |
| condition_name | Disease name, e.g. Diabetes |

One trial with 3 diseases = 3 rows here.

### 3. `study_interventions` — Treatments tested

| Column | Meaning |
|--------|---------|
| nct_id | Links to the trial |
| intervention_name | Drug name, e.g. Nifedipine |
| intervention_type | e.g. Drug, Procedure |

### 4. `study_locations` — Where trials run

| Column | Meaning |
|--------|---------|
| nct_id | Links to the trial |
| country | e.g. United States |
| city | e.g. Charleston |
| state | e.g. South Carolina |

## How we implemented it — step by step

### Step 1: Write `schema.sql`

We wrote SQL `CREATE TABLE` statements for all 4 tables.

- `nct_id` is the **primary key** on `studies` (unique identifier)
- Child tables use **foreign keys** pointing to `studies(nct_id)`
- `ON DELETE CASCADE` means: if you delete a study, its conditions/drugs/locations are deleted too (no orphan rows)

### Step 2: Add indexes

Indexes speed up searches. We added them on columns used in analytics:

- `phase`, `status`, `study_type` on `studies`
- `condition_name` on `study_conditions`
- `country` on `study_locations`

**Simple analogy:** An index is like a book's index — helps you find things faster.

### Step 3: Write `connection.py`

Two main functions:

- `init_database()` — reads `schema.sql` and runs it against SQLite
- `list_tables()` — returns table names (used for checking and tests)
- `get_connection()` — opens the database file

### Step 4: Write `config.py`

One place for all paths so we don't hard-code folders everywhere:

- `DB_PATH` → `data/processed/trials.db`
- `ZIP_PATH` → sample_data zip
- `MAX_STUDIES` → 500 (limit for dev, set via env var)

### Step 5: Write `init_db.py`

A simple script you run once:

```bash
python -m src.init_db
```

It prints:
```
Tables created:
  - studies
  - study_conditions
  - study_interventions
  - study_locations
```

### Step 6: Write tests

`tests/test_schema.py` checks:
1. All 4 tables exist after running schema
2. You can insert a row into `studies`

Run: `pytest tests/test_schema.py -q`

## Why these design choices?

| Choice | Why |
|--------|-----|
| **SQLite** | No server to install — reviewer runs one command and it works |
| **4 tables (normalized)** | Exploration proved multi-value fields — one flat table would break analytics |
| **TEXT for dates (for now)** | Raw XML has messy dates — we clean in Phase 2, store simply first |
| **Foreign keys** | Keeps data linked correctly — every condition must belong to a real trial |
| **Indexes** | Challenge asks for analytics by phase, condition, country — indexes help |
| **schema.sql separate from Python** | SQL lives in its own file — easy to read and review |
| **IF NOT EXISTS** | Safe to run `init_db` multiple times without errors |

## How to check tables were created

**Option A — run init script:**
```bash
python -m src.init_db
```

**Option B — SQLite command line:**
```bash
sqlite3 data/processed/trials.db ".tables"
```

**Option C — run tests:**
```bash
pytest tests/test_schema.py -q
```

**Expected:** 4 tables, 0 rows (empty until Phase 2 loads data).

## Simple example — how one trial will look in the DB

Trial **NCT00000102** (after Phase 2 loads it):

**studies** (1 row)
| nct_id | title | phase | status |
|--------|-------|-------|--------|
| NCT00000102 | Congenital Adrenal Hyperplasia... | Phase 1/Phase 2 | Completed |

**study_conditions** (1 row)
| nct_id | condition_name |
|--------|----------------|
| NCT00000102 | Congenital Adrenal Hyperplasia |

**study_interventions** (1 row)
| nct_id | intervention_name | intervention_type |
|--------|-------------------|-------------------|
| NCT00000102 | Nifedipine | Drug |

**study_locations** (1 row)
| nct_id | city | country |
|--------|------|---------|
| NCT00000102 | Charleston | United States |

## Diagram — tables linked together

```
                    studies
                 (nct_id = main ID)
                       |
       +---------------+---------------+
       |               |               |
study_conditions  study_interventions  study_locations
 (diseases)         (drugs)            (places)
```

## What Phase 1 did NOT do

| Not done yet | Comes in |
|--------------|----------|
| Load XML data into tables | Phase 2 — ETL |
| Clean dates | Phase 2 — transform |
| Validate / quarantine bad rows | Phase 4 |
| Analytics queries | Phase 5 |
| Docker | Phase 6 |

## Interview one-liner (Phase 1)

> "Based on exploration, I designed four normalized SQLite tables — studies plus child tables for conditions, interventions, and locations — linked by nct_id. I wrote schema.sql with foreign keys and indexes for the analytics questions, and a simple init_db script to create the database. Tables are empty until the ETL phase loads data from XML."

## Junior summary — remember this

1. **Exploration told us** → need 4 tables, not 1  
2. **schema.sql** → defines the tables  
3. **init_db.py** → creates `data/processed/trials.db`  
4. **Tables are empty** → Phase 2 will fill them  
5. **nct_id** → the link between all tables  

---

# What's next: Phase 3 — Multi-source connectors

CSV, API, and SQL connectors feeding the same ETL pipeline.

---

# Phase 2: ETL Pipeline (Done)

## What is this phase?

Phase 1 built **empty tables**. Phase 2 **fills them** with data from XML files.

**Analogy:** Phase 1 = filing cabinets. Phase 2 = sorting papers from XML boxes into the right drawers.

## The 3 steps (E → T → L)

| Step | Name | What happens |
|------|------|--------------|
| **E** | Extract | Read XML from zip; parse into Python dicts |
| **T** | Transform | Clean dates/phases; reject bad rows |
| **L** | Load | Insert rows into SQLite tables |

## Files we built

| File | Job |
|------|-----|
| `xml_parser.py` | Read one XML → study + conditions + interventions + locations |
| `xml_ingest.py` | Read many XML files from zip or test folder |
| `clean.py` | Fix dates (`February 1994` → `1994-02-01`), empty phase → `Unknown` |
| `validate.py` | Reject missing title/ID; save bad rows to quarantine CSV |
| `loader.py` | Write valid rows into `trials.db` |
| `pipeline.py` | Run all steps in order |
| `run_pipeline.py` | Command you type to run everything |

## How to run

```bash
python -m src.run_pipeline --fixtures          # 2 test studies (fast)
python -m src.run_pipeline --max-studies 500     # 500 from zip
```

## Example output (50 studies)

```
studies:           50 rows
study_conditions:  86 rows
study_interventions: 78 rows
study_locations:   136 rows
```

One trial with 3 diseases = 1 row in `studies` + 3 rows in `study_conditions`.

## Interview one-liner (Phase 2)

> "My ETL reads XML from the zip, parses each trial into a normalized structure, cleans dates and phases, validates required fields with quarantine for rejects, and loads into four SQLite tables using upsert on nct_id."

