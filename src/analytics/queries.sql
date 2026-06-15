-- Clinical Trial Analytics — 5 required business queries
-- Each block starts with: -- query: <name>

-- query: trials_by_type_and_phase
-- Q1: How many trials by study type and phase?
SELECT
    study_type,
    phase,
    COUNT(*) AS trial_count
FROM studies
GROUP BY study_type, phase
ORDER BY trial_count DESC, study_type, phase;

-- query: top_conditions
-- Q2: Most common conditions (top 10)
SELECT
    condition_name,
    COUNT(*) AS study_count
FROM study_conditions
GROUP BY condition_name
ORDER BY study_count DESC
LIMIT 10;

-- query: intervention_completion_rates
-- Q3: Interventions with highest completion rates
-- completion_rate = completed studies with intervention X / all studies with intervention X
SELECT
    si.intervention_name,
    COUNT(DISTINCT si.nct_id) AS total_studies,
    COUNT(DISTINCT CASE WHEN s.status = 'Completed' THEN si.nct_id END) AS completed_studies,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN s.status = 'Completed' THEN si.nct_id END)
        / COUNT(DISTINCT si.nct_id),
        1
    ) AS completion_rate_pct
FROM study_interventions si
INNER JOIN studies s ON si.nct_id = s.nct_id
GROUP BY si.intervention_name
HAVING COUNT(DISTINCT si.nct_id) >= 2
ORDER BY completion_rate_pct DESC, total_studies DESC
LIMIT 10;

-- query: geographic_distribution
-- Q4: Geographic distribution of trial sites
SELECT
    country,
    COUNT(*) AS site_count,
    COUNT(DISTINCT nct_id) AS study_count
FROM study_locations
WHERE country IS NOT NULL AND TRIM(country) != ''
GROUP BY country
ORDER BY site_count DESC;

-- query: timeline_by_phase
-- Q5: Average study duration (days) by phase where both dates exist
SELECT
    phase,
    COUNT(*) AS trials_with_dates,
    ROUND(AVG(julianday(completion_date) - julianday(start_date)), 0) AS avg_duration_days
FROM studies
WHERE start_date IS NOT NULL
  AND completion_date IS NOT NULL
GROUP BY phase
ORDER BY avg_duration_days DESC;
