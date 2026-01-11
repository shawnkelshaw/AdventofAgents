import json
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
from a2ui.a2ui_extension import create_a2ui_part, try_activate_a2ui_extension

# Import the calendar agent
from agent import root_agent

logger = logging.getLogger(__name__)


class CalendarAgentExecutor(AgentExecutor):
    """Calendar AgentExecutor with A2UI support."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.agent = root_agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = ""
        ui_event_part = None
        action = None

        logger.info(
            f"--- Client requested extensions: {context.requested_extensions} ---"
        )
        use_ui = try_activate_a2ui_extension(context)

        if use_ui:
            logger.info(
                "--- AGENT_EXECUTOR: A2UI extension is active. Will parse and send A2UI messages. ---"
            )
        else:
            logger.info(
                "--- AGENT_EXECUTOR: A2UI extension is not active. Using text-only mode. ---"
            )

        if context.message and context.message.parts:
            logger.info(
                f"--- AGENT_EXECUTOR: Processing {len(context.message.parts)} message parts ---"
            )
            for i, part in enumerate(context.message.parts):
                if isinstance(part.root, DataPart):
                    if "userAction" in part.root.data:
                        logger.info(f"  Part {i}: Found a2ui UI ClientEvent payload.")
                        ui_event_part = part.root.data["userAction"]
                    else:
                        logger.info(f"  Part {i}: DataPart (data: {part.root.data})")
                elif isinstance(part.root, TextPart):
                    logger.info(f"  Part {i}: TextPart (text: {part.root.text})")
                else:
                    logger.info(f"  Part {i}: Unknown part type ({type(part.root)})")

        if ui_event_part:
            logger.info(f"Received a2ui ClientEvent: {ui_event_part}")
            action = ui_event_part.get("actionName")
            ctx = ui_event_part.get("context", {})

            if action == "SELECT_TIME_SLOT":
                slot_index = ctx.get("slotIndex")
                date_time = ctx.get("dateTime")
                query = f"I'd like to book the appointment at {date_time}"
                logger.info(f"User selected time slot {slot_index}: {date_time}")

            elif action == "SUBMIT_BOOKING":
                name = ctx.get("name")
                email = ctx.get("email")
                date_time = ctx.get("dateTime")
                query = f"Please book the appointment for {name} ({email}) at {date_time}"
                logger.info(f"User submitted booking: {name}, {email}, {date_time}")

            else:
                query = f"User submitted an event: {action} with data: {ctx}"
        else:
            logger.info("No a2ui UI event part found. Falling back to text input.")
            query = context.get_user_input()

        logger.info(f"--- AGENT_EXECUTOR: Final query for agent: '{query}' ---")

        # TODO: Integrate with ADK agent runner
        # For now, we'll send the query directly and get a simulated response
        # In production, this would run through the ADK agent execution
        
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        # Simulate agent response - in production this would call the actual agent
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("Processing your request...", task.context_id, task.id),
        )

        # Simulate final response with A2UI JSON
        content = f"Calendar agent received: {query}"
        final_state = (
            TaskState.completed
            if action == "SUBMIT_BOOKING"
            else TaskState.input_required
        )

        final_parts = []
        if "---a2ui_JSON---" in content:
            logger.info("Splitting final response into text and UI parts.")
            text_content, json_string = content.split("---a2ui_JSON---", 1)

            if text_content.strip():
                final_parts.append(Part(root=TextPart(text=text_content.strip())))

            if json_string.strip():
                try:
                    json_string_cleaned = (
                        json_string.strip().lstrip("```json").rstrip("```").strip()
                    )
                    json_data = json.loads(json_string_cleaned)

                    if isinstance(json_data, list):
                        logger.info(
                            f"Found {len(json_data)} messages. Creating individual DataParts."
                        )
                        for message in json_data:
                            final_parts.append(create_a2ui_part(message))
                    else:
                        logger.info(
                            "Received a single JSON object. Creating a DataPart."
                        )
                        final_parts.append(create_a2ui_part(json_data))

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse UI JSON: {e}")
                    final_parts.append(Part(root=TextPart(text=json_string)))
        else:
            final_parts.append(Part(root=TextPart(text=content.strip())))

        logger.info("--- FINAL PARTS TO BE SENT ---")
        for i, part in enumerate(final_parts):
            logger.info(f"  - Part {i}: Type = {type(part.root)}")
            if isinstance(part.root, TextPart):
                logger.info(f"    - Text: {part.root.text[:200]}...")
            elif isinstance(part.root, DataPart):
                logger.info(f"    - Data: {str(part.root.data)[:200]}...")
        logger.info("-----------------------------")

        await updater.update_status(
            final_state,
            new_agent_parts_message(final_parts, task.context_id, task.id),
            final=(final_state == TaskState.completed),
        )

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
