# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import transactions, user_charts
import os

app = FastAPI(
    title="WalnutFolks Transaction API",
    description="Backend service for processing transactions and managing user chart data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://your-frontend-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router, tags=["Transactions"])
app.include_router(user_charts.router, prefix="/api", tags=["User Charts"])

@app.get("/")
async def root():
    return {
        "message": "WalnutFolks Transaction API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    print("Starting WalnutFolks Transaction API...")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down WalnutFolks Transaction API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )