import os
from pathlib import Path
from src.ingest import ingest_csv, simple_analytics


def main():
    repo_root = Path(__file__).resolve().parents[1]
    sample_csv = repo_root / 'sample_data' / 'trials.csv'
    db_path = repo_root / 'data' / 'trials.db'
    db_path.parent.mkdir(exist_ok=True)

    inserted = ingest_csv(str(sample_csv), str(db_path))
    print(f'Inserted {inserted} rows into {db_path}')

    analytics = simple_analytics(str(db_path))
    print('Trials by phase:')
    for phase, cnt in analytics['by_phase'].items():
        print(f'  {phase}: {cnt}')

    print('\nTop conditions:')
    for cond, cnt in analytics['top_conditions']:
        print(f'  {cond}: {cnt}')


if __name__ == '__main__':
    main()
