-- ============================================================
-- Student Success Analytics
-- SQL Analysis 01: Student Activity
--
-- Purpose:
--     Demonstrate SQL queries used to explore synthetic
--     institutional student data.
--
-- Dataset:
--     Synthetic portfolio data only.
-- ============================================================


-- ------------------------------------------------------------
-- 1. Student population by programme
-- ------------------------------------------------------------

SELECT
    programme,
    COUNT(*) AS student_count
FROM students
GROUP BY programme
ORDER BY student_count DESC;


-- ------------------------------------------------------------
-- 2. Students by year of study
-- ------------------------------------------------------------

SELECT
    year_of_study,
    COUNT(*) AS student_count
FROM students
GROUP BY year_of_study
ORDER BY year_of_study;


-- ------------------------------------------------------------
-- 3. Average assessment score by programme
-- ------------------------------------------------------------

SELECT
    s.programme,
    COUNT(a.score) AS assessment_records,
    ROUND(AVG(a.score), 2) AS average_score
FROM students AS s
JOIN assessments AS a
    ON s.student_id = a.student_id
GROUP BY s.programme
ORDER BY average_score DESC;


-- ------------------------------------------------------------
-- 4. Student attendance rate
-- ------------------------------------------------------------

SELECT
    student_id,

    COUNT(*) AS attendance_events,

    SUM(
        CASE
            WHEN status = 'PRESENT'
            THEN 1
            ELSE 0
        END
    ) AS present_events,

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

ORDER BY attendance_rate ASC;


-- ------------------------------------------------------------
-- 5. Students with attendance below 70%
-- ------------------------------------------------------------

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

HAVING attendance_rate < 70

ORDER BY attendance_rate ASC;


-- ------------------------------------------------------------
-- 6. LMS activity by student
-- ------------------------------------------------------------

SELECT
    student_id,

    SUM(login_count) AS total_logins,

    SUM(minutes_active) AS total_minutes_active,

    SUM(assignment_views) AS total_assignment_views,

    COUNT(DISTINCT week_number) AS active_weeks

FROM lms_activity

GROUP BY student_id

ORDER BY total_minutes_active ASC;


-- ------------------------------------------------------------
-- 7. Assignment submission rate
-- ------------------------------------------------------------

SELECT
    student_id,

    COUNT(*) AS assignment_count,

    SUM(
        CASE
            WHEN submitted = 1
            THEN 1
            ELSE 0
        END
    ) AS submitted_count,

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

ORDER BY submission_rate ASC;


-- ------------------------------------------------------------
-- 8. Students with weak academic performance
-- ------------------------------------------------------------

SELECT
    student_id,

    ROUND(
        AVG(score),
        2
    ) AS average_score,

    COUNT(*) AS assessment_count

FROM assessments

GROUP BY student_id

HAVING average_score < 60

ORDER BY average_score ASC;