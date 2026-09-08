from fastapi import APIRouter
from app.api.v1.endpoints import datasets, query, formulas, reports, evaluation, templates

api_router = APIRouter()

api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets & Profiling"])
api_router.include_router(query.router, prefix="/query", tags=["AI Query & Formula Engine"])
api_router.include_router(formulas.router, prefix="/formulas", tags=["Formula Knowledge Base"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Export"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation & Research"])
api_router.include_router(templates.router, prefix="/templates", tags=["Report Templates"])
