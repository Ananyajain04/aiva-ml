"""
Caregiver Weekly Summary Service
─────────────────────────────────
Replaces StaticInsights.caregiverWeeklySummary()

Approach: Analyse 7 days of logs to produce a data-driven narrative.
Computes:
  - Total activity count + trend vs previous week
  - Medication adherence rate (med logs / expected)
  - Activity type breakdown
  - Day-of-week patterns
  - Generates natural language summary from template system
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.models.schemas import LogEntry, WeeklySummaryResponse

logger = logging.getLogger(__name__)

MEAL_KEYWORDS = {"ate", "breakfast", "lunch", "dinner", "snack", "meal", "eat", "food"}
MED_KEYWORDS = {"medicine", "medication", "took_medication", "pill", "drug", "med"}
MOVE_KEYWORDS = {"walk", "exercise", "movement", "stretch", "yoga", "garden"}


def _categorise(activity: str) -> str:
    a = activity.lower().replace("_", " ")
    for kw in MEAL_KEYWORDS:
        if kw in a:
            return "meal"
    for kw in MED_KEYWORDS:
        if kw in a:
            return "medication"
    for kw in MOVE_KEYWORDS:
        if kw in a:
            return "movement"
    return "other"


def compute_weekly_summary(
    logs: list[LogEntry],
    medications: list[dict] | None = None,
) -> WeeklySummaryResponse:
    """Generate a data-driven weekly narrative for caregivers."""

    if not logs:
        return WeeklySummaryResponse(
            narrative=(
                "No activity logs this week. Encourage the patient to open a guided "
                "task or tap a quick log — even small interactions help build awareness."
            ),
            total_logs=0,
            medication_adherence=0.0,
            activity_trend="no_data",
            highlights=["No engagement detected this period"],
        )

    # Parse into DataFrame
    rows = []
    for log in logs:
        if log.createdAt:
            rows.append({
                "activity": log.activity,
                "type": log.type,
                "source": log.source,
                "category": _categorise(log.activity),
                "hour": log.createdAt.hour,
                "date": log.createdAt.date(),
                "weekday": log.createdAt.strftime("%A"),
            })

    if not rows:
        return WeeklySummaryResponse(
            narrative="Logs exist but timestamps couldn't be parsed. Check data format.",
            total_logs=len(logs),
        )

    df = pd.DataFrame(rows)
    total = len(df)

    # ── Category breakdown ───────────────────────────────────────────
    cat_counts = dict(df["category"].value_counts())
    med_count = cat_counts.get("medication", 0)
    meal_count = cat_counts.get("meal", 0)
    move_count = cat_counts.get("movement", 0)

    # ── Activity trend ───────────────────────────────────────────────
    now = datetime.utcnow().date()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    this_week = df[df["date"] >= week_ago]
    prev_week = df[(df["date"] >= two_weeks_ago) & (df["date"] < week_ago)]

    tw_count = len(this_week)
    pw_count = len(prev_week)

    if pw_count == 0:
        trend = "new"
    elif tw_count > pw_count * 1.15:
        trend = "improving"
    elif tw_count < pw_count * 0.85:
        trend = "declining"
    else:
        trend = "stable"

    # ── Medication adherence ─────────────────────────────────────────
    num_meds = len(medications) if medications else 0
    expected_med_logs = max(1, num_meds * 7)  # 1 per med per day for 7 days
    med_adherence = min(1.0, med_count / expected_med_logs) if expected_med_logs > 0 else 0.0

    # ── Day-of-week pattern ──────────────────────────────────────────
    day_counts = dict(df["weekday"].value_counts())
    active_days = [d for d, c in day_counts.items() if c >= 2]
    quiet_days = [d for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                  if day_counts.get(d, 0) == 0]

    # ── Highlights ───────────────────────────────────────────────────
    highlights: list[str] = []

    if med_adherence >= 0.8:
        highlights.append("Strong medication adherence this week")
    elif med_adherence > 0 and med_adherence < 0.5:
        highlights.append("Low medication logging — consider a reminder adjustment")

    if meal_count >= 14:  # ~2 meals/day tracked
        highlights.append("Regular meal logging detected")
    elif meal_count == 0:
        highlights.append("No meals logged — patient may need meal prompts")

    if move_count >= 3:
        highlights.append(f"{move_count} movement activities logged")

    if quiet_days:
        highlights.append(f"Quiet days: {', '.join(quiet_days[:3])}")

    if trend == "improving":
        highlights.append("Activity is trending upward vs last week")
    elif trend == "declining":
        highlights.append("Activity has decreased compared to last week")

    # ── Narrative ────────────────────────────────────────────────────
    narrative = _build_narrative(total, med_count, meal_count, move_count,
                                 med_adherence, trend, active_days, quiet_days, highlights)

    return WeeklySummaryResponse(
        narrative=narrative,
        total_logs=total,
        medication_adherence=round(med_adherence, 2),
        activity_trend=trend,
        highlights=highlights,
    )


def _build_narrative(
    total: int,
    med_count: int,
    meal_count: int,
    move_count: int,
    med_adherence: float,
    trend: str,
    active_days: list[str],
    quiet_days: list[str],
    highlights: list[str],
) -> str:
    parts: list[str] = []

    # Opening
    parts.append(f"This week recorded {total} activities.")

    # Trend
    trend_text = {
        "improving": "Engagement is trending upward — a positive sign.",
        "declining": "Activity has dipped compared to last week. A gentle nudge may help.",
        "stable": "Activity levels are holding steady.",
        "new": "This is the first week of data — patterns will become clearer over time.",
        "no_data": "",
    }
    t = trend_text.get(trend, "")
    if t:
        parts.append(t)

    # Medication
    if med_count > 0:
        pct = int(med_adherence * 100)
        parts.append(f"Medication logging is at {pct}% adherence ({med_count} entries).")
    else:
        parts.append("No medication logs detected. Check if reminders are reaching the patient.")

    # Meals
    if meal_count > 0:
        avg_meals = round(meal_count / 7, 1)
        parts.append(f"About {avg_meals} meals logged per day on average.")

    # Movement
    if move_count > 0:
        parts.append(f"{move_count} movement activities recorded — good for maintaining routine.")

    # Active/quiet days
    if quiet_days and len(quiet_days) <= 3:
        parts.append(f"Consider adding prompts on {', '.join(quiet_days)}.")

    return " ".join(parts)
