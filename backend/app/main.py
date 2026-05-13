from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers.auth import router as auth_router
from app.routers.candidates import router as candidates_router
from app.seed import seed

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed()
    yield


app = FastAPI(title="TechKraft Candidate Dashboard API", version="1.0.0", lifespan=lifespan)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(candidates_router)


@app.get("/health")
def health():
    return {"status": "ok"}
