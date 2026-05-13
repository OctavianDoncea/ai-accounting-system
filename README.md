# AI Duble-Entry Bookkeeping Assistant

A LLM-powered accounting system demonstrating AI-native ERP concepts.

## Quickstart
```bash
cp .env.example .env
# Edit .env: set POSTGRES_USER and POSTGRES_PASSWORD (and optionally POSTGRES_DB).

docker compose up --build
```

Then open http://localhost:5173

## Tech Stack

Backend: FastAPI, async SQLAlchemy, PostgreSQL
Frontend: React, TypeScript, Tailwind, Vite
AI: Ollama (local)
CI: GitHub Actions

### Backend setup

#### backend/requirements.txt
```txt
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
psycopg2-binary
alembic
python-dotenv
pydantic
pytest
httpx
```