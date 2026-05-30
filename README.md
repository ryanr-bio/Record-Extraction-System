# Record Extraction System (RES) (Work In Progress)
### A program designed to retrieve medical record data from hospital databases for research purposes, specifically to automate data entry. This system utilizes advanced OCR techniques and Large Language Models (LLMs) to transform raw image data into structured JSON formats.

## 🚀 Overview

RES automates the labor-intensive process of manual data entry from scanned medical records. By combining PaddleOCR for text extraction and Qwen2.5 7B for intelligent data parsing, the system can handle complex medical tables, varying document layouts, and historical record nuances. The system processes ER visits for patients aged 60 and above, extracting over 30 clinical fields per visit and writing them directly into a master Excel spreadsheet — with zero manual intervention.

## 🛠 Tech Stack

* **Processor:** Intel i7-6700
* **GPU:** AMD Radeon RX 580 (8GB VRAM)
* **Memory:** 20GB RAM
* **OCR Engine:** [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
* **Inference Engine:** [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
* **Language Model:** Qwen2.5 7B
* **Environment:** Local Server (Privacy-focused, no cloud usage)

🏗 Pipeline Architecture

1. Image Retrieval: Files are fetched from Google Drive via the Drive API, with HEIC images converted to JPEG in-memory and PDF files handled through a separate OCR path.
2. Image Processing: Normalization and enhancement using PIL/OpenCV.
3. OCR Execution: PaddleOCR extracts raw text strings with spatial awareness.
4. Master Cleaning: A multi-pass regex pipeline strips administrative noise, sidebar navigation elements, reassessment blocks, and redundant tables.
5. Visit Grouping: Individual pages are correlated and combined by visit date.
6. ICD Pre-extraction: A dedicated regex engine independently locates the primary ICD code from the Provisional Diagnosis table, which is then cross-checked against the LLM output to catch drift.
7. LLM Extraction: The structured text is processed by Qwen2.5 to extract high-value clinical data points using grammar-constrained JSON output (schema-enforced).
8. Post-processing: Vitals range validation, disposition datetime reconciliation (regex vs. LLM, later time wins), age calculation from DOB, and ICD mismatch correction.
9. Excel Write-back: Data is written row-by-row via openpyxl, with automatic row insertion for patients with more visits than existing records. Progress is saved by Comp ID after each patient so interrupted runs resume exactly where they left off.

📋 Extracted Fields

Demographics: Date of Birth, Nationality, Marital Status, Occupation, Age (calculated)
Visit Info: Visit Date, Visit Time, Triage Category
Vitals: Temperature, Pulse, Respiratory Rate, BP, O2 Saturation, Pain Scale, GCS
Clinical: Chief Complaint, Past History, Current Medication, Psychosocial, Travel History
Diagnosis: Primary ICD (Code + Description), Other ICD Codes, Disease Grouping, Remarks
Disposition: Disposition Date/Time, Disposition Type, Condition at Disposition, Advice & Health Education

This is a personal project based on my background in Biomedical Science and my recent interest in the art of programming!
