-- ============================================================
-- Student Success Analytics
-- SQL Analysis 03: Intervention Outcomes
-- ============================================================


-- ------------------------------------------------------------
-- 1. Number of interventions by type
-- ------------------------------------------------------------

SELECT
    intervention_type,
    COUNT(*) AS intervention_count

FROM interventions

GROUP BY intervention_type

ORDER BY intervention_count DESC;


-- ------------------------------------------------------------
-- 2. Intervention status
-- ------------------------------------------------------------

SELECT
    status,
    COUNT(*) AS intervention_count

FROM interventions

GROUP BY status

ORDER BY intervention_count DESC;


-- ------------------------------------------------------------
-- 3. Intervention outcomes
-- ------------------------------------------------------------

SELECT
    outcome,
    COUNT(*) AS intervention_count

FROM interventions

GROUP BY outcome

ORDER BY intervention_count DESC;


-- ------------------------------------------------------------
-- 4. Outcomes by intervention type
-- ------------------------------------------------------------

SELECT

    intervention_type,
    outcome,

    COUNT(*) AS intervention_count

FROM interventions

GROUP BY
    intervention_type,
    outcome

ORDER BY
    intervention_type,
    intervention_count DESC;


-- ------------------------------------------------------------
-- 5. Students receiving multiple interventions
-- ------------------------------------------------------------

SELECT

    student_id,

    COUNT(*) AS intervention_count

FROM interventions

GROUP BY student_id

HAVING intervention_count > 1

ORDER BY intervention_count DESC;


-- ------------------------------------------------------------
-- 6. Intervention workload by advisor
-- ------------------------------------------------------------

SELECT

    advisor,

    COUNT(*) AS assigned_cases,

    SUM(
        CASE
            WHEN status = 'Completed'
            THEN 1
            ELSE 0
        END
    ) AS completed_cases,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN status = 'Completed'
                THEN 1
                ELSE 0
            END
        )
        / COUNT(*),
        2
    ) AS completion_rate

FROM interventions

GROUP BY advisor

ORDER BY assigned_cases DESC;