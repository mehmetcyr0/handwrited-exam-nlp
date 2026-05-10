"""
El Yazısı Sınav Okuyucu — FastAPI backend.
"""
from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from routes import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="El Yazısı Sınav Okuyucu",
    description="Yerel AI destekli el yazısı sınav değerlendirme API",
    version="1.0.0",
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


@app.on_event("startup")
def startup():
    init_db()
    logger.info("Backend hazır")


@app.get("/health")
def health():
    return {"status": "ok", "app": "el-yazisi-sinav-okuyucu"}
