"""
main.py — FastAPI Application Entry Point
==========================================
Run with:  uvicorn main:app --reload --port 8000
Swagger:   http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.session import router as session_router
from samples import SAMPLE_TEXTS

app = FastAPI(
    title="AI Interview Assistant",
    description=(
        "Two-agent system: an executive interviewer and a communication evaluator. "
        "Built for the IS601 hackathon."
    ),
    version="1.0.0",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow all origins in dev. Lock this down if you deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Pair B's Vite dev server on any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(session_router)

# ─── Utility Endpoints ────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "running",
        "docs": "/docs",
        "endpoints": [
            "POST /session/start",
            "POST /session/message",
            "POST /session/{id}/evaluate",
            "GET  /samples",
        ]
    }


@app.get("/samples")
async def get_samples():
    """Returns the list of sample abstracts for the UI quick-load buttons."""
    return [s.dict() for s in SAMPLE_TEXTS]


@app.get("/health")
async def health():
    import llm_client
    from config import INTERVIEWER_MODEL, EVALUATOR_MODEL
    return {
        "status": "ok",
        "provider": llm_client.current_provider(),
        "interviewer_model": INTERVIEWER_MODEL,
        "evaluator_model": EVALUATOR_MODEL,
    }


# ─── Global Error Handler ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )
