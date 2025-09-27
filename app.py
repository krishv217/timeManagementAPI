from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import re
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from database import db
from models import (
    ScheduledTask, TaskPlanningRequest, TaskPlanningResponse, 
    OptimizationRequest, OptimizationResponse, TaskPriority, TaskCategory, 
    User, Task, UserPattern, TaskStats, ProductivityInsight
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize OpenAI client with environment variable (lazy initialization)
client = None

def get_openai_client():
    """Get OpenAI client with lazy initialization"""
    global client
    if client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        client = OpenAI(api_key=api_key)
    return client

# Global storage for persistent task list
persistent_tasks = []

class ScheduleOptimizer:
    """Advanced scheduling optimizer with AI integration"""
    
    def __init__(self):
        self.db = db
    
    def get_user_preferences(self, user_id: str = None) -> dict:
        """Get user preferences for scheduling"""
        default_preferences = {
            "work_hours": {"start": "09:00", "end": "17:00"},
            "focus_times": ["09:00-11:00", "14:00-16:00"],
            "buffer_time": 15,
            "max_daily_tasks": 8,
            "preferred_task_duration": 60
        }
        
        if user_id:
            user_prefs = self.db.get_user_preferences(user_id)
            if user_prefs and user_prefs.get('preferences'):
                merged_preferences = default_preferences.copy()
                merged_preferences.update(user_prefs['preferences'])
                return merged_preferences
        
        return default_preferences
    
    def get_existing_calendar_events(self, user_id: str = None, date: datetime = None) -> list:
        """Get existing calendar events for conflict detection"""
        if user_id and date:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return self.db.get_tasks_by_date_range(user_id, start_of_day, end_of_day)
        return []
    
    def analyze_user_patterns(self, user_id: str = None) -> dict:
        """Analyze user's historical task completion patterns"""
        if user_id:
            patterns = self.db.get_user_patterns(user_id)
            if patterns:
                category_durations = {}
                for pattern in patterns:
                    category = pattern.get('task_category', 'general')
                    if category not in category_durations:
                        category_durations[category] = []
                    actual_duration = pattern.get('actual_duration')
                    if actual_duration:
                        category_durations[category].append(actual_duration)
                
                # Calculate averages
                for category in category_durations:
                    durations = category_durations[category]
                    if durations:
                        category_durations[category] = sum(durations) / len(durations)
                    else:
                        category_durations[category] = 60  # Default duration
                
                # Get optimal time slots
                optimal_slots = []
                for pattern in patterns:
                    slot = pattern.get('optimal_time_slot')
                    if slot and slot not in optimal_slots:
                        optimal_slots.append(slot)
                
                # Calculate average completion time
                actual_durations = [p.get('actual_duration') for p in patterns if p.get('actual_duration')]
                avg_completion = sum(actual_durations) / len(actual_durations) if actual_durations else 60
                
                return {
                    "average_completion_time": avg_completion,
                    "optimal_time_slots": optimal_slots or ["morning"],
                    "category_durations": category_durations
                }
        
        return {
            "average_completion_time": 60,
            "optimal_time_slots": ["morning"],
            "category_durations": {}
        }
    
    def generate_schedule_with_ai(self, user_input: str, user_id: str = None, date: datetime = None) -> TaskPlanningResponse:
        """Use OpenAI to generate optimized schedule"""
        try:
            preferences = self.get_user_preferences(user_id)
            patterns = self.analyze_user_patterns(user_id)
            existing_events = self.get_existing_calendar_events(user_id, date)
            
            # Get current time and ensure we're scheduling for the future
            current_time = datetime.now()
            if date:
                # If date is provided, use it but ensure it's not in the past
                if date.date() < current_time.date():
                    date = current_time
                elif date.date() == current_time.date() and date.time() < current_time.time():
                    date = current_time
            else:
                date = current_time
            
            # Calculate minimum start time (current time + 15 minutes)
            min_start_time = current_time + timedelta(minutes=15)
            
            system_prompt = f"""
You are an intelligent scheduling assistant. Given a user's natural language request 
and their existing calendar, create an optimized daily schedule.

🚨 CRITICAL TIME CONSTRAINT 🚨
Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
MINIMUM start time for ANY task: {min_start_time.strftime('%Y-%m-%d %H:%M:%S')}

ABSOLUTE RULE: ALL task start times MUST be AFTER {min_start_time.strftime('%Y-%m-%d %H:%M:%S')}
If you schedule any task before this time, it will be automatically rejected.

User Preferences:
- Work hours: {preferences.get('work_hours', {})}
- Focus times: {preferences.get('focus_times', [])}
- Buffer time between tasks: {preferences['buffer_time']} minutes
- Maximum daily tasks: {preferences['max_daily_tasks']}

User Patterns (from historical data):
- Average task completion time: {patterns['average_completion_time']} minutes
- Optimal time slots: {patterns['optimal_time_slots']}
- Category-specific durations: {patterns['category_durations']}

Existing calendar events: {existing_events}

Consider:
- Task priorities and dependencies
- Realistic time estimates based on user history
- User's energy patterns and preferred focus times
- Buffer time between tasks
- Existing calendar commitments
- Avoid scheduling conflicts
- Do not miss any tasks
- MANDATORY: All start times must be >= {min_start_time.strftime('%Y-%m-%d %H:%M:%S')}

Respond with a JSON object containing:
{{
  "scheduled_tasks": [
    {{
      "title": "task title",
      "description": "task description",
      "start_time": "{min_start_time.strftime('%Y-%m-%dT%H:%M:%S')}",
      "end_time": "{min_start_time.strftime('%Y-%m-%dT%H:%M:%S')}",
      "priority": 3,
      "category": "work",
      "reasoning": "why this time slot was chosen"
    }}
  ],
  "summary": "Brief explanation of the scheduling decisions",
  "conflicts": ["any conflicts found"],
  "suggestions": ["optimization suggestions"]
}}

User request: "{user_input}"
Date: {date.strftime('%Y-%m-%d')}
Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
Minimum start time: {min_start_time.strftime('%Y-%m-%d %H:%M:%S')}
"""

            print(f"🤖 Calling OpenAI API for schedule generation...")
            print(f"📝 User input received: {user_input}")
            print(f"🕐 Current time for validation: {current_time}")
            print(f"🕐 Minimum start time: {min_start_time}")
            response = get_openai_client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            print(f"✅ OpenAI API call successful")
            print(f"🤖 Raw AI response: {response.choices[0].message.content[:200]}...")
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            try:
                schedule_data = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                schedule_data = {
                    "scheduled_tasks": [],
                    "summary": "Failed to parse AI response",
                    "conflicts": [],
                    "suggestions": ["Please try rephrasing your request"]
                }
            
            # Convert to ScheduledTask objects and validate times
            print(f"🔍 Starting task validation for {len(schedule_data.get('scheduled_tasks', []))} tasks")
            scheduled_tasks = []
            for i, task_data in enumerate(schedule_data.get("scheduled_tasks", [])):
                print(f"🔍 Processing task {i+1}: {task_data.get('title', 'Unknown')}")
                try:
                    start_time = datetime.fromisoformat(task_data["start_time"])
                    end_time = datetime.fromisoformat(task_data["end_time"])
                    
                    print(f"🔍 Validating task '{task_data['title']}':")
                    print(f"   Original start: {start_time}")
                    print(f"   Original end: {end_time}")
                    print(f"   Current time: {current_time}")
                    print(f"   Start in past? {start_time <= current_time}")
                    print(f"   End in past? {end_time <= current_time}")
                    
                    # FORCE all times to be in the future - no exceptions
                    min_start_time = current_time + timedelta(minutes=15)
                    
                    if start_time < min_start_time:
                        # Force start time to be at least 15 minutes from now
                        original_start = start_time
                        start_time = min_start_time
                        # Adjust end time to maintain duration
                        duration = end_time - original_start
                        end_time = start_time + duration
                        print(f"🚨 FORCED past time for task '{task_data['title']}' from {original_start} to {start_time}")
                    
                    if end_time <= start_time:
                        # Ensure end time is after start time
                        end_time = start_time + timedelta(minutes=60)  # Default 1 hour duration
                        print(f"🚨 FORCED end time for task '{task_data['title']}' to {end_time}")
                    
                    # Double-check: if end time is still in the past, force it to future
                    if end_time < min_start_time:
                        end_time = start_time + timedelta(minutes=60)
                        print(f"🚨 FORCED end time to future for task '{task_data['title']}' to {end_time}")
                    
                    print(f"   Final start: {start_time}")
                    print(f"   Final end: {end_time}")
                    
                    scheduled_task = ScheduledTask(
                        title=task_data["title"],
                        description=task_data.get("description", ""),
                        start_time=start_time,
                        end_time=end_time,
                        priority=TaskPriority(task_data.get("priority", 3)),
                        category=TaskCategory(task_data.get("category", "general")),
                        reasoning=task_data.get("reasoning", "")
                    )
                    scheduled_tasks.append(scheduled_task)
                except Exception as e:
                    print(f"Error parsing scheduled task: {e}")
                    continue
            
            # Final validation: ensure ALL tasks are in the future
            final_scheduled_tasks = []
            for task in scheduled_tasks:
                if task.start_time < current_time + timedelta(minutes=15):
                    # Force this task to be in the future
                    task.start_time = current_time + timedelta(minutes=15)
                    task.end_time = task.start_time + timedelta(hours=1)  # Default 1 hour
                    print(f"🚨 FINAL VALIDATION: Forced task '{task.title}' to {task.start_time}")
                final_scheduled_tasks.append(task)
            
            return TaskPlanningResponse(
                scheduled_tasks=final_scheduled_tasks,
                summary=schedule_data.get("summary", "Schedule generated successfully"),
                conflicts=schedule_data.get("conflicts", []),
                suggestions=schedule_data.get("suggestions", [])
            )
            
        except Exception as e:
            print(f"💥 Error generating schedule with AI: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return TaskPlanningResponse(
                scheduled_tasks=[],
                summary=f"Failed to generate schedule due to AI service error: {str(e)}",
                conflicts=[],
                suggestions=["Please check OpenAI API key and try again"]
            )

def format_time_for_display(iso_time_string):
    """
    Convert ISO time string to human-readable format
    """
    try:
        dt = datetime.fromisoformat(iso_time_string.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p")  # e.g., "09:00 AM"
    except:
        return iso_time_string

def format_date_for_display(iso_time_string):
    """
    Convert ISO time string to human-readable date format
    """
    try:
        dt = datetime.fromisoformat(iso_time_string.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")  # e.g., "September 27, 2025"
    except:
        return iso_time_string

def add_display_times(task):
    """
    Add human-readable time formats to a task
    """
    task_copy = task.copy()
    task_copy['start_time_display'] = format_time_for_display(task['start'])
    task_copy['end_time_display'] = format_time_for_display(task['end'])
    task_copy['date_display'] = format_date_for_display(task['start'])
    return task_copy

def extract_tasks_from_text(text):
    """
    Use OpenAI to extract tasks from the input text
    """
    prompt = f"""
    Extract ALL tasks/activities from this text. Count each distinct activity mentioned.
    
    CRITICAL: You MUST extract EVERY task mentioned. Do not miss any.
    
    For each task:
    1. Use the exact activity name or a clear, specific description
    2. Estimate realistic duration in hours
    3. If time is mentioned, include it in the task name
    
    Duration guidelines:
    - Exercise/gym: 1-1.5 hours
    - Study/learning: 1-3 hours  
    - Cleaning: 0.5-2 hours
    - Work projects: 2-4 hours
    - Meetings: 0.5-2 hours
    - Shopping: 1-2 hours
    - Cooking: 0.5-1.5 hours
    
    Text: "{text}"
    
    Return ONLY a JSON array with this exact format:
    [
        {{"name": "task name", "duration_hours": 1.5}},
        {{"name": "another task", "duration_hours": 2.0}}
    ]
    
    Extract ALL tasks mentioned. Do not skip any.
    """
    
    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a task extraction assistant. Your job is to extract EVERY task mentioned in the text. Do not miss any tasks. Count each distinct activity and return all of them."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up the response to ensure it's valid JSON
        content = content.replace('```json', '').replace('```', '').strip()
        
        tasks = json.loads(content)
        return tasks
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw content: {content if 'content' in locals() else 'No content'}")
        return []
    except Exception as e:
        print(f"Error extracting tasks: {e}")
        return []

def extract_explicit_times(task_name):
    """
    Extract explicit start and end times mentioned in task name
    Returns (start_time, end_time) where each is (hour, minute) or None
    """
    import re
    
    # Patterns for time extraction
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 2:30, 2:30pm, 14:30
        r'(\d{1,2})\s*(am|pm)',           # 2pm, 2 am, 14pm
        r'at\s+(\d{1,2}):(\d{2})',        # at 2:30
        r'at\s+(\d{1,2})\s*(am|pm)',      # at 2pm
    ]
    
    def parse_time(match):
        groups = match.groups()
        if len(groups) >= 2:
            hour = int(groups[0])
            minute = int(groups[1]) if groups[1] and groups[1].isdigit() else 0
            
            # Handle AM/PM
            if len(groups) >= 3 and groups[2]:
                ampm = groups[2].lower()
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0
            elif len(groups) >= 2 and groups[1] and groups[1] in ['am', 'pm']:
                ampm = groups[1].lower()
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0
            
            # Validate hour and minute
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)
        return None
    
    task_lower = task_name.lower()
    
    # Look for time ranges (e.g., "2pm to 4pm", "2:30-4:30")
    range_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?\s*to\s*(\d{1,2}):(\d{2})\s*(am|pm)?',  # 2:30pm to 4:30pm
        r'(\d{1,2})\s*(am|pm)\s*to\s*(\d{1,2})\s*(am|pm)',                    # 2pm to 4pm
        r'(\d{1,2}):(\d{2})\s*(am|pm)?\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)?',   # 2:30pm-4:30pm
        r'(\d{1,2})\s*(am|pm)\s*-\s*(\d{1,2})\s*(am|pm)',                     # 2pm-4pm
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, task_lower)
        if match:
            groups = match.groups()
            if len(groups) >= 6:
                # Parse start time
                start_hour = int(groups[0])
                start_minute = int(groups[1]) if groups[1] and groups[1].isdigit() else 0
                start_ampm = groups[2] if len(groups) > 2 else None
                
                # Parse end time
                end_hour = int(groups[3])
                end_minute = int(groups[4]) if groups[4] and groups[4].isdigit() else 0
                end_ampm = groups[5] if len(groups) > 5 else None
                
                # Handle AM/PM for start time
                if start_ampm:
                    if start_ampm.lower() == 'pm' and start_hour != 12:
                        start_hour += 12
                    elif start_ampm.lower() == 'am' and start_hour == 12:
                        start_hour = 0
                
                # Handle AM/PM for end time
                if end_ampm:
                    if end_ampm.lower() == 'pm' and end_hour != 12:
                        end_hour += 12
                    elif end_ampm.lower() == 'am' and end_hour == 12:
                        end_hour = 0
                
                # Validate times
                if (0 <= start_hour <= 23 and 0 <= start_minute <= 59 and 
                    0 <= end_hour <= 23 and 0 <= end_minute <= 59):
                    return ((start_hour, start_minute), (end_hour, end_minute))
    
    # Look for single times
    for pattern in time_patterns:
        match = re.search(pattern, task_lower)
        if match:
            time = parse_time(match)
            if time:
                return (time, None)
    
    return (None, None)

def extract_explicit_time(task_name):
    """
    Extract explicit start time mentioned in task name (for backward compatibility)
    Returns (hour, minute) if found, None otherwise
    """
    start_time, _ = extract_explicit_times(task_name)
    return start_time

def get_task_priority(task_name):
    """
    Get the priority level of a task (1 = highest priority, 5 = lowest priority)
    """
    task_lower = task_name.lower()
    
    # Priority 0: User-specified explicit times (highest priority)
    if extract_explicit_time(task_name):
        return 0
    
    # Priority 1: Critical time-sensitive events
    if any(word in task_lower for word in ['meeting', 'appointment', 'interview', 'deadline']):
        return 1
    
    # Priority 2: Essential daily activities (meals, sleep)
    if any(word in task_lower for word in ['breakfast', 'lunch', 'dinner', 'supper', 'eat', 'sleep']):
        return 2
    
    # Priority 3: Work and important tasks
    if any(word in task_lower for word in ['work', 'project', 'study', 'presentation', 'report']):
        return 3
    
    # Priority 4: Health and exercise
    if any(word in task_lower for word in ['gym', 'exercise', 'workout', 'run', 'jog']):
        return 4
    
    # Priority 5: Low priority tasks (calls, shopping, cleaning)
    if any(word in task_lower for word in ['call', 'phone', 'shop', 'grocery', 'clean', 'laundry']):
        return 5
    
    # Default priority
    return 3

def get_optimal_time_for_task(task_name, current_time):
    """
    Get the optimal time for a specific task based on its type or explicit time
    """
    # First check for explicit time in task name
    explicit_time = extract_explicit_time(task_name)
    if explicit_time:
        hour, minute = explicit_time
        optimal_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # If explicit time is in the past, return current time + 15 minutes
        if optimal_time < current_time:
            return current_time + timedelta(minutes=15)
        return optimal_time
    
    # Fall back to logical optimal times
    task_lower = task_name.lower()
    
    # Meal times
    if any(word in task_lower for word in ['breakfast', 'morning meal']):
        optimal_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
    elif any(word in task_lower for word in ['lunch', 'lunchtime']):
        optimal_time = current_time.replace(hour=12, minute=0, second=0, microsecond=0)
    elif any(word in task_lower for word in ['dinner', 'evening meal', 'supper']):
        optimal_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Sleep times
    elif any(word in task_lower for word in ['sleep', 'nap', 'rest']):
        if 'nap' in task_lower:
            optimal_time = current_time.replace(hour=14, minute=0, second=0, microsecond=0)  # 2 PM nap
        else:
            optimal_time = current_time.replace(hour=22, minute=0, second=0, microsecond=0)  # 10 PM sleep
    
    # Exercise times
    elif any(word in task_lower for word in ['gym', 'exercise', 'workout', 'run', 'jog']):
        optimal_time = current_time.replace(hour=17, minute=0, second=0, microsecond=0)  # 5 PM exercise
    
    # Work/study times
    elif any(word in task_lower for word in ['work', 'study', 'project', 'meeting', 'presentation']):
        optimal_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)  # 9 AM work
    
    else:
        # Default to current time + 15 minutes
        optimal_time = current_time + timedelta(minutes=15)
    
    # Ensure the optimal time is not in the past
    if optimal_time < current_time:
        return current_time + timedelta(minutes=15)
    
    return optimal_time


def has_time_conflict(new_start, new_end, existing_times):
    """
    Check if a new time slot conflicts with existing tasks
    """
    for existing_start, existing_end in existing_times:
        # Check for overlap: new task starts before existing ends AND new task ends after existing starts
        if new_start < existing_end and new_end > existing_start:
            return True
    return False

def find_next_available_time(proposed_start, duration, existing_times, max_hour=22):
    """
    Find the next available time slot that doesn't conflict with existing tasks
    """
    current_time = proposed_start
    end_time = current_time + duration
    
    # Try to find a slot within reasonable hours (9 AM to 10 PM)
    while current_time.hour < max_hour:
        if not has_time_conflict(current_time, end_time, existing_times):
            return current_time
        
        # Move to next 30-minute slot
        current_time += timedelta(minutes=30)
        end_time = current_time + duration
    
    # If no slot found, move to next day
    next_day = current_time.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return next_day

def reschedule_for_priority_task(new_task, new_priority, existing_tasks):
    """
    Reschedule existing lower-priority tasks to make room for a high-priority task
    """
    if new_priority > 2:  # Only reschedule for high-priority tasks (priority 0-2)
        return existing_tasks
    
    # Get the new task's time to check for conflicts
    new_task_name = new_task.get('name', '')
    explicit_start, explicit_end = extract_explicit_times(new_task_name)
    
    if not explicit_start:
        return existing_tasks  # Only reschedule for explicit times
    
    # Calculate new task duration
    if explicit_end:
        new_duration = (explicit_end[0] * 60 + explicit_end[1]) - (explicit_start[0] * 60 + explicit_start[1])
        new_duration = timedelta(minutes=new_duration)
    else:
        new_duration = timedelta(hours=1)  # Default 1 hour
    
    new_start_time = datetime.now().replace(hour=explicit_start[0], minute=explicit_start[1], second=0, microsecond=0)
    new_end_time = new_start_time + new_duration
    
    # Sort existing tasks by priority (lowest priority first)
    existing_tasks_with_priority = []
    for task in existing_tasks:
        priority = get_task_priority(task['name'])
        existing_tasks_with_priority.append((task, priority))
    
    # Sort by priority (lowest first) so we reschedule least important tasks first
    existing_tasks_with_priority.sort(key=lambda x: x[1], reverse=True)
    
    # Try to reschedule lower priority tasks that conflict with the new task
    rescheduled_tasks = []
    for task, priority in existing_tasks_with_priority:
        if priority > new_priority:  # Only reschedule tasks with lower priority
            task_start = datetime.fromisoformat(task['start'])
            task_end = datetime.fromisoformat(task['end'])
            
            # Check if this task conflicts with the new task
            if has_time_conflict(new_start_time, new_end_time, [(task_start, task_end)]):
                # This task conflicts, try to reschedule it
                duration = task_end - task_start
                
                # Get other existing times (excluding this task and the new task)
                other_times = []
                for other_task in existing_tasks:
                    if other_task['name'] != task['name']:
                        other_start = datetime.fromisoformat(other_task['start'])
                        other_end = datetime.fromisoformat(other_task['end'])
                        other_times.append((other_start, other_end))
                
                # Add the new task's time to avoid conflicts
                other_times.append((new_start_time, new_end_time))
                
                # Find new time for this task
                new_start = find_next_available_time(task_start, duration, other_times)
                new_end = new_start + duration
                
                # Update the task
                updated_task = task.copy()
                updated_task['start'] = new_start.isoformat()
                updated_task['end'] = new_end.isoformat()
                rescheduled_tasks.append(updated_task)
            else:
                # No conflict, keep original time
                rescheduled_tasks.append(task)
        else:
            rescheduled_tasks.append(task)
    
    return rescheduled_tasks

def schedule_tasks(tasks, start_date=None, existing_tasks=None):
    """
    Schedule tasks optimally throughout the day with realistic timing
    """
    if not tasks:
        return []
    
    # Get current time to ensure we don't schedule in the past
    current_time = datetime.now()
    
    # Default to today if no start date provided, but ensure it's not in the past
    if start_date is None:
        start_date = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
        # If it's already past 9 AM, start from current time + 15 minutes
        if start_date < current_time:
            start_date = current_time + timedelta(minutes=15)
    else:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        # Ensure start_date is not in the past
        if start_date < current_time:
            start_date = current_time + timedelta(minutes=15)
    
    # Get existing task times to avoid conflicts
    existing_times = []
    if existing_tasks:
        for task in existing_tasks:
            try:
                start_time = datetime.fromisoformat(task['start'])
                end_time = datetime.fromisoformat(task['end'])
                existing_times.append((start_time, end_time))
            except:
                continue
    
    scheduled_tasks = []
    
    # Sort tasks by optimal time, prioritizing explicit times
    tasks_with_times = []
    
    for task in tasks:
        task_name = task.get('name', 'Unknown Task')
        optimal_time = get_optimal_time_for_task(task_name, start_date)
        tasks_with_times.append((task, optimal_time))
    
    # Sort by optimal time, but prioritize explicit times
    def sort_key(task_time_tuple):
        task, optimal_time = task_time_tuple
        task_name = task.get('name', '')
        explicit_time = extract_explicit_time(task_name)
        if explicit_time:
            # Use explicit time for sorting
            hour, minute = explicit_time
            return start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            # Use optimal time for sorting
            return optimal_time
    
    tasks_with_times.sort(key=sort_key)
    
    current_time = start_date
    
    for i, (task, optimal_time) in enumerate(tasks_with_times):
        task_name = task.get('name', 'Unknown Task')
        duration_hours = float(task.get('duration_hours', 1.0))
        
        # Cap duration at 6 hours to prevent unrealistic scheduling
        duration_hours = min(duration_hours, 6.0)
        
        # Convert hours to timedelta
        duration = timedelta(hours=duration_hours)
        
        # Check if this task has explicit times
        explicit_start, explicit_end = extract_explicit_times(task_name)
        if explicit_start:
            # Use explicit start time, but ensure it's not in the past
            hour, minute = explicit_start
            task_start = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If explicit time is in the past, adjust it to current time + 15 minutes
            if task_start < current_time:
                task_start = current_time + timedelta(minutes=15)
                print(f"⚠️ Adjusted past explicit time for task '{task_name}' to {task_start}")
            
            # If explicit end time is provided, calculate duration from it
            if explicit_end:
                end_hour, end_minute = explicit_end
                task_end_time = start_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                # Ensure end time is not in the past
                if task_end_time < current_time:
                    task_end_time = task_start + timedelta(hours=1)  # Default 1 hour duration
                duration = task_end_time - task_start
                duration_hours = duration.total_seconds() / 3600
                duration = timedelta(hours=duration_hours)
        else:
            # Use optimal time if it's later than current time, otherwise use current time
            if optimal_time > current_time:
                task_start = optimal_time
            else:
                task_start = current_time
        
        # Check for conflicts with existing tasks
        if existing_times:
            # If this task has an explicit time, it has priority 0 and should force rescheduling
            task_priority = get_task_priority(task_name)
            if task_priority == 0:  # Explicit time - highest priority
                # Don't change the start time, let conflicts be handled by rescheduling
                pass
            else:
                # For non-explicit times, find next available time
                task_start = find_next_available_time(task_start, duration, existing_times)
        
        # Check if task fits in current day (extend to 10 PM for evening activities)
        work_end = task_start.replace(hour=22, minute=0)
        if task_start + duration > work_end:
            # Move to next day
            task_start = task_start.replace(hour=9, minute=0) + timedelta(days=1)
        
        # Calculate end time
        end_time = task_start + duration
        
        # Add this task's time to existing_times for next tasks
        existing_times.append((task_start, end_time))
        
        scheduled_tasks.append({
            "name": task_name,
            "start": task_start.isoformat(),
            "end": end_time.isoformat()
        })
        
        # Update current_time for next task with standard break
        break_time = timedelta(minutes=30)
        current_time = end_time + break_time
    
    return scheduled_tasks

@app.route('/schedule', methods=['POST'])
def schedule_tasks_endpoint():
    """
    Main endpoint to schedule tasks from text input and append to persistent list
    """
    global persistent_tasks
    
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Please provide 'text' field in request body"}), 400
        
        text = data['text']
        start_date = data.get('start_date')  # Optional start date
        
        # Extract tasks from text
        tasks = extract_tasks_from_text(text)
        
        if not tasks:
            return jsonify({"error": "No tasks could be extracted from the text"}), 400
        
        # Check if any new tasks are high priority and need rescheduling
        new_task_priorities = [get_task_priority(task['name']) for task in tasks]
        highest_new_priority = min(new_task_priorities) if new_task_priorities else 3
        
        # If we have high-priority tasks (including explicit times), try to reschedule existing lower-priority tasks
        if highest_new_priority <= 2 and persistent_tasks:
            # Reschedule existing tasks to make room for high-priority tasks
            persistent_tasks = reschedule_for_priority_task(tasks[0], highest_new_priority, persistent_tasks)
        
        # Schedule the tasks, considering existing tasks to avoid conflicts
        scheduled_tasks = schedule_tasks(tasks, start_date, persistent_tasks)
        
        # Append new tasks to persistent list
        persistent_tasks.extend(scheduled_tasks)
        
        # Add display times to all tasks
        new_tasks_with_display = [add_display_times(task) for task in scheduled_tasks]
        all_tasks_with_display = [add_display_times(task) for task in persistent_tasks]
        
        # Sort all tasks chronologically by start time
        all_tasks_with_display.sort(key=lambda x: x['start'])
        
        return jsonify({
            "new_tasks": new_tasks_with_display,
            "all_tasks": all_tasks_with_display,
            "original_text": text,
            "extracted_tasks": tasks
        })
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    """
    Get all persistent tasks with display times in chronological order
    """
    global persistent_tasks
    tasks_with_display = [add_display_times(task) for task in persistent_tasks]
    
    # Sort tasks chronologically by start time
    tasks_with_display.sort(key=lambda x: x['start'])
    
    return jsonify({
        "tasks": tasks_with_display,
        "total_count": len(persistent_tasks)
    })

@app.route('/tasks', methods=['DELETE'])
def clear_all_tasks():
    """
    Clear all persistent tasks
    """
    global persistent_tasks
    persistent_tasks = []
    return jsonify({
        "message": "All tasks cleared",
        "tasks": persistent_tasks
    })

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy", "message": "TimeAPI is running"})

@app.route('/api/debug/time', methods=['GET'])
def debug_time():
    """
    Debug endpoint to check current time on server
    """
    current_time = datetime.now()
    return jsonify({
        "current_time": current_time.isoformat(),
        "current_time_formatted": current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "timezone": str(current_time.tzinfo),
        "timestamp": current_time.timestamp()
    })

@app.route('/api/debug/validate-time', methods=['POST'])
def debug_validate_time():
    """
    Debug endpoint to test time validation logic
    """
    try:
        data = request.get_json()
        if not data or 'start_time' not in data:
            return jsonify({"error": "Please provide start_time"}), 400
        
        current_time = datetime.now()
        start_time = datetime.fromisoformat(data['start_time'])
        min_start_time = current_time + timedelta(minutes=15)
        
        result = {
            "current_time": current_time.isoformat(),
            "input_start_time": start_time.isoformat(),
            "min_start_time": min_start_time.isoformat(),
            "is_past": start_time < current_time,
            "needs_adjustment": start_time < min_start_time
        }
        
        if start_time < min_start_time:
            adjusted_start = min_start_time
            duration = timedelta(hours=1)  # Default duration
            adjusted_end = adjusted_start + duration
            result["adjusted_start_time"] = adjusted_start.isoformat()
            result["adjusted_end_time"] = adjusted_end.isoformat()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with API documentation
    """
    return jsonify({
        "message": "TimeAPI - Advanced Task Scheduling Service with Supabase",
        "version": "2.0",
        "features": [
            "AI-powered task scheduling",
            "Supabase database integration",
            "User personalization",
            "Schedule optimization",
            "Conflict detection",
            "Task management"
        ],
        "endpoints": {
            "Basic Scheduling": {
                "POST /schedule": "Schedule tasks from text input (legacy)",
                "GET /tasks": "Get all scheduled tasks (legacy)",
                "DELETE /tasks": "Clear all tasks (legacy)"
            },
            "Advanced Scheduling": {
                "POST /api/plan": "AI-powered task planning with personalization",
                "POST /api/optimize": "Optimize existing schedule using AI",
                "POST /api/accept": "Accept generated schedule and save to database",
                "GET /api/conflicts": "Check for scheduling conflicts",
                "GET /api/tasks": "Get user tasks from database",
                "PUT /api/tasks/<id>": "Update specific task",
                "DELETE /api/tasks/<id>": "Delete specific task",
                "PUT /api/tasks/<id>/complete": "Mark task as completed with actual duration"
            },
            "User Management": {
                "POST /api/user/create": "Create new user with Google authentication",
                "GET /api/user/<google_id>": "Get user by Google ID",
                "GET /api/user/stats": "Get user task statistics",
                "GET /api/user/insights": "Get productivity insights"
            },
            "Utility": {
                "GET /health": "Health check",
                "GET /api/test-openai": "Test OpenAI API connection",
                "GET /docs": "Interactive API documentation",
                "GET /": "This API information"
            }
        },
        "example_requests": {
            "basic_scheduling": {
                "endpoint": "POST /schedule",
                "body": {"text": "I have an ML project and want to go to the gym"}
            },
            "advanced_planning": {
                "endpoint": "POST /api/plan",
                "body": {
                    "user_input": "I need to work on my presentation, exercise, and have dinner",
                    "user_id": "user123",
                    "date": "2024-01-15T00:00:00Z"
                }
            },
            "optimize_schedule": {
                "endpoint": "POST /api/optimize",
                "body": {
                    "user_id": "user123",
                    "date": "2024-01-15T00:00:00Z"
                }
            }
        },
        "database_required": "Supabase configuration required for advanced features"
    })

@app.route('/docs')
def docs():
    """
    Serve the API documentation page
    """
    try:
        with open('docs.html', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({"error": "Documentation not found"}), 404

# Advanced Scheduling Endpoints

@app.route('/api/plan', methods=['POST'])
def plan_tasks_advanced():
    """
    Advanced task planning with AI optimization
    """
    try:
        data = request.get_json()
        
        if not data or 'user_input' not in data:
            return jsonify({"error": "Please provide 'user_input' field in request body"}), 400
        
        user_input = data['user_input']
        user_id = data.get('user_id')  # Optional user ID for personalization
        date_str = data.get('date')
        
        # Parse date if provided
        target_date = None
        if date_str:
            try:
                target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return jsonify({"error": "Invalid date format. Use ISO format."}), 400
        
        # Generate schedule using AI
        optimizer = ScheduleOptimizer()
        schedule_response = optimizer.generate_schedule_with_ai(user_input, user_id, target_date)
        
        # CRITICAL: Force all tasks to be in the future before returning
        current_time = datetime.now()
        min_start_time = current_time + timedelta(minutes=15)
        
        for task in schedule_response.scheduled_tasks:
            if task.start_time < min_start_time:
                print(f"🚨 API ENDPOINT: Forcing task '{task.title}' from {task.start_time} to {min_start_time}")
                task.start_time = min_start_time
                task.end_time = task.start_time + timedelta(hours=1)  # Default 1 hour
                min_start_time = task.end_time + timedelta(minutes=15)  # Add buffer for next task
        
        response_dict = schedule_response.to_dict()
        response_dict["debug_message"] = f"API endpoint executed at {datetime.now().isoformat()}"
        return jsonify(response_dict)
        
    except Exception as e:
        return jsonify({"error": f"Failed to plan tasks: {str(e)}"}), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_schedule():
    """
    Optimize existing schedule using AI
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        date_str = data.get('date')
        
        # Parse date if provided
        target_date = None
        if date_str:
            try:
                target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                return jsonify({"error": "Invalid date format. Use ISO format."}), 400
        
        optimizer = ScheduleOptimizer()
        
        # Get existing tasks for the date
        if user_id and target_date:
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            existing_tasks = db.get_tasks_by_date_range(user_id, start_of_day, end_of_day)
            
            if not existing_tasks:
                return jsonify({
                    "optimized_schedule": [],
                    "changes_made": [],
                    "reasoning": "No tasks found for optimization",
                    "success": False
                })
            
            # Create optimization prompt
            task_descriptions = []
            for task in existing_tasks:
                task_descriptions.append(f"- {task['title']} (Priority: {task.get('priority', 3)}, Duration: {task.get('estimated_duration', 60)}min)")
            
            optimization_input = f"Optimize the following tasks: {'; '.join(task_descriptions)}"
            
            # Use AI to optimize
            schedule_response = optimizer.generate_schedule_with_ai(optimization_input, user_id, target_date)
            
            return jsonify({
                "optimized_schedule": [
                    {
                        "title": task.title,
                        "description": task.description,
                        "start_time": task.start_time.isoformat() if task.start_time else None,
                        "end_time": task.end_time.isoformat() if task.end_time else None,
                        "priority": task.priority.value,
                        "category": task.category.value,
                        "reasoning": task.reasoning
                    }
                    for task in schedule_response.scheduled_tasks
                ],
                "changes_made": [],
                "reasoning": schedule_response.summary,
                "success": True
            })
        else:
            return jsonify({
                "optimized_schedule": [],
                "changes_made": [],
                "reasoning": "User ID and date required for optimization",
                "success": False
            })
        
    except Exception as e:
        return jsonify({"error": f"Failed to optimize schedule: {str(e)}"}), 500

@app.route('/api/accept', methods=['POST'])
def accept_schedule():
    """
    Accept a generated schedule and save tasks to database
    """
    try:
        data = request.get_json()
        
        if not data or 'scheduled_tasks' not in data:
            return jsonify({"error": "Please provide 'scheduled_tasks' field in request body"}), 400
        
        user_id = data.get('user_id')
        scheduled_tasks_data = data['scheduled_tasks']
        
        if not scheduled_tasks_data:
            return jsonify({
                "message": "No tasks to create",
                "tasks_created": 0
            })
        
        created_tasks = []
        for task_data in scheduled_tasks_data:
            task_record = {
                "user_id": user_id,
                "title": task_data["title"],
                "description": task_data.get("description", ""),
                "estimated_duration": 60,  # Default duration
                "priority": task_data.get("priority", 3),
                "category": task_data.get("category", "general"),
                "scheduled_start": task_data.get("start_time"),
                "scheduled_end": task_data.get("end_time"),
                "status": "pending"
            }
            
            # Calculate duration if start and end times are provided
            if task_data.get("start_time") and task_data.get("end_time"):
                start_time = datetime.fromisoformat(task_data["start_time"])
                end_time = datetime.fromisoformat(task_data["end_time"])
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
                task_record["estimated_duration"] = duration_minutes
            
            created_task = db.create_task(task_record)
            if created_task:
                created_tasks.append(created_task)
        
        return jsonify({
            "message": f"Successfully created {len(created_tasks)} tasks",
            "tasks_created": len(created_tasks)
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to accept schedule: {str(e)}"}), 500

@app.route('/api/conflicts', methods=['GET'])
def check_schedule_conflicts():
    """
    Check for scheduling conflicts on a specific date
    """
    try:
        user_id = request.args.get('user_id')
        date_str = request.args.get('date')
        
        if not user_id or not date_str:
            return jsonify({"error": "user_id and date parameters are required"}), 400
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get scheduled tasks
        tasks = db.get_tasks_by_date_range(user_id, start_of_day, end_of_day)
        
        # Check for overlapping tasks
        conflicts = []
        for i, task1 in enumerate(tasks):
            if not task1.get('scheduled_start') or not task1.get('scheduled_end'):
                continue
                
            for j, task2 in enumerate(tasks[i+1:], i+1):
                if not task2.get('scheduled_start') or not task2.get('scheduled_end'):
                    continue
                
                # Parse times
                try:
                    start1 = datetime.fromisoformat(task1['scheduled_start'])
                    end1 = datetime.fromisoformat(task1['scheduled_end'])
                    start2 = datetime.fromisoformat(task2['scheduled_start'])
                    end2 = datetime.fromisoformat(task2['scheduled_end'])
                    
                    # Check for overlap
                    if start1 < end2 and end1 > start2:
                        conflicts.append({
                            "task1": {"id": task1['id'], "title": task1['title'], "time": f"{start1} - {end1}"},
                            "task2": {"id": task2['id'], "title": task2['title'], "time": f"{start2} - {end2}"},
                            "type": "task_overlap"
                        })
                except:
                    continue
        
        return jsonify({
            "date": date_str,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "has_conflicts": len(conflicts) > 0
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to check conflicts: {str(e)}"}), 500

@app.route('/api/tasks', methods=['GET'])
def get_user_tasks():
    """
    Get all tasks for a specific user
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        tasks = db.get_tasks_by_user(user_id)
        
        return jsonify({
            "tasks": tasks,
            "total_count": len(tasks)
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get tasks: {str(e)}"}), 500

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Update a specific task
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        updated_task = db.update_task(task_id, data)
        
        if updated_task:
            return jsonify({
                "message": "Task updated successfully",
                "task": updated_task
            })
        else:
            return jsonify({"error": "Task not found or update failed"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Delete a specific task
    """
    try:
        success = db.delete_task(task_id)
        
        if success:
            return jsonify({"message": "Task deleted successfully"})
        else:
            return jsonify({"error": "Task not found or delete failed"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete task: {str(e)}"}), 500

@app.route('/api/test-openai', methods=['GET'])
def test_openai():
    """
    Test OpenAI API connection
    """
    try:
        print(f"🧪 Testing OpenAI API connection...")
        response = get_openai_client().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say hello in one word"}
            ],
            max_tokens=10
        )
        result = response.choices[0].message.content
        print(f"✅ OpenAI test successful: {result}")
        return jsonify({"status": "success", "response": result})
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return jsonify({"status": "error", "error": str(e)})

@app.route('/api/test-supabase', methods=['GET'])
def test_supabase():
    """
    Test Supabase database connection
    """
    try:
        print(f"🧪 Testing Supabase database connection...")
        
        # Ensure database is initialized
        db._ensure_initialized()
        
        # Test basic connection by trying to query the users table
        result = db.supabase.table('users').select('count').execute()
        
        print(f"✅ Supabase connection successful")
        return jsonify({
            "status": "success", 
            "message": "Supabase connection working",
            "database_url": os.getenv('SUPABASE_URL', 'Not set'),
            "has_anon_key": bool(os.getenv('SUPABASE_KEY')),
            "has_service_key": bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY')),
            "table_count": len(result.data) if result.data else 0
        })
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "database_url": os.getenv('SUPABASE_URL', 'Not set'),
            "has_anon_key": bool(os.getenv('SUPABASE_KEY')),
            "has_service_key": bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
        })

@app.route('/api/test-create-user', methods=['POST'])
def test_create_user():
    """
    Test user creation directly using service role
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Please provide user data in request body"}), 400
        
        print(f"🧪 Testing direct user creation with service role...")
        
        # Use service client to bypass RLS
        service_client = db._get_service_client()
        
        # Use data from request
        user_data = {
            "google_id": data.get("google_id"),
            "email": data.get("email"),
            "name": data.get("name"),
            "calendar_id": data.get("calendar_id", "primary"),
            "preferences": data.get("preferences", {})
        }
        
        # Provide defaults for optional fields
        if not user_data["google_id"]:
            user_data["google_id"] = f"user_{int(datetime.now().timestamp())}"
        if not user_data["email"]:
            user_data["email"] = f"user_{int(datetime.now().timestamp())}@example.com"
        if not user_data["name"]:
            user_data["name"] = f"User {int(datetime.now().timestamp())}"
        if not user_data["preferences"]:
            user_data["preferences"] = {
                "work_hours": {"start": "09:00", "end": "17:00"},
                "break_duration": 15,
                "timezone": "UTC"
            }
        
        # Try to insert directly with service client
        result = service_client.table('users').insert(user_data).execute()
        
        print(f"✅ User creation successful: {result.data}")
        return jsonify({
            "status": "success", 
            "message": "User created successfully",
            "user_data": result.data[0] if result.data else None
        })
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        })

@app.route('/api/test-get-users', methods=['GET'])
def test_get_users():
    """
    Test getting all users using service role
    """
    try:
        print(f"🧪 Testing get all users with service role...")
        
        # Use service client to bypass RLS
        service_client = db._get_service_client()
        
        # Get all users
        result = service_client.table('users').select('*').execute()
        
        print(f"✅ Users retrieved successfully: {len(result.data)} users found")
        return jsonify({
            "status": "success", 
            "message": f"Retrieved {len(result.data)} users",
            "users": result.data
        })
    except Exception as e:
        print(f"❌ Get users test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        })

@app.route('/api/test-create-task', methods=['POST'])
def test_create_task():
    """
    Test creating a task for the test user using service role
    """
    try:
        print(f"🧪 Testing task creation with service role...")
        
        # Use service client to bypass RLS
        service_client = db._get_service_client()
        
        # Create test task data
        task_data = {
            "user_id": "296f52b9-df50-4738-a3fa-17302ae2bb13",  # Test user ID
            "title": "Test Task - Work on Project",
            "description": "This is a test task created for the test user",
            "estimated_duration": 120,  # 2 hours in minutes
            "priority": 3,
            "category": "work",
            "status": "pending",
            "scheduled_start": "2025-09-28T09:00:00Z",
            "scheduled_end": "2025-09-28T11:00:00Z"
        }
        
        # Try to insert task with service client
        result = service_client.table('tasks').insert(task_data).execute()
        
        print(f"✅ Task creation successful: {result.data}")
        return jsonify({
            "status": "success", 
            "message": "Task created successfully",
            "task_data": result.data[0] if result.data else None
        })
    except Exception as e:
        print(f"❌ Task creation test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        })

@app.route('/api/test-get-tasks', methods=['GET'])
def test_get_tasks():
    """
    Test getting all tasks using service role
    """
    try:
        print(f"🧪 Testing get all tasks with service role...")
        
        # Use service client to bypass RLS
        service_client = db._get_service_client()
        
        # Get all tasks
        result = service_client.table('tasks').select('*').execute()
        
        print(f"✅ Tasks retrieved successfully: {len(result.data)} tasks found")
        return jsonify({
            "status": "success", 
            "message": f"Retrieved {len(result.data)} tasks",
            "tasks": result.data
        })
    except Exception as e:
        print(f"❌ Get tasks test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        })

@app.route('/api/test-get-user-tasks', methods=['GET'])
def test_get_user_tasks():
    """
    Test getting tasks for specific user using both methods
    """
    try:
        user_id = "296f52b9-df50-4738-a3fa-17302ae2bb13"
        print(f"🧪 Testing get user tasks for user: {user_id}")
        
        # Test the database method directly
        tasks = db.get_tasks_by_user(user_id)
        print(f"✅ Database method returned: {len(tasks)} tasks")
        
        # Also test with service client directly
        service_client = db._get_service_client()
        result = service_client.table('tasks').select('*').eq('user_id', user_id).execute()
        print(f"✅ Service client returned: {len(result.data)} tasks")
        
        return jsonify({
            "status": "success", 
            "database_method_tasks": len(tasks),
            "service_client_tasks": len(result.data),
            "database_method_result": tasks,
            "service_client_result": result.data
        })
    except Exception as e:
        print(f"❌ Get user tasks test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        })

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """
    Get user task statistics
    """
    try:
        user_id = request.args.get('user_id')
        days_back = int(request.args.get('days_back', 30))
        
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        stats = db.get_user_task_stats(user_id, days_back)
        
        if stats:
            return jsonify({
                "user_id": user_id,
                "days_back": days_back,
                "stats": stats
            })
        else:
            return jsonify({
                "user_id": user_id,
                "days_back": days_back,
                "stats": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "completion_rate": 0.0,
                    "avg_completion_time": 0.0
                }
            })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user stats: {str(e)}"}), 500

@app.route('/api/user/insights', methods=['GET'])
def get_productivity_insights():
    """
    Get productivity insights for a user
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        insights = db.get_productivity_insights(user_id)
        
        return jsonify({
            "user_id": user_id,
            "insights": insights
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get productivity insights: {str(e)}"}), 500

@app.route('/api/user/create', methods=['POST'])
def create_user():
    """
    Create a new user with Google authentication
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Provide defaults for all fields - make everything optional
        user_data = {
            'google_id': data.get('google_id', f"user_{int(datetime.now().timestamp())}"),
            'email': data.get('email', f"user_{int(datetime.now().timestamp())}@example.com"),
            'name': data.get('name', f"User {int(datetime.now().timestamp())}"),
            'calendar_id': data.get('calendar_id', 'primary'),
            'preferences': data.get('preferences', {
                "work_hours": {"start": "09:00", "end": "17:00"},
                "break_duration": 15,
                "timezone": "UTC"
            })
        }
        
        created_user = db.create_user_with_google(**user_data)
        
        if created_user:
            return jsonify({
                "message": "User created successfully",
                "user": created_user
            })
        else:
            return jsonify({"error": "Failed to create user"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to create user: {str(e)}"}), 500

@app.route('/api/user/<google_id>', methods=['GET'])
def get_user_by_google_id(google_id):
    """
    Get user by Google ID
    """
    try:
        user = db.get_user_by_google_id(google_id)
        
        if user:
            return jsonify({"user": user})
        else:
            return jsonify({"error": "User not found"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500

@app.route('/api/tasks/<task_id>/complete', methods=['PUT'])
def mark_task_complete(task_id):
    """
    Mark a task as completed and record actual duration
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        actual_duration = data.get('actual_duration')
        if actual_duration is None:
            return jsonify({"error": "actual_duration is required"}), 400
        
        update_data = {
            'status': 'completed',
            'actual_duration': actual_duration
        }
        
        updated_task = db.update_task(task_id, update_data)
        
        if updated_task:
            # Save pattern for AI learning
            pattern_data = {
                'user_id': updated_task['user_id'],
                'task_category': updated_task.get('category', 'general'),
                'estimated_duration': updated_task.get('estimated_duration'),
                'actual_duration': actual_duration,
                'completion_rate': 1.0,  # Completed task
                'optimal_time_slot': 'morning'  # Default, could be calculated from scheduled_start
            }
            db.save_task_pattern(pattern_data)
            
            return jsonify({
                "message": "Task marked as completed",
                "task": updated_task
            })
        else:
            return jsonify({"error": "Task not found or update failed"}), 404
        
    except Exception as e:
        return jsonify({"error": f"Failed to mark task complete: {str(e)}"}), 500

# Google Calendar Integration Endpoints
# These endpoints return JSON in the format expected by your Google Calendar server

@app.route('/api/calendar/events/create', methods=['POST'])
def create_calendar_event():
    """
    Create a calendar event - returns JSON compatible with CreateEventRequest
    """
    try:
        data = request.get_json()
        
        if not data or 'scheduled_tasks' not in data:
            return jsonify({"error": "Please provide 'scheduled_tasks' field in request body"}), 400
        
        user_id = data.get('user_id')
        scheduled_tasks_data = data['scheduled_tasks']
        calendar_id = data.get('calendar_id', 'primary')
        
        if not scheduled_tasks_data:
            return jsonify({"error": "No tasks provided"}), 400
        
        # Convert scheduled tasks to Google Calendar event format
        calendar_events = []
        for task_data in scheduled_tasks_data:
            event = {
                "title": task_data["title"],
                "start_datetime": task_data.get("start_time", ""),
                "end_datetime": task_data.get("end_time", ""),
                "description": task_data.get("description", ""),
                "calendar_id": calendar_id
            }
            calendar_events.append(event)
        
        return jsonify({
            "events": calendar_events,
            "message": f"Created {len(calendar_events)} calendar events",
            "calendar_id": calendar_id
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to create calendar events: {str(e)}"}), 500

@app.route('/api/calendar/events/find', methods=['POST'])
def find_calendar_events():
    """
    Find calendar events by date - returns JSON compatible with FindEventsRequest
    """
    try:
        data = request.get_json()
        
        if not data or 'date' not in data:
            return jsonify({"error": "Please provide 'date' field in request body"}), 400
        
        date_str = data['date']
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        # Get user tasks for the specified date
        try:
            target_date = datetime.fromisoformat(date_str)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            tasks = db.get_tasks_by_date_range(user_id, start_of_day, end_of_day)
            
            # Convert tasks to calendar event format
            events = []
            for task in tasks:
                if task.get('scheduled_start') and task.get('scheduled_end'):
                    event = {
                        "title": task["title"],
                        "start_datetime": task["scheduled_start"],
                        "end_datetime": task["scheduled_end"],
                        "description": task.get("description", ""),
                        "calendar_id": "primary"
                    }
                    events.append(event)
            
            return jsonify({
                "date": date_str,
                "events": events,
                "total_events": len(events)
            })
            
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD format"}), 400
        
    except Exception as e:
        return jsonify({"error": f"Failed to find calendar events: {str(e)}"}), 500

@app.route('/api/calendar/events/move', methods=['POST'])
def move_calendar_event():
    """
    Move a calendar event - returns JSON compatible with MoveEventRequest
    """
    try:
        data = request.get_json()
        
        if not data or 'task_id' not in data:
            return jsonify({"error": "Please provide 'task_id' field in request body"}), 400
        
        task_id = data['task_id']
        new_start_datetime = data.get('new_start_datetime')
        new_end_datetime = data.get('new_end_datetime')
        calendar_id = data.get('calendar_id', 'primary')
        
        if not new_start_datetime or not new_end_datetime:
            return jsonify({"error": "new_start_datetime and new_end_datetime are required"}), 400
        
        # Get the current task
        task = db.get_task_by_id(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        # Update the task with new times
        update_data = {
            'scheduled_start': new_start_datetime,
            'scheduled_end': new_end_datetime
        }
        
        updated_task = db.update_task(task_id, update_data)
        
        if updated_task:
            move_request = {
                "title": updated_task["title"],
                "current_start_datetime": task["scheduled_start"],
                "new_start_datetime": new_start_datetime,
                "new_end_datetime": new_end_datetime,
                "calendar_id": calendar_id
            }
            
            return jsonify({
                "move_request": move_request,
                "message": "Event move request created successfully",
                "task_id": task_id
            })
        else:
            return jsonify({"error": "Failed to update task"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to move calendar event: {str(e)}"}), 500

@app.route('/api/calendar/create', methods=['POST'])
def create_calendar():
    """
    Create a new calendar - returns JSON compatible with CreateCalendarRequest
    """
    try:
        data = request.get_json()
        
        if not data or 'calendar_name' not in data:
            return jsonify({"error": "Please provide 'calendar_name' field in request body"}), 400
        
        calendar_name = data['calendar_name']
        description = data.get('description', '')
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        # Create calendar request
        calendar_request = {
            "calendar_name": calendar_name,
            "description": description
        }
        
        return jsonify({
            "calendar_request": calendar_request,
            "message": "Calendar creation request created successfully",
            "user_id": user_id
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to create calendar request: {str(e)}"}), 500

@app.route('/api/calendar/events/find-specific', methods=['POST'])
def find_specific_calendar_event():
    """
    Find a specific calendar event - returns JSON compatible with FindEventRequest
    """
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'start_datetime' not in data:
            return jsonify({"error": "Please provide 'title' and 'start_datetime' fields in request body"}), 400
        
        title = data['title']
        start_datetime = data['start_datetime']
        calendar_id = data.get('calendar_id', 'primary')
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        # Find task by title and start time
        try:
            target_datetime = datetime.fromisoformat(start_datetime)
            tasks = db.get_tasks_by_user(user_id)
            
            # Find matching task
            matching_task = None
            for task in tasks:
                if (task["title"].lower() == title.lower() and 
                    task.get("scheduled_start") and
                    abs((datetime.fromisoformat(task["scheduled_start"]) - target_datetime).total_seconds()) < 3600):  # Within 1 hour
                    matching_task = task
                    break
            
            if matching_task:
                find_request = {
                    "title": title,
                    "start_datetime": start_datetime,
                    "calendar_id": calendar_id
                }
                
                return jsonify({
                    "find_request": find_request,
                    "task_found": True,
                    "task": matching_task,
                    "message": "Event found successfully"
                })
            else:
                return jsonify({
                    "find_request": {
                        "title": title,
                        "start_datetime": start_datetime,
                        "calendar_id": calendar_id
                    },
                    "task_found": False,
                    "message": "No matching event found"
                })
                
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use ISO format"}), 400
        
    except Exception as e:
        return jsonify({"error": f"Failed to find specific calendar event: {str(e)}"}), 500

# For Vercel deployment
if __name__ == '__main__':
    # Local development
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
