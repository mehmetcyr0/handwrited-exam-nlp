"""
El Yazısı Sınav Okuyucu — FastAPI backend.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.db import init_db
from routes import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Backend hazır")
    yield


app = FastAPI(
    title="El Yazısı Sınav Okuyucu",
    description="Yerel AI destekli el yazısı sınav değerlendirme API",
    version="1.0.0",
    lifespan=lifespan,
)

# Yerel geliştirme: localhost / 127.0.0.1 üzerinde her port (5173, 4173, vb.)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(Exception)
async def unhandled_exception(_request: Request, exc: Exception):
    """HTTPException / RequestValidationError için FastAPI’nın kendi işleyicisi (MRO’da önce) kullanılır."""
    logger.exception("İşlenmeyen sunucu hatası")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Sunucu hatası"},
    )


@app.get("/")
def root():
    """Kök URL; tarayıcıda 8000 açıldığında yönlendirme bilgisi (404 yerine)."""
    return {
        "app": "El Yazısı Sınav Okuyucu",
        "message": "Bu adres API sunucusudur. Arayüzü kullanın: http://127.0.0.1:5173",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "api_upload": "/api/upload",
    }


@app.get("/health")
def health():
    return {"status": "ok", "app": "el-yazisi-sinav-okuyucu"}
