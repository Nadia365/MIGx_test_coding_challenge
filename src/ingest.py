import sqlite3
import pandas as pd
from typing import Optional


def create_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        '''
    CREATE TABLE IF NOT EXISTS studies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nct_id TEXT UNIQUE,
        title TEXT,
        phase TEXT,
        condition TEXT,
        start_date TEXT,
        completion_date TEXT,
        intervention TEXT,
        location TEXT
    );
    '''
    )
    conn.commit()


def validate_df(df: pd.DataFrame) -> pd.DataFrame:
    required = ['nct_id', 'title']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Basic cleaning
    df = df.fillna("")
    # Normalize dates to ISO if possible
    for dcol in ['start_date', 'completion_date']:
        if dcol in df.columns:
            df[dcol] = pd.to_datetime(df[dcol], errors='coerce').dt.date.astype('str')
    return df


def ingest_csv(csv_path: str, db_path: str, table_name: str = 'studies') -> int:
    df = pd.read_csv(csv_path)
    df = validate_df(df)

    conn = create_connection(db_path)
    create_tables(conn)

    cur = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute(
                f"INSERT OR IGNORE INTO {table_name} (nct_id,title,phase,condition,start_date,completion_date,intervention,location) VALUES (?,?,?,?,?,?,?,?)",
                (
                    row.get('nct_id',''),
                    row.get('title',''),
                    row.get('phase',''),
                    row.get('condition',''),
                    row.get('start_date',''),
                    row.get('completion_date',''),
                    row.get('intervention',''),
                    row.get('location',''),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            # For junior-level, keep simple: skip bad rows
            continue

    conn.commit()
    conn.close()
    return inserted


def simple_analytics(db_path: str) -> dict:
    conn = create_connection(db_path)
    cur = conn.cursor()
    # Trials by phase
    cur.execute('SELECT phase, COUNT(*) FROM studies GROUP BY phase')
    by_phase = dict(cur.fetchall())

    # Most common conditions
    cur.execute('SELECT condition, COUNT(*) as cnt FROM studies GROUP BY condition ORDER BY cnt DESC LIMIT 5')
    top_conditions = cur.fetchall()
    conn.close()
    return {'by_phase': by_phase, 'top_conditions': top_conditions}


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python ingest.py <csv_path> <db_path>')
        sys.exit(1)
    csv_path = sys.argv[1]
    db_path = sys.argv[2]
    n = ingest_csv(csv_path, db_path)
    print(f'Inserted {n} rows into {db_path}')
