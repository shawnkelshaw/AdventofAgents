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

- **`calendar_agent/agent.py`**: A2UI-enabled calendar agent with Google Calendar integration
- **`calendar_agent/a2ui_schema.py`**: A2UI JSON schema definition
- **`vehicle_intake_agent/agent.py`**: A2UI-enabled vehicle intake form
- **`orchestrator_agent/a2a_server.py`**: A2A server with A2UI message parsing

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

A2UI uses path-based data binding with a **flat structure** (array indexing like `/slots/0/date` does NOT work):

```json
{
  "component": {
    "Text": {
      "text": {"path": "/slot1/display"}
    }
  }
}
```

The data model uses `contents` array with `key`/`valueMap` pairs:

```json
{
  "dataModelUpdate": {
    "surfaceId": "calendar",
    "contents": [
      {"key": "slot1", "valueMap": [
        {"key": "display", "valueString": "Mon Jan 13 at 10:00 AM"},
        {"key": "dateTime", "valueString": "2026-01-13T10:00:00"}
      ]},
      {"key": "slot2", "valueMap": [
        {"key": "display", "valueString": "Thu Jan 16 at 2:00 PM"},
        {"key": "dateTime", "valueString": "2026-01-16T14:00:00"}
      ]}
    ]
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

## Milestone 3: A2A Protocol Integration ✅

### Completed Implementation

The A2A protocol integration is now complete with the following components:

#### Orchestrator A2A Server
- **File**: `orchestrator_agent/server.py` - Main A2A server entry point
- **File**: `orchestrator_agent/a2a_server.py` - Custom `OrchestratorAgentExecutor` class
- **Port**: 10010
- **Features**:
  - Custom executor that parses `---a2ui_JSON---` delimiter from agent responses
  - Converts A2UI JSON to A2A DataParts for client rendering
  - Handles A2UI user actions (button clicks, form submissions)
  - CORS middleware for client connectivity

#### A2UI Shell Client Configuration
- **File**: `A2UI/samples/client/lit/shell/configs/orchestrator.ts`
- **URL**: http://localhost:5173/?app=orchestrator
- **Features**:
  - Connects to orchestrator A2A server
  - Renders A2UI surfaces (forms, cards, buttons)
  - Sends user actions back to server

### Running the Demo

```bash
cd A2UI/samples/client/lit
npm run demo:vehicle
```

This starts both:
- A2UI Shell Client at http://localhost:5173
- Orchestrator A2A Server at http://localhost:10010

### What's Working

1. **Form Rendering**: Vehicle intake form displays with Year, Make, Model, Mileage fields
2. **Form Value Binding**: User-entered values are captured and passed to the agent via action context
3. **Button Actions**: Submit button triggers action with form data
4. **Estimate Card**: Agent generates trade-in estimate card with valuation ($12k-$17k for 2020 Toyota Camry)
5. **A2UI Extension**: Client correctly requests and activates A2UI extension
6. **Multi-Agent Workflow**: Orchestrator delegates to vehicle_intake_agent which generates A2UI

### Key Implementation Details

1. **TextField Binding**: Use `text` property (not `value`) for data binding:
   ```json
   {"TextField": {"label": {"literalString": "Year"}, "text": {"path": "/vehicle/year"}}}
   ```

2. **Action Context**: Button actions include context with paths to form values:
   ```json
   {"action": {"name": "submit_vehicle_info", "context": [{"key": "year", "value": {"path": "/vehicle/year"}}]}}
   ```

3. **Data Model Initialization**: Initialize data model with empty values:
   ```json
   {"dataModelUpdate": {"surfaceId": "vehicle_form", "contents": [{"key": "vehicle", "valueMap": [...]}]}}
   ```

### Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  A2UI Shell     │────▶│  Orchestrator A2A    │────▶│  Gemini API     │
│  (Lit Client)   │     │  Server (Python)     │     │  (LLM)          │
│  localhost:5173 │◀────│  localhost:10010     │◀────│                 │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                        │
        │                        ▼
        │               ┌──────────────────────┐
        │               │  Sub-Agents          │
        │               │  - vehicle_intake    │
        │               │  - calendar_agent    │
        │               └──────────────────────┘
        │
        ▼
┌─────────────────┐
│  Rendered UI    │
│  - Forms        │
│  - Cards        │
│  - Buttons      │
└─────────────────┘
```

## Completed Features

1. ✅ A2UI JSON generation working
2. ✅ A2A protocol wrapper implemented
3. ✅ A2UI shell client configured
4. ✅ Interactive UI rendering tested
5. ✅ Form value data binding fixed (TextField text property)
6. ✅ Complete vehicle trade-in workflow with estimate card
7. ✅ Calendar agent A2UI templates (time slots, booking form, confirmation)
8. ✅ Google Calendar integration (list available slots, create events)
9. ✅ Email invitations sent to customers
10. ✅ Timezone handling (Eastern → UTC conversion)

## Known Issues & Solutions

| Issue | Solution |
|-------|----------|
| Array indexing paths don't work | Use flat structure: `/slot1/display` not `/slots/0/display` |
| TimeZone field causes API errors | Omit TimeZone, convert times to UTC manually |
| Markdown code blocks in JSON | Never wrap A2UI JSON in \`\`\`json blocks |
| Orchestrator refuses requests | Simplified instructions: always delegate, never refuse |

---

**Status**: A2A/A2UI integration complete and fully functional  
**Last Updated**: January 11, 2026  
**Version**: 0.8 (Public Preview)
