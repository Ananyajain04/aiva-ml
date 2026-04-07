"""
Avia — Production-Ready Demo Data Population
─────────────────────────────────────────────
Seeds the backend with realistic patient/caregiver data including:
  - Activity logs spread across the last 7 days (varied timestamps)
  - Medications for every patient
  - Guided activities for every patient
  - Medical reports for every patient
  - Patient-caregiver linking
  - Behaviour, medication, sensor and quiz logs
"""
from __future__ import annotations

import os
import random
import time
from datetime import datetime, timedelta
from typing import Any

import httpx

BASE_URL = os.getenv("AVIA_BACKEND_URL", "https://aiva-backend-tnp0.onrender.com").rstrip("/")

USERS = [
    {"name": "Ravi Prakash", "email": "ravi@aiva.com", "password": "ravi1234", "role": "patient"},
    {"name": "Lakshmi Nair", "email": "lakshmi@aiva.com", "password": "lakshmi1234", "role": "patient"},
    {"name": "Meera Iyer", "email": "meera@aiva.com", "password": "meera1234", "role": "caregiver"},
    {"name": "Ganesh Rao", "email": "ganesh@aiva.com", "password": "ganesh1234", "role": "patient"},
]

# ── Realistic Activity Logs ─────────────────────────────────────────
# Each patient gets a unique but realistic pattern of daily life

RAVI_DAILY_LOGS = [
    # Morning routine
    ("Woke up and had morning tea", "activity", "app", {"meal": "tea", "time_of_day": "morning"}),
    ("Completed morning breathing exercise", "activity", "app", {"duration_min": 15, "exercise_type": "pranayama"}),
    ("Ate idli and sambar for breakfast", "activity", "app", {"meal": "breakfast", "food": "idli sambar"}),
    ("Took Donepezil after breakfast", "medication", "app", {"medicine": "Donepezil", "dosage": "5mg", "adherence": "on_time"}),
    # Midday
    ("Watered the tulsi plant in the balcony", "activity", "app", {"task": "gardening", "duration_min": 10}),
    ("Read newspaper headlines with magnifying glass", "activity", "app", {"task": "reading", "duration_min": 20}),
    ("Had rice and dal for lunch", "activity", "app", {"meal": "lunch", "food": "rice dal"}),
    ("Took afternoon rest", "behaviour", "app", {"duration_min": 45, "mood": "calm"}),
    # Afternoon
    ("Short walk around the housing society", "activity", "app", {"steps": 2400, "duration_min": 25}),
    ("Spoke with daughter on video call", "behaviour", "app", {"mood": "happy", "contact": "family"}),
    ("Had evening snack with biscuits and chai", "activity", "app", {"meal": "snack", "food": "biscuits chai"}),
    ("Took evening Melatonin", "medication", "app", {"medicine": "Melatonin", "dosage": "3mg", "adherence": "on_time"}),
    # Evening
    ("Watched old family photos on tablet", "behaviour", "app", {"mood": "nostalgic", "activity": "reminiscence"}),
    ("Had dinner — roti and vegetable curry", "activity", "app", {"meal": "dinner", "food": "roti sabzi"}),
    ("Completed evening hydration goal", "activity", "app", {"water_ml": 1800}),
]

RAVI_EXTRA_LOGS = [
    ("Completed Daily Quiz", "quiz", "app", {"score": 3, "total": 3, "percentage": 100}),
    ("Completed Daily Quiz", "quiz", "app", {"score": 2, "total": 3, "percentage": 67}),
    ("Completed Daily Quiz", "quiz", "app", {"score": 3, "total": 3, "percentage": 100}),
    ("Listened to old Hindi film songs", "behaviour", "app", {"mood": "positive", "duration_min": 30}),
    ("Sorted laundry with caregiver assistance", "activity", "app", {"task": "household", "assistance": True}),
    ("Completed Make Tea guided activity", "activity", "app", {"activityName": "Make Tea", "stepsTotal": 4, "skipped": False, "secondsElapsed": 340}),
    ("Mild confusion about day of the week", "behaviour", "caregiver", {"observation": "temporal_disorientation", "severity": "mild"}),
    ("Bathroom visit pattern normal", "sensor", "sensor", {"room": "bathroom", "visits": 6}),
    ("Living room motion detected", "sensor", "sensor", {"room": "living_room", "active_hours": 8}),
    ("Kitchen activity detected", "sensor", "sensor", {"room": "kitchen", "active_hours": 3}),
    ("Bedroom motion — sleep pattern", "sensor", "sensor", {"room": "bedroom", "sleep_hours": 7.5}),
]

LAKSHMI_DAILY_LOGS = [
    # Morning
    ("Morning prayer and meditation", "activity", "app", {"duration_min": 20, "task": "meditation"}),
    ("Had dosa and chutney for breakfast", "activity", "app", {"meal": "breakfast", "food": "dosa chutney"}),
    ("Took morning Memantine", "medication", "app", {"medicine": "Memantine", "dosage": "10mg", "adherence": "on_time"}),
    ("Arranged flowers at the home temple", "activity", "app", {"task": "puja", "duration_min": 15}),
    # Midday
    ("Helped fold clothes with support", "activity", "app", {"task": "household", "assistance": True}),
    ("Had sambar rice for lunch", "activity", "app", {"meal": "lunch", "food": "sambar rice"}),
    ("Afternoon nap", "behaviour", "app", {"duration_min": 60, "mood": "tired"}),
    ("Took afternoon Vitamin D", "medication", "app", {"medicine": "Vitamin D", "dosage": "1000 IU", "adherence": "on_time"}),
    # Afternoon
    ("Listened to Carnatic music", "behaviour", "app", {"mood": "peaceful", "duration_min": 25}),
    ("Light stretching exercise", "activity", "app", {"exercise_type": "stretching", "duration_min": 10}),
    ("Had coffee and murukku for snack", "activity", "app", {"meal": "snack", "food": "coffee murukku"}),
    # Evening
    ("Evening walk in the garden", "activity", "app", {"steps": 1800, "duration_min": 20}),
    ("Took evening Memantine", "medication", "app", {"medicine": "Memantine", "dosage": "10mg", "adherence": "on_time"}),
    ("Had chapati and palak paneer for dinner", "activity", "app", {"meal": "dinner", "food": "chapati palak paneer"}),
    ("Applied night cream and prepared for bed", "activity", "app", {"task": "bedtime_routine"}),
]

LAKSHMI_EXTRA_LOGS = [
    ("Completed Daily Quiz", "quiz", "app", {"score": 2, "total": 3, "percentage": 67}),
    ("Completed Daily Quiz", "quiz", "app", {"score": 3, "total": 3, "percentage": 100}),
    ("Completed Daily Quiz", "quiz", "app", {"score": 1, "total": 3, "percentage": 33}),
    ("Named three grandchildren correctly during recall", "behaviour", "caregiver", {"observation": "memory_recall", "accuracy": "good"}),
    ("Became slightly agitated in the evening", "behaviour", "caregiver", {"observation": "sundowning", "severity": "mild", "time": "6:30 PM"}),
    ("Completed Afternoon Calm Routine guided activity", "activity", "app", {"activityName": "Afternoon Calm Routine", "stepsTotal": 3, "skipped": False, "secondsElapsed": 420}),
    ("Missed lunch — needed prompting", "behaviour", "caregiver", {"observation": "missed_meal", "meal": "lunch"}),
    ("Bathroom visit pattern normal", "sensor", "sensor", {"room": "bathroom", "visits": 7}),
    ("Living room motion detected", "sensor", "sensor", {"room": "living_room", "active_hours": 7}),
    ("Kitchen activity detected", "sensor", "sensor", {"room": "kitchen", "active_hours": 2}),
    ("Bedroom motion — sleep pattern", "sensor", "sensor", {"room": "bedroom", "sleep_hours": 8}),
]

GANESH_DAILY_LOGS = [
    # Morning
    ("Woke up early, sat on the veranda", "activity", "app", {"time_of_day": "morning", "mood": "calm"}),
    ("Had poha and tea for breakfast", "activity", "app", {"meal": "breakfast", "food": "poha tea"}),
    ("Morning walk around the block", "activity", "app", {"steps": 3200, "duration_min": 30}),
    ("Took Rivastigmine after dinner", "medication", "app", {"medicine": "Rivastigmine", "dosage": "3mg", "adherence": "on_time"}),
    # Midday
    ("Watched cricket highlights on TV", "behaviour", "app", {"mood": "engaged", "duration_min": 45}),
    ("Had thali for lunch", "activity", "app", {"meal": "lunch", "food": "thali"}),
    ("Rested after lunch", "behaviour", "app", {"duration_min": 40, "mood": "relaxed"}),
    # Afternoon
    ("Played cards with neighbor", "activity", "app", {"task": "social_activity", "duration_min": 35}),
    ("Had chai and pakora for snack", "activity", "app", {"meal": "snack", "food": "chai pakora"}),
    ("Helped with light kitchen cleaning", "activity", "app", {"task": "household", "assistance": False}),
    # Evening
    ("Evening temple visit with family", "activity", "app", {"task": "outing", "duration_min": 45}),
    ("Had khichdi for dinner", "activity", "app", {"meal": "dinner", "food": "khichdi"}),
    ("Took evening Vitamin B12", "medication", "app", {"medicine": "Vitamin B12", "dosage": "500mcg", "adherence": "on_time"}),
    ("Completed evening stretching routine", "activity", "app", {"exercise_type": "stretching", "duration_min": 10}),
]

GANESH_EXTRA_LOGS = [
    ("Completed Daily Quiz", "quiz", "app", {"score": 2, "total": 3, "percentage": 67}),
    ("Completed Daily Quiz", "quiz", "app", {"score": 3, "total": 3, "percentage": 100}),
    ("Repeated a question about lunch timing", "behaviour", "caregiver", {"observation": "repetitive_questioning", "severity": "mild"}),
    ("Good recall of old cricket match details", "behaviour", "caregiver", {"observation": "long_term_memory", "accuracy": "good"}),
    ("Bathroom visit pattern normal", "sensor", "sensor", {"room": "bathroom", "visits": 5}),
    ("Living room motion detected", "sensor", "sensor", {"room": "living_room", "active_hours": 9}),
    ("Kitchen activity detected", "sensor", "sensor", {"room": "kitchen", "active_hours": 2}),
    ("Bedroom motion — sleep pattern", "sensor", "sensor", {"room": "bedroom", "sleep_hours": 7}),
]

# ── Medications ──────────────────────────────────────────────────────

RAVI_MEDICATIONS = [
    {"medicineName": "Donepezil", "dosage": "5 mg", "timing": "8:00 AM — after breakfast"},
    {"medicineName": "Melatonin", "dosage": "3 mg", "timing": "9:30 PM — before bed"},
    {"medicineName": "Aspirin", "dosage": "75 mg", "timing": "8:00 AM — with breakfast"},
    {"medicineName": "Vitamin E", "dosage": "400 IU", "timing": "1:00 PM — after lunch"},
]

LAKSHMI_MEDICATIONS = [
    {"medicineName": "Memantine", "dosage": "10 mg", "timing": "8:30 AM — morning"},
    {"medicineName": "Memantine", "dosage": "10 mg", "timing": "8:30 PM — evening"},
    {"medicineName": "Vitamin D3", "dosage": "1000 IU", "timing": "1:00 PM — after lunch"},
    {"medicineName": "Calcium", "dosage": "500 mg", "timing": "8:30 PM — with dinner"},
    {"medicineName": "Omega-3 Fish Oil", "dosage": "1000 mg", "timing": "8:30 AM — morning"},
]

GANESH_MEDICATIONS = [
    {"medicineName": "Rivastigmine", "dosage": "3 mg", "timing": "8:00 PM — after dinner"},
    {"medicineName": "Vitamin B12", "dosage": "500 mcg", "timing": "8:00 PM — evening"},
    {"medicineName": "Amlodipine", "dosage": "5 mg", "timing": "7:30 AM — morning"},
    {"medicineName": "Metformin", "dosage": "500 mg", "timing": "1:00 PM — after lunch"},
]

# ── Guided Activities ────────────────────────────────────────────────

RAVI_ACTIVITIES = [
    {
        "name": "Make Tea",
        "steps": [
            {"stepNumber": 1, "instruction": "Fill the kettle with water and place it on the stove"},
            {"stepNumber": 2, "instruction": "Wait for the water to boil — you will hear it bubbling"},
            {"stepNumber": 3, "instruction": "Add one spoon of tea powder and a pinch of ginger"},
            {"stepNumber": 4, "instruction": "Add milk and let it simmer for 2 minutes"},
            {"stepNumber": 5, "instruction": "Strain into your favourite cup and add sugar if you like"},
        ],
    },
    {
        "name": "Morning Orientation Routine",
        "steps": [
            {"stepNumber": 1, "instruction": "Open the curtains and let natural light in"},
            {"stepNumber": 2, "instruction": "Look at the calendar card — read today's date and day aloud"},
            {"stepNumber": 3, "instruction": "Check the weather outside your window"},
            {"stepNumber": 4, "instruction": "Do 5 minutes of gentle arm and neck stretching"},
            {"stepNumber": 5, "instruction": "Have a glass of warm water before breakfast"},
        ],
    },
    {
        "name": "Watering the Plants",
        "steps": [
            {"stepNumber": 1, "instruction": "Pick up the green watering can from the balcony corner"},
            {"stepNumber": 2, "instruction": "Fill it halfway with tap water"},
            {"stepNumber": 3, "instruction": "Water the tulsi plant first — just enough to wet the soil"},
            {"stepNumber": 4, "instruction": "Water the other pots, moving left to right"},
            {"stepNumber": 5, "instruction": "Place the watering can back in its spot"},
        ],
    },
    {
        "name": "Evening Wind-Down",
        "steps": [
            {"stepNumber": 1, "instruction": "Turn off the television and reduce bright lights"},
            {"stepNumber": 2, "instruction": "Sit in your favourite chair and take 5 slow breaths"},
            {"stepNumber": 3, "instruction": "Listen to one calming song or bhajan"},
            {"stepNumber": 4, "instruction": "Drink a small glass of warm milk"},
            {"stepNumber": 5, "instruction": "Brush your teeth and change into nightclothes"},
        ],
    },
]

LAKSHMI_ACTIVITIES = [
    {
        "name": "Afternoon Calm Routine",
        "steps": [
            {"stepNumber": 1, "instruction": "Drink a glass of room-temperature water"},
            {"stepNumber": 2, "instruction": "Sit comfortably and listen to your favourite devotional music for 15 minutes"},
            {"stepNumber": 3, "instruction": "Take a short indoor walk — from the living room to the kitchen and back, three times"},
        ],
    },
    {
        "name": "Morning Puja Routine",
        "steps": [
            {"stepNumber": 1, "instruction": "Wash your hands and face with warm water"},
            {"stepNumber": 2, "instruction": "Light the lamp at the home temple"},
            {"stepNumber": 3, "instruction": "Arrange fresh flowers near the idols"},
            {"stepNumber": 4, "instruction": "Say your morning prayer or chant"},
            {"stepNumber": 5, "instruction": "Sit quietly for 2 minutes with your eyes closed"},
        ],
    },
    {
        "name": "Folding Clothes",
        "steps": [
            {"stepNumber": 1, "instruction": "Spread the clean clothes on the bed"},
            {"stepNumber": 2, "instruction": "Sort into groups — towels, saris, everyday wear"},
            {"stepNumber": 3, "instruction": "Fold each item neatly — take your time"},
            {"stepNumber": 4, "instruction": "Place folded items in the correct shelf or drawer"},
        ],
    },
    {
        "name": "Prepare a Simple Salad",
        "steps": [
            {"stepNumber": 1, "instruction": "Wash the cucumber and tomato under running water"},
            {"stepNumber": 2, "instruction": "Cut the cucumber into thin round slices"},
            {"stepNumber": 3, "instruction": "Cut the tomato into small pieces"},
            {"stepNumber": 4, "instruction": "Add a pinch of salt, black pepper, and a squeeze of lemon"},
            {"stepNumber": 5, "instruction": "Mix gently and serve in a bowl"},
        ],
    },
]

GANESH_ACTIVITIES = [
    {
        "name": "Morning Walk Preparation",
        "steps": [
            {"stepNumber": 1, "instruction": "Put on your walking shoes — they are near the front door"},
            {"stepNumber": 2, "instruction": "Take your house key and mobile phone"},
            {"stepNumber": 3, "instruction": "Walk along the main road inside the colony — stay on the footpath"},
            {"stepNumber": 4, "instruction": "Complete two rounds of the block at a comfortable pace"},
            {"stepNumber": 5, "instruction": "Return home and drink a glass of water"},
        ],
    },
    {
        "name": "Sorting Old Photographs",
        "steps": [
            {"stepNumber": 1, "instruction": "Take out the family photo album from the shelf"},
            {"stepNumber": 2, "instruction": "Open to a page and look at each photo carefully"},
            {"stepNumber": 3, "instruction": "Try to name the people in each photo"},
            {"stepNumber": 4, "instruction": "Share a memory or story about one of the photos"},
            {"stepNumber": 5, "instruction": "Place the album back on the shelf"},
        ],
    },
    {
        "name": "Light Kitchen Cleanup",
        "steps": [
            {"stepNumber": 1, "instruction": "Clear any dishes from the dining table to the sink"},
            {"stepNumber": 2, "instruction": "Wipe the dining table with a damp cloth"},
            {"stepNumber": 3, "instruction": "Rinse the dishes under running water"},
            {"stepNumber": 4, "instruction": "Dry your hands and hang the cloth to dry"},
        ],
    },
]


REQUEST_DELAY = 1.2  # seconds between requests to avoid rate limiting


def post_json(client: httpx.Client, path: str, payload: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        response = client.post(f"{BASE_URL}{path}", json=payload, headers=headers, timeout=30.0)
        if response.status_code == 429:
            wait = REQUEST_DELAY * (attempt + 2)
            print(f"    Rate limited, waiting {wait:.0f}s...")
            time.sleep(wait)
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"{path} failed ({response.status_code}): {response.text}")
        time.sleep(REQUEST_DELAY)
        return response.json()
    raise RuntimeError(f"{path} failed after retries (429)")


def get_json(client: httpx.Client, path: str, token: str) -> Any:
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(3):
        response = client.get(f"{BASE_URL}{path}", headers=headers, timeout=30.0)
        if response.status_code == 429:
            wait = REQUEST_DELAY * (attempt + 2)
            print(f"    Rate limited, waiting {wait:.0f}s...")
            time.sleep(wait)
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"{path} failed ({response.status_code}): {response.text}")
        time.sleep(REQUEST_DELAY)
        return response.json()
    raise RuntimeError(f"{path} failed after retries (429)")


def ensure_user(client: httpx.Client, user: dict[str, str]) -> dict[str, Any]:
    try:
        return post_json(client, "/api/users/login", {"email": user["email"], "password": user["password"]})
    except Exception:
        pass
    try:
        post_json(
            client,
            "/api/users/register",
            {
                "name": user["name"],
                "email": user["email"],
                "password": user["password"],
                "role": user["role"],
            },
        )
    except Exception:
        pass
    return post_json(client, "/api/users/login", {"email": user["email"], "password": user["password"]})


def safe_action(label: str, fn) -> None:
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as exc:
        print(f"  SKIP {label} -> {exc}")


def populate_patient_logs(
    client: httpx.Client,
    patient_token: str,
    patient_id: str,
    patient_name: str,
    daily_logs: list[tuple],
    extra_logs: list[tuple],
) -> None:
    """Create 7 days of realistic activity logs for a patient."""
    print(f"\n  Creating activity logs for {patient_name}...")

    # Create logs spread across the last 7 days
    for day_offset in range(7):
        # Pick a realistic subset of daily logs to simulate natural variation
        day_sample_size = random.randint(5, min(len(daily_logs), 8))
        day_logs = random.sample(daily_logs, day_sample_size)

        for activity, log_type, source, metadata in day_logs:
            safe_action(
                f"log day-{day_offset} {patient_name[:8]} {activity[:30]}",
                lambda a=activity, t=log_type, s=source, m=metadata: post_json(
                    client,
                    "/api/logs",
                    {"activity": a, "type": t, "source": s, "metadata": m},
                    token=patient_token,
                ),
            )

    # Add the extra logs (quizzes, sensor data, caregiver observations)
    for activity, log_type, source, metadata in extra_logs:
        safe_action(
            f"extra {patient_name[:8]} {activity[:30]}",
            lambda a=activity, t=log_type, s=source, m=metadata: post_json(
                client,
                "/api/logs",
                {"activity": a, "type": t, "source": s, "metadata": m},
                token=patient_token,
            ),
        )


def populate_medications(
    client: httpx.Client,
    caregiver_token: str,
    patient_id: str,
    patient_name: str,
    medications: list[dict],
) -> None:
    """Add medications for a patient (posted by caregiver)."""
    print(f"\n  Adding medications for {patient_name}...")
    for med in medications:
        safe_action(
            f"med {patient_name[:8]} {med['medicineName']}",
            lambda m=med: post_json(
                client,
                "/api/medications",
                {"patientId": patient_id, **m},
                token=caregiver_token,
            ),
        )


def populate_activities(
    client: httpx.Client,
    caregiver_token: str,
    patient_id: str,
    patient_name: str,
    activities: list[dict],
) -> None:
    """Create guided activities for a patient (posted by caregiver)."""
    print(f"\n  Creating guided activities for {patient_name}...")
    for act in activities:
        safe_action(
            f"activity {patient_name[:8]} {act['name']}",
            lambda a=act: post_json(
                client,
                "/api/activities",
                {"patientId": patient_id, "name": a["name"], "steps": a["steps"]},
                token=caregiver_token,
            ),
        )


def populate_reports(
    client: httpx.Client,
    caregiver_token: str,
    patient_id: str,
    patient_name: str,
) -> None:
    """Create medical report records for a patient."""
    print(f"\n  Adding medical reports for {patient_name}...")
    # Add 2 reports per patient to simulate real visit records
    for i in range(2):
        safe_action(
            f"report {patient_name[:8]} #{i+1}",
            lambda: post_json(
                client,
                "/api/reports",
                {"patientId": patient_id},
                token=caregiver_token,
            ),
        )


def main() -> None:
    print(f"{'='*60}")
    print(f"Avia Demo Data Population")
    print(f"Backend: {BASE_URL}")
    print(f"{'='*60}")

    with httpx.Client() as client:
        # ── Step 1: Ensure all users exist and get tokens ────────────
        print("\n[1/6] Authenticating users...")
        auth_by_email: dict[str, dict[str, Any]] = {}
        for user in USERS:
            auth_by_email[user["email"]] = ensure_user(client, user)
            print(f"  AUTH {user['email']} ({user['role']})")

        meera = auth_by_email["meera@aiva.com"]
        meera_token = meera["token"]

        # ── Step 2: Discover patient IDs ─────────────────────────────
        print("\n[2/6] Discovering patient IDs...")
        all_patients = get_json(client, "/api/users/all-patients", meera_token)
        patient_ids = {p["email"]: p["_id"] for p in all_patients.get("patients", [])}
        for email, pid in patient_ids.items():
            print(f"  FOUND {email} -> {pid}")

        ravi_id = patient_ids.get("ravi@aiva.com")
        lakshmi_id = patient_ids.get("lakshmi@aiva.com")
        ganesh_id = patient_ids.get("ganesh@aiva.com")

        # ── Step 3: Link patients to Meera ───────────────────────────
        print("\n[3/6] Linking patients to Meera...")
        for email in ("ravi@aiva.com", "lakshmi@aiva.com", "ganesh@aiva.com"):
            pid = patient_ids.get(email)
            if not pid:
                continue
            safe_action(
                f"link {email} -> meera",
                lambda patient_id=pid: post_json(
                    client, "/api/users/link", {"patientId": patient_id}, token=meera_token
                ),
            )

        # Re-login Meera to get a fresh token after linking
        meera = ensure_user(client, {"email": "meera@aiva.com", "password": "meera1234", "role": "caregiver", "name": "Meera Iyer"})
        meera_token = meera["token"]

        # Refresh linked patient list
        linked_patients = get_json(client, "/api/users/my-patients", meera_token)
        linked_by_email = {p["email"]: p["_id"] for p in linked_patients}
        print(f"  Meera's linked patients: {list(linked_by_email.keys())}")

        # Use linked IDs where available
        ravi_id = linked_by_email.get("ravi@aiva.com") or ravi_id
        lakshmi_id = linked_by_email.get("lakshmi@aiva.com") or lakshmi_id
        ganesh_id = linked_by_email.get("ganesh@aiva.com") or ganesh_id

        # ── Step 4: Populate medications ─────────────────────────────
        print("\n[4/6] Adding medications...")
        if ravi_id:
            populate_medications(client, meera_token, ravi_id, "Ravi Prakash", RAVI_MEDICATIONS)
        if lakshmi_id:
            populate_medications(client, meera_token, lakshmi_id, "Lakshmi Nair", LAKSHMI_MEDICATIONS)
        if ganesh_id:
            populate_medications(client, meera_token, ganesh_id, "Ganesh Rao", GANESH_MEDICATIONS)

        # ── Step 5: Populate guided activities ───────────────────────
        print("\n[5/6] Creating guided activities...")
        if ravi_id:
            populate_activities(client, meera_token, ravi_id, "Ravi Prakash", RAVI_ACTIVITIES)
        if lakshmi_id:
            populate_activities(client, meera_token, lakshmi_id, "Lakshmi Nair", LAKSHMI_ACTIVITIES)
        if ganesh_id:
            populate_activities(client, meera_token, ganesh_id, "Ganesh Rao", GANESH_ACTIVITIES)

        # ── Step 6: Populate activity logs (as each patient) ─────────
        print("\n[6/6] Creating activity logs...")

        ravi_auth = auth_by_email.get("ravi@aiva.com")
        lakshmi_auth = auth_by_email.get("lakshmi@aiva.com")
        ganesh_auth = auth_by_email.get("ganesh@aiva.com")

        if ravi_auth and ravi_id:
            populate_patient_logs(
                client, ravi_auth["token"], ravi_id, "Ravi Prakash",
                RAVI_DAILY_LOGS, RAVI_EXTRA_LOGS,
            )
            populate_reports(client, meera_token, ravi_id, "Ravi Prakash")

        if lakshmi_auth and lakshmi_id:
            populate_patient_logs(
                client, lakshmi_auth["token"], lakshmi_id, "Lakshmi Nair",
                LAKSHMI_DAILY_LOGS, LAKSHMI_EXTRA_LOGS,
            )
            populate_reports(client, meera_token, lakshmi_id, "Lakshmi Nair")

        if ganesh_auth and ganesh_id:
            populate_patient_logs(
                client, ganesh_auth["token"], ganesh_id, "Ganesh Rao",
                GANESH_DAILY_LOGS, GANESH_EXTRA_LOGS,
            )
            populate_reports(client, meera_token, ganesh_id, "Ganesh Rao")

    print(f"\n{'='*60}")
    print("Population complete.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
