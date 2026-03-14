"""ARIA — Autonomous Research Literature Agent (Backend Entry Point)."""

import logging
import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env BEFORE importing anything that uses env vars
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("aria")

# Validate required env vars
if not os.getenv("GEMINI_API_KEY"):
    logger.warning(
        "⚠️  GEMINI_API_KEY not set! Get your FREE key at https://ai.google.dev\n"
        "   Copy .env.example to .env and add your key."
    )

# Create FastAPI app
app = FastAPI(
    title="ARIA — Autonomous Research Literature Agent",
    description=(
        "An AI-powered research assistant that crawls academic papers, "
        "extracts claims, builds knowledge graphs, and generates synthesis reports."
    ),
    version="1.0.0",
)

# CORS — allow frontend (local dev + production)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
from api.routes_research import router as research_router
from api.routes_query import router as query_router
from api.routes_graph import router as graph_router
from api.routes_explain import router as explain_router

app.include_router(research_router)
app.include_router(query_router)
app.include_router(graph_router)
app.include_router(explain_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "ARIA",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    has_key = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "gemini_api_key_configured": has_key,
        "endpoints": {
            "research": "/api/research",
            "status": "/api/status/{session_id}",
            "results": "/api/results/{session_id}",
            "query": "/api/query",
            "graph": "/api/graph/{session_id}",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
