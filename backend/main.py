import os, uuid
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import gnani, agents, floorplan
from requirements_extract import extract, follow_up
from report import build_pdf

app = FastAPI(title="BuildWise AI")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")],
                   allow_methods=["*"], allow_headers=["*"])
PROJECTS: dict[str, dict] = {}  # swap for PostgreSQL in production (see README)

# Gnani credit protection: per-visitor and global caps (reset on server restart)
MAX_PER_IP = int(os.getenv("GNANI_CALLS_PER_IP", "6"))
MAX_TOTAL = int(os.getenv("GNANI_CALLS_TOTAL", "150"))
usage = defaultdict(int)
total = [0]

def check_quota(request: Request):
    ip = (request.headers.get("x-forwarded-for") or request.client.host).split(",")[0].strip()
    if total[0] >= MAX_TOTAL or usage[ip] >= MAX_PER_IP:
        raise HTTPException(429, "Gnani voice limit reached. Using browser voice instead.")
    usage[ip] += 1
    total[0] += 1

class GenReq(BaseModel):
    text: str
    project_id: str | None = None
    lang: str = "en-IN"

class UpdReq(BaseModel):
    project_id: str
    text: str
    lang: str = "en-IN"

class CostReq(BaseModel):
    requirements: dict

class IdReq(BaseModel):
    project_id: str

class ExplainReq(BaseModel):
    text: str
    lang: str = "en-IN"

def build(pid, r, lang="en-IN"):
    c = agents.cost(r)
    p = {"id": pid, "requirements": r, "floor_plans": floorplan.all_floors(r), "cost": c,
         "timeline": agents.timeline(r), "sustainability": agents.sustainability(r),
         "interior": agents.interior(r), "utilities": agents.utilities(r),
         "geo": floorplan.all_geo(r), "lang": lang}
    p["explanation"] = agents.llm_explanation(r, c, agents.explanation(r, c, lang), lang)
    PROJECTS[pid] = p
    return p

@app.get("/api/health")
def health(): return {"ok": True, "gnani_configured": gnani.configured()}

@app.get("/")
def root(): return {"name": "BuildWise AI API", "docs": "/docs", "health": "/api/health"}

@app.post("/api/voice/transcribe")
async def transcribe(request: Request, file: UploadFile = File(...), lang: str = Form("en-IN")):
    check_quota(request)
    if not gnani.configured(): raise HTTPException(503, "Gnani not configured; set GNANI_API_KEY")
    try:
        return {"transcript": await gnani.transcribe(await file.read(), file.filename or "audio.webm", file.content_type or "audio/webm", lang)}
    except Exception as e:
        raise HTTPException(502, f"Gnani Prisma error: {e}")

@app.post("/api/design/generate")
def generate(req: GenReq):
    prev = PROJECTS.get(req.project_id, {}).get("requirements") if req.project_id else None
    r = extract(req.text, prev); q = follow_up(r, req.lang)
    pid = req.project_id or uuid.uuid4().hex[:10]
    if q:
        PROJECTS.setdefault(pid, {"id": pid})["requirements"] = r
        return {"project_id": pid, "needs_more_info": True, "question": q, "requirements": r}
    return {"project_id": pid, "needs_more_info": False, "project": build(pid, r, req.lang)}

@app.post("/api/design/update")
def update(req: UpdReq):
    if req.project_id not in PROJECTS: raise HTTPException(404, "Unknown project")
    r = extract(req.text, PROJECTS[req.project_id]["requirements"])
    return {"project": build(req.project_id, r, req.lang)}

@app.post("/api/cost/estimate")
def estimate(req: CostReq): return agents.cost(req.requirements)

@app.post("/api/report/generate")
def report(req: IdReq):
    p = PROJECTS.get(req.project_id)
    if not p or "cost" not in p: raise HTTPException(404, "Unknown project")
    return {"report_url": f"/api/report/{req.project_id}"}

@app.post("/api/voice/explain")
async def explain(request: Request, req: ExplainReq):
    check_quota(request)
    if not gnani.configured(): raise HTTPException(503, "Gnani not configured")
    try:
        audio, ct = await gnani.synthesize(req.text, req.lang)
        return Response(audio, media_type=ct)
    except Exception as e:
        raise HTTPException(502, f"Gnani Timbre error: {e}")

@app.get("/api/project/{pid}")
def get_project(pid: str):
    if pid not in PROJECTS: raise HTTPException(404, "Unknown project")
    return PROJECTS[pid]

@app.get("/api/report/{pid}")
def get_report(pid: str):
    p = PROJECTS.get(pid)
    if not p or "cost" not in p: raise HTTPException(404, "Unknown project")
    return Response(build_pdf(p), media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=buildwise-{pid}.pdf"})