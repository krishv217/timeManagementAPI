# TimeAPI 2.0 - Advanced Task Scheduling with Supabase Integration

## Overview

TimeAPI has been upgraded to version 2.0 with advanced AI-powered scheduling capabilities and Supabase database integration. The application now supports user personalization, schedule optimization, conflict detection, and persistent task management.

## New Features

### 🚀 Advanced AI Scheduling
- **Intelligent Task Planning**: AI analyzes user input and creates optimized schedules
- **Personalization**: Learns from user patterns and preferences
- **Schedule Optimization**: Automatically optimizes existing schedules
- **Conflict Detection**: Identifies and resolves scheduling conflicts

### 🗄️ Database Integration
- **Supabase Integration**: Full PostgreSQL database support
- **User Management**: Individual user accounts and preferences
- **Task Persistence**: Tasks are saved and managed in the database
- **Pattern Learning**: Tracks user completion patterns for better scheduling

### 📊 Enhanced API
- **RESTful Endpoints**: Clean API design with proper HTTP methods
- **User-Specific Data**: All operations are scoped to individual users
- **Real-time Updates**: Tasks can be updated and managed in real-time
- **Comprehensive Error Handling**: Detailed error messages and status codes

## Setup Instructions

### 1. Environment Variables

Add these environment variables to your Vercel project:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

### 2. Supabase Database Setup

1. Create a new Supabase project
2. Run the SQL schema from `supabase_schema.sql` in your Supabase SQL editor
3. Copy your project URL and API keys to Vercel environment variables

### 3. Deploy to Vercel

The application is ready to deploy with the included `vercel.json` configuration.

## API Endpoints

### Basic Scheduling (Legacy)
- `POST /schedule` - Schedule tasks from text input
- `GET /tasks` - Get all scheduled tasks
- `DELETE /tasks` - Clear all tasks

### Advanced Scheduling
- `POST /api/plan` - AI-powered task planning
- `POST /api/optimize` - Optimize existing schedule
- `POST /api/accept` - Accept generated schedule
- `GET /api/conflicts` - Check for conflicts
- `GET /api/tasks` - Get user tasks
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task

### Utility
- `GET /health` - Health check
- `GET /api/test-openai` - Test OpenAI connection
- `GET /docs` - API documentation

## Usage Examples

### Basic Task Planning

```bash
curl -X POST https://your-app.vercel.app/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I need to work on my presentation, exercise, and have dinner",
    "user_id": "user123",
    "date": "2024-01-15T00:00:00Z"
  }'
```

### Schedule Optimization

```bash
curl -X POST https://your-app.vercel.app/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "date": "2024-01-15T00:00:00Z"
  }'
```

### Accept Generated Schedule

```bash
curl -X POST https://your-app.vercel.app/api/accept \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "scheduled_tasks": [
      {
        "title": "Work on presentation",
        "description": "Prepare slides for quarterly review",
        "start_time": "2024-01-15T09:00:00",
        "end_time": "2024-01-15T11:00:00",
        "priority": 4,
        "category": "work"
      }
    ]
  }'
```

### Check for Conflicts

```bash
curl "https://your-app.vercel.app/api/conflicts?user_id=user123&date=2024-01-15"
```

## Database Schema

### Users Table
- `id` - UUID primary key
- `email` - User email (unique)
- `name` - User display name
- `preferences` - JSON preferences object
- `created_at`, `updated_at` - Timestamps

### Tasks Table
- `id` - UUID primary key
- `user_id` - Foreign key to users
- `title` - Task title
- `description` - Task description
- `estimated_duration` - Duration in minutes
- `priority` - Priority level (1-5)
- `category` - Task category
- `scheduled_start`, `scheduled_end` - Scheduled times
- `status` - Task status
- `created_at`, `updated_at` - Timestamps

### User Preferences Table
- `id` - UUID primary key
- `user_id` - Foreign key to users
- `preferences` - JSON preferences object
- `created_at`, `updated_at` - Timestamps

### Task Patterns Table
- `id` - UUID primary key
- `user_id` - Foreign key to users
- `task_category` - Category of task
- `estimated_duration` - Estimated duration
- `actual_duration` - Actual completion time
- `optimal_time_slot` - Best time for this task type
- `completion_rate` - Success rate
- `created_at` - Timestamp

## Migration from v1.0

The original endpoints (`/schedule`, `/tasks`) are still available for backward compatibility. To migrate:

1. Update your client to use the new `/api/*` endpoints
2. Implement user authentication to get user IDs
3. Use the new task management endpoints for CRUD operations
4. Take advantage of AI optimization features

## Security

- Row Level Security (RLS) is enabled on all tables
- Users can only access their own data
- API keys are stored securely in Vercel environment variables
- Supabase handles authentication and authorization

## Performance

- Database indexes on frequently queried columns
- Efficient query patterns for date ranges
- Caching of user preferences and patterns
- Optimized AI prompts for faster responses

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify Supabase URL and keys are correct
   - Check if database schema is properly set up
   - Ensure RLS policies are configured

2. **OpenAI API Errors**
   - Verify API key is valid and has credits
   - Check rate limits and usage quotas
   - Test connection with `/api/test-openai` endpoint

3. **Task Creation Failures**
   - Ensure user_id is provided for database operations
   - Check date formats (use ISO 8601)
   - Verify required fields are present

### Debug Mode

Enable debug logging by setting `FLASK_ENV=development` in your environment variables.

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Test endpoints with the provided examples
3. Review error messages in the response body
4. Check Vercel function logs for detailed error information

## Future Enhancements

- Calendar integration (Google Calendar, Outlook)
- Team scheduling and collaboration
- Mobile app support
- Advanced analytics and reporting
- Integration with productivity tools
