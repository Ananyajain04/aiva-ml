"""
Sensor Rhythm Service
──────────────────────
Analyses sensor-type logs to learn daily rhythm patterns.

Approach:
  - Groups sensor logs by hour-of-day
  - Detects wake/sleep boundaries from activity onset/offset
  - Identifies active rooms from metadata
  - Computes a rhythm consistency score using coefficient of variation
  - Flags anomalies (unusual rooms, unusual times)
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.models.schemas import (
    AdaptiveRemindersResponse,
    LogEntry,
    ReminderSlot,
    SensorRhythmResponse,
)

logger = logging.getLogger(__name__)

MEAL_KEYWORDS = {"ate", "breakfast", "lunch", "dinner", "snack", "meal", "eat", "food"}
MED_KEYWORDS = {"medicine", "medication", "took_medication", "pill", "drug", "med"}


def analyse_sensor_rhythm(logs: list[LogEntry]) -> SensorRhythmResponse:
    """Analyse sensor logs to learn daily rhythm patterns."""

    sensor_logs = [l for l in logs if l.source == "sensor" and l.createdAt]
    all_logs = [l for l in logs if l.createdAt]

    if not all_logs:
        return SensorRhythmResponse(
            predicted_wake_time="",
            predicted_sleep_time="",
            active_rooms=[],
            rhythm_score=0.0,
            anomalies=["No data available for rhythm analysis"],
        )

    # Use all logs for rhythm, sensor logs for room tracking
    rows = []
    for log in all_logs:
        room = ""
        if log.metadata and isinstance(log.metadata, dict):
            room = str(log.metadata.get("room", ""))
        rows.append({
            "hour": log.createdAt.hour,
            "date": log.createdAt.date(),
            "is_sensor": log.source == "sensor",
            "room": room,
            "activity": log.activity,
        })

    df = pd.DataFrame(rows)

    # ── Wake / Sleep prediction ──────────────────────────────────────
    # Wake = median of earliest activity each day
    # Sleep = median of latest activity each day
    daily_bounds = []
    for date, group in df.groupby("date"):
        hours = group["hour"].values
        daily_bounds.append({
            "date": date,
            "first": int(hours.min()),
            "last": int(hours.max()),
        })

    if daily_bounds:
        firsts = [d["first"] for d in daily_bounds]
        lasts = [d["last"] for d in daily_bounds]
        wake_hour = int(np.median(firsts))
        sleep_hour = int(np.median(lasts))

        from datetime import time
        wake_time = time(wake_hour, 0).strftime("%-I:%M %p")
        sleep_time = time(min(23, sleep_hour + 1), 0).strftime("%-I:%M %p")
    else:
        wake_time = ""
        sleep_time = ""

    # ── Active rooms ─────────────────────────────────────────────────
    rooms = [r["room"] for r in rows if r["room"]]
    room_counts = Counter(rooms)
    active_rooms = [room for room, _ in room_counts.most_common(5)]

    # ── Rhythm consistency score ─────────────────────────────────────
    # How consistent is the daily activity pattern?
    daily_counts = df.groupby("date").size()
    if len(daily_counts) >= 3:
        cv = daily_counts.std() / max(daily_counts.mean(), 1)
        rhythm_score = round(max(0.0, 1.0 - cv), 2)
    else:
        rhythm_score = 0.0

    # ── Anomalies ────────────────────────────────────────────────────
    anomalies: list[str] = []

    # Night activity
    night_logs = df[(df["hour"] >= 23) | (df["hour"] < 5)]
    if len(night_logs) > 3:
        anomalies.append(f"{len(night_logs)} activities between 11 PM and 5 AM")

    # Unusual rooms at unusual times
    if rooms:
        night_rooms = night_logs[night_logs["room"] != ""]["room"].tolist()
        unusual_night_rooms = set(night_rooms) - {"bedroom"}
        if unusual_night_rooms:
            anomalies.append(f"Night-time activity in: {', '.join(unusual_night_rooms)}")

    return SensorRhythmResponse(
        predicted_wake_time=wake_time,
        predicted_sleep_time=sleep_time,
        active_rooms=active_rooms,
        rhythm_score=rhythm_score,
        anomalies=anomalies,
    )


def compute_adaptive_reminders(logs: list[LogEntry]) -> AdaptiveRemindersResponse:
    """Generate adaptive reminder times based on actual patient rhythm."""

    if not logs:
        # Fallback to static defaults
        return AdaptiveRemindersResponse(
            reminders=[
                ReminderSlot(label="Morning medicine", time="8:00 AM", learned=False),
                ReminderSlot(label="Lunch", time="1:15 PM", learned=False),
                ReminderSlot(label="Afternoon activity", time="3:30 PM", learned=False),
            ]
        )

    rows = []
    for log in logs:
        if log.createdAt:
            a = log.activity.lower().replace("_", " ")
            rows.append({
                "activity": log.activity,
                "hour": log.createdAt.hour,
                "minute": log.createdAt.minute,
                "frac_hour": log.createdAt.hour + log.createdAt.minute / 60.0,
                "date": log.createdAt.date(),
                "is_med": any(kw in a for kw in MED_KEYWORDS),
                "is_meal": any(kw in a for kw in MEAL_KEYWORDS),
            })

    if not rows:
        return AdaptiveRemindersResponse(
            reminders=[
                ReminderSlot(label="Morning medicine", time="8:00 AM", learned=False),
                ReminderSlot(label="Lunch", time="1:15 PM", learned=False),
                ReminderSlot(label="Afternoon activity", time="3:30 PM", learned=False),
            ]
        )

    df = pd.DataFrame(rows)
    reminders: list[ReminderSlot] = []

    # ── Morning medication time ──────────────────────────────────────
    morning_meds = df[(df["is_med"]) & (df["hour"] >= 5) & (df["hour"] < 12)]
    if len(morning_meds) >= 2:
        med_time = _median_time(morning_meds["frac_hour"])
        reminders.append(ReminderSlot(label="Morning medicine", time=med_time, learned=True))
    else:
        reminders.append(ReminderSlot(label="Morning medicine", time="8:00 AM", learned=False))

    # ── Lunch time ───────────────────────────────────────────────────
    lunch_meals = df[(df["is_meal"]) & (df["hour"] >= 10) & (df["hour"] <= 15)]
    if len(lunch_meals) >= 2:
        lunch_time = _median_time(lunch_meals["frac_hour"])
        reminders.append(ReminderSlot(label="Lunch", time=lunch_time, learned=True))
    else:
        reminders.append(ReminderSlot(label="Lunch", time="1:15 PM", learned=False))

    # ── Afternoon activity ───────────────────────────────────────────
    afternoon = df[(df["hour"] >= 13) & (df["hour"] < 18) & (~df["is_med"]) & (~df["is_meal"])]
    if len(afternoon) >= 3:
        act_time = _median_time(afternoon["frac_hour"])
        reminders.append(ReminderSlot(label="Afternoon activity", time=act_time, learned=True))
    else:
        reminders.append(ReminderSlot(label="Afternoon activity", time="3:30 PM", learned=False))

    # ── Evening medication (if pattern exists) ───────────────────────
    evening_meds = df[(df["is_med"]) & (df["hour"] >= 17) & (df["hour"] < 22)]
    if len(evening_meds) >= 2:
        eve_time = _median_time(evening_meds["frac_hour"])
        reminders.append(ReminderSlot(label="Evening medicine", time=eve_time, learned=True))

    return AdaptiveRemindersResponse(reminders=reminders)


def _median_time(frac_hours: pd.Series) -> str:
    """Convert fractional hour series to median formatted time string."""
    from datetime import time

    median = float(frac_hours.median())
    h = int(median)
    m = int((median - h) * 60)
    m = 5 * round(m / 5)  # round to 5 min
    if m == 60:
        h += 1
        m = 0
    return time(h % 24, m).strftime("%-I:%M %p")
