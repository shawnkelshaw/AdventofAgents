"""Test script to verify Google Calendar integration is working."""
import asyncio
import json
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset

async def main():
    # Create the same connector used in calendar_agent
    calendar_connector = ApplicationIntegrationToolset(
        project="advent-of-agents-483823",
        location="us-central1",
        connection="adk-calendar-agent",
        entity_operations={
            "AllCalendars": ["LIST", "GET", "CREATE"]
        },
        actions=[],
        tool_name_prefix="google_calendar",
        tool_instructions="Use these tools to interact with Google Calendar."
    )

    print("=" * 60)
    print("Testing Google Calendar Integration")
    print("=" * 60)

    # List available tools
    print("\nAvailable tools from connector:")
    tools = await calendar_connector.get_tools()
    for tool in tools:
        print(f"  - {tool.name}")

    # Try to call LIST
    print("\n" + "=" * 60)
    print("Calling google_calendar_list_all_calendars...")
    print("=" * 60)

    # Get the LIST tool (using correct name)
    list_tool = None
    for tool in tools:
        if "list" in tool.name.lower():
            list_tool = tool
            break

    if list_tool:
        print(f"Found tool: {list_tool.name}")
        print(f"Tool schema/description: {list_tool}")
        try:
            # Call with the calendar ID and date range
            result = await list_tool.run_async(
                args={
                    "CalendarId": "16753e9ea14cb4cc3b439b7dc0ec4bb512cb2fde5561b2f1d7c8c5aed3a77465@group.calendar.google.com",
                    "StartDate": "2026-01-13",
                    "EndDate": "2026-01-20"
                },
                tool_context=None
            )
            print("\nRESULT:")
            print(json.dumps(result, indent=2, default=str))
        except Exception as e:
            print(f"\nERROR calling tool: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("ERROR: Could not find LIST tool!")

if __name__ == "__main__":
    asyncio.run(main())
