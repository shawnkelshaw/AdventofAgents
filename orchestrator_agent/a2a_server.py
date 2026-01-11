"""A2A server for orchestrator agent with A2UI support."""

import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
# A2UI helper functions
def try_activate_a2ui_extension(context):
    """Check if A2UI extension is requested."""
    if not context.requested_extensions:
        return False
    return any("a2ui" in ext.lower() for ext in context.requested_extensions)

def create_a2ui_part(data):
    """Create an A2UI data part.
    
    The A2A SDK DataPart has: data (dict), kind ('data'), metadata (optional dict).
    The A2UI message is passed directly in the data field.
    """
    return Part(root=DataPart(
        data=data
    ))
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types as genai_types
import json

logger = logging.getLogger(__name__)

class OrchestratorAgentExecutor(AgentExecutor):
    """AgentExecutor that parses A2UI JSON from orchestrator responses."""
    
    def __init__(self, agent):
        self.agent = agent
        self._runner = Runner(
            app_name=agent.name,
            agent=agent,
            session_service=InMemorySessionService(),
        )
        self._user_id = "orchestrator_user"
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = ""
        
        logger.info(f"Client requested extensions: {context.requested_extensions}")
        use_ui = try_activate_a2ui_extension(context)
        
        if use_ui:
            logger.info("A2UI extension is active")
        else:
            logger.info("A2UI extension is not active")
        
        # Extract query from message - handle both text and A2UI user actions
        user_action = None
        if context.message and context.message.parts:
            for part in context.message.parts:
                if isinstance(part.root, TextPart):
                    query = part.root.text
                elif isinstance(part.root, DataPart):
                    # Check for A2UI user action
                    data = part.root.data
                    if "userAction" in data:
                        user_action = data["userAction"]
                        action_name = user_action.get("name", "")
                        action_context = user_action.get("context", {})
                        logger.info(f"Received A2UI action: {action_name}, context: {action_context}")
                        
                        # Convert user action to natural language query for the agent
                        if action_name == "submit_vehicle_info":
                            # Extract form values from context
                            year = action_context.get("year", "")
                            make = action_context.get("make", "")
                            model = action_context.get("model", "")
                            mileage = action_context.get("mileage", "")
                            condition = action_context.get("condition", "good")
                            query = f"User submitted vehicle info: {year} {make} {model}, {mileage} miles, {condition} condition. Please provide a trade-in estimate."
                        else:
                            query = f"User performed action: {action_name}"
        
        if not query:
            query = context.get_user_input()
        
        if not query:
            query = "Hello, I'd like to trade in my vehicle."
        
        logger.info(f"Processing query: '{query}'")
        
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        
        # Get or create session
        session = await self._runner.session_service.get_session(
            app_name=self.agent.name,
            user_id=self._user_id,
            session_id=task.context_id,
        )
        
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self.agent.name,
                user_id=self._user_id,
                session_id=task.context_id,
            )
        
        # Create Content object for the message (required by Runner API)
        new_message = genai_types.Content(
            parts=[genai_types.Part(text=query)],
            role="user"
        )
        
        # Stream from agent using correct run_async API
        full_response = ""
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=task.context_id,
            new_message=new_message
        ):
            # Extract text from event.content.parts
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_response += part.text
                        
                        # Send intermediate updates (skip if partial JSON)
                        if not part.text.strip().endswith(('```', '---', '{')):
                            await updater.update_status(
                                TaskState.working,
                                new_agent_text_message(part.text, task.context_id, task.id),
                            )
        
        # Parse final response for A2UI JSON
        logger.info(f"Full response length: {len(full_response)}")
        logger.info(f"Full response preview: {full_response[:500]}...")
        logger.info(f"Contains delimiter: {'---a2ui_JSON---' in full_response}")
        
        final_parts = []
        if "---a2ui_JSON---" in full_response:
            logger.info("Splitting response into text and UI parts")
            text_content, json_string = full_response.split("---a2ui_JSON---", 1)
            
            if text_content.strip():
                final_parts.append(Part(root=TextPart(text=text_content.strip())))
            
            if json_string.strip():
                try:
                    # Strip markdown code blocks
                    json_string_cleaned = (
                        json_string.strip()
                        .lstrip("```json")
                        .lstrip("```")
                        .rstrip("```")
                        .strip()
                    )
                    
                    json_data = json.loads(json_string_cleaned)
                    
                    if isinstance(json_data, list):
                        logger.info(f"Found {len(json_data)} A2UI messages")
                        for message in json_data:
                            final_parts.append(create_a2ui_part(message))
                    else:
                        logger.info("Found single A2UI message")
                        final_parts.append(create_a2ui_part(json_data))
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse A2UI JSON: {e}")
                    final_parts.append(Part(root=TextPart(text=json_string)))
        else:
            final_parts.append(Part(root=TextPart(text=full_response.strip())))
        
        logger.info(f"Sending {len(final_parts)} parts to client")
        for i, p in enumerate(final_parts):
            logger.info(f"  Part {i}: type={type(p.root).__name__}")
        
        # Create the message and log it
        final_message = new_agent_parts_message(final_parts, task.context_id, task.id)
        logger.info(f"Final message has {len(final_message.parts)} parts")
        
        await updater.update_status(
            TaskState.input_required,
            final_message,
            final=False,
        )
    
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
