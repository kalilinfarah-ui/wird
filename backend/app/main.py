"""
ورد — FastAPI Application
No in-process scheduler. All timed tasks are driven externally by cron-job.org.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import Base, engine
from app.api.routes import auth, classes, attendance, wird, reports, telegram_webhook
from app.api.routes.tasks import router as tasks_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting ورد backend...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Backend stopped.")


app = FastAPI(
    title="ورد API",
    description="نظام إدارة الورد اليومي عبر تيليغرام",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router,             prefix="/api")
app.include_router(classes.router,          prefix="/api")
app.include_router(attendance.router,       prefix="/api")
app.include_router(wird.router,             prefix="/api")
app.include_router(reports.router,          prefix="/api")
app.include_router(telegram_webhook.router, prefix="/api")
app.include_router(tasks_router,            prefix="/api")


@app.get("/health")
def health():
    """
    Pinged every 5 min by UptimeRobot to keep Render's free tier awake.
    No auth required — it's just a heartbeat.
    """
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
def root():
    return {"message": "ورد API — منصة إدارة الورد اليومي"}
