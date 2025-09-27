"""
Data models for TimeAPI
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class TaskStatus(Enum):
    """Task status options"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskCategory(Enum):
    """Task categories"""
    WORK = "work"
    PERSONAL = "personal"
    HEALTH = "health"
    LEARNING = "learning"
    SOCIAL = "social"
    GENERAL = "general"

class ScheduledTask:
    """Represents a scheduled task"""
    def __init__(self, title: str, description: str = "", start_time: datetime = None, 
                 end_time: datetime = None, priority: TaskPriority = TaskPriority.MEDIUM,
                 category: TaskCategory = TaskCategory.GENERAL, reasoning: str = ""):
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
        self.category = category
        self.reasoning = reasoning

class TaskPlanningRequest:
    """Request for task planning"""
    def __init__(self, user_input: str, date: Optional[datetime] = None, user_id: str = None):
        self.user_input = user_input
        self.date = date
        self.user_id = user_id

class TaskPlanningResponse:
    """Response from task planning"""
    def __init__(self, scheduled_tasks: List[ScheduledTask], summary: str = "", 
                 conflicts: List[str] = None, suggestions: List[str] = None):
        self.scheduled_tasks = scheduled_tasks
        self.summary = summary
        self.conflicts = conflicts or []
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "scheduled_tasks": [
                {
                    "title": task.title,
                    "description": task.description,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "priority": task.priority.value,
                    "category": task.category.value,
                    "reasoning": task.reasoning
                }
                for task in self.scheduled_tasks
            ],
            "summary": self.summary,
            "conflicts": self.conflicts,
            "suggestions": self.suggestions
        }

class OptimizationRequest:
    """Request for schedule optimization"""
    def __init__(self, date: Optional[datetime] = None, user_id: str = None):
        self.date = date
        self.user_id = user_id

class OptimizationResponse:
    """Response from schedule optimization"""
    def __init__(self, optimized_schedule: List[ScheduledTask], changes_made: List[str] = None,
                 reasoning: str = "", success: bool = True):
        self.optimized_schedule = optimized_schedule
        self.changes_made = changes_made or []
        self.reasoning = reasoning
        self.success = success
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
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
                for task in self.optimized_schedule
            ],
            "changes_made": self.changes_made,
            "reasoning": self.reasoning,
            "success": self.success
        }

class User:
    """User model with Google integration"""
    def __init__(self, id: str = None, google_id: str = "", email: str = "", name: str = "", 
                 calendar_id: str = "", preferences: Dict[str, Any] = None, 
                 created_at: datetime = None, updated_at: datetime = None):
        self.id = id
        self.google_id = google_id
        self.email = email
        self.name = name
        self.calendar_id = calendar_id
        self.preferences = preferences or {}
        self.created_at = created_at
        self.updated_at = updated_at

class Task:
    """Task model for database operations with enhanced fields"""
    def __init__(self, id: str = None, user_id: str = None, title: str = "", 
                 description: str = "", estimated_duration: int = None, 
                 actual_duration: int = None, priority: int = 3, 
                 category: str = None, status: str = "pending",
                 google_event_id: str = None, scheduled_start: datetime = None, 
                 scheduled_end: datetime = None, created_at: datetime = None, 
                 updated_at: datetime = None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.estimated_duration = estimated_duration
        self.actual_duration = actual_duration
        self.priority = priority
        self.category = category
        self.status = status
        self.google_event_id = google_event_id
        self.scheduled_start = scheduled_start
        self.scheduled_end = scheduled_end
        self.created_at = created_at
        self.updated_at = updated_at

class UserPattern:
    """User pattern model for AI learning"""
    def __init__(self, id: str = None, user_id: str = None, task_category: str = None,
                 estimated_duration: int = None, actual_duration: int = None,
                 completion_rate: float = None, optimal_time_slot: str = None,
                 created_at: datetime = None):
        self.id = id
        self.user_id = user_id
        self.task_category = task_category
        self.estimated_duration = estimated_duration
        self.actual_duration = actual_duration
        self.completion_rate = completion_rate
        self.optimal_time_slot = optimal_time_slot
        self.created_at = created_at

class TaskStats:
    """Task statistics model"""
    def __init__(self, total_tasks: int = 0, completed_tasks: int = 0, 
                 completion_rate: float = 0.0, avg_completion_time: float = 0.0):
        self.total_tasks = total_tasks
        self.completed_tasks = completed_tasks
        self.completion_rate = completion_rate
        self.avg_completion_time = avg_completion_time

class ProductivityInsight:
    """Productivity insight model"""
    def __init__(self, category: str = "", task_count: int = 0, 
                 completion_rate: float = 0.0, avg_duration: float = 0.0,
                 most_productive_time: str = "morning"):
        self.category = category
        self.task_count = task_count
        self.completion_rate = completion_rate
        self.avg_duration = avg_duration
        self.most_productive_time = most_productive_time
