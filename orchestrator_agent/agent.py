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

CRITICAL RULES:
1. For vehicle questions/info → transfer_to_agent(agent_name='vehicle_intake_agent')
2. For calendar/scheduling/booking/CREATE event → transfer_to_agent(agent_name='calendar_agent')
3. NEVER respond yourself - ALWAYS delegate
4. NEVER generate A2UI JSON yourself - only sub-agents do that

WHEN TO USE EACH AGENT:
- "trade in", "vehicle info", "estimate" → vehicle_intake_agent
- "schedule", "appointment", "time slot", "booking", "create event", "SUBMIT_BOOKING" → calendar_agent

CRITICAL: When you see "SUBMIT_BOOKING" or "create calendar event" or "book appointment":
You MUST call: transfer_to_agent(agent_name='calendar_agent')
The calendar_agent will use google_calendar_AllCalendars_CREATE to book the appointment.

DO NOT respond with text. DO NOT generate UI. ONLY use transfer_to_agent.
""",
    sub_agents=[vehicle_intake_agent, calendar_agent]
)
