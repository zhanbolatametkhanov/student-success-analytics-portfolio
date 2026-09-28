# Early-Warning Risk Model Card

## Model purpose

The model is a transparent early-warning demonstration designed to show how
institutional student-activity indicators can be combined into an interpretable
risk signal.

It is a portfolio prototype only.

It is not an institutional decision-making system.

## Intended use

The prototype is intended to demonstrate:

- construction of student-level indicators
- explainable risk scoring
- model evaluation
- threshold analysis
- evidence presentation
- intervention decision-support concepts

The model is not intended to automatically determine student support,
disciplinary action, progression, admission, funding, or other consequential
institutional decisions.

## Inputs

The demonstration model uses:

- attendance
- LMS engagement
- assignment submission
- assessment performance
- assessment trend

The synthetic simulation reference is not used as a model input.

## Outputs

The model produces:

- risk score from 0 to 100
- demonstration risk band
- risk reason codes
- intervention priority

## Explainability

The score is decomposed into five components:

| Component | Maximum |
|---|---:|
| Attendance | 25 |
| LMS engagement | 20 |
| Assignment submission | 20 |
| Academic performance | 25 |
| Performance trend | 10 |
| Total | 100 |

The system also produces reason codes so that a stakeholder can see which
observable indicators contributed to the signal.

## Demonstration risk bands

| Score | Demonstration band |
|---:|---|
| 0-29 | Low |
| 30-59 | Moderate |
| 60-79 | High |
| 80-100 | Critical |

These thresholds are prototype assumptions and are not claims about any
institutional policy or intervention framework.

## Evaluation

The prototype is evaluated against a separate synthetic simulation reference.

The reference data is not used to generate the model score.

The evaluation includes:

- accuracy
- precision
- recall
- specificity
- F1
- exact four-band agreement
- false positives
- false negatives
- threshold analysis

Current synthetic evaluation:

| Metric | Result |
|---|---:|
| Accuracy | 82.5% |
| Precision | 73.5% |
| Recall | 43.1% |
| Specificity | 95.0% |
| F1 | 54.4% |
| Exact four-band agreement | 58.6% |

These figures describe the synthetic experiment only.

## Threshold analysis

The prototype evaluates multiple thresholds rather than assuming that one
threshold is universally correct.

In the current synthetic experiment:

| Threshold | Flagged | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|
| 30 | 1,659 | 35.8% | 98.2% | 52.5% |
| 40 | 1,217 | 45.4% | 91.4% | 60.7% |
| 50 | 714 | 59.0% | 69.6% | 63.8% |
| 60 | 355 | 73.5% | 43.1% | 54.4% |
| 70 | 140 | 85.7% | 19.8% | 32.2% |
| 80 | 27 | 96.3% | 4.3% | 8.2% |

These results demonstrate the trade-off between the volume of cases flagged,
precision, recall and operational workload.

They are specific to the synthetic dataset and should not be interpreted as
empirical university evidence.

## False positives and false negatives

### False positive

The model flags a student as High/Critical while the synthetic reference
does not classify the student as High/Critical.

Potential implications include:

- unnecessary review
- additional advisor workload
- additional student contact

### False negative

The model does not flag a student as High/Critical while the synthetic
reference classifies the student as High/Critical.

Potential implications include:

- missed opportunity for support
- delayed intervention
- incomplete coverage

The prototype therefore reports both error types.

## Human oversight

The risk signal is intended to support professional review.

It should not automatically determine a student's outcome.

The intended workflow is:

Risk signal
  ->
Evidence review
  ->
Human judgement
  ->
Intervention
  ->
Outcome
  ->
Evaluation

## Important limitation

The reference population is generated through simulation.

It is not real student-outcome data and has not been empirically validated
for an actual university environment.

Model performance in this repository therefore demonstrates the evaluation
process rather than expected real-world performance.

## Production considerations

A production implementation would require additional work, including:

- validated institutional outcome labels
- historical evaluation
- fairness and subgroup analysis
- data-protection controls
- access management
- audit logging
- model version management
- drift monitoring
- threshold governance
- stakeholder validation
- documented intervention policies
- ongoing performance monitoring
