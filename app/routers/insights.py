"""
Avia ML API — Router: Insights
───────────────────────────────
All ML endpoints that the iOS app and caregiver dashboard consume.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, UploadFile

from app.models.schemas import (
    AdaptiveRemindersRequest,
    AdaptiveRemindersResponse,
    BehaviourFlagsRequest,
    BehaviourFlagsResponse,
    FaceSimilarityResponse,
    PredictedLunchRequest,
    PredictedLunchResponse,
    ReportSummaryRequest,
    ReportSummaryResponse,
    RoutineHintRequest,
    RoutineHintResponse,
    SensorRhythmRequest,
    SensorRhythmResponse,
    WeeklySummaryRequest,
    WeeklySummaryResponse,
    QuizRequest,
    QuizResponse,
)
from app.services.behaviour_service import detect_behaviour_flags
from app.services.face_service import find_similar_face, register_face
from app.services.lunch_service import predict_lunch_time
from app.services.report_service import summarise_report
from app.services.routine_service import compute_routine_hint
from app.services.sensor_service import analyse_sensor_rhythm, compute_adaptive_reminders
from app.services.summary_service import compute_weekly_summary
from app.services.quiz_service import generate_daily_quiz

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ML Insights"])


# ── 1. Routine Hint ─────────────────────────────────────────────────
@router.post("/routine-hint", response_model=RoutineHintResponse)
async def routine_hint(req: RoutineHintRequest):
    """Personalised routine guidance based on patient's activity logs."""
    return compute_routine_hint(req.logs)


# ── 2. Predicted Lunch Time ─────────────────────────────────────────
@router.post("/predicted-lunch", response_model=PredictedLunchResponse)
async def predicted_lunch(req: PredictedLunchRequest):
    """Predict likely lunch time from historical meal logs."""
    return predict_lunch_time(req.logs)


# ── 3. Caregiver Weekly Summary ─────────────────────────────────────
@router.post("/weekly-summary", response_model=WeeklySummaryResponse)
async def weekly_summary(req: WeeklySummaryRequest):
    """Data-driven weekly narrative for caregivers."""
    return compute_weekly_summary(req.logs, req.medications)


# ── 4. Behaviour Flags ──────────────────────────────────────────────
@router.post("/behaviour-flags", response_model=BehaviourFlagsResponse)
async def behaviour_flags(req: BehaviourFlagsRequest):
    """Detect anomalies and concerning patterns from activity logs."""
    return detect_behaviour_flags(req.logs)


# ── 5. Report Summary ───────────────────────────────────────────────
@router.post("/report-summary", response_model=ReportSummaryResponse)
async def report_summary_json(req: ReportSummaryRequest):
    """Summarise a medical report from text content or URL."""
    return summarise_report(text_content=req.text_content)


@router.post("/report-summary/upload", response_model=ReportSummaryResponse)
async def report_summary_upload(file: UploadFile = File(...)):
    """Upload a PDF/DOCX medical report and get a structured summary."""
    content = await file.read()
    return summarise_report(
        file_bytes=content,
        filename=file.filename or "",
    )


# ── 6. Face Similarity ──────────────────────────────────────────────
@router.post("/face/register")
async def face_register(
    user_id: str = Form(...),
    name: str = Form(...),
    image: UploadFile = File(...),
):
    """Register a face embedding for a memory book entry."""
    image_bytes = await image.read()
    return register_face(user_id, name, image_bytes)


@router.post("/face/match", response_model=FaceSimilarityResponse)
async def face_match(
    user_id: str = Form(...),
    image: UploadFile = File(...),
):
    """Match an uploaded face against stored memory book entries."""
    image_bytes = await image.read()
    return find_similar_face(user_id, image_bytes)


# ── 7. Sensor Rhythm ────────────────────────────────────────────────
@router.post("/sensor-rhythm", response_model=SensorRhythmResponse)
async def sensor_rhythm(req: SensorRhythmRequest):
    """Analyse sensor and activity logs to learn daily rhythm patterns."""
    return analyse_sensor_rhythm(req.logs)


# ── 8. Adaptive Reminders ───────────────────────────────────────────
@router.post("/adaptive-reminders", response_model=AdaptiveRemindersResponse)
async def adaptive_reminders(req: AdaptiveRemindersRequest):
    """Generate personalised reminder times based on patient's actual rhythm."""
    return compute_adaptive_reminders(req.logs)


# ── 9. Daily Quiz ───────────────────────────────────────────────────
@router.post("/daily-quiz", response_model=QuizResponse)
async def daily_quiz(req: QuizRequest):
    """Generate custom daily quiz questions."""
    return generate_daily_quiz(req.user_id)
