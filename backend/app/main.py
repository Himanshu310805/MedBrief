import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.extract import router as extract_router
from app.api.analyze import router as analyze_router
from app.api.download import router as download_router
from app.api.auth import router as auth_router
from app.api.reports import router as reports_router
from app.database import init_db

app = FastAPI(
    title="MedBrief API",
    description="Backend API service for MedBrief - Medical Report Summarizer",
    version="1.0.0"
)

# Initialize PostgreSQL database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Enable CORS for frontend development & production deployment via ALLOWED_ORIGIN env var
allowed_origin_env = os.getenv("ALLOWED_ORIGIN")
if allowed_origin_env and allowed_origin_env.strip():
    origins = [o.strip() for o in allowed_origin_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix="/api", tags=["User Authentication"])
app.include_router(extract_router, prefix="/api", tags=["Text Extraction"])
app.include_router(analyze_router, prefix="/api", tags=["Medical Entity Analysis"])
app.include_router(download_router, prefix="/api", tags=["PDF Report Export"])
app.include_router(reports_router, prefix="/api", tags=["Report History"])




@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "MedBrief backend"
    }
