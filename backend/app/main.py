"""《山货有话说》后端入口。

开发：cd backend && python run.py
    （或 uvicorn app.main:app --reload）
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routers import auth, generate, guide, poster, recognize, settings, tts

db.init_db()

app = FastAPI(title="山货有话说 · AI助农数字文创平台", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/poster", StaticFiles(directory=config.GENERATED_DIR / "poster"), name="poster")
app.mount("/static/audio", StaticFiles(directory=config.GENERATED_DIR / "audio"), name="audio")

for r in (auth, recognize, generate, poster, tts, guide, settings):
    app.include_router(r.router)


@app.get("/api/health")
def health():
    return {"ok": True, "demo": config.DEMO_MODE}


# 前端 build 产物存在时，由后端统一托管（生产演示模式）
if config.FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=config.FRONTEND_DIST, html=True), name="frontend")
