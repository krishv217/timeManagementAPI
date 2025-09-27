from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
import json

from app.models import (
    User, Task, TaskPlanningRequest, TaskPlanningResponse, 
    ScheduledTask, TaskPriority, OptimizationRequest, OptimizationResponse
)
from app.routers.auth import get_current_user
from app.database import get_db, Database

router = APIRouter()

# OpenAI Configuration
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ScheduleOptimizer:
    def __init__(self, db: Database):
        self.db = db
    
    async def get_user_preferences(self, user: User) -> Dict[str, Any]:
        """Get user preferences for scheduling"""
        default_preferences = {
            "work_hours": {"start": "09:00", "end": "17:00"},
            "focus_times": ["09:00-11:00", "14:00-16:00"],
            "buffer_time": 15,
            "max_daily_tasks": 8,
            "preferred_task_duration": 60
        }
        
        # Merge user preferences with defaults to ensure all keys exist
        if user.preferences:
            merged_preferences = default_preferences.copy()
            merged_preferences.update(user.preferences)
            return merged_preferences
        
        return default_preferences
    
    async def get_existing_calendar_events(self, user: User, date: datetime) -> List[Dict]:
        """Get existing calendar events for conflict detection"""
        # This would integrate with the calendar service
        # For now, return mock data
        return []
    
    async def analyze_user_patterns(self, user: User) -> Dict[str, Any]:
        """Analyze user's historical task completion patterns"""
        patterns = await self.db.get_user_patterns(user.id)
        
        if not patterns:
            return {
                "average_completion_time": 60,
                "optimal_time_slots": ["morning"],
                "category_durations": {}
            }
        
        # Analyze patterns
        category_durations = {}
        for pattern in patterns:
            if pattern.task_category not in category_durations:
                category_durations[pattern.task_category] = []
            category_durations[pattern.task_category].append(pattern.actual_duration)
        
        # Calculate averages
        for category in category_durations:
            durations = category_durations[category]
            category_durations[category] = sum(durations) / len(durations)
        
        return {
            "average_completion_time": sum(p.actual_duration for p in patterns) / len(patterns),
            "optimal_time_slots": list(set(p.optimal_time_slot for p in patterns)),
            "category_durations": category_durations
        }
    
    async def generate_schedule_with_ai(self, user_input: str, user: User, date: datetime) -> TaskPlanningResponse:
        """Use OpenAI to generate optimized schedule"""
        try:
            preferences = await self.get_user_preferences(user)
            patterns = await self.analyze_user_patterns(user)
            existing_events = await self.get_existing_calendar_events(user, date)
            
            system_prompt = f"""
You are an intelligent scheduling assistant. Given a user's natural language request 
and their existing calendar, create an optimized daily schedule.

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

Respond with a JSON object containing:
{{
  "scheduled_tasks": [
    {{
      "title": "task title",
      "description": "task description",
      "start_time": "2024-01-01T09:00:00",
      "end_time": "2024-01-01T10:00:00",
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
"""

            print(f"🤖 Calling OpenAI API for schedule generation...")
            print(f"📝 User input received: {user_input}")
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using gpt-3.5-turbo instead of gpt-4 for better availability
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
            
            # Convert to Pydantic models
            scheduled_tasks = []
            for task_data in schedule_data.get("scheduled_tasks", []):
                try:
                    scheduled_task = ScheduledTask(
                        title=task_data["title"],
                        description=task_data.get("description", ""),
                        start_time=datetime.fromisoformat(task_data["start_time"]),
                        end_time=datetime.fromisoformat(task_data["end_time"]),
                        priority=TaskPriority(task_data.get("priority", 3)),
                        category=task_data.get("category", "general"),
                        reasoning=task_data.get("reasoning", "")
                    )
                    scheduled_tasks.append(scheduled_task)
                except Exception as e:
                    print(f"Error parsing scheduled task: {e}")
                    continue
            
            return TaskPlanningResponse(
                scheduled_tasks=scheduled_tasks,
                summary=schedule_data.get("summary", "Schedule generated successfully"),
                conflicts=schedule_data.get("conflicts", []),
                suggestions=schedule_data.get("suggestions", [])
            )
            
        except Exception as e:
            print(f"💥 Error generating schedule with AI: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return TaskPlanningResponse(
                scheduled_tasks=[],
                summary=f"Failed to generate schedule due to AI service error: {str(e)}",
                conflicts=[],
                suggestions=["Please check OpenAI API key and try again"]
            )

@router.post("/plan", response_model=TaskPlanningResponse)
async def plan_tasks(
    planning_request: TaskPlanningRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Process natural language input and create optimized schedule"""
    try:
        print(f"🎯 Generating schedule for user: {current_user.email}")
        print(f"📝 User input: {planning_request.user_input}")
        
        optimizer = ScheduleOptimizer(db)
        
        # Use provided date or default to today
        target_date = planning_request.date or datetime.now()
        
        # Generate schedule using AI
        schedule_response = await optimizer.generate_schedule_with_ai(
            planning_request.user_input,
            current_user,
            target_date
        )
        
        # Don't save tasks yet - wait for user to accept the schedule
        print(f"✅ Generated {len(schedule_response.scheduled_tasks)} tasks (not saved until accepted)")
        
        return schedule_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to plan tasks: {str(e)}"
        )

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_schedule(
    optimization_request: OptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Trigger AI-powered schedule optimization"""
    try:
        optimizer = ScheduleOptimizer(db)
        target_date = optimization_request.date or datetime.now()
        
        # Get existing tasks for the date
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        existing_tasks = await db.get_tasks_by_date_range(
            current_user.id, 
            start_of_day, 
            end_of_day
        )
        
        if not existing_tasks:
            return OptimizationResponse(
                optimized_schedule=[],
                changes_made=[],
                reasoning="No tasks found for optimization",
                success=False
            )
        
        # Create optimization prompt
        task_descriptions = []
        for task in existing_tasks:
            task_descriptions.append(f"- {task.title} (Priority: {task.priority}, Duration: {task.estimated_duration}min)")
        
        optimization_input = f"Optimize the following tasks: {'; '.join(task_descriptions)}"
        
        # Use AI to optimize
        schedule_response = await optimizer.generate_schedule_with_ai(
            optimization_input,
            current_user,
            target_date
        )
        
        # Update existing tasks with optimized schedule
        changes_made = []
        for i, scheduled_task in enumerate(schedule_response.scheduled_tasks):
            if i < len(existing_tasks):
                existing_task = existing_tasks[i]
                update_data = {
                    "scheduled_start": scheduled_task.start_time,
                    "scheduled_end": scheduled_task.end_time,
                    "priority": scheduled_task.priority.value
                }
                
                updated_task = await db.update_task(existing_task.id, update_data)
                if updated_task:
                    changes_made.append(f"Moved '{existing_task.title}' to {scheduled_task.start_time.strftime('%H:%M')}")
        
        return OptimizationResponse(
            optimized_schedule=schedule_response.scheduled_tasks,
            changes_made=changes_made,
            reasoning=schedule_response.summary,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize schedule: {str(e)}"
        )

@router.get("/conflicts")
async def check_schedule_conflicts(
    date: str,  # YYYY-MM-DD format
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Check for scheduling conflicts on a specific date"""
    try:
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get scheduled tasks
        tasks = await db.get_tasks_by_date_range(current_user.id, start_of_day, end_of_day)
        
        # Check for overlapping tasks
        conflicts = []
        for i, task1 in enumerate(tasks):
            if not task1.scheduled_start or not task1.scheduled_end:
                continue
                
            for j, task2 in enumerate(tasks[i+1:], i+1):
                if not task2.scheduled_start or not task2.scheduled_end:
                    continue
                
                # Check for overlap
                if (task1.scheduled_start < task2.scheduled_end and 
                    task1.scheduled_end > task2.scheduled_start):
                    conflicts.append({
                        "task1": {"id": task1.id, "title": task1.title, "time": f"{task1.scheduled_start} - {task1.scheduled_end}"},
                        "task2": {"id": task2.id, "title": task2.title, "time": f"{task2.scheduled_start} - {task2.scheduled_end}"},
                        "type": "task_overlap"
                    })
        
        return {
            "date": date,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "has_conflicts": len(conflicts) > 0
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check conflicts: {str(e)}"
        )

@router.post("/accept")
async def accept_schedule(
    schedule_data: TaskPlanningResponse,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Accept a generated schedule and save tasks to database"""
    try:
        print(f"� Received schedule data: {schedule_data}")
        print(f"📝 Schedule data dict: {schedule_data.dict()}")
        print(f"📊 Scheduled tasks count: {len(schedule_data.scheduled_tasks)}")
        print(f"�💾 Accepting schedule with {len(schedule_data.scheduled_tasks)} tasks for user: {current_user.email}")
        
        if not schedule_data.scheduled_tasks:
            print("⚠️ No tasks in the schedule data!")
            return {
                "message": "No tasks to create",
                "tasks_created": 0
            }
        
        created_tasks = []
        for i, scheduled_task in enumerate(schedule_data.scheduled_tasks):
            print(f"🔄 Processing task {i+1}: {scheduled_task.title}")
            task_data = {
                "user_id": current_user.id,
                "title": scheduled_task.title,
                "description": scheduled_task.description,
                "estimated_duration": int((scheduled_task.end_time - scheduled_task.start_time).total_seconds() / 60),
                "priority": scheduled_task.priority.value,
                "category": scheduled_task.category,
                "scheduled_start": scheduled_task.start_time.isoformat(),
                "scheduled_end": scheduled_task.end_time.isoformat(),
                "status": "pending"
            }
            
            created_task = await db.create_task(task_data)
            if created_task:
                created_tasks.append(created_task)
        
        print(f"✅ Successfully created {len(created_tasks)} tasks in database")
        
        return {
            "message": f"Successfully created {len(created_tasks)} tasks",
            "tasks_created": len(created_tasks)
        }
        
    except Exception as e:
        print(f"💥 Error accepting schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept schedule: {str(e)}"
        )

@router.get("/test-openai")
async def test_openai():
    """Test OpenAI API connection"""
    try:
        print(f"🧪 Testing OpenAI API connection...")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using cheaper model for testing
            messages=[
                {"role": "user", "content": "Say hello in one word"}
            ],
            max_tokens=10
        )
        result = response.choices[0].message.content
        print(f"✅ OpenAI test successful: {result}")
        return {"status": "success", "response": result}
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return {"status": "error", "error": str(e)}

@router.post("/reschedule/{task_id}")
async def reschedule_task(
    task_id: str,
    reschedule_request: dict,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Reschedule a specific task and adjust dependent tasks"""
    try:
        # Get task to reschedule
        task = await db.get_task_by_id(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        if task.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Calculate new end time
        if task.estimated_duration:
            new_end_time = new_start_time + timedelta(minutes=task.estimated_duration)
        else:
            new_end_time = new_start_time + timedelta(hours=1)  # Default 1 hour
        
        # Update task
        update_data = {
            "scheduled_start": new_start_time,
            "scheduled_end": new_end_time
        }
        
        updated_task = await db.update_task(task_id, update_data)
        
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reschedule task"
            )
        
        return {
            "message": "Task rescheduled successfully",
            "task": updated_task,
            "new_schedule": {
                "start_time": new_start_time,
                "end_time": new_end_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule task: {str(e)}"
        )
