"""Custom AgentExecutor for orchestrator that parses A2UI JSON from agent responses."""

import json
import logging
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

logger = logging.getLogger(__name__)

class OrchestratorAgentExecutor:
    """AgentExecutor that parses A2UI JSON from orchestrator agent responses."""
    
    def __init__(self, agent):
        self.agent = agent
        self._runner = Runner(
            agent=agent,
            session_service=InMemorySessionService(),
        )
        self._user_id = "orchestrator_user"
    
    async def stream(self, query: str, session_id: str):
        """Stream responses from the agent, parsing A2UI JSON."""
        
        session = await self._runner.session_service.get_session(
            app_name=self.agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self.agent.name,
                user_id=self._user_id,
                session_id=session_id,
            )
        
        # Stream from the agent
        full_response = ""
        async for event in self._runner.run(query, session_id=session_id):
            if hasattr(event, 'content') and event.content:
                full_response += event.content
                
                # Send intermediate updates
                if not event.content.strip().endswith(('```', '---')):
                    yield {
                        "is_task_complete": False,
                        "updates": event.content
                    }
        
        # Parse final response for A2UI JSON
        yield {
            "is_task_complete": True,
            "content": full_response
        }
