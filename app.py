"""Periscope Schema Harmonizer — FastAPI entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.routes import upload, mapping, reviews, cdm, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up DB pool on startup."""
    from server.db import get_db
    try:
        await get_db()
        print("[startup] Lakebase pool ready")
    except Exception as e:
        print(f"[startup] Lakebase unavailable: {e}")
    yield


app = FastAPI(
    title="Periscope Schema Harmonizer",
    description="Periscope — AI-powered schema harmonization for customer sales data",
    version="1.0.0",
    lifespan=lifespan,
)

# --- API routes ---
app.include_router(upload.router, prefix="/api")
app.include_router(mapping.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(cdm.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


# --- Health check ---
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "periscope-schema-harmonizer"}


# --- Serve React frontend (production build) ---
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)
