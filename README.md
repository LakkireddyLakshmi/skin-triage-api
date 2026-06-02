# Skin Triage API

A backend that turns a skin-disease classification model into a **real app with user accounts and saved scan history**.

The deep-learning model (a DenseNet-201 + ViT-B16 ensemble, 87.9% test accuracy)
is already deployed as a live demo on
[Hugging Face Spaces](https://huggingface.co/spaces/sweety783/skin-disease-classifier).
This project adds the engineering around it: accounts, a database, an API, tests, and CI/CD.

## What it does

> Sign up → log in → upload a skin photo → get a triage result → it's saved to your
> personal history, so you can revisit all your past scans any time.

## Architecture

```
  Browser ──► Skin Triage API (FastAPI)            ──► Hugging Face Space
              • accounts (sign up / log in)             (runs the actual model)
              • saves each scan to a database
              • returns your scan history
                       │
                       ▼
                  PostgreSQL
```

The API does **not** load the heavy model itself — it calls the already-deployed
Hugging Face Space for predictions and focuses on the product engineering.

## Tech stack

| Layer    | Choice                                  |
|----------|-----------------------------------------|
| API      | FastAPI (async)                         |
| Database | PostgreSQL (SQLite for quick local runs) |
| Auth     | JWT access tokens                       |
| Tests    | pytest                                  |
| CI/CD    | GitHub Actions                          |
| Deploy   | Docker + Docker Compose                 |

## Run it locally

```bash
# 1. Create a virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt

# 2. Run the tests
pytest -v

# 3. Start the server
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs
```

Or with Docker:

```bash
docker compose up --build
```

## Project status

Built in small, reviewable steps:

- [x] **Step 1 — Skeleton:** healthy FastAPI server, tests, Docker, green CI
- [x] **Step 2 — Accounts:** sign up, log in, JWT auth
- [x] **Step 3 — Scan history:** upload a photo, save it, list/view your scans (ownership enforced)
- [x] **Step 4 — Predictions:** uploads are sent to the live Hugging Face model; the real class + confidence are saved
- [ ] **Step 5 — Polish:** full test coverage, deploy live, frontend
