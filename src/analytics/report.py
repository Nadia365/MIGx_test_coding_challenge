"""
Run the 5 analytics SQL queries and print results.

Usage:
    python -m src.analytics.report
"""

import argparse

from src.config import DB_PATH, QUERIES_PATH
from src.db.connection import get_connection

# Friendly titles for each query in queries.sql
QUERY_TITLES = {
    "trials_by_type_and_phase": "1. Trials by study type and phase",
    "top_conditions": "2. Most common conditions (top 10)",
    "intervention_completion_rates": "3. Interventions — highest completion rates",
    "geographic_distribution": "4. Geographic distribution of trial sites",
    "timeline_by_phase": "5. Average study duration by phase (days)",
}


def load_queries(queries_path=None):
    """
    Read queries.sql and split it into named queries.
    Each query starts with a line like: -- query: trials_by_type_and_phase
    """
    path = queries_path or QUERIES_PATH
    text = path.read_text(encoding="utf-8")

    queries = []
    current_name = None
    current_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("-- query:"):
            # Save previous query before starting a new one
            if current_name and current_lines:
                sql = "\n".join(current_lines).strip()
                queries.append((current_name, sql))

            current_name = stripped.replace("-- query:", "").strip()
            current_lines = []

        elif current_name is not None:
            # Skip comment lines at the top of each query block
            if stripped.startswith("--") and len(current_lines) == 0:
                continue
            current_lines.append(line)

    # Don't forget the last query
    if current_name and current_lines:
        sql = "\n".join(current_lines).strip()
        queries.append((current_name, sql))

    return queries


def format_results(columns, rows):
    """Print query results as a simple text table."""
    if not rows:
        return "  (no rows)"

    lines = []
    lines.append("  ".join(columns))
    lines.append("  ".join("-" * len(c) for c in columns))

    for row in rows:
        cells = ["" if v is None else str(v) for v in row]
        lines.append("  ".join(cells))

    return "\n".join(lines)


def run_report(db_path=None, queries_path=None):
    """Run all queries and return results as a list of dicts."""
    queries = load_queries(queries_path)
    conn = get_connection(db_path)
    results = []

    try:
        for name, sql in queries:
            cur = conn.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            results.append({"name": name, "columns": columns, "rows": rows})
    finally:
        conn.close()

    return results


def print_report(db_path=None):
    """Run all queries and print them."""
    results = run_report(db_path=db_path)

    print("\n" + "=" * 60)
    print("CLINICAL TRIAL ANALYTICS REPORT")
    print("=" * 60)

    for item in results:
        title = QUERY_TITLES.get(item["name"], item["name"])
        print(f"\n{title}")
        print("-" * len(title))
        print(format_results(item["columns"], item["rows"]))

    print()


def main():
    parser = argparse.ArgumentParser(description="Run clinical trial analytics report")
    parser.add_argument("--db", default=DB_PATH, help="Path to trials.db")
    args = parser.parse_args()
    print_report(db_path=args.db)


if __name__ == "__main__":
    main()
