"""
Medical Report Summary Service
───────────────────────────────
Replaces StaticInsights.reportSummaryPlaceholder()

Approach:
  1. Accept PDF/DOCX file upload or raw text
  2. Extract text from document
  3. Use regex + spaCy NLP to find:
     - Medication names (NER + pharmaceutical patterns)
     - Dates
     - Dosage instructions
     - Key medical terms
  4. Generate a structured summary

Lightweight: no LLM needed. Uses spaCy's en_core_web_sm for NER
and regex patterns for medical document parsing.
"""
from __future__ import annotations

import io
import logging
import re
from datetime import datetime
from typing import Any

import httpx

from app.config import get_settings
from app.models.schemas import ReportSummaryResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Patterns for medical documents ───────────────────────────────────
DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
]

DOSAGE_PATTERN = r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|units?|tabs?|capsules?|tablets?|drops?|puffs?)\b"

INSTRUCTION_KEYWORDS = [
    "take", "administer", "apply", "inject", "inhale",
    "once daily", "twice daily", "three times", "every",
    "before meals", "after meals", "at bedtime", "with food",
    "as needed", "PRN", "morning", "evening",
]

# Common medication suffixes/patterns
MED_SUFFIXES = [
    "ol", "il", "in", "an", "ine", "ide", "ate", "one", "ase",
    "pril", "artan", "statin", "prazole", "mab", "nib",
    "olol", "dipine", "azepam", "etine", "amine",
]

COMMON_MEDS = {
    "acetaminophen", "ibuprofen", "aspirin", "metformin", "lisinopril",
    "amlodipine", "metoprolol", "omeprazole", "losartan", "atorvastatin",
    "levothyroxine", "gabapentin", "sertraline", "hydrochlorothiazide",
    "furosemide", "prednisone", "amoxicillin", "azithromycin",
    "donepezil", "memantine", "rivastigmine", "galantamine",  # dementia-specific
    "quetiapine", "risperidone", "haloperidol", "lorazepam",
    "melatonin", "trazodone", "mirtazapine", "citalopram",
    "warfarin", "apixaban", "rivaroxaban",
    "insulin", "methotrexate", "albuterol",
}


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"PDF extraction failed: {e}")
        return ""


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.warning(f"DOCX extraction failed: {e}")
        return ""


def _find_dates(text: str) -> list[str]:
    """Find all date mentions in text."""
    dates = set()
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            dates.add(match.group())
    return sorted(dates)[:10]  # cap at 10


def _find_medications(text: str) -> list[str]:
    """Find medication names using pattern matching and common drug list."""
    found = set()

    # Check against known medications
    text_lower = text.lower()
    for med in COMMON_MEDS:
        if med in text_lower:
            found.add(med.title())

    # Find capitalized words near dosage patterns
    dosage_matches = list(re.finditer(DOSAGE_PATTERN, text, re.IGNORECASE))
    for m in dosage_matches:
        # Look for the word before the dosage
        start = max(0, m.start() - 50)
        context = text[start:m.start()]
        words = re.findall(r"\b[A-Z][a-z]{3,}\b", context)
        for w in words:
            if w.lower() not in {"take", "give", "once", "twice", "daily", "after", "before", "with"}:
                found.add(w)

    # Try spaCy NER if available
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text[:5000])  # limit for performance
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT"):
                    # Pharmaceutical names often get tagged as ORG/PRODUCT
                    name = ent.text.strip()
                    if 3 < len(name) < 30 and name.lower() in text_lower:
                        found.add(name)
        except OSError:
            pass  # model not installed — fine, use regex only
    except ImportError:
        pass

    return sorted(found)[:15]


def _find_instructions(text: str) -> list[str]:
    """Extract dosage instructions and directives."""
    instructions = []
    sentences = re.split(r"[.!?\n]", text)

    for sentence in sentences:
        s = sentence.strip()
        if len(s) < 10 or len(s) > 200:
            continue
        s_lower = s.lower()
        if any(kw in s_lower for kw in INSTRUCTION_KEYWORDS):
            # Likely an instruction
            instructions.append(s)

    return instructions[:10]  # cap at 10


def _generate_summary(
    text: str,
    medications: list[str],
    dates: list[str],
    instructions: list[str],
) -> str:
    """Generate a human-readable summary from extracted information."""
    parts: list[str] = []

    # Document size info
    word_count = len(text.split())
    parts.append(f"Document contains approximately {word_count} words.")

    # Medications
    if medications:
        med_list = ", ".join(medications[:5])
        parts.append(f"Medications identified: {med_list}.")
        if len(medications) > 5:
            parts.append(f"({len(medications)} total medications found.)")
    else:
        parts.append("No specific medications identified in the document.")

    # Dates
    if dates:
        parts.append(f"Key dates: {', '.join(dates[:3])}.")

    # Instructions
    if instructions:
        parts.append(f"Found {len(instructions)} dosage/care instructions.")
        # Include the first instruction as example
        parts.append(f"Example: \"{instructions[0]}\"")

    # Dementia-specific keywords check
    dementia_terms = ["dementia", "alzheimer", "cognitive", "memory loss", "confusion",
                      "sundowning", "wandering", "agitation"]
    found_terms = [t for t in dementia_terms if t in text.lower()]
    if found_terms:
        parts.append(f"Relevant terms: {', '.join(found_terms)}.")

    return " ".join(parts)


def _hf_generate_summary(text: str) -> str | None:
    """Use Hugging Face Inference API for a concise medical summary."""
    if not settings.huggingface_api_token:
        return None

    model = settings.huggingface_summary_model
    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_token}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "inputs": text[:4500],
        "parameters": {
            "max_length": 220,
            "min_length": 70,
            "do_sample": False,
        },
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.warning("HF summarization failed (%s): %s", resp.status_code, resp.text[:300])
            return None

        data = resp.json()
        if isinstance(data, list) and data and isinstance(data[0], dict):
            summary = data[0].get("summary_text")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()

        if isinstance(data, dict):
            # Some models may return generated_text
            summary = data.get("generated_text")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
    except Exception as exc:
        logger.warning("HF summarization unavailable: %s", exc)

    return None


def summarise_report(
    text_content: str = "",
    file_bytes: bytes | None = None,
    filename: str = "",
) -> ReportSummaryResponse:
    """Summarise a medical report from text or file upload."""

    # Extract text from file if provided
    if file_bytes and not text_content:
        if filename.lower().endswith(".pdf"):
            text_content = _extract_text_from_pdf(file_bytes)
        elif filename.lower().endswith((".docx", ".doc")):
            text_content = _extract_text_from_docx(file_bytes)
        else:
            # Try as plain text
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = file_bytes.decode("latin-1", errors="ignore")

    if not text_content or len(text_content.strip()) < 20:
        return ReportSummaryResponse(
            summary="Document is empty or too short to summarise. Please upload a medical report (PDF, DOCX, or text).",
            medications_found=[],
            dates_found=[],
            instructions=[],
        )

    # Extract structured info
    medications = _find_medications(text_content)
    dates = _find_dates(text_content)
    instructions = _find_instructions(text_content)

    # Generate summary (HF first, deterministic fallback otherwise)
    summary = _hf_generate_summary(text_content)
    if not summary:
        summary = _generate_summary(text_content, medications, dates, instructions)

    return ReportSummaryResponse(
        summary=summary,
        medications_found=medications,
        dates_found=dates,
        instructions=instructions,
    )
