Bunu direkt Cursor’a verip proje scaffold’ını çıkartabilirsin:

# AI Handwritten Exam Grading System

## Project Description

Build a local web-based AI system that can automatically grade handwritten exam papers using image processing, handwriting recognition, OCR, semantic analysis, and AI-based scoring.

The system must:
- Accept uploaded handwritten exam images or PDFs
- Extract handwritten text from exam papers
- Compare student answers with an answer key
- Analyze semantic similarity instead of exact keyword matching
- Generate scores automatically
- Display grading results in a web dashboard

---

# Tech Stack

## Frontend
- React
- TailwindCSS

## Backend
- FastAPI (Python)

## AI / ML
- OpenCV
- PaddleOCR
- sentence-transformers
- scikit-learn

## Database
- SQLite

---

# Main Features

## 1. Upload Exam Paper
Teachers can upload:
- JPG
- PNG
- PDF

The backend should save uploaded files locally.

---

# 2. Image Processing Pipeline

Use OpenCV for:
- Grayscale conversion
- Noise removal
- Thresholding
- Perspective correction
- Image enhancement

Create a service called:

services/image_processing.py

---

# 3. Handwriting Recognition

Use PaddleOCR to extract handwritten text from processed images.

Create a service:

services/ocr_service.py

The OCR service should:
- Detect text regions
- Extract handwritten text
- Return structured question-answer data

---

# 4. Semantic Analysis

Use sentence-transformers for semantic similarity.

Model:
- all-MiniLM-L6-v2

Create:

services/semantic_service.py

The service should:
- Compare answer key and student answer
- Generate cosine similarity score
- Return similarity percentage

---

# 5. AI Grading System

Create:

services/grading_service.py

Logic:
- 90-100 similarity → full score
- 70-89 → high partial score
- 50-69 → medium score
- below 50 → low score

The system must support:
- semantic understanding
- synonyms
- different sentence structures
- spelling tolerance

---

# 6. API Endpoints

## Upload Exam
POST /api/upload

## Extract Text
POST /api/extract

## Grade Exam
POST /api/grade

## Get Results
GET /api/results/{id}

---

# 7. Frontend Requirements

Create pages:

## Dashboard
- upload exam image
- upload answer key
- start grading button

## Results Page
Display:
- extracted text
- similarity score
- final score
- feedback

Use clean modern UI.

---

# 8. Project Structure

project/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   │   ├── image_processing.py
│   │   ├── ocr_service.py
│   │   ├── semantic_service.py
│   │   └── grading_service.py
│   ├── uploads/
│   └── database/
│
├── frontend/
│
└── README.md

---

# Additional Requirements

- Run fully locally
- No cloud dependency
- Modular architecture
- Clean code
- REST API architecture
- Error handling
- Logging support

---

# Expected Workflow

1. Teacher uploads handwritten exam paper
2. Backend processes image
3. OCR extracts handwritten text
4. Semantic AI compares answers
5. System generates scores
6. Results displayed on dashboard

---

# Important

The project must focus on:
- semantic grading
- contextual understanding
- handwriting recognition
- AI-assisted scoring

Do NOT use simple keyword matching.
Use semantic similarity and contextual meaning analysis.

---

# Bonus Features

Optional:
- PDF export
- Teacher authentication
- Multiple students
- Analytics dashboard
- Question segmentation
- Turkish language optimization