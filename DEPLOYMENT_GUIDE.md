# TimeAPI 2.0 Deployment Guide

## 🚀 Quick Deployment to Vercel

### 1. Environment Variables Setup

In your Vercel project settings, add these environment variables:

```bash
# Required for OpenAI integration
OPENAI_API_KEY=your_openai_api_key_here

# Required for Supabase database features
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

### 2. Supabase Database Setup

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL and API keys

2. **Run Database Schema**
   - Open your Supabase project dashboard
   - Go to SQL Editor
   - Copy and paste the contents of `supabase_schema.sql`
   - Execute the SQL to create all required tables

3. **Configure Row Level Security**
   - The schema includes RLS policies
   - Adjust authentication policies based on your needs
   - For testing, you can temporarily disable RLS if needed

### 3. Deploy to Vercel

1. **Connect Repository**
   - Connect your GitHub repository to Vercel
   - The `vercel.json` configuration is already included

2. **Deploy**
   - Vercel will automatically detect the Python app
   - The deployment will use the configuration in `vercel.json`

### 4. Test Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.vercel.app/health

# API documentation
curl https://your-app.vercel.app/

# Test OpenAI connection (requires API key)
curl https://your-app.vercel.app/api/test-openai
```

## 📋 API Endpoints Overview

### Basic Scheduling (Legacy - Still Available)
- `POST /schedule` - Schedule tasks from text input
- `GET /tasks` - Get all scheduled tasks  
- `DELETE /tasks` - Clear all tasks

### Advanced Scheduling (New Features)
- `POST /api/plan` - AI-powered task planning with personalization
- `POST /api/optimize` - Optimize existing schedule using AI
- `POST /api/accept` - Accept generated schedule and save to database
- `GET /api/conflicts` - Check for scheduling conflicts
- `GET /api/tasks` - Get user tasks from database
- `PUT /api/tasks/<id>` - Update specific task
- `DELETE /api/tasks/<id>` - Delete specific task

### Utility Endpoints
- `GET /health` - Health check
- `GET /api/test-openai` - Test OpenAI API connection
- `GET /docs` - Interactive API documentation
- `GET /` - API information and documentation

## 🔧 Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai_api_key",
    "SUPABASE_URL": "@supabase_url",
    "SUPABASE_KEY": "@supabase_key",
    "SUPABASE_SERVICE_ROLE_KEY": "@supabase_service_role_key"
  }
}
```

### requirements.txt
```
Flask==2.3.3
flask-cors==4.0.0
openai==1.12.0
python-dotenv==1.0.0
requests==2.31.0
httpx==0.25.2
supabase==2.3.4
postgrest==0.13.2
```

## 🗄️ Database Schema

The application uses these main tables:

- **users** - User accounts and profiles
- **tasks** - Individual tasks with scheduling information
- **user_preferences** - User scheduling preferences
- **task_patterns** - Historical data for AI optimization

## 🔒 Security Features

- **Row Level Security (RLS)** enabled on all tables
- **User isolation** - users can only access their own data
- **Environment variable protection** - sensitive keys stored securely
- **Input validation** - comprehensive error handling

## 🧪 Testing

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test import
python -c "from app import app; print('✅ App imports successfully')"

# Run locally (optional)
python app.py
```

### API Testing Examples

```bash
# Basic scheduling
curl -X POST https://your-app.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I have a meeting at 2pm and need to exercise"}'

# Advanced planning
curl -X POST https://your-app.vercel.app/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I need to work on my presentation, exercise, and have dinner",
    "user_id": "user123",
    "date": "2024-01-15T00:00:00Z"
  }'

# Check conflicts
curl "https://your-app.vercel.app/api/conflicts?user_id=user123&date=2024-01-15"
```

## 🚨 Troubleshooting

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

## 📈 Performance Considerations

- **Database indexes** on frequently queried columns
- **Efficient query patterns** for date ranges
- **Lazy initialization** of database and OpenAI clients
- **Optimized AI prompts** for faster responses

## 🔄 Migration from v1.0

The original endpoints (`/schedule`, `/tasks`) are still available for backward compatibility. To migrate:

1. Update your client to use the new `/api/*` endpoints
2. Implement user authentication to get user IDs
3. Use the new task management endpoints for CRUD operations
4. Take advantage of AI optimization features

## 📞 Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Test endpoints with the provided examples
3. Review error messages in the response body
4. Check Vercel function logs for detailed error information

## 🎯 Next Steps

After successful deployment:
1. Set up user authentication system
2. Implement frontend client
3. Add calendar integrations
4. Set up monitoring and analytics
5. Configure backup and recovery procedures
