"""
Supabase database integration for TimeAPI
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL', '').strip()
        self.supabase_key = os.getenv('SUPABASE_KEY', '').strip()
        self.supabase: Client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of Supabase client"""
        if not self._initialized:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                self._initialized = True
            except Exception as e:
                print(f"Error initializing Supabase client: {e}")
                raise e
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user in the database"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new task"""
        try:
            self._ensure_initialized()
            # Ensure required fields are present
            required_fields = ['user_id', 'title']
            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"Missing required field: {field}")
            
            result = self.supabase.table('tasks').insert(task_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('tasks').select('*').eq('id', task_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
    
    def get_tasks_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a user"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('tasks').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting user tasks: {e}")
            return []
    
    def get_tasks_by_date_range(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get tasks within a date range"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('tasks').select('*').eq('user_id', user_id).gte('scheduled_start', start_date.isoformat()).lte('scheduled_start', end_date.isoformat()).order('scheduled_start').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting tasks by date range: {e}")
            return []
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('tasks').update(update_data).eq('id', task_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating task: {e}")
            return None
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('tasks').delete().eq('id', task_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
    
    def get_user_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's task completion patterns for AI optimization"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('user_patterns').select('*').eq('user_id', user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting user patterns: {e}")
            return []
    
    def save_task_pattern(self, pattern_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save task completion pattern for future optimization"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('user_patterns').insert(pattern_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error saving task pattern: {e}")
            return None
    
    def get_user_task_stats(self, user_id: str, days_back: int = 30) -> Optional[Dict[str, Any]]:
        """Get user task statistics using the database function"""
        try:
            self._ensure_initialized()
            result = self.supabase.rpc('get_user_task_stats', {
                'user_uuid': user_id,
                'days_back': days_back
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user task stats: {e}")
            return None
    
    def get_productivity_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Get productivity insights using the database function"""
        try:
            self._ensure_initialized()
            result = self.supabase.rpc('get_productivity_insights', {
                'user_uuid': user_id
            }).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting productivity insights: {e}")
            return []
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences from users table"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('users').select('preferences').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user preferences in users table"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('users').update({'preferences': preferences}).eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating user preferences: {e}")
            return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID"""
        try:
            self._ensure_initialized()
            result = self.supabase.table('users').select('*').eq('google_id', google_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user by Google ID: {e}")
            return None
    
    def create_user_with_google(self, google_id: str, email: str, name: str = "", calendar_id: str = "", preferences: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Create a new user with Google authentication"""
        try:
            self._ensure_initialized()
            user_data = {
                'google_id': google_id,
                'email': email,
                'name': name,
                'calendar_id': calendar_id,
                'preferences': preferences or {}
            }
            result = self.supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating user with Google: {e}")
            return None

# Global database instance
db = Database()
