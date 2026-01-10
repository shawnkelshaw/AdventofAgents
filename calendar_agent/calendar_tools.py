"""Google Calendar integration tools for the calendar agent."""

import os
import datetime
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Authenticate and return Google Calendar service."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.pickle')
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'calendar-credentials.json')
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def find_available_slots(calendar_id: str = None, days_ahead: int = 14, meeting_duration_hours: int = 1) -> List[Dict[str, Any]]:
    """
    Find 3 available time slots in the calendar: near-term, mid-term, and long-term.
    
    Args:
        calendar_id: Calendar ID to check (default: uses SALES_CALENDAR_ID env var or 'primary')
        days_ahead: Number of days to look ahead (default: 14)
        meeting_duration_hours: Duration of meeting in hours (default: 1)
    
    Returns:
        List of 3 available time slots with start and end times
    """
    if calendar_id is None:
        calendar_id = os.getenv('SALES_CALENDAR_ID', 'primary')
    
    service = get_calendar_service()
    
    now = datetime.datetime.utcnow()
    end_date = now + datetime.timedelta(days=days_ahead)
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now.isoformat() + 'Z',
        timeMax=end_date.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    available_slots = []
    
    # Define time ranges for near, mid, and long term
    ranges = [
        (1, 5),   # Near-term: days 1-5
        (6, 10),  # Mid-term: days 6-10
        (11, 14)  # Long-term: days 11-14
    ]
    
    for start_day, end_day in ranges:
        slot = find_slot_in_range(events, now, start_day, end_day, meeting_duration_hours)
        if slot:
            available_slots.append(slot)
    
    return available_slots

def find_slot_in_range(events: List[Dict], base_time: datetime.datetime, 
                       start_day: int, end_day: int, duration_hours: int) -> Dict[str, Any]:
    """Find an available slot within a specific day range."""
    # Business hours: 9 AM to 5 PM
    business_start = 9
    business_end = 17
    
    for day_offset in range(start_day, end_day + 1):
        current_date = base_time + datetime.timedelta(days=day_offset)
        
        # Skip weekends
        if current_date.weekday() >= 5:
            continue
        
        # Check each hour in business hours
        for hour in range(business_start, business_end - duration_hours + 1):
            slot_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end = slot_start + datetime.timedelta(hours=duration_hours)
            
            # Check if this slot conflicts with any existing events
            is_available = True
            for event in events:
                event_start = datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00'))
                event_end = datetime.datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00'))
                
                # Make timezone aware if needed
                if slot_start.tzinfo is None:
                    slot_start = slot_start.replace(tzinfo=datetime.timezone.utc)
                    slot_end = slot_end.replace(tzinfo=datetime.timezone.utc)
                
                if not (slot_end <= event_start or slot_start >= event_end):
                    is_available = False
                    break
            
            if is_available:
                return {
                    'start': slot_start.isoformat(),
                    'end': slot_end.isoformat(),
                    'display': slot_start.strftime('%A, %B %d, %Y at %I:%M %p')
                }
    
    return None

def book_appointment(start_time: str, end_time: str, customer_email: str, 
                    customer_name: str, vehicle_info: str, 
                    calendar_id: str = None) -> Dict[str, Any]:
    """
    Book an appointment on the calendar.
    
    Args:
        start_time: ISO format start time
        end_time: ISO format end time
        customer_email: Customer's email address
        customer_name: Customer's name
        vehicle_info: Vehicle information for the meeting description
        calendar_id: Calendar ID to book on (default: uses SALES_CALENDAR_ID env var or 'primary')
    
    Returns:
        Created event details
    """
    if calendar_id is None:
        calendar_id = os.getenv('SALES_CALENDAR_ID', 'primary')
    
    service = get_calendar_service()
    
    event = {
        'summary': f'Vehicle Trade-In Appraisal - {customer_name}',
        'description': f'Vehicle trade-in appraisal appointment.\n\nVehicle Information:\n{vehicle_info}',
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/New_York',
        },
        'attendees': [
            {'email': customer_email},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 30},
            ],
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f'trade-in-{datetime.datetime.now().timestamp()}',
            }
        }
    }
    
    event = service.events().insert(
        calendarId=calendar_id,
        body=event,
        sendUpdates='all',
        conferenceDataVersion=1
    ).execute()
    
    return {
        'event_id': event.get('id'),
        'html_link': event.get('htmlLink'),
        'status': 'confirmed'
    }
