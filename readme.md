# jobalign ai

**match your skills. find your future.**

---

## project overview

jobalign ai is an ai-powered resume and job matching platform built for modern technical recruitment and job search. the application analyzes messy, multi-column resumes across multiple document formats (pdf, docx, txt, png, jpg, jpeg), extracts structured candidate profiles, normalizes technical terminology, and compares candidate qualifications against real job requirements using a multi-signal semantic matching engine.

---

## features

- **multi-format resume ingestion**: support for pdf, docx, txt, and image resumes (png, jpg, jpeg) with optical character recognition (ocr) fallback.
- **messy resume robustness**: intelligent text normalization handling multiple columns, missing or unusual section headings, varied date formats, tables, and bullet points.
- **skill taxonomy & abbreviation resolution**: normalization of technical terminology (e.g., js to javascript, ml to machine learning, aws to amazon web services, restful api to rest api).
- **multi-signal ai matching engine**: comprehensive weighted compatibility scoring based on skills (40%), experience (20%), semantic job fit (20%), education (10%), and project relevance (10%).
- **explainable ai & gap analysis**: clear breakdown of matched skills, skills not detected in your resume, partial matches with reasoning, and actionable recommendations.
- **dynamic job ranking & filtering**: job search with multi-parameter filtering (location, experience, job type, minimum score) and dynamic ranking powered by actual cosine compatibility.
- **match history & candidate profile editing**: persistent storage in mysql allowing candidates to review past evaluations and refine extracted profile details.
- **interactive demo mode**: one-click end-to-end demo flow that loads sample data, executes real extraction and matching, and renders live score reports.

---

## technology stack

- **backend**: python, flask, flask-sqlalchemy, pymysql, werkzeug
- **database**: mysql (database name: `jobalign_ai`)
- **frontend**: html5, css3, vanilla javascript, jinja2, fetch api
- **ai / nlp / ocr**: sentence-transformers (`all-minilm-l6-v2`), scikit-learn (tf-idf cosine similarity fallback), pymupdf, python-docx, pillow, pytesseract

---

## architecture

```text
resume (pdf / docx / txt / image)
            ↓
document parser & ocr service
            ↓
text cleaning & normalization
            ↓
section & entity detection
            ↓
candidate profile & skill extractor
            ↓
job description parser (must-have & nice-to-have)
            ↓
semantic embeddings & skill alignment
            ↓
multi-signal matching engine (weighted 0-100%)
            ↓
explainable breakdown & recommendations
```

---

## installation & setup

### 1. python setup
ensure python 3.10+ is installed on your system.

### 2. mysql setup
ensure mysql server is running. create the database `jobalign_ai` if it does not already exist:
```sql
create database if not exists jobalign_ai character set utf8mb4 collate utf8mb4_unicode_ci;
```

### 3. environment configuration
create a `.env` file in the root directory:
```text
flask_secret_key=your_secret_key_here
mysql_host=localhost
mysql_port=3306
mysql_user=root
mysql_password=your_password
mysql_database=jobalign_ai
upload_folder=uploads
max_content_length=16777216
```

### 4. dependency installation
install required python packages:
```bash
pip install -r requirements.txt
```

### 5. database initialization
run the database setup script to create tables, populate the skill taxonomy, and seed realistic sample jobs:
```bash
python init_db.py
```

### 6. running the flask application
start the development server:
```bash
python app.py
```
open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## demo flow

1. navigate to the landing page at `http://127.0.0.1:5000`.
2. click **try demo** or register a new user account.
3. upload a sample resume or use the preloaded demo profile.
4. view extracted candidate information under **my resume**.
5. open **job matcher** and paste a job description or click **use sample job**.
6. click **analyze match** to run the matching engine.
7. review your animated compatibility score, matched skills, skills not detected, partial matches, and dynamic recommendations.
8. open **job search** to view active jobs ranked by compatibility with your resume.

---

## ai matching & scoring methodology

the scoring pipeline avoids simplistic keyword counting and applies a balanced multi-signal formulation:

| component | weight | description |
| :--- | :--- | :--- |
| **skills match** | 40% | compares normalized candidate skills against must-have and nice-to-have job skills, identifying exact, partial, and missing skills. |
| **experience match** | 20% | calculates verified tenure and duration against the role's required years of experience. |
| **semantic job fit** | 20% | computes dense vector cosine similarity using sentence-transformers (`all-minilm-l6-v2`) between the full resume context and the job description. |
| **education match** | 10% | checks credential level (bachelor's, master's, doctorate) and field of study alignment. |
| **project relevance** | 10% | evaluates semantic alignment between candidate technical projects and job responsibilities. |

### score categories
- **90–100%**: excellent match
- **75–89%**: strong match
- **60–74%**: good match
- **40–59%**: moderate match
- **0–39%**: low match

---

## ocr methodology

when a scanned pdf or image file (png, jpg, jpeg) is uploaded:
1. document parser detects whether text extraction produces readable characters.
2. if text is absent or minimal, the file is routed to the ocr service.
3. images are pre-processed (grayscale conversion) and processed via tesseract ocr.
4. the extracted text is cleaned, normalized, and passed into section and skill detection.
5. if ocr tools are unavailable, a clear, friendly error is returned rather than crashing.

---

## project structure

```text
c:\shannu\hackathons\algothon 26\
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── init_db.py
├── readme.md
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── resume.py
│   ├── job.py
│   ├── match.py
│   └── skill.py
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py
│   ├── dashboard_routes.py
│   ├── resume_routes.py
│   ├── job_routes.py
│   └── matching_routes.py
│
├── services/
│   ├── __init__.py
│   ├── document_parser.py
│   ├── resume_parser.py
│   ├── ocr_service.py
│   ├── skill_extractor.py
│   ├── job_parser.py
│   ├── embedding_service.py
│   ├── matching_engine.py
│   ├── ranking_engine.py
│   └── recommendation_engine.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── upload_resume.html
│   ├── resume.html
│   ├── job_matcher.html
│   ├── match_result.html
│   ├── jobs.html
│   ├── job_details.html
│   ├── history.html
│   ├── skills.html
│   ├── profile.html
│   ├── settings.html
│   ├── 404.html
│   └── 500.html
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── dashboard.css
│   │   └── responsive.css
│   ├── js/
│   │   ├── main.js
│   │   ├── upload.js
│   │   ├── matcher.js
│   │   ├── jobs.js
│   │   └── dashboard.js
│   └── images/
│
├── uploads/
│   ├── resumes/
│   └── job_descriptions/
│
└── tests/
    ├── __init__.py
    ├── test_flow.py
    └── test_upload_pipeline.py
```

---

## api routes

- `post /api/resume/upload`: upload and analyze a resume file.
- `get /api/resume/<id>`: retrieve parsed resume data by id.
- `post /api/resume/update`: update editable candidate profile fields.
- `post /api/job/analyze`: parse and analyze a job description.
- `post /api/match`: run compatibility evaluation between active resume and target job.
- `post /api/demo-match`: run one-click demo matching flow with sample data.
- `get /api/jobs`: fetch all job listings with dynamic match scores if resume is present.
- `get /api/jobs/<id>`: fetch detailed job information.
- `get /api/matches`: list user match history.
- `get /api/matches/<id>`: retrieve detailed match report.
- `get /api/skills`: list taxonomy skills.

---

## troubleshooting

- **mysql connection issues**: verify that mysql service is active and the credentials in `.env` match your local setup.
- **ocr processing**: for scanned images, ensure tesseract ocr is installed on your machine and present in your system path.
- **first-time model load**: on first execution, sentence-transformers downloads the lightweight `all-minilm-l6-v2` model weights (~80mb). if offline, the application automatically falls back to tf-idf cosine similarity.
