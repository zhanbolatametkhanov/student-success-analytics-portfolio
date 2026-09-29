from __future__ import annotations

from html import escape

import streamlit as st


NAVY = "#243447"
NAVY_DARK = "#1B2838"
GOLD = "#DDAF53"
GOLD_DARK = "#9A7432"
INK = "#24231F"
MUTED = "#6F6B61"
SURFACE = "#FFFFFF"
SURFACE_SOFT = "#F3F1EA"
BORDER = "#DDD9CF"
SUCCESS = "#3F6B55"
WARNING = "#9A6A1F"
CRITICAL = "#8C4040"


def inject_ui_styles() -> None:
    """Inject the shared visual system used across the dashboard."""

    st.markdown(
        """
        <style>
        :root {
            --ssa-navy: #243447;
            --ssa-navy-dark: #1B2838;
            --ssa-gold: #DDAF53;
            --ssa-gold-dark: #9A7432;
            --ssa-ink: #24231F;
            --ssa-muted: #6F6B61;
            --ssa-surface: #FFFFFF;
            --ssa-surface-soft: #F3F1EA;
            --ssa-border: #DDD9CF;
            --ssa-success: #3F6B55;
            --ssa-warning: #9A6A1F;
            --ssa-critical: #8C4040;
        }

        .ssa-app-header {
            background: linear-gradient(135deg, #243447 0%, #1B2838 100%);
            border-radius: 14px;
            padding: 1.6rem 1.7rem 1.4rem 1.7rem;
            margin: 0.2rem 0 1rem 0;
            box-shadow: 0 6px 22px rgba(27, 40, 56, 0.10);
        }

        .ssa-header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .ssa-header-kicker {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.70rem;
            font-weight: 800;
            color: #E8C97F;
        }

        .ssa-live-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            background: rgba(255,255,255,0.10);
            color: #F7F6F1;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 999px;
            padding: 0.36rem 0.68rem;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.05em;
        }

        .ssa-live-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #DDAF53;
            display: inline-block;
        }

        .ssa-app-title {
            font-family: Georgia, "Times New Roman", serif;
            color: #FFFFFF;
            font-size: clamp(2.2rem, 4vw, 3.35rem);
            line-height: 1.02;
            margin: 0.7rem 0 0.45rem 0;
        }

        .ssa-app-description {
            max-width: 900px;
            color: rgba(255,255,255,0.82);
            font-size: 1rem;
            line-height: 1.6;
            margin: 0;
        }

        .ssa-header-meta {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
            color: rgba(255,255,255,0.66);
            font-size: 0.76rem;
        }

        .ssa-trust-banner {
            display: flex;
            gap: 0.9rem;
            align-items: flex-start;
            background: #F3F1EA;
            border: 1px solid #DDD9CF;
            border-left: 4px solid #DDAF53;
            border-radius: 10px;
            padding: 0.9rem 1rem;
            margin: 0 0 1.6rem 0;
        }

        .ssa-trust-icon {
            width: 28px;
            height: 28px;
            flex: 0 0 28px;
            border-radius: 50%;
            background: #E9D9AF;
            color: #6D5423;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 0.82rem;
        }

        .ssa-trust-title {
            color: #3F3D35;
            font-weight: 800;
            font-size: 0.84rem;
            margin-bottom: 0.18rem;
        }

        .ssa-trust-text {
            color: #6B675C;
            font-size: 0.79rem;
            line-height: 1.5;
            margin: 0;
        }

        .ssa-page-kicker {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: var(--ssa-gold-dark);
            font-size: 0.68rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .ssa-page-title {
            font-family: Georgia, "Times New Roman", serif;
            color: var(--ssa-ink);
            font-size: clamp(1.9rem, 3vw, 2.45rem);
            line-height: 1.08;
            margin: 0;
        }

        .ssa-page-description {
            max-width: 900px;
            color: var(--ssa-muted);
            font-size: 0.94rem;
            line-height: 1.55;
            margin: 0.45rem 0 0 0;
        }

        .ssa-section {
            margin-top: 1.65rem;
            margin-bottom: 0.85rem;
        }

        .ssa-section-kicker {
            text-transform: uppercase;
            letter-spacing: 0.13em;
            color: var(--ssa-gold-dark);
            font-size: 0.66rem;
            font-weight: 800;
            margin-bottom: 0.24rem;
        }

        .ssa-section-title {
            font-family: Georgia, "Times New Roman", serif;
            color: var(--ssa-ink);
            font-size: 1.45rem;
            line-height: 1.2;
            margin: 0;
        }

        .ssa-section-description {
            color: var(--ssa-muted);
            font-size: 0.82rem;
            line-height: 1.5;
            margin: 0.3rem 0 0 0;
        }

        .ssa-insight {
            background: #FFFFFF;
            border: 1px solid var(--ssa-border);
            border-radius: 11px;
            padding: 0.95rem 1rem;
            box-shadow: 0 3px 12px rgba(36, 52, 71, 0.05);
        }

        .ssa-insight-label {
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: var(--ssa-gold-dark);
            font-size: 0.64rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .ssa-insight-text {
            color: #47443C;
            font-size: 0.86rem;
            line-height: 1.52;
            margin: 0;
        }

        .ssa-status {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            border-radius: 999px;
            padding: 0.30rem 0.62rem;
            font-size: 0.68rem;
            font-weight: 800;
            border: 1px solid transparent;
        }

        .ssa-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            display: inline-block;
        }

        .ssa-status-healthy {
            color: var(--ssa-success);
            background: #EDF4EF;
            border-color: #D2E2D7;
        }

        .ssa-status-warning {
            color: var(--ssa-warning);
            background: #FAF1DF;
            border-color: #EBD8AD;
        }

        .ssa-status-critical {
            color: var(--ssa-critical);
            background: #F8EAEA;
            border-color: #E9CACA;
        }

        .ssa-status-neutral {
            color: #5D5A52;
            background: #F1F0EB;
            border-color: #DDDACF;
        }

        .ssa-footer {
            border-top: 1px solid var(--ssa-border);
            margin-top: 2.5rem;
            padding: 1.2rem 0 0.6rem 0;
            color: #7C786E;
            font-size: 0.72rem;
            line-height: 1.5;
        }

        @media (max-width: 800px) {
            .ssa-app-header {
                padding: 1.25rem 1.1rem;
                border-radius: 11px;
            }

            .ssa-app-title {
                font-size: 2.2rem;
            }

            .ssa-page-title {
                font-size: 1.9rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(
    title: str,
    description: str,
    population_label: str = "2,500 synthetic student records",
) -> None:
    """Render the application-level branded header."""

    safe_title = escape(title)
    safe_description = escape(description)
    safe_population = escape(population_label)

    st.markdown(
        f"""
        <div class="ssa-app-header">
            <div class="ssa-header-row">
                <div class="ssa-header-kicker">Academic Success Center · Systems & Data</div>
                <div class="ssa-live-badge">
                    <span class="ssa-live-dot"></span>
                    LIVE DEMONSTRATION
                </div>
            </div>
            <div class="ssa-app-title">{safe_title}</div>
            <p class="ssa-app-description">{safe_description}</p>
            <div class="ssa-header-meta">
                <span>Python · SQL · SQLite · Streamlit</span>
                <span>{safe_population}</span>
                <span>Portfolio prototype</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trust_banner() -> None:
    """Render the persistent synthetic-data and governance notice."""

    st.markdown(
        """
        <div class="ssa-trust-banner">
            <div class="ssa-trust-icon">i</div>
            <div>
                <div class="ssa-trust-title">Synthetic prototype — interpretation requires professional review</div>
                <p class="ssa-trust-text">
                    All records are simulated for portfolio demonstration. This application is not an
                    operational university system, does not contain real student information, and does
                    not reproduce any institution's internal methodology.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(
    title: str,
    description: str,
    kicker: str = "Student Success Analytics",
) -> None:
    """Render a consistent page heading."""

    st.markdown(
        f"""
        <div class="ssa-section">
            <div class="ssa-page-kicker">{escape(kicker)}</div>
            <h1 class="ssa-page-title">{escape(title)}</h1>
            <p class="ssa-page-description">{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(
    title: str,
    description: str = "",
    kicker: str = "",
) -> None:
    """Render a consistent section heading."""

    kicker_html = ""
    if kicker:
        kicker_html = f'<div class="ssa-section-kicker">{escape(kicker)}</div>'

    description_html = ""
    if description:
        description_html = (
            f'<p class="ssa-section-description">{escape(description)}</p>'
        )

    st.markdown(
        f"""
        <div class="ssa-section">
            {kicker_html}
            <h2 class="ssa-section-title">{escape(title)}</h2>
            {description_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(
    text: str,
    label: str = "Analytical context",
) -> None:
    """Render a concise interpretive note below a visual or table."""

    st.markdown(
        f"""
        <div class="ssa-insight">
            <div class="ssa-insight-label">{escape(label)}</div>
            <p class="ssa-insight-text">{escape(text)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(
    label: str,
    status: str = "neutral",
) -> None:
    """Render an accessible semantic status badge."""

    normalized = status.lower().strip()
    class_name = {
        "healthy": "ssa-status-healthy",
        "success": "ssa-status-healthy",
        "warning": "ssa-status-warning",
        "critical": "ssa-status-critical",
    }.get(normalized, "ssa-status-neutral")

    dot_color = {
        "healthy": "#3F6B55",
        "success": "#3F6B55",
        "warning": "#9A6A1F",
        "critical": "#8C4040",
    }.get(normalized, "#6F6B61")

    st.markdown(
        f"""
        <span class="ssa-status {class_name}">
            <span class="ssa-status-dot" style="background:{dot_color};"></span>
            {escape(label)}
        </span>
        """,
        unsafe_allow_html=True,
    )
