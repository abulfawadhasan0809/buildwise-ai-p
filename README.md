# BuildWise AI: Your AI Architect & Construction Copilot

Voice-first conceptual home design. Speak requirements, get a floor plan, cost estimate, timeline, sustainability notes and a PDF report.

## Run it

Backend (Python 3.10+):
```
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add GNANI_API_KEY and the Gnani endpoint URLs
uvicorn main:app --reload --port 8000
```

Frontend (Node 18+):
```
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                 # http://localhost:3000
```

## Gnani setup
`backend/gnani.py` calls the official Gnani endpoints (Prisma STT at `https://api.vachana.ai/stt/v3`, Timbre TTS at `https://api.vachana.ai/api/v1/tts/inference`) with the `X-API-Key-ID` header. Put your key in `backend/.env` as `GNANI_API_KEY`; it never reaches the browser. Browser recordings are converted to WAV in the frontend before upload.
Usage limits protect your credits: `GNANI_CALLS_PER_IP` (default 6) and `GNANI_CALLS_TOTAL` (default 150). Past the limit, the app falls back to free browser voice.
Without a key, the app falls back to the browser's speech recognition and speech synthesis so you can demo the flow immediately (Chrome recommended).

## What is real vs simplified
- Consultant agent: regex extraction and follow-up question (asks about Vastu, plot, budget). Replace with an LLM or LangGraph graph for richer parsing.
- Architect agent: slice-and-dice room layout drawn as SVG. Conceptual only, not code-compliant.
- Cost: area x rate model (Hyderabad ballpark). Tune `agents.py`.
- Explanation: rule-based; set `OPENAI_API_KEY` for LLM-written text.
- Storage: in-memory dict in `main.py`. Swap for PostgreSQL (SQLAlchemy) for persistence.
- Not included yet: 3D exterior (React Three Fiber), image generation, Cloudinary storage.

## API
POST /api/voice/transcribe, /api/design/generate, /api/design/update, /api/cost/estimate, /api/report/generate, /api/voice/explain; GET /api/project/{id}, /api/report/{id}; GET /api/health

## Demo
Say: "I have a 30 by 40 plot in Hyderabad with a 60 lakh budget. I need a modern 3 BHK house with a study room, open kitchen, garden and parking." Answer yes to the Vastu question.
