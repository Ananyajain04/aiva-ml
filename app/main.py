"""
Avia ML Service — FastAPI Application
──────────────────────────────────────
Lightweight ML micro-service that powers the Avia iOS app's
intelligent features. Runs on CPU, no GPU needed.

Start: uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.schemas import HealthResponse
from app.routers.insights import router as insights_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-20s %(levelname)-7s %(message)s",
)
logger = logging.getLogger("avia-ml")

settings = get_settings()

app = FastAPI(
    title="Avia ML Service",
    description=(
        "Lightweight ML layer for the Avia dementia-care iOS app. "
        "Provides personalised insights, behaviour analysis, document "
        "summarisation, face matching, and rhythm learning — all on CPU."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the iOS app and any local/dev frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(insights_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check."""
    services = {
        "insights": "ok",
        "lunch_prediction": "ok",
        "behaviour_flags": "ok",
        "report_summary": "ok",
        "sensor_rhythm": "ok",
    }

    # Check optional services
    try:
        import face_recognition
        services["face_similarity"] = "ok"
    except ImportError:
        services["face_similarity"] = "unavailable (install face_recognition)"

    try:
        import spacy
        spacy.load("en_core_web_sm")
        services["spacy_ner"] = "ok"
    except Exception:
        services["spacy_ner"] = "unavailable (install en_core_web_sm)"

    return HealthResponse(
        status="ok",
        version="0.1.0",
        services=services,
    )


@app.on_event("startup")
async def startup():
    logger.info("Avia ML Service starting on %s:%s", settings.ml_service_host, settings.ml_service_port)
    logger.info("Backend URL: %s", settings.avia_backend_url)
