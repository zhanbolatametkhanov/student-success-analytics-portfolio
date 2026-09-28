# Data Lineage

## Purpose

This document describes how synthetic source data moves through the Student Success Analytics portfolio.

All records in this repository are synthetic.

## End-to-end lineage

```text
Synthetic source data
        |
        +--> Data quality validation
        |
        +--> SQLite source tables
                    |
                    +--> SQL analytical queries
                    |
                    +--> Python analytics
                    |
                    +--> Student profile analysis
                    |
                    +--> Integration monitoring
                    |
                    +--> Survey analytics
                    |
                    v
              Analytical outputs
                    |
                    v
             Streamlit dashboard
```

## Risk analytics lineage

```text
Attendance
LMS activity
Assignments
Assessments
      |
      v
Student-level indicators
      |
      v
Transparent risk score
      |
      v
Risk band and reason codes
      |
      v
Risk Monitor / Student Profile
```

## Student Profile lineage

```text
Attendance
      \
LMS    ---> Weekly profile transformation
Assignments
      /
      v
25,000 weekly student records
      |
      v
Student Profile
```

## Integration lineage

```text
Synthetic source systems
        |
        v
Synthetic interface telemetry
        |
        +--> integration_health
        |
        +--> integration_events
        |
        v
Integration Monitor
```

## Intervention lineage

```text
Risk signal
      |
      v
Intervention workflow
      |
      v
Synthetic intervention record
      |
      v
Outcome analytics
```

## Feedback lineage

```text
Synthetic student and faculty survey responses
        |
        v
Survey analysis
        |
        +--> respondent summaries
        +--> theme summaries
        +--> trend summaries
        |
        v
Feedback analytics
```

## Presentation principle

The dashboard is a presentation layer.

Analytical transformations should remain reproducible in Python or SQL and should not depend on manual dashboard calculations.

## Governance principle

Each important metric should have a documented:

- source
- definition
- transformation
- owner
- intended use

The definitions in this document describe the portfolio prototype and do not represent any real university architecure.
