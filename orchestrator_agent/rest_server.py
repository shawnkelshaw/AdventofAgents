"""REST API server for React client to connect to orchestrator agent."""

import logging
import uuid
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types as genai_types

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Orchestrator REST API")

# Enable CORS for React client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session management
session_service = InMemorySessionService()
runner = Runner(
    app_name=root_agent.name,
    agent=root_agent,
    session_service=session_service,
)

class ChatRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None

class ActionRequest(BaseModel):
    action: str
    context: Dict[str, Any]
    sessionId: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    sessionId: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages from React client."""
    try:
        # Get or create session
        if request.sessionId:
            session_id = request.sessionId
        else:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            # Create session with the generated ID
            await session_service.create_session(
                app_name=root_agent.name,
                user_id="default_user",
                session_id=session_id
            )
        
        # Create Content object for the message (required by Runner API)
        new_message = genai_types.Content(
            parts=[genai_types.Part(text=request.message)],
            role="user"
        )
        
        # Run the agent with the user's message (returns async generator)
        result_generator = runner.run_async(
            user_id="default_user",
            session_id=session_id,
            new_message=new_message
        )
        
        # Collect all responses from the async generator
        content = ""
        async for event in result_generator:
            # Extract text from event.content.parts
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        content += part.text
        
        return ChatResponse(
            content=content,
            sessionId=session_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action", response_model=ChatResponse)
async def action(request: ActionRequest):
    """Handle user actions (button clicks, form submissions)."""
    try:
        # Get session
        if not request.sessionId:
            raise HTTPException(status_code=400, detail="Session ID required for actions")
        
        session_id = request.sessionId
        
        # Format action as a message to the agent
        action_message = f"User action: {request.action}"
        if request.context:
            context_str = ", ".join([f"{k}={v}" for k, v in request.context.items()])
            action_message += f" with context: {context_str}"
        
        # Create Content object for the action message
        new_message = genai_types.Content(
            parts=[genai_types.Part(text=action_message)],
            role="user"
        )
        
        # Run the agent (returns async generator)
        result_generator = runner.run_async(
            user_id="default_user",
            session_id=session_id,
            new_message=new_message
        )
        
        # Collect all responses from the async generator
        content = ""
        async for event in result_generator:
            # Extract text from event.content.parts
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        content += part.text
        
        return ChatResponse(
            content=content,
            sessionId=session_id
        )
        
    except Exception as e:
        logger.error(f"Action error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting REST API server on http://localhost:10010")
    uvicorn.run(app, host="0.0.0.0", port=10010)
