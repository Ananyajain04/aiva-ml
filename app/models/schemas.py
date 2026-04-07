"""
Avia ML Service — Pydantic models for request/response schemas.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime


# ── Shared log model (mirrors backend ActivityLogEntry) ──────────────
class LogEntry(BaseModel):
    id: str = Field(alias="_id", default="")
    userId: str = ""
    activity: str = ""
    source: str = "app"
    type: str = "activity"
    metadata: dict | None = None
    createdAt: datetime | None = None

    class Config:
        populate_by_name = True


# ── 1. Routine Hint ──────────────────────────────────────────────────
class RoutineHintRequest(BaseModel):
    user_id: str
    logs: list[LogEntry] = []


class RoutineHintResponse(BaseModel):
    hint: str
    confidence: float = 0.0
    suggested_activities: list[str] = []


# ── 2. Predicted Lunch Time ──────────────────────────────────────────
class PredictedLunchRequest(BaseModel):
    user_id: str
    logs: list[LogEntry] = []


class PredictedLunchResponse(BaseModel):
    predicted_time: str  # "1:15 PM"
    confidence: float = 0.0
    based_on_days: int = 0


# ── 3. Caregiver Weekly Summary ──────────────────────────────────────
class WeeklySummaryRequest(BaseModel):
    user_id: str
    logs: list[LogEntry] = []
    medications: list[dict] = []


class WeeklySummaryResponse(BaseModel):
    narrative: str
    total_logs: int = 0
    medication_adherence: float = 0.0
    activity_trend: str = "stable"
    highlights: list[str] = []


# ── 4. Behaviour Flags ──────────────────────────────────────────────
class BehaviourFlagsRequest(BaseModel):
    user_id: str
    logs: list[LogEntry] = []


class BehaviourFlag(BaseModel):
    flag: str
    severity: str = "info"  # info | warning | alert
    detail: str = ""


class BehaviourFlagsResponse(BaseModel):
    flags: list[BehaviourFlag] = []


# ── 5. Report Summary ───────────────────────────────────────────────
class ReportSummaryRequest(BaseModel):
    file_url: str = ""
    text_content: str = ""  # raw text fallback


class ReportSummaryResponse(BaseModel):
    summary: str
    medications_found: list[str] = []
    dates_found: list[str] = []
    instructions: list[str] = []


# ── 6. Face Similarity ──────────────────────────────────────────────
class FaceSimilarityResponse(BaseModel):
    match_found: bool = False
    matched_name: str = ""
    confidence: float = 0.0
    all_scores: dict[str, float] = {}


# ── 7. Sensor Rhythm ────────────────────────────────────────────────
class SensorRhythmRequest(BaseModel):
    user_id: str
    logs: list[LogEntry] = []


class SensorRhythmResponse(BaseModel):
    predicted_wake_time: str = ""
    predicted_sleep_time: str = ""
    active_rooms: list[str] = []
    rhythm_score: float = 0.0  # 0-1, how consistent
    anomalies: list[str] = []


# ── Adaptive Reminders ──────────────────────────────────────────────
class AdaptiveRemindersRequest(BaseModel):
    user_id: str
    logs: list[LogEntry] = []


class ReminderSlot(BaseModel):
    label: str
    time: str
    learned: bool = False


class AdaptiveRemindersResponse(BaseModel):
    reminders: list[ReminderSlot] = []


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    services: dict[str, str] = {}


# ── Daily Quiz ───────────────────────────────────────────────────────
class QuizRequest(BaseModel):
    user_id: str


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: list[str]
    correct_option_index: int


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]

