"""
Behaviour Flags Service
────────────────────────
Replaces StaticInsights.behaviourFlags()

Real anomaly detection from log patterns:
  - Missed meal detection (time gaps where meals usually happen)
  - Inactivity windows (unusual silence periods)
  - Medication gaps
  - Night-time activity spikes (possible sundowning)
  - Repetitive behaviour patterns
  - Sudden activity drops vs personal baseline

Uses z-score based anomaly detection on rolling windows.
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.models.schemas import BehaviourFlag, BehaviourFlagsResponse, LogEntry

logger = logging.getLogger(__name__)

MEAL_KEYWORDS = {"ate", "breakfast", "lunch", "dinner", "snack", "meal", "eat", "food"}
MED_KEYWORDS = {"medicine", "medication", "took_medication", "pill", "drug", "med"}


def _categorise(activity: str) -> str:
    a = activity.lower().replace("_", " ")
    for kw in MEAL_KEYWORDS:
        if kw in a:
            return "meal"
    for kw in MED_KEYWORDS:
        if kw in a:
            return "medication"
    return "other"


def detect_behaviour_flags(logs: list[LogEntry]) -> BehaviourFlagsResponse:
    """Detect anomalies and concerning patterns from log data."""

    flags: list[BehaviourFlag] = []

    if not logs:
        flags.append(BehaviourFlag(
            flag="No activity data available",
            severity="warning",
            detail="Cannot assess behaviour without log data. Encourage the patient to log activities.",
        ))
        return BehaviourFlagsResponse(flags=flags)

    rows = []
    for log in logs:
        if log.createdAt:
            rows.append({
                "activity": log.activity,
                "type": log.type,
                "category": _categorise(log.activity),
                "hour": log.createdAt.hour,
                "date": log.createdAt.date(),
                "timestamp": log.createdAt,
            })

    if not rows:
        return BehaviourFlagsResponse(flags=flags)

    df = pd.DataFrame(rows)
    today = datetime.utcnow().date()

    # ── 1. Missed meals ──────────────────────────────────────────────
    flags.extend(_check_missed_meals(df, today))

    # ── 2. Medication gaps ───────────────────────────────────────────
    flags.extend(_check_medication_gaps(df, today))

    # ── 3. Inactivity detection ──────────────────────────────────────
    flags.extend(_check_inactivity(df, today))

    # ── 4. Night-time activity (sundowning signal) ───────────────────
    flags.extend(_check_night_activity(df))

    # ── 5. Repetitive behaviour ──────────────────────────────────────
    flags.extend(_check_repetitive_behaviour(df, today))

    # ── 6. Activity drop-off ─────────────────────────────────────────
    flags.extend(_check_activity_dropoff(df, today))

    # Sort by severity
    severity_order = {"alert": 0, "warning": 1, "info": 2}
    flags.sort(key=lambda f: severity_order.get(f.severity, 3))

    return BehaviourFlagsResponse(flags=flags)


def _check_missed_meals(df: pd.DataFrame, today) -> list[BehaviourFlag]:
    flags = []
    meals = df[df["category"] == "meal"]

    if meals.empty:
        if datetime.utcnow().hour >= 14:
            flags.append(BehaviourFlag(
                flag="No meals logged today",
                severity="warning",
                detail="It's past 2 PM and no meal activity has been recorded.",
            ))
        return flags

    # Check today's meals
    today_meals = meals[meals["date"] == today]
    current_hour = datetime.utcnow().hour

    if today_meals.empty and current_hour >= 13:
        # Check if patient usually eats by now
        historical_before_now = meals[meals["hour"] <= current_hour]
        if not historical_before_now.empty:
            avg_meals_by_now = len(historical_before_now) / max(1, df["date"].nunique())
            if avg_meals_by_now >= 0.5:
                flags.append(BehaviourFlag(
                    flag="Possible missed meal",
                    severity="warning",
                    detail=f"Usually {avg_meals_by_now:.1f} meals are logged by this time. None today.",
                ))

    return flags


def _check_medication_gaps(df: pd.DataFrame, today) -> list[BehaviourFlag]:
    flags = []
    meds = df[df["category"] == "medication"]

    if meds.empty:
        return flags

    # Days with med logs vs total days
    days_with_meds = meds["date"].nunique()
    total_days = df["date"].nunique()

    if total_days >= 3 and days_with_meds / total_days < 0.5:
        flags.append(BehaviourFlag(
            flag="Inconsistent medication logging",
            severity="warning",
            detail=f"Medication was logged on {days_with_meds}/{total_days} days. Adherence may need attention.",
        ))

    # Check if today is missing meds when they're usually taken by now
    today_meds = meds[meds["date"] == today]
    if today_meds.empty and datetime.utcnow().hour >= 10:
        usual_morning_meds = meds[meds["hour"] < 12]
        if not usual_morning_meds.empty:
            flags.append(BehaviourFlag(
                flag="Morning medication not logged",
                severity="info",
                detail="Morning medication is usually logged by now.",
            ))

    return flags


def _check_inactivity(df: pd.DataFrame, today) -> list[BehaviourFlag]:
    flags = []

    # Check today vs average
    today_count = len(df[df["date"] == today])
    daily_counts = df.groupby("date").size()
    avg_daily = daily_counts.mean()

    if len(daily_counts) >= 3 and today_count == 0 and datetime.utcnow().hour >= 12:
        flags.append(BehaviourFlag(
            flag="No activity today",
            severity="warning",
            detail=f"Average daily activity is {avg_daily:.1f} logs. None recorded today by noon.",
        ))
    elif len(daily_counts) >= 5 and today_count > 0:
        std_daily = daily_counts.std()
        if std_daily > 0 and today_count < avg_daily - 2 * std_daily:
            flags.append(BehaviourFlag(
                flag="Unusually low activity",
                severity="info",
                detail=f"Today has {today_count} logs vs average {avg_daily:.1f}.",
            ))

    return flags


def _check_night_activity(df: pd.DataFrame) -> list[BehaviourFlag]:
    flags = []

    # Night = 11pm - 5am
    night = df[(df["hour"] >= 23) | (df["hour"] < 5)]
    if len(night) >= 3:
        night_ratio = len(night) / max(1, len(df))
        if night_ratio > 0.15:
            flags.append(BehaviourFlag(
                flag="Elevated night-time activity",
                severity="warning",
                detail=f"{len(night)} activities logged between 11 PM and 5 AM "
                       f"({night_ratio:.0%} of total). May indicate sleep disruption or sundowning.",
            ))

    return flags


def _check_repetitive_behaviour(df: pd.DataFrame, today) -> list[BehaviourFlag]:
    flags = []

    today_df = df[df["date"] == today]
    if len(today_df) >= 4:
        activity_counts = Counter(today_df["activity"].tolist())
        for activity, count in activity_counts.items():
            if count >= 4:
                flags.append(BehaviourFlag(
                    flag="Repetitive activity pattern",
                    severity="info",
                    detail=f"'{activity.replace('_', ' ')}' logged {count} times today.",
                ))

    return flags


def _check_activity_dropoff(df: pd.DataFrame, today) -> list[BehaviourFlag]:
    flags = []

    daily = df.groupby("date").size().reset_index(name="count")
    if len(daily) < 5:
        return flags

    # Compare last 3 days vs previous 4
    daily = daily.sort_values("date")
    recent = daily.tail(3)["count"].mean()
    earlier = daily.iloc[-7:-3]["count"].mean() if len(daily) >= 7 else daily.head(4)["count"].mean()

    if earlier > 0 and recent / earlier < 0.4:
        flags.append(BehaviourFlag(
            flag="Significant activity drop",
            severity="alert",
            detail=f"Recent daily average ({recent:.1f}) is less than half of earlier period ({earlier:.1f}).",
        ))

    return flags
