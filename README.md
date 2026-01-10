# Advent of Agents - Vehicle Trade-In Multi-Agent System

A multi-agent workflow system built with Google ADK for managing vehicle trade-in appointments.

## Overview

This project implements a multi-agent system that coordinates vehicle information intake, calendar scheduling, and appointment booking using Google's Agent Development Kit (ADK).

## Agents

### 1. Calendar Agent ✅ COMPLETE
- **Status**: Fully functional
- **Features**:
  - Google Calendar integration via Integration Connectors
  - OAuth2 authentication
  - Lists available appointment slots
  - Creates calendar events with proper timezone handling
  - Sends email invitations to customers
- **Location**: `calendar_agent/`

### 2. Vehicle Intake Agent 🚧 IN PROGRESS
- **Status**: Basic implementation
- **Location**: `vehicle_intake_agent/`

### 3. Orchestrator Agent 🚧 IN PROGRESS
- **Status**: Basic implementation
- **Location**: `orchestrator_agent/`

## Setup

### Prerequisites
- Python 3.10+
- Google Cloud Project with:
  - Calendar API enabled
  - Integration Connectors API enabled
  - Application Integration API enabled
- OAuth 2.0 credentials (Web application type)

### Installation

1. Install Google ADK:
```bash
pip install google-adk
```

2. Configure environment variables in each agent's `.env` file:
```
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
```

3. Set up Google Calendar connection in Integration Connectors:
   - Create OAuth 2.0 Web application credentials
   - Create Integration Connector connection for Google Calendar
   - Authorize the connection

### Running the Server

```bash
cd /path/to/AdventofAgents
uvx --from google-adk adk web
```

Access the web UI at: http://127.0.0.1:8000

## Project Structure

```
AdventofAgents/
├── calendar_agent/
│   ├── agent.py              # Calendar agent implementation
│   ├── .env                  # Environment configuration
│   └── __init__.py
├── vehicle_intake_agent/
│   ├── root_agent.yaml       # Vehicle intake configuration
│   ├── .env
│   └── __init__.py
├── orchestrator_agent/
│   ├── root_agent.yaml       # Orchestrator configuration
│   ├── .env
│   └── __init__.py
└── README.md
```

## Milestones

### Milestone 1: Calendar Agent Integration ✅
- [x] Set up Google Calendar OAuth2 connection
- [x] Implement Integration Connectors entity operations
- [x] List available appointment slots
- [x] Create calendar events
- [x] Send email invitations
- [x] Fix timezone handling

### Milestone 2: Multi-Agent Orchestration 🚧
- [ ] Implement vehicle intake agent
- [ ] Implement orchestrator agent
- [ ] Test agent handoffs
- [ ] End-to-end workflow testing

## Technical Details

### Calendar Agent Implementation
- Uses `ApplicationIntegrationToolset` with entity operations
- Entity: `AllCalendars` with `LIST` and `CREATE` operations
- Timezone: `America/New_York` (configurable)
- Datetime format: `YYYY-MM-DD HH:MM:SS`

### Key Learnings
1. Integration Connectors use simplified field names (capitalized)
2. Entity operations are preferred over raw REST API actions
3. `TimeZone` field is required for proper timezone handling
4. OAuth 2.0 Web application credentials needed (not Desktop)

## License

MIT

## Contact

For questions or issues, please open a GitHub issue.
