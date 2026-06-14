# Clinical Trial Data Pipeline (Junior-level)

Simple prototype that ingests clinical trial CSV data into a SQLite database,
performs minimal validation, and shows a couple of analytics queries.

Quick start

1. Create a virtualenv and activate it (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the sample pipeline (reads `sample_data/trials.csv`):

```bash
python src/run_pipeline.py
```

4. Run tests:

```bash
pytest -q
```

What this includes

- `src/ingest.py`: functions to ingest CSV data into SQLite with simple validation.
- `src/run_pipeline.py`: small runner that ingests sample data and prints analytics.
- `tests/test_ingest.py`: unit test for the ingest function.
- `sample_data/trials.csv`: tiny example dataset.

This is a focused, junior-level solution. If you want, I can:
- Add Dockerfile
- Replace SQLite with Postgres
- Add more robust validation and logging
