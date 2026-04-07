"""
Face Similarity Service
────────────────────────
For Memory Book: compare an uploaded face against stored memory entries.

Approach: Uses the `face_recognition` library (dlib-based, CPU-friendly)
to compute 128-d face embeddings, then cosine similarity for matching.

Gracefully degrades: if face_recognition is not installed (it requires
dlib + cmake which can be tricky), falls back to a stub response.
"""
from __future__ import annotations

import io
import logging
import os
import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.models.schemas import FaceSimilarityResponse

logger = logging.getLogger(__name__)

# Embedding store path
EMBEDDINGS_DIR = Path(__file__).parent.parent.parent / "data" / "face_embeddings"

_face_recognition_available = False
try:
    import face_recognition
    _face_recognition_available = True
except ImportError:
    logger.warning("face_recognition not installed. Face similarity will return stub results.")


def _ensure_embeddings_dir():
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


def _embedding_path(user_id: str) -> Path:
    return EMBEDDINGS_DIR / f"{user_id}_embeddings.json"


def _load_embeddings(user_id: str) -> dict[str, list[float]]:
    """Load stored face embeddings for a user's memory book."""
    path = _embedding_path(user_id)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_embeddings(user_id: str, embeddings: dict[str, list[float]]):
    _ensure_embeddings_dir()
    path = _embedding_path(user_id)
    with open(path, "w") as f:
        json.dump(embeddings, f)


def register_face(
    user_id: str,
    name: str,
    image_bytes: bytes,
) -> dict:
    """Register a face embedding for a memory book entry."""
    if not _face_recognition_available:
        return {"registered": False, "reason": "face_recognition not installed"}

    try:
        img = face_recognition.load_image_file(io.BytesIO(image_bytes))
        encodings = face_recognition.face_encodings(img, model="small")

        if not encodings:
            return {"registered": False, "reason": "No face detected in image"}

        embedding = encodings[0].tolist()

        # Store
        store = _load_embeddings(user_id)
        store[name] = embedding
        _save_embeddings(user_id, store)

        return {"registered": True, "name": name, "faces_stored": len(store)}
    except Exception as e:
        logger.error(f"Face registration failed: {e}")
        return {"registered": False, "reason": str(e)}


def find_similar_face(
    user_id: str,
    image_bytes: bytes,
    threshold: float = 0.6,
) -> FaceSimilarityResponse:
    """Compare an uploaded face against stored memory book embeddings."""

    if not _face_recognition_available:
        return FaceSimilarityResponse(
            match_found=False,
            matched_name="",
            confidence=0.0,
            all_scores={},
        )

    try:
        img = face_recognition.load_image_file(io.BytesIO(image_bytes))
        encodings = face_recognition.face_encodings(img, model="small")

        if not encodings:
            return FaceSimilarityResponse(
                match_found=False,
                matched_name="",
                confidence=0.0,
                all_scores={},
            )

        query_enc = encodings[0]
        store = _load_embeddings(user_id)

        if not store:
            return FaceSimilarityResponse(
                match_found=False,
                matched_name="",
                confidence=0.0,
                all_scores={},
            )

        # Compare against all stored faces
        scores: dict[str, float] = {}
        for name, stored_enc in store.items():
            stored_arr = np.array(stored_enc)
            # face_recognition uses Euclidean distance; convert to similarity
            distance = float(np.linalg.norm(query_enc - stored_arr))
            similarity = max(0.0, 1.0 - distance)  # rough conversion
            scores[name] = round(similarity, 3)

        # Find best match
        best_name = max(scores, key=scores.get)
        best_score = scores[best_name]

        return FaceSimilarityResponse(
            match_found=best_score >= threshold,
            matched_name=best_name if best_score >= threshold else "",
            confidence=best_score,
            all_scores=scores,
        )

    except Exception as e:
        logger.error(f"Face similarity failed: {e}")
        return FaceSimilarityResponse(
            match_found=False,
            matched_name="",
            confidence=0.0,
            all_scores={},
        )
