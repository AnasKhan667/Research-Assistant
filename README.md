# Multi-Agent Researcher

A LangGraph-powered multi-agent research pipeline (supervisor → researcher → critic → writer) with a FastAPI backend and a Next.js frontend.

```
multi-agent-researcher/
├── backend/                # Python / FastAPI
│   ├── app/
│   │   ├── main.py         # FastAPI entrypoint
│   │   ├── config.py       # env-driven settings
│   │   ├── llm_manager.py  # Hugging Face LLM wrapper
│   │   ├── agent.py        # LangGraph multi-agent workflow
│   │   ├── api/routes.py   # /api/research, /api/health
│   │   └── models/schemas.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Next.js (React) + Tailwind
│   ├── app/                 # pages, layout, global styles
│   ├── components/          # PipelineDiagram, ResultsView
│   ├── lib/api.ts           # backend API client
│   └── .env.example
└── .gitignore
```

## 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set HUGGINGFACEHUB_API_TOKEN=<your rotated token>

python -m app.main
```

Runs on **http://localhost:8000**. Interactive API docs at `/docs`.

## 2. Frontend setup

```bash
cd frontend
npm install

cp .env.example .env.local
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 (default is already correct for local dev)

npm run dev
```

Runs on **http://localhost:3000**.

## 3. Using it

Open the frontend, type a research question, and hit "Run research." The request goes to `POST /api/research` on the backend, which runs the full supervisor → researcher → critic → writer LangGraph workflow and returns the plan, findings, sources, and final report.

## Notes

- **Never commit `.env` files.** Both `backend/.env` and `frontend/.env.local` are gitignored.
- The Hugging Face token that was previously hardcoded in the source has been removed. If you haven't already, **rotate that token** at https://huggingface.co/settings/tokens — it was exposed in plaintext.
- `LLM_REPO_ID` in `backend/.env` defaults to `Qwen/Qwen2.5-7B-Instruct`; swap it for any model your HF token has inference access to.
- CORS on the backend is controlled by `ALLOWED_ORIGINS` in `backend/.env` — add your deployed frontend's URL there before going to production.
