from fastapi import APIRouter

from . import extract, grade, results, upload

api_router = APIRouter(prefix="/api")
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(extract.router, tags=["extract"])
api_router.include_router(grade.router, tags=["grade"])
api_router.include_router(results.router, tags=["results"])
