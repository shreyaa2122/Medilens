# MediLens: Healthcare Document Intelligence

> Informational tool only. MediLens does not diagnose conditions, prescribe, or replace a
> qualified healthcare professional.

Upload a lab report or prescription, extract its contents, check lab values against the
reference range printed on the report, and track results over time.

**Status: work in progress.** Document upload, validation and storage work. OCR, extraction
and trends are being built.

## Run (no Docker needed)
Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Frontend (second terminal):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. API docs: http://localhost:8000/docs

## Run with Docker (optional)
```bash
cp .env.example .env
docker compose up --build                      # SQLite
docker compose --profile postgres up --build   # with PostgreSQL
```

## API (so far)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Server status |
| POST | `/api/documents/upload` | Upload a PDF, JPG, JPEG or PNG (max `MAX_UPLOAD_MB`) |
| GET | `/api/documents` | List documents, newest first |
| GET | `/api/documents/{id}` | One document |
| DELETE | `/api/documents/{id}` | Delete the document and its file |

Uploads are validated by size and by real file content (not just the extension), stored under
random names, and never logged.

## Tests
```bash
cd backend && pytest
```

## Configuration
Copy `.env.example` to `.env`. The AI provider is selected with `LLM_PROVIDER`
(`none`, `gemini` or `ollama`). All options are free; see the comments in `.env.example`.
