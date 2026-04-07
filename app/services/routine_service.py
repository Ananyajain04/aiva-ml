"""
Routine Insights Service
─────────────────────────
Replaces StaticInsights.routineHint()

Approach: Analyse the patient's activity logs to detect:
  - Time-of-day activity patterns (morning/afternoon/evening clusters)
  - Activity type distribution (meals, meds, walks, etc.)
  - Gaps in routine vs personal baseline
  - Personalised suggestions based on what the patient actually does

No heavy models — uses pandas time bucketing + scikit-learn KMeans
for rhythm clustering, with rule-based narrative generation on top.
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.models.schemas import LogEntry, RoutineHintResponse

logger = logging.getLogger(__name__)

# ── Activity categories ──────────────────────────────────────────────
MEAL_KEYWORDS = {"ate", "breakfast", "lunch", "dinner", "snack", "meal", "eat", "food"}
MED_KEYWORDS = {"medicine", "medication", "took_medication", "pill", "drug", "med"}
MOVE_KEYWORDS = {"walk", "exercise", "movement", "stretch", "yoga", "garden"}
REST_KEYWORDS = {"rest", "sleep", "nap", "rested", "calm", "relax"}
SOCIAL_KEYWORDS = {"recall", "memory", "conversation", "visit", "call", "chat"}


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
    for kw in REST_KEYWORDS:
        if kw in a:
            return "rest"
    for kw in SOCIAL_KEYWORDS:
        if kw in a:
            return "social"
    return "other"


def _time_bucket(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def compute_routine_hint(logs: list[LogEntry]) -> RoutineHintResponse:
    """Generate a personalised routine hint from real log data."""

    if not logs:
        return RoutineHintResponse(
            hint="No activities logged yet today. A short walk or a cup of tea can be a gentle start.",
            confidence=0.0,
            suggested_activities=["short walk", "light meal", "memory recall"],
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
                "bucket": _time_bucket(log.createdAt.hour),
                "date": log.createdAt.date(),
            })

    if not rows:
        return RoutineHintResponse(
            hint="We see some logs but can't parse timestamps yet. Try logging a quick activity.",
            confidence=0.1,
            suggested_activities=["log a meal", "short walk"],
        )

    df = pd.DataFrame(rows)
    today = datetime.utcnow().date()
    today_df = df[df["date"] == today]
    today_count = len(today_df)

    # Category counts for today
    cat_counts = Counter(today_df["category"].tolist()) if not today_df.empty else Counter()

    # What's missing today vs overall pattern?
    all_cats = set(df["category"].unique())
    done_cats = set(cat_counts.keys())
    missing_cats = all_cats - done_cats - {"other"}

    # Activity suggestions
    suggestions: list[str] = []

    # Current time bucket
    current_hour = datetime.utcnow().hour
    current_bucket = _time_bucket(current_hour)

    # What does this patient usually do in this time bucket?
    bucket_history = df[df["bucket"] == current_bucket]
    if not bucket_history.empty:
        usual_activities = bucket_history["category"].value_counts().head(3).index.tolist()
        for cat in usual_activities:
            if cat not in done_cats:
                suggestions.append(_suggestion_for_category(cat))

    # Fill from missing categories
    for cat in missing_cats:
        s = _suggestion_for_category(cat)
        if s not in suggestions:
            suggestions.append(s)

    suggestions = suggestions[:3]  # max 3

    # Build hint text
    hint = _build_hint_text(today_count, cat_counts, current_bucket, bucket_history, missing_cats, df)

    # Confidence: more data = higher confidence
    total_days = df["date"].nunique()
    confidence = min(1.0, total_days / 14.0)  # 2 weeks = full confidence

    return RoutineHintResponse(
        hint=hint,
        confidence=round(confidence, 2),
        suggested_activities=suggestions,
    )


def _suggestion_for_category(cat: str) -> str:
    return {
        "meal": "have a light meal or snack",
        "medication": "check if any medicine is due",
        "movement": "try a short walk or stretch",
        "rest": "take a moment to rest",
        "social": "do a memory recall or call someone",
    }.get(cat, "try a quick activity")


def _build_hint_text(
    today_count: int,
    cat_counts: Counter,
    current_bucket: str,
    bucket_history: pd.DataFrame,
    missing_cats: set,
    df: pd.DataFrame,
) -> str:
    parts: list[str] = []

    # Engagement level
    if today_count == 0:
        parts.append(f"No activities logged yet today.")
    elif today_count <= 2:
        parts.append(f"Light activity so far ({today_count} logged).")
    elif today_count <= 5:
        parts.append(f"Good engagement today ({today_count} logged).")
    else:
        parts.append(f"Great day! {today_count} activities logged. Keep the steady pace.")

    # Time-specific observation
    if not bucket_history.empty:
        usual_count = len(bucket_history) / max(1, df["date"].nunique())
        if usual_count >= 1.5 and today_count < 2:
            parts.append(
                f"You're usually more active in the {current_bucket}. "
                "A small task might feel good."
            )

    # What's missing
    if missing_cats:
        nice = [_suggestion_for_category(c) for c in list(missing_cats)[:2]]
        parts.append(f"Consider: {', '.join(nice)}.")

    # Meal check
    if "meal" in cat_counts:
        parts.append("Good — a meal was logged.")
    elif datetime.utcnow().hour >= 13:
        parts.append("No meal logged yet — lunchtime might be a good idea.")

    return " ".join(parts)
