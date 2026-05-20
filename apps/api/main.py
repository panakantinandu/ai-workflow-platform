import os
import pathlib

# Must be set before any prometheus_client import so multiprocess mode works.
_prom_dir = pathlib.Path("prometheus_multiproc")
_prom_dir.mkdir(exist_ok=True)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", str(_prom_dir.resolve()))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi import Depends, Request, APIRouter
from apps.api.db.deps import get_db
from apps.api.db.models import Task
from apps.api.routes.incidents import router as incident_router
from apps.api.routes.workflows import router as workflow_router
from apps.api.routes.task import router as task_router
from apps.api.schemas.task import PaginatedTaskResponse
from fastapi.responses import JSONResponse, Response
import logging
from apps.api.db.base import Base
from apps.api.db.database import engine

from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    multiprocess
)
from apps.api.services.task_worker import run_worker



app = FastAPI()

app.include_router(incident_router)
app.include_router(workflow_router)
app.include_router(task_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn.error")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "details": str(exc)},
    )


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    return Response(data, media_type="text/plain")

from fastapi import Query

@app.get("/tasks", response_model=PaginatedTaskResponse)
def get_all_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    total = db.query(Task).count()
    items = db.query(Task).order_by(Task.id.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@app.on_event("startup")
def startup_event():
    from apps.api.db import models

    print("🔧 Creating tables...")

    Base.metadata.create_all(bind=engine)

    # 🔥 VERIFY TABLES ACTUALLY EXIST
    print("📦 Tables in metadata:", Base.metadata.tables.keys())

    import time
    time.sleep(2)   # ⛔ IMPORTANT (temporary stabilization)

    print("✅ Tables should exist now")

    # start worker AFTER delay
    import threading

    def start_worker():
        print("🚀 Worker started AFTER DB ready")
        run_worker()

    thread = threading.Thread(target=start_worker, daemon=True)
    thread.start()