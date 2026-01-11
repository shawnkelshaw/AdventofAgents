"""Orchestrator agent that coordinates the vehicle trade-in workflow."""

from google.adk.agents import LlmAgent

# Import the sub-agents directly - ADK will handle them as sub_agents
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_intake_agent.agent import root_agent as vehicle_intake_agent
from calendar_agent.agent import root_agent as calendar_agent

# Define the orchestrator agent
root_agent = LlmAgent(
    name="orchestrator_agent",
    model="gemini-2.0-flash-exp",
    description="Coordinates the vehicle trade-in workflow across specialized agents",
    instruction="""
You are the orchestrator for vehicle trade-in and appointment scheduling.

YOUR ONLY JOB: Delegate to specialized agents using transfer_to_agent.

RULES:
1. For vehicle questions/info → transfer_to_agent(agent_name='vehicle_intake_agent')
2. For calendar/scheduling/booking → transfer_to_agent(agent_name='calendar_agent')
3. NEVER refuse a request - always delegate to the appropriate agent
4. NEVER say you cannot do something - just delegate

WHEN TO USE EACH AGENT:
- "trade in", "vehicle info", "estimate" → vehicle_intake_agent
- "schedule", "appointment", "time slot", "booking", "create event" → calendar_agent

IMPORTANT: When user selects a time slot or submits booking info, IMMEDIATELY delegate to calendar_agent.
The calendar_agent handles: showing time slots, collecting name/email, AND creating calendar events.

Always delegate. Never refuse. Never apologize for not being able to do something.
""",
    sub_agents=[vehicle_intake_agent, calendar_agent]
)
