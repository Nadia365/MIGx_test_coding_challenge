-- Clinical Trial Data Pipeline — normalized schema
-- One studies row per trial; child tables for repeating XML fields.

PRAGMA foreign_keys = ON;

-- Main trial record (one row per nct_id)
CREATE TABLE IF NOT EXISTS studies (
    nct_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    study_type TEXT,
    phase TEXT,
    status TEXT,
    start_date TEXT,
    completion_date TEXT,
    enrollment INTEGER,
    source_file TEXT,
    ingested_at TEXT DEFAULT (datetime('now'))
);

-- Diseases / conditions (one row per condition per trial)
CREATE TABLE IF NOT EXISTS study_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    condition_name TEXT NOT NULL,
    FOREIGN KEY (nct_id) REFERENCES studies(nct_id) ON DELETE CASCADE
);

-- Treatments / drugs (one row per intervention per trial)
CREATE TABLE IF NOT EXISTS study_interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    intervention_name TEXT NOT NULL,
    intervention_type TEXT,
    FOREIGN KEY (nct_id) REFERENCES studies(nct_id) ON DELETE CASCADE
);

-- Trial sites (one row per location per trial)
CREATE TABLE IF NOT EXISTS study_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    country TEXT,
    city TEXT,
    state TEXT,
    FOREIGN KEY (nct_id) REFERENCES studies(nct_id) ON DELETE CASCADE
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_studies_study_type ON studies(study_type);
CREATE INDEX IF NOT EXISTS idx_studies_phase ON studies(phase);
CREATE INDEX IF NOT EXISTS idx_studies_status ON studies(status);
CREATE INDEX IF NOT EXISTS idx_conditions_nct_id ON study_conditions(nct_id);
CREATE INDEX IF NOT EXISTS idx_conditions_name ON study_conditions(condition_name);
CREATE INDEX IF NOT EXISTS idx_interventions_nct_id ON study_interventions(nct_id);
CREATE INDEX IF NOT EXISTS idx_interventions_name ON study_interventions(intervention_name);
CREATE INDEX IF NOT EXISTS idx_locations_nct_id ON study_locations(nct_id);
CREATE INDEX IF NOT EXISTS idx_locations_country ON study_locations(country);
