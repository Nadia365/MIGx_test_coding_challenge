"""
Load validated study records into SQLite.
"""

import sqlite3


def _delete_children(conn: sqlite3.Connection, nct_id: str) -> None:
    """Remove old child rows before re-inserting (handles reloads)."""
    for table in ("study_conditions", "study_interventions", "study_locations"):
        conn.execute(f"DELETE FROM {table} WHERE nct_id = ?", (nct_id,))


def load_records(conn: sqlite3.Connection, records: list[dict]) -> dict[str, int]:
    """
    Insert or replace studies and their child rows.
    Returns row counts per table for this batch.
    """
    counts = {
        "studies": 0,
        "study_conditions": 0,
        "study_interventions": 0,
        "study_locations": 0,
    }

    study_sql = """
        INSERT OR REPLACE INTO studies (
            nct_id, title, study_type, phase, status,
            start_date, completion_date, enrollment, source_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for record in records:
        study = record["study"]
        nct_id = study["nct_id"]

        conn.execute(
            study_sql,
            (
                nct_id,
                study["title"],
                study.get("study_type"),
                study.get("phase"),
                study.get("status"),
                study.get("start_date"),
                study.get("completion_date"),
                study.get("enrollment"),
                study.get("source_file"),
            ),
        )
        counts["studies"] += 1

        _delete_children(conn, nct_id)

        for cond in record.get("conditions", []):
            conn.execute(
                "INSERT INTO study_conditions (nct_id, condition_name) VALUES (?, ?)",
                (nct_id, cond["condition_name"]),
            )
            counts["study_conditions"] += 1

        for inter in record.get("interventions", []):
            conn.execute(
                """INSERT INTO study_interventions
                   (nct_id, intervention_name, intervention_type)
                   VALUES (?, ?, ?)""",
                (nct_id, inter["intervention_name"], inter.get("intervention_type")),
            )
            counts["study_interventions"] += 1

        for loc in record.get("locations", []):
            conn.execute(
                """INSERT INTO study_locations (nct_id, country, city, state)
                   VALUES (?, ?, ?, ?)""",
                (nct_id, loc.get("country"), loc.get("city"), loc.get("state")),
            )
            counts["study_locations"] += 1

    conn.commit()
    return counts
