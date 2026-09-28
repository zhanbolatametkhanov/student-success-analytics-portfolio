"""
Reusable Student Success Analytics dashboard components.

This module keeps presentation logic separate from data-access
and analytical logic.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def section_title(
    title: str,
    eyebrow: str | None = None,
) -> None:
    """Render a consistent dashboard section heading."""

    if eyebrow:

        st.markdown(
            f"""
            <div class="eyebrow">
                {eyebrow}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="section-heading">
            {title}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    description: str = "",
) -> None:
    """Render a consistent metric card."""

    st.markdown(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                {label}
            </div>

            <div class="kpi-value">
                {value}
            </div>

            <div class="kpi-description">
                {description}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(
    risk_band: str,
) -> None:
    """Render a simple risk-band badge."""

    st.markdown(
        f"""
        <div class="risk-card">
            <div class="risk-card-title">
                Demonstration risk band
            </div>

            <div class="risk-card-value">
                {risk_band}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_table(
    dataframe: pd.DataFrame,
) -> None:
    """Consistent table presentation."""

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )
