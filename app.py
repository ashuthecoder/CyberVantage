"""
FastAPI Main Application
Modern async backend for CyberVantage
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from api.core.config import settings
from api.core.database import engine, Base
from api.routers import auth, simulation, analysis, threats

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    print("🚀 Starting CyberVantage FastAPI Application...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔐 JWT Secret configured: {bool(settings.JWT_SECRET_KEY)}")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")
    
    yield
    
    # Shutdown
    print("👋 Shutting down CyberVantage...")

# Create FastAPI app
app = FastAPI(
    title="CyberVantage API",
    description="Next-generation security training platform API",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(threats.router, prefix="/api/threats", tags=["Threats"])

# Serve React frontend static files (production)
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint - serves React app in production"""
    if os.path.exists("frontend/dist/index.html"):
        from fastapi.responses import FileResponse
        return FileResponse("frontend/dist/index.html")
    return {"message": "CyberVantage API is running. Frontend not built yet."}

# Catch-all route for React Router (SPA)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all routes (SPA routing)"""
    if os.path.exists("frontend/dist/index.html"):
        from fastapi.responses import FileResponse
        return FileResponse("frontend/dist/index.html")
    return {"message": f"Path: {full_path} - Frontend not built"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
