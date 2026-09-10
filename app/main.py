import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.schemas import HealthResponse

from app.routes.customers import router as customer_router
from app.routes.dashboard import router as dashboard_router
from app.routes.dataset import router as dataset_router
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.history import router as history_router

from app.database.connection import engine, Base, SessionLocal
from app.database import models
from app.services.auth_service import seed_default_users
from app.services.history_service import seed_default_history


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = FastAPI(
    title="Customer Segmentation & AI Marketing API",
    description=(
        "An industry-level customer analytics API built using "
        "RFM analysis, K-Means clustering, customer segmentation, "
        "marketing analytics, database integration, and "
        "AI-powered recommendations."
    ),
    version="1.0.0",
    contact={
        "name": "Customer Segmentation Project",
        "email": "saichethanadigavinti@gmail.com",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

# app/main.py
# parent        -> app
# parent.parent -> customer-segmentation
PROJECT_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = PROJECT_DIR / "frontend"


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    try:
        Base.metadata.create_all(bind=engine)

        print("✅ Database tables initialized successfully.")

    except Exception as error:
        print("❌ Database initialization failed.")
        print(f"Error: {error}")
        raise


# ============================================================
# APPLICATION STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    print("🚀 Starting Customer Segmentation API...")

    print(f"📁 Frontend directory: {FRONTEND_DIR}")

    print(
        f"📄 Index file exists: "
        f"{(FRONTEND_DIR / 'index.html').exists()}"
    )

    initialize_database()
    
    # Seed default admin & analyst users and initial analysis history
    db = SessionLocal()
    try:
        seed_default_users(db)
        seed_default_history(db)
    finally:
        db.close()


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(customer_router)
app.include_router(dashboard_router)
app.include_router(dataset_router)
app.include_router(history_router)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


# ============================================================
# FRONTEND HOME PAGE
# ============================================================

@app.get("/", include_in_schema=False)
def serve_frontend():

    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return {
            "error": "index.html not found",
            "expected_path": str(index_file),
        }

    return FileResponse(
        path=str(index_file),
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check():

    return {
        "status": "healthy",
        "service": "Customer Segmentation API",
    }