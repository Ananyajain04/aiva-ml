"""
Lunch Time Prediction Service
──────────────────────────────
Replaces StaticInsights.predictedLunchTime()

Approach: Look at historical meal-type logs around midday (10am-3pm),
compute the median time, and use exponential moving average to weight
recent days more. Falls back to 1:15 PM if insufficient data.
"""
from __future__ import annotations

import logging
from datetime import datetime, time

import numpy as np
import pandas as pd

from app.models.schemas import LogEntry, PredictedLunchResponse

logger = logging.getLogger(__name__)

MEAL_KEYWORDS = {"ate", "breakfast", "lunch", "dinner", "snack", "meal", "eat", "food"}
DEFAULT_LUNCH = "1:15 PM"


def _is_lunch_candidate(log: LogEntry) -> bool:
    """Check if this log is a meal-like event in the lunch window (10am-3pm)."""
    if not log.createdAt:
        return False
    hour = log.createdAt.hour
    if hour < 10 or hour > 15:
        return False
    activity = log.activity.lower().replace("_", " ")
    return any(kw in activity for kw in MEAL_KEYWORDS)


def predict_lunch_time(logs: list[LogEntry]) -> PredictedLunchResponse:
    """Predict lunch time from historical meal logs."""

    lunch_logs = [log for log in logs if _is_lunch_candidate(log)]

    if len(lunch_logs) < 2:
        return PredictedLunchResponse(
            predicted_time=DEFAULT_LUNCH,
            confidence=0.0,
            based_on_days=0,
        )

    # Extract hour + minute as fractional hours
    times: list[float] = []
    dates_seen: set = set()
    for log in lunch_logs:
        t = log.createdAt
        times.append(t.hour + t.minute / 60.0)
        dates_seen.add(t.date())

    times_arr = np.array(times)

    # Exponential weighting: more recent logs matter more
    n = len(times_arr)
    weights = np.exp(np.linspace(-1, 0, n))  # oldest=-1, newest=0
    weighted_mean = np.average(times_arr, weights=weights)

    # Convert back to time
    pred_hour = int(weighted_mean)
    pred_minute = int((weighted_mean - pred_hour) * 60)

    # Round to nearest 5 minutes for readability
    pred_minute = 5 * round(pred_minute / 5)
    if pred_minute == 60:
        pred_hour += 1
        pred_minute = 0

    pred_time = time(pred_hour % 24, pred_minute)

    # Format as "1:15 PM"
    formatted = pred_time.strftime("%-I:%M %p")

    # Confidence based on data quantity and consistency
    std = float(np.std(times_arr))
    data_conf = min(1.0, len(dates_seen) / 7.0)
    consistency_conf = max(0.0, 1.0 - std / 3.0)  # std of 3+ hours = 0 confidence
    confidence = round(data_conf * consistency_conf, 2)

    return PredictedLunchResponse(
        predicted_time=formatted,
        confidence=confidence,
        based_on_days=len(dates_seen),
    )
