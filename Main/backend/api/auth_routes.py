from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.storage.mongodb_manager import MongoDBManager

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

db_manager = MongoDBManager()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    role: str
    full_name: str

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = db_manager.get_user(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    hashed_input = db_manager.hash_password(request.password)
    if user["password_hash"] != hashed_input:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    return LoginResponse(
        username=user["username"],
        role=user["role"],
        full_name=user["full_name"]
    )
