# Multi-Agent Orchestration Guide

## Overview

The vehicle trade-in system uses a multi-agent architecture where specialized agents handle specific tasks, coordinated by an orchestrator agent.

## Architecture

### Agent Hierarchy

```
orchestrator_agent (Coordinator)
├── vehicle_intake_agent (Specialist)
└── calendar_agent (Specialist)
```

### Communication Pattern

**LLM Transfer Pattern**: The orchestrator uses ADK's `transfer_to_agent()` function to dynamically route conversations to specialized agents based on workflow stage.

## Agents

### 1. Orchestrator Agent

**File**: `orchestrator_agent/agent.py`

**Role**: Coordinator and workflow manager

**Responsibilities**:
- Greet the user and explain the process
- Delegate to vehicle_intake_agent for vehicle information collection
- Delegate to calendar_agent for appointment scheduling
- Wrap up and provide final instructions

**Key Configuration**:
```python
root_agent = LlmAgent(
    name="orchestrator_agent",
    model="gemini-2.0-flash-exp",
    description="Coordinates the vehicle trade-in workflow",
    instruction="...",  # Workflow instructions
    sub_agents=[vehicle_intake_agent, calendar_agent]
)
```

**Important**: The orchestrator does NOT collect data itself - it only coordinates and delegates.

### 2. Vehicle Intake Agent

**File**: `vehicle_intake_agent/agent.py`

**Role**: Vehicle information specialist

**Responsibilities**:
- Collect vehicle details conversationally:
  - Year, Make, Model, Trim
  - Mileage, Color, Condition
  - Notable features or issues
- Provide trade-in value estimate
- Store information in `state['vehicle_info']`
- Signal completion

**Key Configuration**:
```python
root_agent = LlmAgent(
    name="vehicle_intake_agent",
    model="gemini-2.0-flash-exp",
    description="Collects vehicle information for trade-in evaluation",
    instruction="...",  # Collection instructions
    output_key="vehicle_info"
)
```

### 3. Calendar Agent

**File**: `calendar_agent/agent.py`

**Role**: Appointment scheduling specialist

**Responsibilities**:
- Query Google Calendar for available slots
- Present 3 time slot options (with A2UI formatting)
- Collect customer name and email
- Book appointment with proper timezone handling
- Send calendar invitation

**Key Features**:
- Google Calendar Integration via Integration Connectors
- A2UI support for rich interactive UI
- OAuth2 authentication
- Timezone handling (America/New_York)

## Workflow

### Complete User Journey

```
1. User: "I want to trade in my vehicle"
   ↓
2. Orchestrator: Greets, explains process
   ↓
3. Orchestrator: transfer_to_agent('vehicle_intake_agent')
   ↓
4. Vehicle Intake: Collects vehicle information
   - Year, make, model, trim, mileage, color, condition
   - Provides trade-in estimate
   - Saves to state['vehicle_info']
   ↓
5. Orchestrator: Acknowledges estimate
   ↓
6. Orchestrator: transfer_to_agent('calendar_agent')
   ↓
7. Calendar Agent: Shows available time slots
   - Queries Google Calendar
   - Presents 3 options (A2UI format)
   ↓
8. User: Selects time slot
   ↓
9. Calendar Agent: Collects name and email
   ↓
10. Calendar Agent: Books appointment
    - Creates calendar event
    - Sends email invitation
    ↓
11. Orchestrator: Confirms booking, provides final instructions
```

## State Management

### Shared State

Agents share state through the `InvocationContext`:

```python
# Vehicle intake agent stores data
output_key="vehicle_info"
# Data available in state['vehicle_info']

# Other agents can reference this data
instruction="Use the vehicle info from {vehicle_info}..."
```

### State Flow

```
orchestrator_agent (initial state)
    ↓
vehicle_intake_agent (adds vehicle_info to state)
    ↓
orchestrator_agent (reads vehicle_info from state)
    ↓
calendar_agent (can access vehicle_info from state)
    ↓
orchestrator_agent (final state with all data)
```

## Implementation Details

### LLM Transfer Pattern

The orchestrator uses the LLM Transfer pattern where the LLM decides when to delegate:

```python
# Orchestrator instruction includes:
"Use transfer_to_agent(agent_name='vehicle_intake_agent') to delegate"

# The LLM generates:
FunctionCall(
    name='transfer_to_agent',
    args={'agent_name': 'vehicle_intake_agent'}
)

# ADK framework routes execution to the sub-agent
```

### Agent Registration

Sub-agents are registered with the orchestrator:

```python
from vehicle_intake_agent.agent import root_agent as vehicle_intake_agent
from calendar_agent.agent import root_agent as calendar_agent

root_agent = LlmAgent(
    name="orchestrator_agent",
    # ...
    sub_agents=[vehicle_intake_agent, calendar_agent]
)
```

### Delegation vs. Data Collection

**Orchestrator Role**:
- ✅ Greet and explain
- ✅ Delegate to specialists
- ✅ Acknowledge and transition
- ✅ Wrap up
- ❌ Ask vehicle questions
- ❌ Ask appointment questions
- ❌ Collect data directly

**Specialist Role**:
- ✅ Collect specific data
- ✅ Perform specialized tasks
- ✅ Store results in state
- ✅ Signal completion

## Testing

### Test the Complete Workflow

1. Start ADK server:
   ```bash
   cd /path/to/AdventofAgents
   uvx --from google-adk adk web
   ```

2. Open http://127.0.0.1:8000

3. Select `orchestrator_agent`

4. Start conversation: "I want to trade in my vehicle"

5. Follow the workflow:
   - Provide vehicle details when asked
   - Review trade-in estimate
   - Select appointment time slot
   - Provide name and email
   - Confirm booking

### Expected Behavior

**Successful Workflow**:
- Orchestrator greets once
- Vehicle intake asks vehicle questions (no duplicates)
- Smooth transition to calendar agent
- Calendar agent shows time slots (may show A2UI JSON)
- Appointment booked successfully
- Orchestrator wraps up

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Duplicate questions | Orchestrator collecting data | Ensure orchestrator only delegates |
| No transition | Missing transfer_to_agent call | Check orchestrator instructions |
| Agent not found | Import error | Verify agent imports and paths |
| State not shared | Missing output_key | Add output_key to agents |

## A2UI Integration ✅ COMPLETE

Both the vehicle intake agent and calendar agent generate A2UI JSON for rich UI components.

### Vehicle Intake Agent A2UI
```json
{
  "surfaceUpdate": {
    "surfaceId": "vehicle_form",
    "components": [
      // Year, Make, Model, Mileage text fields
      // Submit button with action context
    ]
  }
}
```

After form submission, generates estimate card:
```json
{
  "surfaceUpdate": {
    "surfaceId": "estimate_card",
    "components": [
      // Trade-In Estimate heading
      // Vehicle summary text
      // Valuation range ($12,000 - $17,000)
      // Schedule Appraisal button
    ]
  }
}
```

### Calendar Agent A2UI
```json
{
  "surfaceUpdate": {
    "surfaceId": "time-slots",
    "components": [
      // Interactive time slot cards
      // Booking form
      // Confirmation screen
    ]
  }
}
```

**Current Status**: A2UI renders as interactive UI via A2A protocol (Milestone 3 complete).

## Best Practices

### Orchestrator Design

1. **Keep it simple**: Orchestrator should only coordinate, not execute
2. **Clear transitions**: Explicitly signal when delegating
3. **No data collection**: Let specialists handle their domains
4. **Maintain context**: Reference previous agent outputs

### Agent Communication

1. **Use output_key**: Store important data in state
2. **Signal completion**: Let orchestrator know when done
3. **Stay focused**: Each agent handles one domain
4. **Be conversational**: Natural language, not robotic

### Error Handling

1. **Graceful degradation**: Handle missing data
2. **Clear messages**: Explain what went wrong
3. **Recovery paths**: Offer alternatives
4. **Logging**: Use ADK logging for debugging

## Troubleshooting

### Check Server Logs

```bash
# Server logs show:
# - Agent loading
# - LLM requests
# - Function calls (transfer_to_agent)
# - State updates
# - Errors
```

### Debug State

Add logging to agent instructions:
```python
instruction="""
...
When you complete, say: "DEBUG: State contains {vehicle_info}"
"""
```

### Test Individual Agents

Test each agent separately before orchestration:
1. Test `vehicle_intake_agent` alone
2. Test `calendar_agent` alone
3. Test `orchestrator_agent` with both

## Completed Milestones

### Milestone 3: A2A Protocol Integration ✅
- Full A2UI rendering with interactive components
- A2A server for orchestrator agent
- Custom executor for A2UI parsing and user action handling
- Form value binding and estimate card generation

## Completed Enhancements

- ✅ Calendar agent integration with A2A workflow
- ✅ Full end-to-end booking flow with Google Calendar
- ✅ Email invitations sent to customers
- ✅ Timezone handling (Eastern → UTC)

## Future Enhancements

- Error recovery and retry logic
- User authentication and personalization
- Multi-language support
- Analytics and tracking
- CRM integration
- Session persistence across page reloads

## Resources

- **ADK Multi-Agent Docs**: https://google.github.io/adk-docs/agents/multi-agents/
- **LLM Transfer Pattern**: Agent-driven routing with `transfer_to_agent()`
- **State Management**: Shared context via `InvocationContext`
- **A2UI Integration**: See `docs/A2UI_INTEGRATION.md`
- **A2A Integration**: See `docs/A2A_INTEGRATION_STATUS.md`

---

**Status**: Multi-agent orchestration complete with A2A/A2UI integration  
**Last Updated**: January 11, 2026  
**Version**: 1.1
