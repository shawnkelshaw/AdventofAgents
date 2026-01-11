"""Simplified calendar agent for A2UI demonstration."""

import json
from typing import AsyncIterator, Dict

SUPPORTED_CONTENT_TYPES = ["text/plain"]

# Sample time slots for demonstration
SAMPLE_TIME_SLOTS = [
    {"date": "2026-01-15", "time": "10:00 AM", "dateTime": "2026-01-15T10:00:00"},
    {"date": "2026-01-16", "time": "2:00 PM", "dateTime": "2026-01-16T14:00:00"},
    {"date": "2026-01-17", "time": "11:00 AM", "dateTime": "2026-01-17T11:00:00"},
]


def get_time_slot_ui():
    """Generate A2UI JSON for time slot selection."""
    return {
        "surfaceUpdate": {
            "surfaceId": "time-slots",
            "components": [
                {
                    "type": "Text",
                    "text": "Available Appointment Times",
                    "style": {"fontSize": "large", "fontWeight": "bold"}
                },
                {
                    "type": "List",
                    "items": [
                        {
                            "type": "Card",
                            "components": [
                                {
                                    "type": "Row",
                                    "components": [
                                        {
                                            "type": "Column",
                                            "components": [
                                                {"type": "Text", "text": slot["date"], "style": {"fontWeight": "bold"}},
                                                {"type": "Text", "text": slot["time"]}
                                            ]
                                        },
                                        {
                                            "type": "Button",
                                            "text": "Select",
                                            "action": {
                                                "actionName": "SELECT_TIME_SLOT",
                                                "context": {"slotIndex": i, "dateTime": slot["dateTime"]}
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                        for i, slot in enumerate(SAMPLE_TIME_SLOTS)
                    ]
                }
            ]
        }
    }


def get_booking_form_ui(selected_time):
    """Generate A2UI JSON for booking form."""
    return {
        "surfaceUpdate": {
            "surfaceId": "booking-form",
            "components": [
                {"type": "Text", "text": "Complete Your Booking", "style": {"fontSize": "large", "fontWeight": "bold"}},
                {"type": "Text", "text": f"Selected: {selected_time['date']} at {selected_time['time']}"},
                {"type": "TextField", "label": "Name", "id": "name", "required": True},
                {"type": "TextField", "label": "Email", "id": "email", "required": True},
                {
                    "type": "Button",
                    "text": "Book Appointment",
                    "action": {
                        "actionName": "SUBMIT_BOOKING",
                        "context": {
                            "name": "{{name}}",
                            "email": "{{email}}",
                            "dateTime": selected_time["dateTime"]
                        }
                    }
                }
            ]
        }
    }


class CalendarAgent:
    """Simplified Calendar Agent for A2UI demonstration."""
    
    SUPPORTED_CONTENT_TYPES = SUPPORTED_CONTENT_TYPES
    
    def __init__(self, base_url: str, use_ui: bool = True):
        self.base_url = base_url
        self.use_ui = use_ui
        self.selected_time = None
    
    async def stream(self, query: str, context_id: str) -> AsyncIterator[Dict]:
        """Stream responses from the agent."""
        
        # Determine what stage we're at based on the query
        if "available" in query.lower() or "schedule" in query.lower() or "appointment" in query.lower():
            # Show time slots
            if self.use_ui:
                content = "Here are the available appointment times:\n\n---a2ui_JSON---\n" + json.dumps([get_time_slot_ui()])
            else:
                content = "Here are the available times:\n" + "\n".join(
                    f"- {slot['date']} at {slot['time']}" for slot in SAMPLE_TIME_SLOTS
                )
            
            yield {"is_task_complete": False, "updates": "Finding available times..."}
            yield {"is_task_complete": True, "content": content}
            
        elif "book" in query.lower() and ("at" in query.lower() or "2026" in query):
            # Extract selected time
            for slot in SAMPLE_TIME_SLOTS:
                if slot["dateTime"] in query:
                    self.selected_time = slot
                    break
            
            if self.use_ui and self.selected_time:
                # Show booking form
                content = f"Great! Please provide your details:\n\n---a2ui_JSON---\n" + json.dumps([get_booking_form_ui(self.selected_time)])
            else:
                content = "Please provide your name and email to complete the booking."
            
            yield {"is_task_complete": False, "updates": "Preparing booking form..."}
            yield {"is_task_complete": True, "content": content}
            
        elif "Please book" in query or "SUBMIT_BOOKING" in query:
            # Booking confirmation
            content = "✅ Your appointment has been booked successfully! You'll receive a confirmation email shortly."
            yield {"is_task_complete": True, "content": content}
            
        else:
            # Default response
            content = "I can help you schedule an appointment. Would you like to see available times?"
            yield {"is_task_complete": True, "content": content}


# Create a default agent instance
root_agent = CalendarAgent(base_url="http://localhost:10003", use_ui=True)
