import os
import sqlite3
import tempfile
from src.ingest import ingest_csv, create_connection


def test_ingest_csv_creates_rows():
    tmpdir = tempfile.TemporaryDirectory()
    csv_path = os.path.join(tmpdir.name, 'sample.csv')
    db_path = os.path.join(tmpdir.name, 'test.db')

    with open(csv_path, 'w') as f:
        f.write('nct_id,title,phase,condition,start_date,completion_date,intervention,location\n')
        f.write('TST0001,Test Trial,Phase 1,Cond A,2020-01-01,2020-12-31,Drug X,USA\n')

    inserted = ingest_csv(csv_path, db_path)
    assert inserted >= 0

    conn = create_connection(db_path)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM studies')
    cnt = cur.fetchone()[0]
    conn.close()
    assert cnt == 1
