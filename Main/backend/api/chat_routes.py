from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import uuid

from backend.storage.mongodb_manager import MongoDBManager
from backend.agents.query_agent import QueryAgent
from backend.models.query_models import QueryResponse

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

db_manager = MongoDBManager()
query_agent = QueryAgent()

class ChatMessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatMessageResponse(BaseModel):
    session_id: str
    response: QueryResponse

@router.get("/sessions")
def list_sessions():
    try:
        return db_manager.list_chat_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
def get_history(session_id: str):
    try:
        return db_manager.get_chat_history(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message", response_model=ChatMessageResponse)
def send_message(request: ChatMessageRequest, x_user_role: Optional[str] = Header(None)):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        role = (x_user_role or "engineer").lower()
        
        # Save user message to MongoDB
        db_manager.save_chat_message(
            session_id=session_id,
            role="user",
            content=request.message
        )

        # Get response from the QueryAgent with role clearance
        agent_response = query_agent.query(request.message, user_role=role)

        # Convert agent response for saving and typing
        if isinstance(agent_response, dict):
            response_dict = agent_response
            answer_text = agent_response.get("answer", "")
            query_resp = QueryResponse(**agent_response)
        else:
            response_dict = agent_response.model_dump() if hasattr(agent_response, "model_dump") else agent_response.dict()
            answer_text = getattr(agent_response, "answer", "")
            query_resp = agent_response

        # Save assistant response to MongoDB
        db_manager.save_chat_message(
            session_id=session_id,
            role="assistant",
            content=answer_text,
            response_data=response_dict
        )

        return ChatMessageResponse(
            session_id=session_id,
            response=query_resp
        )
    except Exception as e:
        print(f"Error handling chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    try:
        db_manager.delete_session(session_id)
        return {"status": "success", "message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
