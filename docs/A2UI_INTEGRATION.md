# A2UI Integration Guide

## Overview

The calendar agent has been enhanced with A2UI (Agent-to-User Interface) support, enabling it to generate rich, interactive UI components instead of plain text responses.

## What is A2UI?

A2UI is an open standard that allows agents to "speak UI" by generating declarative JSON descriptions of user interfaces. The client application then renders these using native components (buttons, forms, cards, etc.).

### Key Benefits

- **Security**: Declarative data format, not executable code
- **Framework-agnostic**: Same JSON works across web, mobile, Flutter, React, etc.
- **LLM-friendly**: Easy for models to generate incrementally
- **Interactive**: Rich UI components with actions and data binding

## Implementation

### Files

- **`calendar_agent/agent.py`**: A2UI-enabled calendar agent (formerly `agent_a2ui.py`)
- **`calendar_agent/agent_original.py`**: Original non-A2UI version (backup)
- **`calendar_agent/a2ui_schema.py`**: A2UI JSON schema definition

### UI Components

The calendar agent generates three types of interactive UIs:

#### 1. Time Slot Selection
```json
{
  "surfaceUpdate": {
    "surfaceId": "time-slots",
    "components": [
      // Interactive cards with calendar icons
      // Clickable "Select" buttons for each slot
      // Data-bound date and time displays
    ]
  }
}
```

**Features:**
- Visual cards for each available time slot
- Calendar icons for visual clarity
- Interactive "Select" buttons with action handlers
- Data binding from calendar API results

#### 2. Booking Form
```json
{
  "surfaceUpdate": {
    "surfaceId": "booking-form",
    "components": [
      // Text fields for Name, Email, Vehicle
      // Email validation with regex
      // Submit button with context passing
    ]
  }
}
```

**Features:**
- Structured form with labeled input fields
- Client-side email validation
- Optional vehicle information field
- Submit button that passes collected data

#### 3. Confirmation Card
```json
{
  "surfaceUpdate": {
    "surfaceId": "confirmation",
    "components": [
      // Success icon (checkmark)
      // Confirmation message
      // Appointment details
    ]
  }
}
```

**Features:**
- Visual success indicator
- Appointment details display
- Email notification confirmation

## Testing

### Current Status: JSON Generation ✅

The agent successfully generates A2UI JSON format. To test:

1. Start the ADK server:
   ```bash
   cd /path/to/AdventofAgents
   uvx --from google-adk adk web
   ```

2. Open http://127.0.0.1:8000

3. Select `calendar_agent`

4. Request available appointment times

5. Observe the response contains:
   - Conversational text
   - `---a2ui_JSON---` delimiter
   - A2UI JSON array with UI components

### Example Output Structure

```
I'd be happy to help you schedule an appointment. Here are the available times:

---a2ui_JSON---
[
  {
    "surfaceUpdate": {
      "surfaceId": "time-slots",
      "components": [...]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "time-slots",
      "path": "/",
      "contents": {...}
    }
  }
]
```

## Future Work: A2A Protocol Integration

To get fully rendered interactive UI components, the agent needs to be wrapped with the A2A (Agent-to-Agent) protocol:

### Requirements
- A2A SDK installation
- A2A server wrapper for calendar agent
- Agent executor to handle UI events
- A2UI shell client configuration

### Benefits of Full Integration
- Rendered interactive UI components
- Clickable buttons and forms
- Real-time UI updates
- Event handling (button clicks, form submissions)

### Planned for Milestone 3
See [Milestone 3: A2A Protocol Integration](#milestone-3) for details.

## Technical Details

### Agent Configuration

```python
from .a2ui_schema import A2UI_SCHEMA

A2UI_AND_AGENT_INSTRUCTION = AGENT_INSTRUCTION + f"""
Your final output MUST be an A2UI UI JSON response.

Rules:
1. Response in two parts, separated by: `---a2ui_JSON---`
2. First part: conversational text
3. Second part: JSON array of A2UI messages
4. JSON must validate against A2UI schema

{CALENDAR_UI_EXAMPLES}

---BEGIN A2UI JSON SCHEMA---
{A2UI_SCHEMA}
---END A2UI JSON SCHEMA---
"""
```

### Data Binding

A2UI uses path-based data binding:

```json
{
  "component": {
    "Text": {
      "text": {"path": "/slots/0/date"}
    }
  }
}
```

The data model is populated separately:

```json
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
                "time": {"stringValue": "10:00 AM - 11:00 AM"}
              }
            }
          ]
        }
      }
    }
  }
}
```

### Action Handlers

Buttons trigger named actions with context:

```json
{
  "component": {
    "Button": {
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
}
```

## Resources

- **A2UI Official Website**: https://a2ui.org
- **A2UI GitHub**: https://github.com/google/A2UI
- **A2UI Documentation**: https://a2ui.org/guides/agent-development/
- **A2UI Composer**: https://www.copilotkit.ai/a2ui-composer

## Security Considerations

A2UI is designed with security in mind:

- **Declarative format**: Not executable code
- **Component catalog**: Only pre-approved components can be rendered
- **Data validation**: All JSON validated against schema
- **Sandboxing**: Client controls rendering and security policies

Always treat A2UI payloads as untrusted input and validate appropriately.

## Troubleshooting

### Agent not generating A2UI JSON

**Check:**
- Agent is using `agent.py` (A2UI version)
- A2UI schema is imported correctly
- Agent instructions include A2UI format rules

### JSON validation errors

**Check:**
- Component IDs are unique
- Required fields are present
- Data types match schema
- Paths reference valid data model locations

### UI not rendering (when A2A is implemented)

**Check:**
- A2A server is running
- A2UI extension is activated
- Client supports requested components
- CORS is configured correctly

## Next Steps

1. ✅ A2UI JSON generation working
2. ⏳ Implement A2A protocol wrapper
3. ⏳ Configure A2UI shell client
4. ⏳ Test full interactive UI flow
5. ⏳ Add custom components (if needed)

---

**Status**: A2UI JSON generation complete and tested  
**Last Updated**: January 10, 2026  
**Version**: 0.8 (Public Preview)
