# Student Success Analytics — Methodology

## 1. Purpose

This project is a technical portfolio demonstration of how institutional
student data could be transformed into analytical signals that support
academic-success workflows.

The project demonstrates:

- data integration concepts
- data quality assurance
- SQL analytics
- transparent early-warning scoring
- model evaluation
- threshold analysis
- intervention reporting
- dashboard development

This is a prototype and not a production university system.

---

## 2. Data Disclaimer

All records used in this project are synthetic.

No real student, faculty, advisor, LMS, SIS, CRM, or university records are
included.

The dataset is generated reproducibly by Python.

---

## 3. Simulated Data Sources

The project models several institutional data domains:

### Students

Basic programme and enrolment information.

### Courses

Course identifiers, course names, credits, and department information.

### Enrolments

Relationships between students and courses.

### Attendance

Student attendance events associated with courses and dates.

### LMS Activity

Synthetic engagement measures including:

- login count
- active minutes
- assignment views
- active weeks

### Assignment Submissions

Synthetic submission status and lateness information.

### Assessments

Assessment type, date, and score.

### Interventions

Synthetic intervention records including:

- risk type
- intervention type
- advisor
- status
- outcome

---

## 4. Data Pipeline

The analytical workflow is:

```text
Synthetic Source Data
        |
        v
Data Quality Validation
        |
        v
SQLite Relational Database
        |
        +------> SQL Analysis
        |
        v
Student-Level Risk Indicators
        |
        v
Transparent Risk Score
        |
        v
Model Evaluation
        |
        v
Threshold Analysis
        |
        v
Dashboard / Intervention Prototype