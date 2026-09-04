import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.db.session import engine, Base
import apps.api.models # Ensure all models are loaded

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WarrantyPatternMiner")

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI early-warning intelligence system for field defects."
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
from apps.api.routes.claims import router as claims_router
from apps.api.routes.analysis import router as analysis_router
from apps.api.routes.clusters import router as clusters_router
from apps.api.routes.alerts import router as alerts_router
from apps.api.routes.baseline import router as baseline_router
from apps.api.routes.feedback import router as feedback_router
from apps.api.routes.fingerprints import router as fingerprints_router

app.include_router(claims_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(clusters_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(baseline_router, prefix=settings.API_V1_STR)
app.include_router(feedback_router, prefix=settings.API_V1_STR)
app.include_router(fingerprints_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main.py:app", host="0.0.0.0", port=8000, reload=True)
