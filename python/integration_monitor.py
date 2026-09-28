"""
Student Success Analytics
Synthetic Integration Health Monitor

Purpose
-------
Generate synthetic operational telemetry for the interfaces
that connect institutional source systems to the analytical
environment.

This is NOT connected to any real university system.

The generated data demonstrates:

- interface health
- synchronization frequency
- data freshness
- latency
- record volumes
- error monitoring
- recent integration events

All values are synthetic.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

RANDOM_SEED = 20260928

OUTPUT_DIR = (
    Path("data/synthetic/integration")
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

rng = np.random.default_rng(
    RANDOM_SEED
)

SIMULATION_NOW = datetime(
    2026,
    9,
    28,
    18,
    0,
)


# ============================================================
# Integration definitions
# ============================================================

INTEGRATIONS = [
    {
        "integration_id": "INT-SIS-ANL",
        "source_system": "Student Information System",
        "target_system": "Analytics Data Layer",
        "interface_type": "REST API",
        "sync_frequency": "Every 15 minutes",
        "owner": "Data Platform",
        "base_records": 250,
        "base_latency": 820,
    },
    {
        "integration_id": "INT-LMS-ANL",
        "source_system": "Learning Management System",
        "target_system": "Analytics Data Layer",
        "interface_type": "REST API",
        "sync_frequency": "Every 10 minutes",
        "owner": "Learning Technology",
        "base_records": 1450,
        "base_latency": 1050,
    },
    {
        "integration_id": "INT-ATT-ANL",
        "source_system": "Attendance Platform",
        "target_system": "Analytics Data Layer",
        "interface_type": "Scheduled API",
        "sync_frequency": "Every 30 minutes",
        "owner": "Academic Operations",
        "base_records": 900,
        "base_latency": 740,
    },
    {
        "integration_id": "INT-ANL-ASC",
        "source_system": "Analytics Data Layer",
        "target_system": "Student Support Workflow",
        "interface_type": "Secure API",
        "sync_frequency": "Event-driven",
        "owner": "Academic Success Center",
        "base_records": 80,
        "base_latency": 610,
    },
]


# ============================================================
# Helpers
# ============================================================

def determine_status(
    freshness_minutes: float,
    error_count: int,
    success_rate: float,
) -> str:
    """Classify operational integration health."""

    if (
        freshness_minutes > 60
        or success_rate < 95
        or error_count >= 8
    ):
        return "Attention"

    if (
        freshness_minutes > 30
        or success_rate < 99
        or error_count > 2
    ):
        return "Warning"

    return "Healthy"


# ============================================================
# Generate integration health
# ============================================================

health_rows = []

for integration in INTEGRATIONS:

    freshness = max(
        3,
        rng.normal(
            18,
            7,
        ),
    )

    error_count = int(
        rng.poisson(2.0)
    )

    success_rate = max(
        90,
        min(
            100,
            100
            - error_count
            * rng.uniform(
                0.15,
                0.45,
            ),
        ),
    )

    records_processed = int(
        integration["base_records"]
        * rng.uniform(
            0.80,
            1.20,
        )
    )

    latency = max(
        150,
        rng.normal(
            integration["base_latency"],
            120,
        ),
    )

    last_success = (
        SIMULATION_NOW
        - timedelta(
            minutes=float(freshness)
        )
    )

    status = determine_status(
        freshness_minutes=freshness,
        error_count=error_count,
        success_rate=success_rate,
    )

    health_rows.append(
        {
            "integration_id":
                integration["integration_id"],

            "source_system":
                integration["source_system"],

            "target_system":
                integration["target_system"],

            "interface_type":
                integration["interface_type"],

            "sync_frequency":
                integration["sync_frequency"],

            "last_success_at":
                last_success.isoformat(
                    sep=" "
                ),

            "records_last_sync":
                records_processed,

            "latency_ms":
                round(
                    latency
                ),

            "error_count_24h":
                error_count,

            "data_freshness_minutes":
                round(
                    freshness,
                    1,
                ),

            "success_rate_24h":
                round(
                    success_rate,
                    2,
                ),

            "status":
                status,

            "owner":
                integration["owner"],
        }
    )


health_df = pd.DataFrame(
    health_rows
)


# ============================================================
# Generate event history
# ============================================================

event_rows = []

EVENT_TYPES = [
    "Successful synchronization",
    "Timeout",
    "Authentication failure",
    "Schema validation warning",
    "Rate-limit response",
    "Connection retry",
]


for integration in INTEGRATIONS:

    for event_number in range(1, 61):

        event_time = (
            SIMULATION_NOW
            - timedelta(
                minutes=event_number * 30
            )
        )

        probability = rng.random()

        if probability < 0.94:

            status = "SUCCESS"

            event_type = (
                "Successful synchronization"
            )

            error_message = ""

        elif probability < 0.975:

            status = "WARNING"

            event_type = rng.choice(
                [
                    "Schema validation warning",
                    "Connection retry",
                    "Rate-limit response",
                ]
            )

            error_message = (
                "Transient condition; "
                "retry completed."
            )

        else:

            status = "FAILED"

            event_type = rng.choice(
                [
                    "Timeout",
                    "Authentication failure",
                ]
            )

            error_message = (
                "Synthetic integration "
                "failure for demonstration."
            )

        integration_record = (
            next(
                item
                for item in INTEGRATIONS
                if item["integration_id"]
                == integration["integration_id"]
            )
        )

        records_processed = int(
            integration_record["base_records"]
            * rng.uniform(
                0.75,
                1.20,
            )
        )

        latency = max(
            100,
            int(
                rng.normal(
                    integration_record[
                        "base_latency"
                    ],
                    150,
                )
            ),
        )

        event_rows.append(
            {
                "event_id":
                    f'{integration["integration_id"]}-EVT-{event_number:04d}',

                "integration_id":
                    integration[
                        "integration_id"
                    ],

                "event_time":
                    event_time.isoformat(
                        sep=" "
                    ),

                "status":
                    status,

                "event_type":
                    event_type,

                "records_processed":
                    records_processed,

                "latency_ms":
                    latency,

                "error_message":
                    error_message,
            }
        )


events_df = pd.DataFrame(
    event_rows
)


# ============================================================
# Save
# ============================================================

health_path = (
    OUTPUT_DIR
    / "integration_health.csv"
)

events_path = (
    OUTPUT_DIR
    / "integration_events.csv"
)


health_df.to_csv(
    health_path,
    index=False,
)

events_df.to_csv(
    events_path,
    index=False,
)


# ============================================================
# Console report
# ============================================================

print("\n")
print("=" * 72)
print(
    "STUDENT SUCCESS ANALYTICS — INTEGRATION MONITOR"
)
print("=" * 72)

print(
    "\nSynthetic integration telemetry generated."
)

print(
    f"\nInterfaces: {len(health_df):,}"
)

print(
    f"Events:     {len(events_df):,}"
)


print("\n")
print("-" * 72)
print("INTEGRATION HEALTH")
print("-" * 72)

print(
    health_df[
        [
            "integration_id",
            "source_system",
            "target_system",
            "status",
            "data_freshness_minutes",
            "success_rate_24h",
            "error_count_24h",
            "latency_ms",
        ]
    ].to_string(
        index=False
    )
)


print("\n")
print("-" * 72)
print("RECENT EVENT COUNTS")
print("-" * 72)

print(
    events_df[
        "status"
    ]
    .value_counts()
    .to_string()
)


print("\n")
print("-" * 72)
print("OUTPUT FILES")
print("-" * 72)

print(
    health_path
)

print(
    events_path
)


print("\n")
print("=" * 72)
print(
    "INTEGRATION TELEMETRY GENERATION COMPLETE"
)
print("=" * 72)