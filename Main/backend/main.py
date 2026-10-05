# Industrial Agentic Query System - FastAPI Application Entrypoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.graph_routes import router as graph_router
from backend.documents.routes import router as document_router
from backend.api.routes import router as query_router
from backend.api.chat_routes import router as chat_router
from backend.api.auth_routes import router as auth_router
from backend.storage.mongodb_manager import MongoDBManager

app = FastAPI(
    title="Industrial Knowledge Intelligence Platform",
    version="1.0.0",
    description="Backend API"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_db_seeding():
    try:
        db = MongoDBManager()
        db.seed_users()
    except Exception as e:
        print(f"[MONGODB ERROR] Failed to seed users: {e}")


@app.get("/")
def root():
    return {
        "message": "Welcome to Industrial Knowledge Intelligence Platform"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(graph_router)
app.include_router(document_router)
app.include_router(query_router)
app.include_router(chat_router)
app.include_router(auth_router)

