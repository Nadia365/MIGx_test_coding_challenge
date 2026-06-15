"""
Insert validated study records into SQLite.
"""

def load_records(conn, records):
    """
    Save studies and their child rows to the database.
    Returns how many rows were written in this batch.
    """
    counts = {
        "studies": 0,
        "study_conditions": 0,
        "study_interventions": 0,
        "study_locations": 0,
    }

    for record in records:
        study = record["study"]
        nct_id = study["nct_id"]

        # Upsert main study row
        conn.execute(
            """
            INSERT OR REPLACE INTO studies (
                nct_id, title, study_type, phase, status,
                start_date, completion_date, enrollment, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
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

        # Remove old child rows (in case we reload this study)
        conn.execute("DELETE FROM study_conditions WHERE nct_id = ?", (nct_id,))
        conn.execute("DELETE FROM study_interventions WHERE nct_id = ?", (nct_id,))
        conn.execute("DELETE FROM study_locations WHERE nct_id = ?", (nct_id,))

        for cond in record.get("conditions", []):
            conn.execute(
                "INSERT INTO study_conditions (nct_id, condition_name) VALUES (?, ?)",
                (nct_id, cond["condition_name"]),
            )
            counts["study_conditions"] += 1

        for inter in record.get("interventions", []):
            conn.execute(
                """
                INSERT INTO study_interventions
                    (nct_id, intervention_name, intervention_type)
                VALUES (?, ?, ?)
                """,
                (nct_id, inter["intervention_name"], inter.get("intervention_type")),
            )
            counts["study_interventions"] += 1

        for loc in record.get("locations", []):
            conn.execute(
                """
                INSERT INTO study_locations (nct_id, country, city, state)
                VALUES (?, ?, ?, ?)
                """,
                (nct_id, loc.get("country"), loc.get("city"), loc.get("state")),
            )
            counts["study_locations"] += 1

    conn.commit()
    return counts
