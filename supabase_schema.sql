-- AI Personal Scheduler Database Schema
-- This SQL script creates the necessary tables for the Supabase database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    name TEXT,
    calendar_id TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    estimated_duration INTEGER, -- minutes
    actual_duration INTEGER,
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5), -- 1-5 scale
    category TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    google_event_id TEXT,
    scheduled_start TIMESTAMP WITH TIME ZONE,
    scheduled_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning data for AI improvements
CREATE TABLE IF NOT EXISTS user_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_category TEXT,
    estimated_duration INTEGER,
    actual_duration INTEGER,
    completion_rate FLOAT,
    optimal_time_slot TEXT CHECK (optimal_time_slot IN ('morning', 'afternoon', 'evening')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_start ON tasks(scheduled_start);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_user_patterns_user_id ON user_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_user_patterns_category ON user_patterns(task_category);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop triggers if they exist, then recreate them
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_patterns ENABLE ROW LEVEL SECURITY;

-- Users can only see and modify their own data
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = google_id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = google_id);

DROP POLICY IF EXISTS "Users can insert own profile" ON users;
CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid()::text = google_id);

-- Tasks policies
DROP POLICY IF EXISTS "Users can view own tasks" ON tasks;
CREATE POLICY "Users can view own tasks" ON tasks
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE google_id = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can insert own tasks" ON tasks;
CREATE POLICY "Users can insert own tasks" ON tasks
    FOR INSERT WITH CHECK (
        user_id IN (
            SELECT id FROM users WHERE google_id = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can update own tasks" ON tasks;
CREATE POLICY "Users can update own tasks" ON tasks
    FOR UPDATE USING (
        user_id IN (
            SELECT id FROM users WHERE google_id = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can delete own tasks" ON tasks;
CREATE POLICY "Users can delete own tasks" ON tasks
    FOR DELETE USING (
        user_id IN (
            SELECT id FROM users WHERE google_id = auth.uid()::text
        )
    );

-- User patterns policies
DROP POLICY IF EXISTS "Users can view own patterns" ON user_patterns;
CREATE POLICY "Users can view own patterns" ON user_patterns
    FOR SELECT USING (
        user_id IN (
            SELECT id FROM users WHERE google_id = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can insert own patterns" ON user_patterns;
CREATE POLICY "Users can insert own patterns" ON user_patterns
    FOR INSERT WITH CHECK (
        user_id IN (
            SELECT id FROM users WHERE google_id = auth.uid()::text
        )
    );

-- Create a function to get user statistics
CREATE OR REPLACE FUNCTION get_user_task_stats(user_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    total_tasks BIGINT,
    completed_tasks BIGINT,
    completion_rate FLOAT,
    avg_completion_time FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_tasks,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                COUNT(*) FILTER (WHERE status = 'completed')::FLOAT / COUNT(*)::FLOAT 
            ELSE 0 
        END as completion_rate,
        AVG(CASE WHEN actual_duration IS NOT NULL THEN actual_duration ELSE estimated_duration END) as avg_completion_time
    FROM tasks
    WHERE user_id = user_uuid
        AND created_at >= NOW() - INTERVAL '%s days' % days_back;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to get productivity insights
CREATE OR REPLACE FUNCTION get_productivity_insights(user_uuid UUID)
RETURNS TABLE (
    category TEXT,
    task_count BIGINT,
    completion_rate FLOAT,
    avg_duration FLOAT,
    most_productive_time TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH category_stats AS (
        SELECT 
            COALESCE(t.category, 'general') as cat,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE t.status = 'completed') as completed,
            AVG(COALESCE(t.actual_duration, t.estimated_duration)) as avg_dur,
            MODE() WITHIN GROUP (ORDER BY 
                CASE 
                    WHEN EXTRACT(HOUR FROM t.scheduled_start) BETWEEN 6 AND 11 THEN 'morning'
                    WHEN EXTRACT(HOUR FROM t.scheduled_start) BETWEEN 12 AND 17 THEN 'afternoon'
                    ELSE 'evening'
                END
            ) as productive_time
        FROM tasks t
        WHERE t.user_id = user_uuid
            AND t.created_at >= NOW() - INTERVAL '30 days'
        GROUP BY COALESCE(t.category, 'general')
    )
    SELECT 
        cat,
        total,
        CASE WHEN total > 0 THEN completed::FLOAT / total::FLOAT ELSE 0 END,
        COALESCE(avg_dur, 0),
        COALESCE(productive_time, 'morning')
    FROM category_stats
    ORDER BY total DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
