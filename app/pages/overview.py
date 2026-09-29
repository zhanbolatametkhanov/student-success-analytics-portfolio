"""
Student Success Analytics — Executive Overview.

Presentation layer for the main decision-support landing page.
All records are synthetic.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.ui import insight_card, page_header, section_header, status_badge
from components.dashboard import metric_card


RISK_ORDER = [
    "Low",
    "Moderate",
    "High",
    "Critical",
]


def _risk_distribution(risk_df: pd.DataFrame) -> pd.DataFrame:
    """Return risk-band counts in presentation order."""

    return (
        risk_df["risk_band"]
        .value_counts()
        .reindex(RISK_ORDER, fill_value=0)
        .rename_axis("risk_band")
        .reset_index(name="students")
    )


def _programme_summary(risk_df: pd.DataFrame) -> pd.DataFrame:
    """Return the highest-average-risk programmes."""

    return (
        risk_df.groupby("programme")
        .agg(
            students=("student_id", "count"),
            average_risk=("risk_score", "mean"),
        )
        .reset_index()
        .sort_values("average_risk", ascending=False)
        .head(8)
    )


def render_overview(
    risk_df: pd.DataFrame,
    intervention_df: pd.DataFrame,
) -> None:
    """Render the executive overview."""

    total_students = len(risk_df)

    risk_counts = (
        risk_df["risk_band"]
        .value_counts()
        .to_dict()
    )

    low_count = int(risk_counts.get("Low", 0))
    moderate_count = int(risk_counts.get("Moderate", 0))
    high_count = int(risk_counts.get("High", 0))
    critical_count = int(risk_counts.get("Critical", 0))
    high_critical = high_count + critical_count

    completed_interventions = int(
        (intervention_df["status"] == "Completed").sum()
    )

    completion_rate = (
        completed_interventions / len(intervention_df) * 100
        if len(intervention_df)
        else 0.0
    )

    high_critical_rate = (
        high_critical / total_students * 100
        if total_students
        else 0.0
    )

    page_header(
        title="Executive overview",
        description=(
            "A decision-support view of the synthetic student population, "
            "early-warning signals, intervention activity and data trust."
        ),
        kicker="Student Success Analytics",
    )

    status_badge(
        "Synthetic analytical environment",
        "neutral",
    )

    st.markdown("")

    metric_cols = st.columns(4)

    metrics = [
        (
            "Students",
            f"{total_students:,}",
            "Synthetic active population",
        ),
        (
            "High / Critical",
            f"{high_critical:,}",
            f"{high_critical_rate:.1f}% of population",
        ),
        (
            "Interventions",
            f"{len(intervention_df):,}",
            "Synthetic workflow records",
        ),
        (
            "Completed",
            f"{completed_interventions:,}",
            f"{completion_rate:.1f}% completion rate",
        ),
    ]

    for column, (label, value, description) in zip(metric_cols, metrics):
        with column:
            metric_card(label, value, description)

    section_header(
        "Current risk picture",
        "The risk bands summarize the current demonstration population; they are not decisions about individual students.",
        "Population",
    )

    chart_left, chart_right = st.columns([1.08, 0.92])

    distribution = _risk_distribution(risk_df)

    with chart_left:
        figure = px.bar(
            distribution,
            x="risk_band",
            y="students",
            text="students",
            category_orders={"risk_band": RISK_ORDER},
        )

        figure.update_traces(
            textposition="outside",
            marker_line_width=0,
        )

        figure.update_layout(
            height=390,
            template="simple_white",
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis_title=None,
            yaxis_title="Students",
            font=dict(color="#58574b"),
            showlegend=False,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

        insight_card(
            f"{high_critical:,} students ({high_critical_rate:.1f}%) are currently in the High or Critical demonstration bands. The score is intended to surface evidence for review, not to determine an outcome.",
            "What the chart says",
        )

    with chart_right:
        programme_summary = _programme_summary(risk_df)

        figure = px.bar(
            programme_summary,
            x="average_risk",
            y="programme",
            orientation="h",
            text="average_risk",
        )

        figure.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            marker_line_width=0,
        )

        figure.update_layout(
            height=390,
            template="simple_white",
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis_title="Average demonstration risk score",
            yaxis_title=None,
            font=dict(color="#58574b"),
            showlegend=False,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

        insight_card(
            "Programme averages describe population patterns. They should be investigated with underlying evidence and local context rather than treated as causal explanations.",
            "Interpretation guardrail",
        )

    section_header(
        "What needs attention?",
        "This section translates the population view into an operational review question.",
        "Attention",
    )

    attention_cols = st.columns(3)

    with attention_cols[0]:
        metric_card(
            "High risk",
            f"{high_count:,}",
            "Demonstration band requiring review",
        )

    with attention_cols[1]:
        metric_card(
            "Critical risk",
            f"{critical_count:,}",
            "Highest demonstration band",
        )

    with attention_cols[2]:
        metric_card(
            "Moderate",
            f"{moderate_count:,}",
            "Largest non-low-risk population",
        )

    section_header(
        "Operational response",
        "The prototype connects an analytical signal to a review-and-intervention workflow.",
        "Workflow",
    )

    workflow_cols = st.columns(4)

    workflow = [
        ("01", "Signal", "Evidence produces a transparent demonstration score."),
        ("02", "Review", "Staff examine the underlying student evidence."),
        ("03", "Intervene", "A support action can be recorded in the workflow layer."),
        ("04", "Evaluate", "Outcomes can be summarized and reviewed over time."),
    ]

    for column, (step, title, description) in zip(workflow_cols, workflow):
        with column:
            st.markdown(
                f"""
                <div class=\"ssa-insight\">
                    <div class=\"ssa-insight-label\">Step {step}</div>
                    <div style=\"font-family: Georgia, serif; font-size: 1.15rem; color: #24231F; margin-bottom: 0.3rem;\">{title}</div>
                    <p class=\"ssa-insight-text\">{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section_header(
        "Data trust",
        "The dashboard should make data limitations visible alongside analytical results.",
        "Trust",
    )

    trust_cols = st.columns(3)

    with trust_cols[0]:
        status_badge("Quality checks available", "healthy")
        st.caption("The project includes explicit data-quality checks and exception reporting.")

    with trust_cols[1]:
        status_badge("Synthetic records only", "neutral")
        st.caption("No real student information is used in this portfolio demonstration.")

    with trust_cols[2]:
        status_badge("Human review required", "warning")
        st.caption("Signals support professional review and should not automate student decisions.")

    st.markdown("")

    insight_card(
        "The intended operating model is data → trust → signal → evidence → action → outcome → evaluation. The application is designed to demonstrate that complete workflow rather than only the risk calculation.",
        "System perspective",
    )
