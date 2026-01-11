"""Agent executor for calendar agent with A2UI support."""

import json
import logging
from typing import Optional

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import DataPart, Part, TextPart
from a2a.utils import new_agent_text_message
from a2ui.a2ui_extension import create_a2ui_part, try_activate_a2ui_extension

# Import the calendar agent
from calendar_agent.agent import root_agent as calendar_agent

logger = logging.getLogger(__name__)


class CalendarAgentExecutor(AgentExecutor):
    """Calendar Agent Executor with A2UI support."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.agent = calendar_agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the calendar agent and handle A2UI responses."""
        
        logger.info(f"--- Client requested extensions: {context.requested_extensions} ---")
        use_ui = try_activate_a2ui_extension(context)
        
        if use_ui:
            logger.info("--- A2UI extension is active. Will parse and send A2UI messages. ---")
        else:
            logger.info("--- A2UI extension is not active. Using text-only mode. ---")

        # Extract user message
        user_message = ""
        ui_event_part = None
        
        if context.message and context.message.parts:
            logger.info(f"--- Processing {len(context.message.parts)} message parts ---")
            for i, part in enumerate(context.message.parts):
                if isinstance(part.root, DataPart):
                    if "userAction" in part.root.data:
                        logger.info(f"  Part {i}: Found A2UI UI ClientEvent payload.")
                        ui_event_part = part.root.data["userAction"]
                    else:
                        logger.info(f"  Part {i}: DataPart (data: {part.root.data})")
                elif isinstance(part.root, TextPart):
                    user_message += part.root.text
                    logger.info(f"  Part {i}: TextPart (text: {part.root.text})")

        # Handle UI events (button clicks, form submissions)
        if ui_event_part:
            action = ui_event_part.get("actionName")
            ctx = ui_event_part.get("context", {})
            
            logger.info(f"Received A2UI ClientEvent: action={action}, context={ctx}")
            
            if action == "SELECT_TIME_SLOT":
                slot_index = ctx.get("slotIndex")
                date_time = ctx.get("dateTime")
                user_message = f"I'd like to book the appointment at {date_time}"
                logger.info(f"User selected time slot {slot_index}: {date_time}")
                
            elif action == "SUBMIT_BOOKING":
                name = ctx.get("name")
                email = ctx.get("email")
                vehicle = ctx.get("vehicle", "")
                date_time = ctx.get("dateTime")
                user_message = f"Please book the appointment for {name} ({email}) at {date_time}. Vehicle: {vehicle}"
                logger.info(f"User submitted booking: {name}, {email}, {date_time}")

        # Run the calendar agent
        logger.info(f"Running calendar agent with message: {user_message}")
        
        # TODO: Actually run the agent through ADK
        # For now, we'll simulate the agent response
        # In production, you'd integrate with the ADK agent runner
        
        response_text = f"Calendar agent received: {user_message}"
        
        # Check if response contains A2UI JSON
        if use_ui and "---a2ui_JSON---" in response_text:
            parts = response_text.split("---a2ui_JSON---")
            text_part = parts[0].strip()
            json_part = parts[1].strip() if len(parts) > 1 else ""
            
            # Send text message
            if text_part:
                await event_queue.send_message(
                    new_agent_text_message(text_part)
                )
            
            # Parse and send A2UI messages
            if json_part:
                try:
                    a2ui_messages = json.loads(json_part)
                    if isinstance(a2ui_messages, list):
                        for msg in a2ui_messages:
                            a2ui_part = create_a2ui_part(msg)
                            await event_queue.send_message(
                                message=None,
                                parts=[Part(root=a2ui_part)]
                            )
                            logger.info(f"Sent A2UI message: {msg.get('surfaceUpdate', {}).get('surfaceId', 'unknown')}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse A2UI JSON: {e}")
                    await event_queue.send_message(
                        new_agent_text_message(f"Error parsing UI: {str(e)}")
                    )
        else:
            # Send plain text response
            await event_queue.send_message(
                new_agent_text_message(response_text)
            )
