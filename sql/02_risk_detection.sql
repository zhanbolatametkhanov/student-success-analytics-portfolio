-- ============================================================
-- Student Success Analytics
-- SQL Analysis 02: Risk Detection
--
-- Purpose:
--     Demonstrate SQL-based construction of analytical
--     indicators that can support early-warning workflows.
--
-- Important:
--     Thresholds are demonstration assumptions only.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Build attendance indicators
-- ------------------------------------------------------------

WITH attendance_metrics AS (

    SELECT
        student_id,

        COUNT(*) AS attendance_events,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN status = 'PRESENT'
                    THEN 1
                    ELSE 0
                END
            )
            / COUNT(*),
            2
        ) AS attendance_rate

    FROM attendance

    GROUP BY student_id
)


SELECT *
FROM attendance_metrics
ORDER BY attendance_rate ASC;


-- ------------------------------------------------------------
-- 2. Build LMS engagement indicators
-- ------------------------------------------------------------

WITH lms_metrics AS (

    SELECT
        student_id,

        SUM(login_count) AS total_logins,

        SUM(minutes_active) AS total_minutes_active,

        COUNT(
            DISTINCT week_number
        ) AS active_weeks

    FROM lms_activity

    GROUP BY student_id
)


SELECT *
FROM lms_metrics
ORDER BY total_minutes_active ASC;


-- ------------------------------------------------------------
-- 3. Build assignment indicators
-- ------------------------------------------------------------

WITH assignment_metrics AS (

    SELECT
        student_id,

        COUNT(*) AS assignment_count,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN submitted = 1
                    THEN 1
                    ELSE 0
                END
            )
            / COUNT(*),
            2
        ) AS submission_rate

    FROM assignment_submissions

    GROUP BY student_id
)


SELECT *
FROM assignment_metrics
ORDER BY submission_rate ASC;


-- ------------------------------------------------------------
-- 4. Build assessment indicators
-- ------------------------------------------------------------

WITH assessment_metrics AS (

    SELECT
        student_id,

        ROUND(
            AVG(score),
            2
        ) AS average_score

    FROM assessments

    GROUP BY student_id
)


SELECT *
FROM assessment_metrics
ORDER BY average_score ASC;


-- ------------------------------------------------------------
-- 5. Identify students with multiple signals
-- ------------------------------------------------------------

WITH attendance_metrics AS (

    SELECT
        student_id,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN status = 'PRESENT'
                    THEN 1
                    ELSE 0
                END
            )
            / COUNT(*),
            2
        ) AS attendance_rate

    FROM attendance

    GROUP BY student_id
),

assignment_metrics AS (

    SELECT
        student_id,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN submitted = 1
                    THEN 1
                    ELSE 0
                END
            )
            / COUNT(*),
            2
        ) AS submission_rate

    FROM assignment_submissions

    GROUP BY student_id
),

assessment_metrics AS (

    SELECT
        student_id,

        ROUND(
            AVG(score),
            2
        ) AS average_score

    FROM assessments

    GROUP BY student_id
)


SELECT

    s.student_id,
    s.programme,

    a.attendance_rate,
    sub.submission_rate,
    ass.average_score,

    (
        CASE
            WHEN a.attendance_rate < 70
            THEN 1
            ELSE 0
        END
        +
        CASE
            WHEN sub.submission_rate < 60
            THEN 1
            ELSE 0
        END
        +
        CASE
            WHEN ass.average_score < 55
            THEN 1
            ELSE 0
        END
    ) AS signal_count

FROM students AS s

JOIN attendance_metrics AS a
    ON s.student_id = a.student_id

JOIN assignment_metrics AS sub
    ON s.student_id = sub.student_id

JOIN assessment_metrics AS ass
    ON s.student_id = ass.student_id

WHERE
    (
        CASE
            WHEN a.attendance_rate < 70
            THEN 1
            ELSE 0
        END
        +
        CASE
            WHEN sub.submission_rate < 60
            THEN 1
            ELSE 0
        END
        +
        CASE
            WHEN ass.average_score < 55
            THEN 1
            ELSE 0
        END
    ) >= 2

ORDER BY signal_count DESC;