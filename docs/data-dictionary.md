# Data Dictionary

## Purpose

This document defines the principal fields used in the Student Success
Analytics synthetic demonstration.

All records are synthetic.

---

## Student table

| Field | Description |
|---|---|
| `student_id` | Synthetic student identifier |
| `programme` | Synthetic academic programme |
| `school` | Synthetic academic school |
| `year_of_study` | Synthetic year of study |

---

## Risk table

| Field | Description |
|---|---|
| `student_id` | Synthetic student identifier |
| `risk_score` | Transparent demonstration score from 0–100 |
| `risk_band` | Low, Moderate, High or Critical |
| `attendance_rate` | Derived attendance measure |
| `lms_change_pct` | Change in LMS engagement |
| `submission_rate` | Assignment submission measure |
| `average_score` | Assessment average |
| `score_change` | Assessment trend |
| `risk_reasons` | Human-readable contributing indicators |
| `intervention_priority` | Demonstration workflow priority |

---

## Weekly student profile

| Field | Description |
|---|---|
| `student_id` | Synthetic student identifier |
| `week_number` | Synthetic study week |
| `attendance_rate` | Weekly attendance percentage |
| `login_count` | Weekly LMS login count |
| `minutes_active` | Weekly LMS active minutes |
| `assignment_views` | Weekly assignment views |
| `submission_rate` | Weekly submission percentage |

---

## Integration health

| Field | Description |
|---|---|
| `integration_id` | Synthetic interface identifier |
| `source_system` | Source system |
| `target_system` | Receiving system |
| `interface_type` | Interface mechanism |
| `last_success_at` | Most recent successful synchronization |
| `records_last_sync` | Records processed in the latest synchronization |
| `latency_ms` | Synthetic interface latency |
| `error_count_24h` | Synthetic errors over 24 hours |
| `data_freshness_minutes` | Age of the current data |
| `success_rate_24h` | Synthetic 24-hour success rate |
| `status` | Health classification |

---

## Survey feedback

| Field | Description |
|---|---|
| `response_id` | Synthetic survey response identifier |
| `respondent_type` | Student or Faculty |
| `survey_date` | Survey date |
| `theme` | Synthetic feedback theme |
| `question` | Survey question |
| `score` | 1–5 response scale |
| `would_recommend` | Binary recommendation indicator |

---

## Governance note

Definitions in this dictionary describe the portfolio's synthetic data model.
They are not definitions of any real university information system.
