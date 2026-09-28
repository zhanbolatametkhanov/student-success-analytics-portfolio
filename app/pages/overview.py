"""
Student Success Analytics — Overview page.

Presentation layer for the executive overview.

All records are synthetic.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_overview(
    risk_df: pd.DataFrame,
    intervention_df: pd.DataFrame,
) -> None:
    """Render the executive overview."""



    total_students = len(risk_df)

    low_count = int(
        (
            risk_df["risk_band"]
            == "Low"
        ).sum()
    )

    moderate_count = int(
        (
            risk_df["risk_band"]
            == "Moderate"
        ).sum()
    )

    high_count = int(
        (
            risk_df["risk_band"]
            == "High"
        ).sum()
    )

    critical_count = int(
        (
            risk_df["risk_band"]
            == "Critical"
        ).sum()
    )

    high_critical = (
        high_count
        + critical_count
    )

    completed_interventions = int(
        (
            intervention_df["status"]
            == "Completed"
        ).sum()
    )

    st.markdown(
        '<div class="section-heading">Executive overview</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(5)

    kpis = [
        (
            "Students",
            f"{total_students:,}",
            "Synthetic active population",
        ),
        (
            "Low risk",
            f"{low_count:,}",
            "Current demonstration band",
        ),
        (
            "Moderate",
            f"{moderate_count:,}",
            "Current demonstration band",
        ),
        (
            "High",
            f"{high_count:,}",
            "Current demonstration band",
        ),
        (
            "Critical",
            f"{critical_count:,}",
            "Current demonstration band",
        ),
    ]

    for column, (label, value, description) in zip(
        cols,
        kpis,
    ):

        with column:

            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-description">
                        {description}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


    st.markdown("")

    left, right = st.columns(
        [1.05, 0.95]
    )


    with left:

        st.markdown(
            '<div class="section-heading">Risk distribution</div>',
            unsafe_allow_html=True,
        )

        distribution = (
            risk_df
            .groupby("risk_band")
            .size()
            .reindex(
                [
                    "Low",
                    "Moderate",
                    "High",
                    "Critical",
                ],
                fill_value=0,
            )
            .reset_index(
                name="students"
            )
        )

        figure = px.bar(
            distribution,
            x="risk_band",
            y="students",
            text="students",
        )

        figure.update_traces(
            textposition="outside"
        )

        figure.update_layout(
            height=370,
            template="simple_white",
            margin=dict(
                l=10,
                r=10,
                t=30,
                b=10,
            ),
            xaxis_title=None,
            yaxis_title="Students",
            font=dict(
                color="#58574b"
            ),
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


    with right:

        st.markdown(
            '<div class="section-heading">Programme overview</div>',
            unsafe_allow_html=True,
        )

        programme_chart = (
            risk_df
            .groupby("programme")
            .agg(
                students=(
                    "student_id",
                    "count",
                ),
                average_risk=(
                    "risk_score",
                    "mean",
                ),
            )
            .reset_index()
            .sort_values(
                "average_risk",
                ascending=False,
            )
            .head(10)
        )

        figure = px.bar(
            programme_chart,
            x="average_risk",
            y="programme",
            orientation="h",
            text="average_risk",
        )

        figure.update_layout(
            height=370,
            template="simple_white",
            margin=dict(
                l=10,
                r=10,
                t=30,
                b=10,
            ),
            xaxis_title="Average risk score",
            yaxis_title=None,
            font=dict(
                color="#58574b"
            ),
        )

        figure.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


    st.markdown(
        '<div class="section-heading">Operational snapshot</div>',
        unsafe_allow_html=True,
    )

    op_cols = st.columns(3)

    with op_cols[0]:

        st.markdown(
            f"""
            <div class="risk-card">
                <div class="risk-card-title">
                    High / Critical students
                </div>
                <div class="risk-card-value">
                    {high_critical:,}
                </div>
                <div class="muted">
                    Current demonstration risk population
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with op_cols[1]:

        st.markdown(
            f"""
            <div class="risk-card">
                <div class="risk-card-title">
                    Intervention records
                </div>
                <div class="risk-card-value">
                    {len(intervention_df):,}
                </div>
                <div class="muted">
                    Synthetic workflow records
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with op_cols[2]:

        st.markdown(
            f"""
            <div class="risk-card">
                <div class="risk-card-title">
                    Completed interventions
                </div>
                <div class="risk-card-value">
                    {completed_interventions:,}
                </div>
                <div class="muted">
                    Status = Completed
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


