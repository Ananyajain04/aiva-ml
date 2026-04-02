# aiva-ml

This workspace contains two notebook-based ML projects:

- OCR pipeline using EasyOCR
- Alzheimer's progression quiz modeling and forecasting

## Project structure

- `orc/easy_ocr.ipynb`: OCR and image optimization workflow
- `orc/optimized_output/`: generated OCR/optimized image outputs
- `alzheimers_model_quiz/alzheimers_model.ipynb`: quiz scoring, stage estimation, and progression forecasting
- `alzheimers_model_quiz/alzheimers_grade_history.csv`: sample/history input data for the Alzheimer's notebook
- `requirements.txt`: shared Python dependencies

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run notebooks

- Open and run `orc/easy_ocr.ipynb` for OCR processing.
- Open and run `alzheimers_model_quiz/alzheimers_model.ipynb` for progression analysis.

## Notes

- Update notebook input paths (for example `IMAGE_PATH`) as needed for local files.
- OCR outputs are generated in `orc/optimized_output/`.
