"""A2A server for the orchestrator agent with A2UI support."""

import os
import logging
from dotenv import load_dotenv
from agent import root_agent
from a2a_server import OrchestratorAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentExtension
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# A2UI extension definition
def get_a2ui_agent_extension():
    """Get the A2UI agent extension."""
    return AgentExtension(
        uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
        capabilities={}
    )

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create the A2A server application."""
    
    # Create agent card
    skill = AgentSkill(
        id="orchestrator_agent",
        name="Vehicle Trade-In Orchestrator",
        description=root_agent.description,
        tags=["orchestrator", "vehicle", "trade-in", "appointment"],
    )
    
    agent_card = AgentCard(
        name="orchestrator_agent",
        url="http://localhost:10010",
        description=root_agent.description,
        version="0.1.0",
        capabilities={},
        skills=[skill],
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        supportsAuthenticatedExtendedCard=False,
    )
    
    # Create custom agent executor
    agent_executor = OrchestratorAgentExecutor(root_agent)
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    
    # Build the app
    app = server.build()
    
    # Add CORS middleware - allow all localhost ports for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.route("/health")
    async def health_check(request):
        return JSONResponse({
            "status": "healthy",
            "version": "0.9",
            "agent": "orchestrator_agent"
        })
    
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    logger.info("Starting orchestrator A2A server on http://0.0.0.0:10010")
    uvicorn.run(app, host="0.0.0.0", port=10010)
