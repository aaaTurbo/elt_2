from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_handlers
from app.api.routers import campaigns_router, editor_router, offers_router
from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="AdRobot — Keitaro control plane",
    version="0.1.0",
    description="API-обёртка над Keitaro: кампании, потоки, офферы, push.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_handlers(app)
app.include_router(campaigns_router.router, prefix="/api/v1")
app.include_router(editor_router.router, prefix="/api/v1")
app.include_router(offers_router.router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}