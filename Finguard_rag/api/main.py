"""
M11 -- FastAPI Application Entry Point
============================================================================
Creates the FastAPI app, configures CORS middleware for the React frontend,
and mounts all route handlers from routes.py.

Run with:
    uvicorn Finguard_rag.api.main:app --reload --port 8000

Swagger UI available at:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title       = "FinGuard-RAG API",
    description = "Compliance-Aware Financial RAG System for BharatFinServ Ltd.",
    version     = "1.0.0",
)

# Allow React dev server on :3000
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(router)
