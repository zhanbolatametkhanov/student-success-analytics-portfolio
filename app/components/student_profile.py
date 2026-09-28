"""
Student Success Analytics
Student Profile 2.0

Detailed evidence-oriented profile for a synthetic student.

The profile combines:
- current risk summary
- weekly attendance
- weekly LMS activity
- weekly assignment submission
- assessment trajectory
- risk contribution
- intervention history

All data is synthetic.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd
import plotly.express as px
import streamlit as st


QueryFunction = Callable[[str, tuple], pd.DataFrame]


def _safe_float(
    value,
    default: float = 0.0,
) -> float:
    """Convert a value safely to float."""

    try:
        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):

        return default


def _metric_row(
    label: str,
    value: str,
    contribution: float,
    maximum: float,
) -> dict:

    return {
        "Indicator": label,
        "Value": value,
        "Contribution": contribution,
        "Maximum": maximum,
        "Contribution label": (
            f"{contribution:.0f} / {maximum:.0f}"
        ),
    }


def render_student_profile(
    run_query: QueryFunction,
    risk_df: pd.DataFrame,
    intervention_df: pd.DataFrame,
) -> None:
    """Render Student Profile 2.0."""

    # ========================================================
    # Header
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Student profile'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Review the evidence underlying a synthetic early-warning
        signal. The profile separates observable indicators from
        the resulting risk signal so that a professional can review
        the context before taking action.
        """,
    )

    # ========================================================
    # Student selector
    # ========================================================

    student_ids = (
        risk_df["student_id"]
        .dropna()
        .astype(str)
        .sort_values()
        .tolist()
    )

    if not student_ids:

        st.warning(
            "No student records are available."
        )

        return

    selected_student = st.selectbox(
        "Select synthetic student",
        student_ids,
        key="profile_student_selector",
    )

    student_rows = risk_df[
        risk_df["student_id"].astype(str)
        == selected_student
    ]

    if student_rows.empty:

        st.error(
            "The selected student could not be found."
        )

        return

    student = student_rows.iloc[0]

    # ========================================================
    # Retrieve weekly profile
    # ========================================================

    weekly = run_query(
        """
        SELECT
            student_id,
            week_number,
            attendance_rate,
            attendance_events,
            login_count,
            minutes_active,
            assignment_views,
            submission_rate,
            assignments
        FROM weekly_student_profile
        WHERE student_id = ?
        ORDER BY week_number
        """,
        (selected_student,),
    ).copy()

    # ========================================================
    # Retrieve assessments
    # ========================================================

    assessments = run_query(
        """
        SELECT
            student_id,
            course_id,
            assessment_type,
            assessment_date,
            score,
            assessment_number
        FROM student_assessment_trajectory
        WHERE student_id = ?
        ORDER BY assessment_date
        """,
        (selected_student,),
    ).copy()

    # ========================================================
    # Retrieve interventions
    # ========================================================

    student_interventions = intervention_df[
        intervention_df["student_id"].astype(str)
        == selected_student
    ].copy()

    # ========================================================
    # HERO
    # ========================================================

    hero_left, hero_right = st.columns(
        [2.35, 1],
        gap="large",
    )

    with hero_left:

        st.markdown(
            f"""
            <div class="student-panel">

                <div class="eyebrow">
                    Synthetic student profile
                </div>

                <div class="student-id">
                    {student["student_id"]}
                </div>

                <div class="student-programme">
                    {student["programme"]}
                    · Year {student["year_of_study"]}
                </div>

                <div class="muted">
                    {student["school"]}
                </div>

                <div style="margin-top: 1rem;">
                    <strong>Intervention priority:</strong>
                    {student.get("intervention_priority", "Review")}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_right:

        score = _safe_float(
            student["risk_score"]
        )

        st.markdown(
            f"""
            <div class="risk-card"
                 style="text-align:center; min-height:170px;">

                <div class="kpi-label">
                    Demonstration risk score
                </div>

                <div style="
                    font-family: Georgia, serif;
                    font-size: 4rem;
                    line-height: 1;
                    color: #24231f;
                    margin: 0.45rem 0;
                ">
                    {score:.0f}
                </div>

                <div class="risk-card-title"
                     style="font-size:1rem;">
                    {student["risk_band"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    summary_cols = st.columns(
        4,
        gap="medium",
    )

    summary = [
        (
            "Attendance",
            f'{_safe_float(student["attendance_rate"]):.1f}%',
        ),
        (
            "LMS change",
            f'{_safe_float(student["lms_change_pct"]):+.1f}%',
        ),
        (
            "Submission rate",
            f'{_safe_float(student["submission_rate"]):.1f}%',
        ),
        (
            "Assessment average",
            f'{_safe_float(student["average_score"]):.1f}',
        ),
    ]

    for column, (label, value) in zip(
        summary_cols,
        summary,
    ):

        with column:

            st.metric(
                label,
                value,
            )

    # ========================================================
    # WEEKLY TRAJECTORIES
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Engagement trajectory'
        '</div>',
        unsafe_allow_html=True,
    )

    if weekly.empty:

        st.info(
            "No weekly profile records are available."
        )

    else:

        weekly["week_number"] = pd.to_numeric(
            weekly["week_number"],
            errors="coerce",
        )

        weekly["attendance_rate"] = pd.to_numeric(
            weekly["attendance_rate"],
            errors="coerce",
        )

        weekly["minutes_active"] = pd.to_numeric(
            weekly["minutes_active"],
            errors="coerce",
        )

        weekly["submission_rate"] = pd.to_numeric(
            weekly["submission_rate"],
            errors="coerce",
        )

        # ----------------------------------------------------
        # Attendance
        # ----------------------------------------------------

        chart_left, chart_right = st.columns(
            2,
            gap="large",
        )

        with chart_left:

            st.markdown(
                "**Attendance by week**"
            )

            attendance_chart = px.line(
                weekly,
                x="week_number",
                y="attendance_rate",
                markers=True,
            )

            attendance_chart.update_traces(
                hovertemplate=(
                    "Week %{x}<br>"
                    "Attendance %{y:.1f}%"
                    "<extra></extra>"
                ),
            )

            attendance_chart.update_layout(
                template="simple_white",
                height=330,
                margin=dict(
                    l=10,
                    r=20,
                    t=25,
                    b=20,
                ),
                xaxis_title="Week",
                yaxis_title="Attendance (%)",
                yaxis=dict(
                    range=[
                        0,
                        100,
                    ]
                ),
            )

            st.plotly_chart(
                attendance_chart,
                use_container_width=True,
            )

        # ----------------------------------------------------
        # LMS
        # ----------------------------------------------------

        with chart_right:

            st.markdown(
                "**LMS active minutes by week**"
            )

            lms_chart = px.line(
                weekly,
                x="week_number",
                y="minutes_active",
                markers=True,
            )

            lms_chart.update_traces(
                hovertemplate=(
                    "Week %{x}<br>"
                    "Active minutes %{y:.1f}"
                    "<extra></extra>"
                ),
            )

            lms_chart.update_layout(
                template="simple_white",
                height=330,
                margin=dict(
                    l=10,
                    r=20,
                    t=25,
                    b=20,
                ),
                xaxis_title="Week",
                yaxis_title="Active minutes",
            )

            st.plotly_chart(
                lms_chart,
                use_container_width=True,
            )

        # ----------------------------------------------------
        # Assignment submission
        # ----------------------------------------------------

        st.markdown(
            "**Assignment submission rate by week**"
        )

        submission_chart = px.bar(
            weekly,
            x="week_number",
            y="submission_rate",
            text="submission_rate",
        )

        submission_chart.update_traces(
            texttemplate="%{text:.0f}%",
            textposition="outside",
        )

        submission_chart.update_layout(
            template="simple_white",
            height=330,
            margin=dict(
                l=10,
                r=35,
                t=35,
                b=20,
            ),
            xaxis_title="Week",
            yaxis_title="Submission rate (%)",
            yaxis=dict(
                range=[
                    0,
                    100,
                ]
            ),
        )

        st.plotly_chart(
            submission_chart,
            use_container_width=True,
        )

    # ========================================================
    # ASSESSMENT TRAJECTORY
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Assessment trajectory'
        '</div>',
        unsafe_allow_html=True,
    )

    if assessments.empty:

        st.info(
            "No assessment records are available."
        )

    else:

        assessments["assessment_number"] = pd.to_numeric(
            assessments["assessment_number"],
            errors="coerce",
        )

        assessments["score"] = pd.to_numeric(
            assessments["score"],
            errors="coerce",
        )

        assessments["assessment_date"] = pd.to_datetime(
            assessments["assessment_date"],
            errors="coerce",
        )

        assessments["assessment_label"] = (
            assessments["assessment_type"].astype(str)
            + " · "
            + assessments["course_id"].astype(str)
        )

        assessment_chart = px.line(
            assessments,
            x="assessment_number",
            y="score",
            markers=True,
            hover_data=[
                "assessment_label",
                "assessment_date",
            ],
        )

        assessment_chart.update_traces(
            hovertemplate=(
                "Assessment %{x}<br>"
                "Score %{y:.1f}<br>"
                "%{customdata[0]}"
                "<extra></extra>"
            ),
        )

        assessment_chart.update_layout(
            template="simple_white",
            height=360,
            margin=dict(
                l=10,
                r=30,
                t=30,
                b=20,
            ),
            xaxis_title="Assessment sequence",
            yaxis_title="Score",
            yaxis=dict(
                range=[
                    0,
                    100,
                ]
            ),
        )

        st.plotly_chart(
            assessment_chart,
            use_container_width=True,
        )

        assessment_display = assessments[
            [
                "assessment_number",
                "assessment_date",
                "assessment_type",
                "course_id",
                "score",
            ]
        ].copy()

        assessment_display["score"] = (
            assessment_display["score"]
            .round(1)
        )

        st.dataframe(
            assessment_display,
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # RISK CONTRIBUTION
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Risk contribution'
        '</div>',
        unsafe_allow_html=True,
    )

    contribution = pd.DataFrame(
        [
            _metric_row(
                "Attendance",
                f'{_safe_float(student["attendance_rate"]):.1f}%',
                _safe_float(student["attendance_risk"]),
                25,
            ),
            _metric_row(
                "LMS engagement",
                f'{_safe_float(student["lms_change_pct"]):+.1f}%',
                _safe_float(student["engagement_risk"]),
                20,
            ),
            _metric_row(
                "Assignment submission",
                f'{_safe_float(student["submission_rate"]):.1f}%',
                _safe_float(student["assignment_risk"]),
                20,
            ),
            _metric_row(
                "Academic performance",
                f'{_safe_float(student["average_score"]):.1f}',
                _safe_float(student["performance_risk"]),
                25,
            ),
            _metric_row(
                "Performance trend",
                f'{_safe_float(student["score_change"]):+.1f}',
                _safe_float(student["trend_risk"]),
                10,
            ),
        ]
    )

    contribution_chart = px.bar(
        contribution,
        x="Contribution",
        y="Indicator",
        orientation="h",
        text="Contribution label",
        custom_data=[
            "Maximum",
            "Value",
        ],
    )

    contribution_chart.update_traces(
        textposition="outside",
        hovertemplate=(
            "%{y}<br>"
            "Observed: %{customdata[1]}<br>"
            "Risk contribution: %{x:.1f} / "
            "%{customdata[0]:.0f}"
            "<extra></extra>"
        ),
    )

    contribution_chart.update_layout(
        template="simple_white",
        height=370,
        margin=dict(
            l=10,
            r=85,
            t=20,
            b=20,
        ),
        xaxis_title="Risk points",
        yaxis_title=None,
    )

    st.plotly_chart(
        contribution_chart,
        use_container_width=True,
    )

    # ========================================================
    # WHY FLAGGED
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Why this profile was flagged'
        '</div>',
        unsafe_allow_html=True,
    )

    reasons = [
        reason.strip()
        for reason in str(
            student["risk_reasons"]
        ).split(";")
        if reason.strip()
    ]

    if reasons:

        reasons_html = "".join(
            [
                (
                    '<span class="signal">'
                    f'{reason}'
                    '</span>'
                )
                for reason in reasons
            ]
        )

        st.markdown(
            reasons_html,
            unsafe_allow_html=True,
        )

    else:

        st.caption(
            "No material risk reasons are recorded."
        )

    # ========================================================
    # TREND SUMMARY
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Trend summary'
        '</div>',
        unsafe_allow_html=True,
    )

    trend_cols = st.columns(
        3,
        gap="medium",
    )

    with trend_cols[0]:

        st.metric(
            "Assessment change",
            f'{_safe_float(student["score_change"]):+.1f}',
        )

    with trend_cols[1]:

        if len(weekly) >= 2:

            first_lms = _safe_float(
                weekly.iloc[0]["minutes_active"]
            )

            last_lms = _safe_float(
                weekly.iloc[-1]["minutes_active"]
            )

            st.metric(
                "LMS minutes change",
                f"{last_lms - first_lms:+.1f}",
            )

        else:

            st.metric(
                "LMS minutes change",
                "n/a",
            )

    with trend_cols[2]:

        if len(weekly) >= 2:

            first_attendance = _safe_float(
                weekly.iloc[0]["attendance_rate"]
            )

            last_attendance = _safe_float(
                weekly.iloc[-1]["attendance_rate"]
            )

            st.metric(
                "Attendance change",
                f"{last_attendance - first_attendance:+.1f} pp",
            )

        else:

            st.metric(
                "Attendance change",
                "n/a",
            )

    # ========================================================
    # INTERVENTION HISTORY
    # ========================================================

    st.markdown(
        '<div class="section-heading">'
        'Intervention history'
        '</div>',
        unsafe_allow_html=True,
    )

    if student_interventions.empty:

        st.info(
            "No synthetic intervention records exist "
            "for this student."
        )

    else:

        available_columns = [
            column
            for column in [
                "intervention_id",
                "risk_type",
                "trigger_date",
                "intervention_type",
                "advisor",
                "status",
                "outcome",
            ]
            if column
            in student_interventions.columns
        ]

        intervention_display = (
            student_interventions[
                available_columns
            ]
            .sort_values(
                "trigger_date",
                ascending=False,
            )
        )

        st.dataframe(
            intervention_display,
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # HUMAN REVIEW PRINCIPLE
    # ========================================================

    st.markdown(
        """
        <div class="prototype-notice">

            <strong>Human-review principle</strong><br>

            The risk signal is an analytical prompt for professional
            review, not an automatic determination of a student's
            outcome. The profile exposes the underlying evidence,
            contributing indicators, trends and intervention history
            to support informed review.

        </div>
        """,
        unsafe_allow_html=True,
    )
