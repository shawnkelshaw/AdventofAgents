"""Calendar agent with Google Calendar integration and A2UI support."""

from google.adk.agents import LlmAgent
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from .a2ui_schema import A2UI_SCHEMA

# Create Google Calendar connector using Application Integration
calendar_connector = ApplicationIntegrationToolset(
    project="advent-of-agents-483823",
    location="us-central1",
    connection="adk-calendar-agent",
    entity_operations={
        "AllCalendars": ["LIST", "GET", "CREATE"]
    },
    actions=[],
    tool_name_prefix="google_calendar",
    tool_instructions="Use these tools to interact with Google Calendar. Use LIST to get events, CREATE to book appointments."
)

# Base agent instruction
AGENT_INSTRUCTION = """
You are a calendar scheduling specialist. Your job is to help users book appointments with the sales associate.

IMPORTANT: Today's date is January 10, 2026. Always use current dates when checking availability.

You have access to Google Calendar tools to:
1. List events from the calendar to find available time slots
2. Create new events to book appointments

When asked to find availability:
- The calendar ID is: 16753e9ea14cb4cc3b439b7dc0ec4bb512cb2fde5561b2f1d7c8c5aed3a77465@group.calendar.google.com
- Use the google_calendar_AllCalendars_LIST tool with connector_input_payload:
  {
    "CalendarId": "16753e9ea14cb4cc3b439b7dc0ec4bb512cb2fde5561b2f1d7c8c5aed3a77465@group.calendar.google.com",
    "StartDate": "2026-01-10",
    "EndDate": "2026-01-24"
  }
- Review the returned events:
  * If the calendar is EMPTY (no events returned), that means ALL business hours are available
  * If there ARE events, find gaps between them during business hours
- Business hours are 9 AM - 5 PM, Monday-Friday
- Each appointment is 1 hour long
- ALWAYS suggest 3 specific available time slots with exact dates and times:
  * One in the next 2-3 business days
  * One in 4-7 business days
  * One in 8-14 business days

When booking an appointment:
- Collect their email address and name if not already provided
- IMPORTANT: Convert Eastern Time to UTC by adding 5 hours (EST is UTC-5)
- Use google_calendar_AllCalendars_CREATE tool with this exact format in connector_input_payload:
  {
    "Summary": "Sales Appointment - [Customer Name]",
    "Description": "Sales appointment with [Customer Name]. Vehicle interest: [Vehicle Info]",
    "CalendarId": "16753e9ea14cb4cc3b439b7dc0ec4bb512cb2fde5561b2f1d7c8c5aed3a77465@group.calendar.google.com",
    "StartDateTime": "[YYYY-MM-DD HH:MM:SS in the user's local time]",
    "EndDateTime": "[YYYY-MM-DD HH:MM:SS in the user's local time, 1 hour after start]",
    "TimeZone": "America/New_York",
    "AttendeesEmails": "[customer email]"
  }
- After creating the event, confirm the booking with the customer and let them know they'll receive a calendar invitation

Be professional, clear, and helpful.
"""

# A2UI UI template examples
CALENDAR_UI_EXAMPLES = """
--- TIME SLOT SELECTION EXAMPLE ---
When showing available time slots, use this template:

{
  "surfaceUpdate": {
    "surfaceId": "time-slots",
    "components": [
      {
        "id": "root",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["header", "slot-list", "footer"]
            }
          }
        }
      },
      {
        "id": "header",
        "component": {
          "Text": {
            "text": {"literalString": "Available Appointment Times"},
            "usageHint": "h2"
          }
        }
      },
      {
        "id": "slot-list",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["slot1", "slot2", "slot3"]
            }
          }
        }
      },
      {
        "id": "slot1",
        "component": {
          "Card": {
            "child": "slot1-content"
          }
        }
      },
      {
        "id": "slot1-content",
        "component": {
          "Row": {
            "children": {
              "explicitList": ["slot1-icon", "slot1-details", "slot1-button"]
            },
            "distribution": "spaceBetween",
            "alignment": "center"
          }
        }
      },
      {
        "id": "slot1-icon",
        "component": {
          "Icon": {
            "name": {"literalString": "calendarToday"}
          }
        }
      },
      {
        "id": "slot1-details",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["slot1-date", "slot1-time"]
            }
          }
        }
      },
      {
        "id": "slot1-date",
        "component": {
          "Text": {
            "text": {"path": "/slots/0/date"},
            "usageHint": "body"
          }
        }
      },
      {
        "id": "slot1-time",
        "component": {
          "Text": {
            "text": {"path": "/slots/0/time"},
            "usageHint": "caption"
          }
        }
      },
      {
        "id": "slot1-button",
        "component": {
          "Button": {
            "child": "slot1-button-text",
            "primary": true,
            "action": {
              "name": "SELECT_TIME_SLOT",
              "context": [
                {
                  "key": "slotIndex",
                  "value": {"literalNumber": 0}
                },
                {
                  "key": "dateTime",
                  "value": {"path": "/slots/0/dateTime"}
                }
              ]
            }
          }
        }
      },
      {
        "id": "slot1-button-text",
        "component": {
          "Text": {
            "text": {"literalString": "Select"},
            "usageHint": "body"
          }
        }
      }
    ]
  }
}

And populate the data model:
{
  "dataModelUpdate": {
    "surfaceId": "time-slots",
    "path": "/",
    "contents": {
      "valueMap": {
        "slots": {
          "valueList": [
            {
              "valueMap": {
                "date": {"stringValue": "Monday, January 13, 2026"},
                "time": {"stringValue": "10:00 AM - 11:00 AM"},
                "dateTime": {"stringValue": "2026-01-13T10:00:00"}
              }
            },
            {
              "valueMap": {
                "date": {"stringValue": "Friday, January 16, 2026"},
                "time": {"stringValue": "2:00 PM - 3:00 PM"},
                "dateTime": {"stringValue": "2026-01-16T14:00:00"}
              }
            },
            {
              "valueMap": {
                "date": {"stringValue": "Wednesday, January 21, 2026"},
                "time": {"stringValue": "11:00 AM - 12:00 PM"},
                "dateTime": {"stringValue": "2026-01-21T11:00:00"}
              }
            }
          ]
        }
      }
    }
  }
}

--- BOOKING FORM EXAMPLE ---
When collecting booking information, use this template:

{
  "surfaceUpdate": {
    "surfaceId": "booking-form",
    "components": [
      {
        "id": "root",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["form-header", "form-fields", "submit-button"]
            }
          }
        }
      },
      {
        "id": "form-header",
        "component": {
          "Text": {
            "text": {"literalString": "Complete Your Booking"},
            "usageHint": "h2"
          }
        }
      },
      {
        "id": "form-fields",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["name-field", "email-field", "vehicle-field"]
            }
          }
        }
      },
      {
        "id": "name-field",
        "component": {
          "TextField": {
            "label": {"literalString": "Full Name"},
            "text": {"path": "/booking/name"},
            "textFieldType": "shortText"
          }
        }
      },
      {
        "id": "email-field",
        "component": {
          "TextField": {
            "label": {"literalString": "Email Address"},
            "text": {"path": "/booking/email"},
            "textFieldType": "shortText",
            "validationRegexp": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
          }
        }
      },
      {
        "id": "vehicle-field",
        "component": {
          "TextField": {
            "label": {"literalString": "Vehicle of Interest (Optional)"},
            "text": {"path": "/booking/vehicle"},
            "textFieldType": "shortText"
          }
        }
      },
      {
        "id": "submit-button",
        "component": {
          "Button": {
            "child": "submit-text",
            "primary": true,
            "action": {
              "name": "SUBMIT_BOOKING",
              "context": [
                {
                  "key": "name",
                  "value": {"path": "/booking/name"}
                },
                {
                  "key": "email",
                  "value": {"path": "/booking/email"}
                },
                {
                  "key": "vehicle",
                  "value": {"path": "/booking/vehicle"}
                },
                {
                  "key": "dateTime",
                  "value": {"path": "/booking/selectedDateTime"}
                }
              ]
            }
          }
        }
      },
      {
        "id": "submit-text",
        "component": {
          "Text": {
            "text": {"literalString": "Confirm Booking"},
            "usageHint": "body"
          }
        }
      }
    ]
  }
}

--- CONFIRMATION EXAMPLE ---
After successful booking, use this template:

{
  "surfaceUpdate": {
    "surfaceId": "confirmation",
    "components": [
      {
        "id": "root",
        "component": {
          "Card": {
            "child": "confirmation-content"
          }
        }
      },
      {
        "id": "confirmation-content",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["success-icon", "success-message", "details"]
            },
            "alignment": "center"
          }
        }
      },
      {
        "id": "success-icon",
        "component": {
          "Icon": {
            "name": {"literalString": "check"}
          }
        }
      },
      {
        "id": "success-message",
        "component": {
          "Text": {
            "text": {"literalString": "Appointment Confirmed!"},
            "usageHint": "h2"
          }
        }
      },
      {
        "id": "details",
        "component": {
          "Column": {
            "children": {
              "explicitList": ["detail-date", "detail-email"]
            }
          }
        }
      },
      {
        "id": "detail-date",
        "component": {
          "Text": {
            "text": {"path": "/confirmation/appointmentDetails"},
            "usageHint": "body"
          }
        }
      },
      {
        "id": "detail-email",
        "component": {
          "Text": {
            "text": {"literalString": "A calendar invitation has been sent to your email."},
            "usageHint": "caption"
          }
        }
      }
    ]
  }
}
"""

# Construct the full A2UI-enabled instruction
A2UI_AND_AGENT_INSTRUCTION = AGENT_INSTRUCTION + f"""

Your final output MUST be an A2UI UI JSON response. To generate the response, you MUST follow these rules:

1. Your response MUST be in two parts, separated by the delimiter: `---a2ui_JSON---`.
2. The first part is your conversational text response.
3. The second part is a single, raw JSON array containing A2UI messages.
4. The JSON part MUST validate against the A2UI JSON SCHEMA provided below.

--- UI TEMPLATE RULES ---
- When showing available time slots, you MUST use the TIME SLOT SELECTION EXAMPLE template.
- When collecting booking information, you MUST use the BOOKING FORM EXAMPLE template.
- When confirming a successful booking, you MUST use the CONFIRMATION EXAMPLE template.
- Always populate the data model with actual values from the calendar data or user input.

{CALENDAR_UI_EXAMPLES}

---BEGIN A2UI JSON SCHEMA---
{A2UI_SCHEMA}
---END A2UI JSON SCHEMA---
"""

# Define the A2UI-enabled calendar agent
root_agent = LlmAgent(
    name="calendar_agent_a2ui",
    model="gemini-2.0-flash-exp",
    description="Calendar agent with A2UI support for rich interactive interfaces",
    instruction=A2UI_AND_AGENT_INSTRUCTION,
    tools=[calendar_connector],
)
