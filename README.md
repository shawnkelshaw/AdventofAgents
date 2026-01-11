# Advent of Agents - Vehicle Trade-In Multi-Agent System

A multi-agent workflow system built with Google ADK for managing vehicle trade-in appointments.

## Overview

This project implements a multi-agent system that coordinates vehicle information intake, calendar scheduling, and appointment booking using Google's Agent Development Kit (ADK).

## Agents

### 1. Calendar Agent ✅ COMPLETE + A2UI ENABLED
- **Status**: Fully functional with A2UI support
- **Features**:
  - Google Calendar integration via Integration Connectors
  - OAuth2 authentication
  - Lists available appointment slots
  - Creates calendar events with proper timezone handling
  - Sends email invitations to customers
  - **A2UI support**: Generates rich interactive UI components (time slot cards, booking forms, confirmation screens)
- **Location**: `calendar_agent/`
- **Documentation**: See `docs/A2UI_INTEGRATION.md`

### 2. Vehicle Intake Agent ✅ COMPLETE + A2UI ENABLED
- **Status**: Fully functional with A2UI support
- **Features**:
  - Interactive A2UI form for vehicle information collection
  - Collects: year, make, model, mileage, condition via form
  - Provides trade-in value estimates with A2UI card display
  - Form data binding with path-based values
  - Schedule Appraisal button for next step
- **Location**: `vehicle_intake_agent/`
- **Documentation**: See `docs/A2UI_INTEGRATION.md`

### 3. Orchestrator Agent ✅ COMPLETE + A2A SERVER
- **Status**: Fully functional with A2A protocol support
- **Features**:
  - A2A server running at `http://localhost:10010`
  - Custom executor for A2UI message parsing
  - Handles A2UI user actions (button clicks, form submissions)
  - Coordinates complete vehicle trade-in workflow
  - LLM Transfer pattern for dynamic routing
  - Delegates to vehicle intake and calendar agents
- **Location**: `orchestrator_agent/`
- **Documentation**: See `docs/A2UI_INTEGRATION.md`

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ (for A2UI client)
- Google Cloud Project with:
  - Integration Connectors API enabled
  - Application Integration API enabled
  - A configured Google Calendar connection
- Gemini API key OR Google Cloud credentials

### Installation

1. Install Google ADK:
```bash
pip install google-adk
```

2. Configure environment variables in each agent's `.env` file:
```
GEMINI_API_KEY=your-gemini-api-key
```

3. Authenticate with Google Cloud (for Integration Connectors):
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project your-project-id
gcloud auth application-default set-quota-project your-project-id
```

4. Install A2UI client dependencies:
```bash
cd A2UI/samples/client/lit
npm install
```

### Running the Demo

Start the full demo (A2UI client + orchestrator server):
```bash
cd A2UI/samples/client/lit
npm run demo:vehicle
```

Access the UI at: http://localhost:5173/?app=orchestrator (port may vary)

## Project Structure

```
AdventofAgents/
├── calendar_agent/
│   ├── agent.py              # Calendar agent with A2UI + Google Calendar
│   ├── a2ui_schema.py        # A2UI JSON schema
│   ├── agent_executor.py     # Custom executor for A2UI parsing
│   └── .env                  # GEMINI_API_KEY
├── vehicle_intake_agent/
│   ├── agent.py              # Vehicle intake agent with A2UI forms
│   ├── a2ui_schema.py        # A2UI JSON schema
│   └── .env                  # GEMINI_API_KEY
├── orchestrator_agent/
│   ├── agent.py              # Orchestrator with sub-agent delegation
│   ├── a2a_server.py         # A2A protocol server
│   ├── server.py             # Main server entry point
│   └── .env                  # GEMINI_API_KEY
├── A2UI/                     # A2UI client renderer (Lit-based)
├── docs/                     # Documentation
└── README.md
```

## Milestones

### Milestone 1: Calendar Agent Integration ✅ CLOSED
- [x] Set up Google Calendar OAuth2 connection
- [x] Implement Integration Connectors entity operations
- [x] List available appointment slots
- [x] Create calendar events
- [x] Send email invitations
- [x] Fix timezone handling

### Milestone 1.5: A2UI Integration ✅ CLOSED
- [x] Integrate A2UI schema and format
- [x] Create time slot selection UI template
- [x] Create booking form UI template
- [x] Create confirmation UI template
- [x] Test A2UI JSON generation
- [x] Document A2UI integration

### Milestone 2: Multi-Agent Orchestration ✅ CLOSED
- [x] Implement vehicle intake agent
- [x] Implement orchestrator agent with LLM Transfer pattern
- [x] Test agent handoffs and state management
- [x] End-to-end workflow testing
- [x] Document multi-agent orchestration

### Milestone 3: A2A Protocol Integration ✅ CLOSED
- [x] Install A2A SDK dependencies
- [x] Create A2A server for orchestrator agent
- [x] Implement custom agent executor with A2UI parsing
- [x] Configure A2UI shell client connection
- [x] Test full interactive UI rendering
- [x] Fix form value binding (TextField text property)
- [x] Complete vehicle trade-in workflow with estimate card
- [x] Document A2A/A2UI integration

## Technical Details

### Calendar Agent Implementation
- Uses `ApplicationIntegrationToolset` with entity operations
- Entity: `AllCalendars` with `LIST` and `CREATE` operations
- Timezone: `America/New_York` (configurable)
- Datetime format: `YYYY-MM-DD HH:MM:SS`

### A2UI Integration
- Agents generate declarative JSON UI descriptions
- Vehicle intake: form with Year/Make/Model/Mileage fields, estimate card
- Calendar: time slot selection, booking form, confirmation
- Data binding with path references (e.g., `/vehicle/year`)
- Action handlers for button clicks and form submissions
- Framework-agnostic format works across web, mobile, Flutter, React
- See `docs/A2UI_INTEGRATION.md` for details

### Running the A2UI Demo
```bash
cd A2UI/samples/client/lit
npm run demo:vehicle
```
Open http://localhost:5173/?app=orchestrator (port may vary)

### Key Learnings
1. Integration Connectors use simplified field names (capitalized)
2. Entity operations are preferred over raw REST API actions
3. Times must be converted to UTC (Eastern + 5 hours) - TimeZone field causes errors
4. A2UI data model uses flat structure with path references (e.g., `/slot1/display`)
5. A2UI JSON must not be wrapped in markdown code blocks
6. Orchestrator should always delegate, never refuse requests

## License

MIT

## Contact

For questions or issues, please open a GitHub issue.
