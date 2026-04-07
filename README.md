# Avia ML Service

This repository contains a FastAPI ML micro-service for the Avia dementia-care app, plus supporting notebooks for OCR and Alzheimer's quiz modeling.

## What is in this repo

- FastAPI service with ML endpoints: routine hints, lunch prediction, behaviour flags, report summarization, face match, sensor rhythm, adaptive reminders, and daily quiz generation.
- Notebook workflows:
   - OCR workflow (`notebooks/ocr/easy_ocr.ipynb`)
   - Alzheimer's quiz modeling (`notebooks/alzheimers_model_quiz/alzheimers_model.ipynb`)

## Project structure

```text
.
|-- app/
|   |-- main.py
|   |-- config.py
|   |-- models/
|   |   |-- schemas.py
|   |-- routers/
|   |   |-- insights.py
|   |-- services/
|       |-- behaviour_service.py
|       |-- face_service.py
|       |-- lunch_service.py
|       |-- quiz_service.py
|       |-- report_service.py
|       |-- routine_service.py
|       |-- sensor_service.py
|       |-- summary_service.py
|-- scripts/
|   |-- populate_demo_data.py
|-- notebooks/
|   |-- ocr/
|   |   |-- easy_ocr.ipynb
|   |   |-- optimized_output/
|   |-- alzheimers_model_quiz/
|       |-- alzheimers_model.ipynb
|       |-- alzheimers_grade_history.csv
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- run.sh
```

## Local setup

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

Service URLs:

- API docs: `http://localhost:8100/docs`
- Health check: `http://localhost:8100/health`

## Docker

```bash
docker compose up --build
```

The service will be available on port `8100`.

## Environment variables

Create a `.env` file in the repo root only if you want to override defaults:

```env
AVIA_BACKEND_URL=https://aiva-backend-tnp0.onrender.com
ML_SERVICE_PORT=8100
ML_SERVICE_HOST=0.0.0.0
OPENAI_API_KEY=
HUGGINGFACE_API_TOKEN=
HUGGINGFACE_SUMMARY_MODEL=Falconsai/medical_summarization
FACE_MODEL=small
```

## Seed demo data (optional)

```bash
python scripts/populate_demo_data.py
```

This seeds realistic patient, caregiver, medication, activity, sensor, and quiz logs into the configured backend.

## Notebook usage

- OCR notebook: open `notebooks/ocr/easy_ocr.ipynb`.
- Alzheimer's notebook: open `notebooks/alzheimers_model_quiz/alzheimers_model.ipynb`.

Notes:

- Update notebook input paths (for example `IMAGE_PATH`) for your local files.
- OCR outputs are written to `notebooks/ocr/optimized_output/`.
