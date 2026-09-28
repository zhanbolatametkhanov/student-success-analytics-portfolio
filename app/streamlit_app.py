"""
Student Success Analytics
Interactive Academic Success Center Prototype

Purpose
-------
Demonstrate how synthetic institutional data can be transformed
into decision-support views for academic-success teams.

Important
---------
This is a portfolio demonstration using synthetic data only.

It is NOT:

- a Nazarbayev University operational system
- an NU RISE implementation
- a production student-risk system
- a source of real student information
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional
from bootstrap import ensure_demo_environment
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


st.set_page_config(
    page_title="Student Success Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# VISUAL STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* -------------------------------------------------------
       Global
       ------------------------------------------------------- */

    .stApp {
        background: #f7f6f1;
    }

    .main {
        padding-top: 1.5rem;
    }

    /* -------------------------------------------------------
       Sidebar
       ------------------------------------------------------- */

    [data-testid="stSidebar"] {
        background: #efede5;
        border-right: 1px solid #ddd7c8;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #58574b;
    }

    /* -------------------------------------------------------
       Typography
       ------------------------------------------------------- */

    .portfolio-title {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 3.5rem;
        line-height: 1.05;
        color: #24231f;
        margin-bottom: 0.3rem;
    }

    .portfolio-subtitle {
        color: #58574b;
        font-size: 1.05rem;
        margin-bottom: 1rem;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-size: 0.72rem;
        font-weight: 800;
        color: #9a7432;
        margin-bottom: 0.5rem;
    }

    .section-heading {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2rem;
        color: #24231f;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }

    .muted {
        color: #736f62;
        font-size: 0.9rem;
    }

    /* -------------------------------------------------------
       Gold divider
       ------------------------------------------------------- */

    .gold-rule {
        height: 3px;
        background: #DDAF53;
        width: 72px;
        margin: 1rem 0 1.8rem 0;
    }

    /* -------------------------------------------------------
       Notice
       ------------------------------------------------------- */

    .prototype-notice {
        background: #efede5;
        border-left: 4px solid #DDAF53;
        padding: 1rem 1.2rem;
        margin: 1rem 0 1.5rem 0;
        color: #58574b;
        border-radius: 0 6px 6px 0;
    }

    /* -------------------------------------------------------
       KPI cards
       ------------------------------------------------------- */

    .kpi-card {
        background: white;
        border: 1px solid #ddd9cf;
        border-top: 3px solid #DDAF53;
        border-radius: 8px;
        padding: 1.1rem 1.2rem;
        min-height: 125px;
    }

    .kpi-label {
        color: #777266;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 800;
    }

    .kpi-value {
        font-family: Georgia, "Times New Roman", serif;
        color: #24231f;
        font-size: 2.25rem;
        line-height: 1.1;
        margin-top: 0.35rem;
    }

    .kpi-description {
        color: #7b776d;
        font-size: 0.78rem;
        margin-top: 0.35rem;
    }

    /* -------------------------------------------------------
       Risk cards
       ------------------------------------------------------- */

    .risk-card {
        background: white;
        border: 1px solid #ddd9cf;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }

    .risk-card-title {
        font-weight: 800;
        color: #58574b;
    }

    .risk-card-value {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.8rem;
        color: #24231f;
    }

    /* -------------------------------------------------------
       Student profile
       ------------------------------------------------------- */

    .student-panel {
        background: white;
        border: 1px solid #ddd9cf;
        border-radius: 10px;
        padding: 1.4rem;
        margin-bottom: 1rem;
    }

    .student-id {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2rem;
        color: #24231f;
    }

    .student-programme {
        color: #776f60;
        font-size: 1rem;
    }

    .signal {
        display: inline-block;
        padding: 0.4rem 0.65rem;
        margin: 0.2rem 0.2rem 0.2rem 0;
        background: #efede5;
        border: 1px solid #ddd7c8;
        border-radius: 20px;
        color: #58574b;
        font-size: 0.8rem;
        font-weight: 700;
    }

    /* -------------------------------------------------------
       Footer
       ------------------------------------------------------- */

    .footer {
        border-top: 1px solid #ddd9cf;
        margin-top: 3rem;
        padding: 1.5rem 0;
        color: #7b776d;
        font-size: 0.8rem;
    }

    /* -------------------------------------------------------
       Buttons
       ------------------------------------------------------- */

    .stButton > button {
        border-radius: 5px;
        border: 1px solid #a58a55;
    }

    /* -------------------------------------------------------
       Tables
       ------------------------------------------------------- */

    [data-testid="stDataFrame"] {
        border: 1px solid #ddd9cf;
        border-radius: 6px;
    }

    /* -------------------------------------------------------
       Mobile
       ------------------------------------------------------- */

    @media (max-width: 800px) {

        .portfolio-title {
            font-size: 2.5rem;
        }

        .section-heading {
            font-size: 1.6rem;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DEMO ENVIRONMENT
# ============================================================

ensure_demo_environment()

# ============================================================
# DATABASE
# ============================================================

@st.cache_resource
def get_connection() -> sqlite3.Connection:

    if not DATABASE_PATH.exists():

        raise FileNotFoundError(
            f"Database not found at: {DATABASE_PATH}"
        )

    return sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )


@st.cache_data
def run_query(
    query: str,
    params: tuple = (),
) -> pd.DataFrame:

    connection = get_connection()

    return pd.read_sql_query(
        query,
        connection,
        params=params,
    )


# ============================================================
# SAFE DATA LOAD
# ============================================================

try:

    risk_df = run_query(
        """
        SELECT *
        FROM student_risk_scores
        """
    )

    students_df = run_query(
        """
        SELECT *
        FROM students
        """
    )

    intervention_df = run_query(
        """
        SELECT *
        FROM interventions
        """
    )

    outcome_metrics_df = run_query(
        """
        SELECT *
        FROM outcome_summary_metrics
        """
    )

    intervention_type_outcomes_df = run_query(
        """
        SELECT *
        FROM intervention_type_summary
        """
    )

    outcome_distribution_df = run_query(
        """
        SELECT *
        FROM outcome_distribution
        """
    )

    intervention_funnel_df = run_query(
        """
        SELECT *
        FROM intervention_status_funnel
        """
    )
    integration_health_df = run_query(
        """
        SELECT *
        FROM integration_health
        """
    )
    
    integration_events_df = run_query(
        """
        SELECT *
        FROM integration_events
        """
    )
    programme_df = run_query(
        """
        SELECT *
        FROM programme_risk_summary
        """
    )

    quality_df = run_query(
        """
        SELECT *
        FROM database_metadata
        """
    )

    connection_ok = True

except Exception as exc:

    connection_ok = False
    connection_error = str(exc)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        font-family: Georgia, serif;
        font-size: 1.45rem;
        color: #24231f;
        margin-bottom: 0.2rem;
    ">
        Student Success
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="
        color: #756f61;
        font-size: 0.82rem;
        margin-bottom: 1rem;
    ">
        Systems & Data Prototype
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")


page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Risk Monitor",
        "Student Profile",
        "Interventions",
        "Integration Monitor",
        "Outcome Analytics",
        "Data Quality",
        "Model Evaluation",
        "SQL Lab",
        "About Prototype",
    ],
)


st.sidebar.markdown("---")

st.sidebar.caption(
    "Synthetic demonstration environment"
)

st.sidebar.caption(
    "No real student information is used."
)


# ============================================================
# ERROR STATE
# ============================================================

if not connection_ok:

    st.error(
        "The application could not connect to the SQLite database."
    )

    st.code(
        connection_error
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="eyebrow">Academic Success Center · Systems & Data</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="portfolio-title">Student Success Analytics</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="portfolio-subtitle">'
    "Interactive prototype for academic-risk monitoring, "
    "data quality and intervention support."
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="gold-rule"></div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="prototype-notice">
        <strong>Prototype environment.</strong>
        All records are synthetic and created exclusively for demonstration.
        This application does not represent an operational university system
        and does not reproduce any institution's internal methodology.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

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


# ============================================================
# RISK MONITOR
# ============================================================

elif page == "Risk Monitor":

    st.markdown(
        '<div class="section-heading">Risk monitor</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Review students using transparent demonstration indicators.
        Filters operate directly against the analytical dataset in SQLite.
        """,
    )

    filter_cols = st.columns(4)

    with filter_cols[0]:

        schools = (
            ["All"]
            + sorted(
                risk_df["school"]
                .dropna()
                .unique()
                .tolist()
            )
        )

        selected_school = st.selectbox(
            "School",
            schools,
        )

    with filter_cols[1]:

        programmes = (
            ["All"]
            + sorted(
                risk_df["programme"]
                .dropna()
                .unique()
                .tolist()
            )
        )

        selected_programme = st.selectbox(
            "Programme",
            programmes,
        )

    with filter_cols[2]:

        bands = [
            "All",
            "Low",
            "Moderate",
            "High",
            "Critical",
        ]

        selected_band = st.selectbox(
            "Risk band",
            bands,
        )

    with filter_cols[3]:

        minimum_score = st.slider(
            "Minimum score",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
        )


    filtered = risk_df.copy()


    if selected_school != "All":

        filtered = filtered[
            filtered["school"]
            == selected_school
        ]


    if selected_programme != "All":

        filtered = filtered[
            filtered["programme"]
            == selected_programme
        ]


    if selected_band != "All":

        filtered = filtered[
            filtered["risk_band"]
            == selected_band
        ]


    filtered = filtered[
        filtered["risk_score"]
        >= minimum_score
    ]


    st.markdown(
        f"**{len(filtered):,} students** match the current filter.",
    )


    display = filtered[
        [
            "student_id",
            "programme",
            "year_of_study",
            "risk_score",
            "risk_band",
            "attendance_rate",
            "lms_change_pct",
            "submission_rate",
            "average_score",
            "risk_reasons",
        ]
    ].sort_values(
        [
            "risk_score",
            "student_id",
        ],
        ascending=[
            False,
            True,
        ],
    )


    for numeric_column in [
        "attendance_rate",
        "lms_change_pct",
        "submission_rate",
        "average_score",
        "risk_score",
    ]:

        display[numeric_column] = (
            display[numeric_column]
            .round(1)
        )


    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

elif page == "Student Profile":

    st.markdown(
        '<div class="section-heading">Student profile</div>',
        unsafe_allow_html=True,
    )

    student_ids = (
        risk_df["student_id"]
        .sort_values()
        .tolist()
    )

    selected_student = st.selectbox(
        "Select synthetic student",
        student_ids,
    )

    student = risk_df[
        risk_df["student_id"]
        == selected_student
    ].iloc[0]


    st.markdown(
        f"""
        <div class="student-panel">

            <div class="student-id">
                {student["student_id"]}
            </div>

            <div class="student-programme">
                {student["programme"]}
                · Year {student["year_of_study"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    profile_cols = st.columns(4)

    profile_metrics = [
        (
            "Risk score",
            f'{student["risk_score"]:.1f}',
        ),
        (
            "Risk band",
            student["risk_band"],
        ),
        (
            "Attendance",
            f'{student["attendance_rate"]:.1f}%',
        ),
        (
            "Assessment average",
            f'{student["average_score"]:.1f}',
        ),
    ]


    for column, (label, value) in zip(
        profile_cols,
        profile_metrics,
    ):

        with column:

            st.metric(
                label,
                value,
            )


    st.markdown(
        '<div class="section-heading">Risk signals</div>',
        unsafe_allow_html=True,
    )


    reason_list = [
        reason.strip()
        for reason in str(
            student["risk_reasons"]
        ).split(";")
        if reason.strip()
    ]


    if reason_list:

        signals_html = "".join(
            [
                f'<span class="signal">{reason}</span>'
                for reason in reason_list
            ]
        )

        st.markdown(
            signals_html,
            unsafe_allow_html=True,
        )

    else:

        st.caption(
            "No material signal identified."
        )


    st.markdown(
        '<div class="section-heading">Analytical evidence</div>',
        unsafe_allow_html=True,
    )


    evidence = pd.DataFrame(
        [
            {
                "Indicator":
                    "Attendance rate",
                "Value":
                    f'{student["attendance_rate"]:.1f}%',
                "Risk contribution":
                    f'{student["attendance_risk"]:.0f} / 25',
            },
            {
                "Indicator":
                    "LMS engagement change",
                "Value":
                    f'{student["lms_change_pct"]:.1f}%',
                "Risk contribution":
                    f'{student["engagement_risk"]:.0f} / 20',
            },
            {
                "Indicator":
                    "Assignment submission",
                "Value":
                    f'{student["submission_rate"]:.1f}%',
                "Risk contribution":
                    f'{student["assignment_risk"]:.0f} / 20',
            },
            {
                "Indicator":
                    "Assessment average",
                "Value":
                    f'{student["average_score"]:.1f}',
                "Risk contribution":
                    f'{student["performance_risk"]:.0f} / 25',
            },
            {
                "Indicator":
                    "Assessment trend",
                "Value":
                    f'{student["score_change"]:.1f}',
                "Risk contribution":
                    f'{student["trend_risk"]:.0f} / 10',
            },
        ]
    )


    st.dataframe(
        evidence,
        use_container_width=True,
        hide_index=True,
    )


    st.markdown(
        '<div class="section-heading">Intervention history</div>',
        unsafe_allow_html=True,
    )


    student_interventions = intervention_df[
        intervention_df["student_id"]
        == selected_student
    ].copy()


    if student_interventions.empty:

        st.info(
            "No synthetic intervention records exist "
            "for this student."
        )

    else:

        st.dataframe(
            student_interventions[
                [
                    "intervention_id",
                    "risk_type",
                    "trigger_date",
                    "intervention_type",
                    "advisor",
                    "status",
                    "outcome",
                ]
            ].sort_values(
                "trigger_date",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# INTERVENTIONS
# ============================================================

elif page == "Integration Monitor":

    st.markdown(
        '<div class="section-heading">'
        'Integration monitor'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        This page demonstrates operational monitoring of the synthetic
        interfaces connecting source systems to the analytical layer
        and student-support workflow.

        The telemetry is synthetic and does not represent real
        institutional infrastructure.
        """,
    )

    # --------------------------------------------------------
    # KPI calculations
    # --------------------------------------------------------

    total_integrations = len(
        integration_health_df
    )

    healthy_integrations = int(
        (
            integration_health_df["status"]
            == "Healthy"
        ).sum()
    )

    warning_integrations = int(
        (
            integration_health_df["status"]
            == "Warning"
        ).sum()
    )

    attention_integrations = int(
        (
            integration_health_df["status"]
            == "Attention"
        ).sum()
    )

    average_freshness = (
        integration_health_df[
            "data_freshness_minutes"
        ]
        .mean()
    )

    average_success_rate = (
        integration_health_df[
            "success_rate_24h"
        ]
        .mean()
    )

    total_errors = int(
        integration_health_df[
            "error_count_24h"
        ].sum()
    )

    # --------------------------------------------------------
    # KPI cards
    # --------------------------------------------------------

    kpi_cols = st.columns(5)

    integration_kpis = [
        (
            "Interfaces",
            f"{total_integrations}",
        ),
        (
            "Healthy",
            f"{healthy_integrations}",
        ),
        (
            "Warning",
            f"{warning_integrations}",
        ),
        (
            "Attention",
            f"{attention_integrations}",
        ),
        (
            "24h errors",
            f"{total_errors}",
        ),
    ]

    for column, (label, value) in zip(
        kpi_cols,
        integration_kpis,
    ):

        with column:

            st.metric(
                label,
                value,
            )

    # --------------------------------------------------------
    # Operational summary
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Operational health'
        '</div>',
        unsafe_allow_html=True,
    )

    op_cols = st.columns(2)

    with op_cols[0]:

        st.metric(
            "Average data freshness",
            f"{average_freshness:.1f} min",
        )

    with op_cols[1]:

        st.metric(
            "Average 24h success rate",
            f"{average_success_rate:.2f}%",
        )

    # --------------------------------------------------------
    # Health table
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Interface health'
        '</div>',
        unsafe_allow_html=True,
    )

    health_display = integration_health_df[
        [
            "integration_id",
            "source_system",
            "target_system",
            "interface_type",
            "sync_frequency",
            "last_success_at",
            "records_last_sync",
            "latency_ms",
            "error_count_24h",
            "data_freshness_minutes",
            "success_rate_24h",
            "status",
            "owner",
        ]
    ].copy()

    st.dataframe(
        health_display,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Latency chart
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Interface latency'
        '</div>',
        unsafe_allow_html=True,
    )

    latency_chart = (
        integration_health_df[
            [
                "integration_id",
                "latency_ms",
            ]
        ]
        .sort_values(
            "latency_ms",
            ascending=True,
        )
    )

    latency_figure = px.bar(
        latency_chart,
        x="latency_ms",
        y="integration_id",
        orientation="h",
        text="latency_ms",
    )

    latency_figure.update_traces(
        textposition="outside"
    )

    latency_figure.update_layout(
        template="simple_white",
        height=320,
        margin=dict(
            l=20,
            r=80,
            t=20,
            b=20,
        ),
        xaxis_title="Latency (ms)",
        yaxis_title=None,
    )

    st.plotly_chart(
        latency_figure,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Event history
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Recent integration events'
        '</div>',
        unsafe_allow_html=True,
    )

    event_filter = st.selectbox(
        "Event status",
        [
            "All",
            "SUCCESS",
            "WARNING",
            "FAILED",
        ],
    )

    event_display = integration_events_df.copy()

    if event_filter != "All":

        event_display = event_display[
            event_display["status"]
            == event_filter
        ]

    event_display = (
        event_display
        .sort_values(
            "event_time",
            ascending=False,
        )
        .head(100)
    )

    st.dataframe(
        event_display,
        use_container_width=True,
        hide_index=True,
    )
elif page == "Interventions":

    st.markdown(
        '<div class="section-heading">Intervention workflow</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        This page demonstrates how analytical signals can be connected
        to an operational workflow.

        In a production environment, workflow rules, permissions,
        communications and intervention definitions would need to be
        governed institutionally.
        """,
    )


    intervention_status = (
        intervention_df
        .groupby("status")
        .size()
        .reindex(
            [
                "Pending",
                "In progress",
                "Completed",
            ],
            fill_value=0,
        )
        .reset_index(
            name="interventions"
        )
    )


    left, right = st.columns(
        [1, 1]
    )


    with left:

        figure = px.bar(
            intervention_status,
            x="status",
            y="interventions",
            text="interventions",
        )

        figure.update_traces(
            textposition="outside"
        )

        figure.update_layout(
            template="simple_white",
            height=350,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
            xaxis_title=None,
            yaxis_title="Interventions",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


    with right:

        intervention_types = (
            intervention_df
            .groupby(
                "intervention_type"
            )
            .size()
            .reset_index(
                name="count"
            )
            .sort_values(
                "count",
                ascending=False,
            )
        )

        figure = px.bar(
            intervention_types,
            x="count",
            y="intervention_type",
            orientation="h",
            text="count",
        )

        figure.update_traces(
            textposition="outside"
        )

        figure.update_layout(
            template="simple_white",
            height=350,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
            xaxis_title="Interventions",
            yaxis_title=None,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


    st.markdown(
        '<div class="section-heading">Workflow records</div>',
        unsafe_allow_html=True,
    )


    st.dataframe(
        intervention_df.sort_values(
            "trigger_date",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DATA QUALITY
# ============================================================

# ============================================================
# OUTCOME ANALYTICS
# ============================================================

elif page == "Outcome Analytics":

    st.markdown(
        '<div class="section-heading">'
        'Intervention outcome analytics'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        This page demonstrates how intervention activity can be measured
        after the initial risk signal.

        Results are descriptive summaries of synthetic records.
        They do not establish causal intervention effectiveness.
        """,
    )

    # --------------------------------------------------------
    # KPI extraction
    # --------------------------------------------------------

    def metric_value(
        metric_name: str,
    ):

        row = outcome_metrics_df[
            outcome_metrics_df["metric"]
            == metric_name
        ]

        if row.empty:

            return 0

        return float(
            row.iloc[0]["value"]
        )


    total_interventions = metric_value(
        "Total interventions"
    )

    completed_interventions = metric_value(
        "Completed interventions"
    )

    completion_rate = metric_value(
        "Completion rate"
    )

    positive_outcomes = metric_value(
        "Positive synthetic outcomes"
    )


    # --------------------------------------------------------
    # KPI cards
    # --------------------------------------------------------

    kpi_cols = st.columns(4)

    with kpi_cols[0]:

        st.metric(
            "Interventions",
            f"{total_interventions:,.0f}",
        )

    with kpi_cols[1]:

        st.metric(
            "Completed",
            f"{completed_interventions:,.0f}",
        )

    with kpi_cols[2]:

        st.metric(
            "Completion rate",
            f"{completion_rate:.1f}%",
        )

    with kpi_cols[3]:

        st.metric(
            "Positive outcomes",
            f"{positive_outcomes:,.0f}",
        )


    # --------------------------------------------------------
    # Intervention status
    # --------------------------------------------------------

    left, right = st.columns(
        2
    )


    with left:

        st.markdown(
            '<div class="section-heading">'
            'Workflow status'
            '</div>',
            unsafe_allow_html=True,
        )

        figure = px.bar(
            intervention_funnel_df,
            x="status",
            y="interventions",
            text="interventions",
        )

        figure.update_traces(
            textposition="outside"
        )

        figure.update_layout(
            template="simple_white",
            height=350,
            margin=dict(
                l=10,
                r=10,
                t=30,
                b=10,
            ),
            xaxis_title=None,
            yaxis_title="Cases",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


    with right:

        st.markdown(
            '<div class="section-heading">'
            'Outcome distribution'
            '</div>',
            unsafe_allow_html=True,
        )

        outcome_chart = (
            outcome_distribution_df
            .groupby(
                "outcome"
            )["interventions"]
            .sum()
            .reset_index()
            .sort_values(
                "interventions",
                ascending=False,
            )
        )

        figure = px.bar(
            outcome_chart,
            x="interventions",
            y="outcome",
            orientation="h",
            text="interventions",
        )

        figure.update_traces(
            textposition="outside"
        )

        figure.update_layout(
            template="simple_white",
            height=350,
            margin=dict(
                l=10,
                r=60,
                t=30,
                b=10,
            ),
            xaxis_title="Cases",
            yaxis_title=None,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )


    # --------------------------------------------------------
    # Intervention type
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Intervention-type effectiveness view'
        '</div>',
        unsafe_allow_html=True,
    )

    type_display = (
        intervention_type_outcomes_df[
            [
                "intervention_type",
                "interventions",
                "completed",
                "completion_rate",
                "assessed",
                "positive_outcomes",
                "positive_outcome_rate_all",
                "positive_outcome_rate_assessed",
                "estimated_cost",
                "cost_per_completed",
                "cost_per_positive_outcome",
            ]
        ]
        .copy()
    )


    for column in [
        "completion_rate",
        "positive_outcome_rate_all",
        "positive_outcome_rate_assessed",
    ]:

        type_display[column] = (
            type_display[column]
            .round(1)
        )


    for column in [
        "estimated_cost",
        "cost_per_completed",
        "cost_per_positive_outcome",
    ]:

        type_display[column] = (
            type_display[column]
            .round(2)
        )


    st.dataframe(
        type_display,
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------------------
    # Cost-efficiency caveat
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="prototype-notice">
            <strong>Financial interpretation</strong><br>
            The cost figures are synthetic assumptions introduced only to
            demonstrate a cost-efficiency framework. A production ROI
            calculation would require validated institutional costs and an
            agreed method for valuing student-success outcomes.
        </div>
        """,
        unsafe_allow_html=True,
    )



elif page == "Data Quality":

    st.markdown(
        '<div class="section-heading">Data quality monitor</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Data quality is treated as a prerequisite to analytical use.

        The dashboard displays the results produced by the project's
        data-quality validation layer.
        """,
    )


    try:

        quality_results = run_query(
            """
            SELECT *
            FROM data_quality_report
            """
        )

    except Exception:

        quality_results = pd.DataFrame()


    if quality_results.empty:

        st.warning(
            "Detailed data-quality results are not stored in the "
            "SQLite database yet."
        )

        st.info(
            "The validation report is currently generated by "
            "python/data_quality.py. The next integration step will "
            "load that report into the database."
        )

    else:

        passed = int(
            (
                quality_results["status"]
                == "PASS"
            ).sum()
        )

        failed = int(
            (
                quality_results["status"]
                == "FAIL"
            ).sum()
        )

        quality_cols = st.columns(3)

        with quality_cols[0]:

            st.metric(
                "Checks",
                f"{len(quality_results):,}",
            )

        with quality_cols[1]:

            st.metric(
                "Passed",
                f"{passed:,}",
            )

        with quality_cols[2]:

            st.metric(
                "Failed",
                f"{failed:,}",
            )


        st.dataframe(
            quality_results,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# MODEL EVALUATION
# ============================================================

elif page == "Model Evaluation":

    st.markdown(
        '<div class="section-heading">Model evaluation</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        The risk model is evaluated against an independent synthetic
        simulation reference.

        The reference data is not used as a model input.
        """,
    )


    try:

        metrics = run_query(
            """
            SELECT *
            FROM model_metrics
            """
        )

        confusion = run_query(
            """
            SELECT *
            FROM model_confusion_matrix
            """
        )

    except Exception:

        metrics = pd.DataFrame()
        confusion = pd.DataFrame()


    if metrics.empty:

        st.warning(
            "Model-evaluation outputs have not yet been loaded "
            "into the SQLite database."
        )

    else:

        metric_cols = st.columns(
            4
        )


        metric_map = {
            "Accuracy": "Accuracy",
            "Precision": "Precision",
            "Recall": "Recall",
            "F1": "F1",
        }


        for column, metric_name in zip(
            metric_cols,
            [
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
            ],
        ):

            match = metrics[
                metrics["metric"]
                == metric_name
            ]

            if not match.empty:

                value = float(
                    match.iloc[0]["value"]
                )

                with column:

                    st.metric(
                        metric_name,
                        f"{value * 100:.1f}%",
                    )


        if not confusion.empty:

            st.markdown(
                '<div class="section-heading">Confusion matrix</div>',
                unsafe_allow_html=True,
            )

            st.dataframe(
                confusion,
                use_container_width=True,
                hide_index=True,
            )


        st.markdown(
            '<div class="section-heading">Metric definitions</div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            metrics,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# SQL LAB
# ============================================================

elif page == "SQL Lab":

    st.markdown(
        '<div class="section-heading">SQL lab</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        These examples demonstrate how SQL can transform relational
        institutional data into analytical information.

        The queries are executed against the same SQLite database
        used by the dashboard.
        """,
    )


    sql_options = {
        "Risk distribution":
            """
            SELECT
                risk_band,
                COUNT(*) AS students
            FROM student_risk_scores
            GROUP BY risk_band
            ORDER BY
                CASE risk_band
                    WHEN 'Low' THEN 1
                    WHEN 'Moderate' THEN 2
                    WHEN 'High' THEN 3
                    WHEN 'Critical' THEN 4
                END;
            """,

        "High / Critical students":
            """
            SELECT
                student_id,
                programme,
                risk_score,
                risk_band,
                risk_reasons
            FROM student_risk_scores
            WHERE risk_band IN ('High', 'Critical')
            ORDER BY risk_score DESC
            LIMIT 20;
            """,

        "Intervention outcomes":
            """
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
            """,

        "Programme risk":
            """
            SELECT
                school,
                programme,
                students,
                average_risk_score,
                high_or_critical,
                high_or_critical_rate
            FROM programme_risk_summary
            ORDER BY
                average_risk_score DESC;
            """,
    }


    selected_sql_name = st.selectbox(
        "Query",
        list(sql_options.keys()),
    )


    query = sql_options[
        selected_sql_name
    ]


    st.code(
        query,
        language="sql",
    )


    result = run_query(
        query
    )


    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ABOUT
# ============================================================

elif page == "About Prototype":

    st.markdown(
        '<div class="section-heading">About the prototype</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ## Purpose

        This prototype demonstrates an end-to-end approach to student-success
        analytics:

        **Source data → validation → relational data → analytics →
        early-warning signals → intervention support → reporting**

        ## Synthetic data

        The entire environment uses fictional records generated by Python.

        No real student information is used.

        ## Risk methodology

        The demonstration risk model combines:

        - attendance
        - LMS engagement
        - assignment submission
        - assessment performance
        - performance trend

        The maximum demonstration score is 100.

        ## Governance principle

        A risk score should support professional review rather than replace
        professional judgment.

        The prototype therefore exposes the evidence and indicators behind
        the score instead of treating the score as an unexplained decision.

        ## Important limitation

        The simulated reference population is not real institutional outcome
        data. Model-performance results in this project demonstrate the
        evaluation process only.

        ## Intended interview demonstration

        A five-minute walkthrough can follow this sequence:

        **Overview → Risk Monitor → Student Profile → Intervention →
        Data Quality → Model Evaluation → SQL Lab**

        This demonstrates the connection between systems, data, analytics
        and operational decision support.
        """,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        Student Success Analytics & Systems Lab · Synthetic demonstration
        environment · 2026
    </div>
    """,
    unsafe_allow_html=True,
)