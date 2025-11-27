-- Swifty Backend API - PostgreSQL 16 Database Schema
-- Generated from ERD diagram
-- Schema: swifty_app

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS swifty_app;

-- Set search path to the schema
SET search_path TO swifty_app;

-- =====================================================
-- Table: users
-- Description: Stores user account information
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    user_key VARCHAR(255) PRIMARY KEY,
    gender VARCHAR(50) NOT NULL,
    age_range VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- =====================================================
-- Table: exercise_logs
-- Description: Stores exercise activity logs
-- =====================================================
CREATE TABLE IF NOT EXISTS exercise_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_key VARCHAR(255) NOT NULL,
    exercise_type VARCHAR(100),
    duration INTEGER, -- in minutes
    calories INTEGER,
    distance NUMERIC(10, 2), -- in kilometers
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_exercise_user 
        FOREIGN KEY (user_key) 
        REFERENCES users(user_key) 
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_exercise_logs_user_key ON exercise_logs(user_key);
CREATE INDEX IF NOT EXISTS idx_exercise_logs_date ON exercise_logs(date);
CREATE INDEX IF NOT EXISTS idx_exercise_logs_created_at ON exercise_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_exercise_logs_user_date ON exercise_logs(user_key, date);

-- =====================================================
-- Table: food_logs
-- Description: Stores food/meal logs
-- =====================================================
CREATE TABLE IF NOT EXISTS food_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_key VARCHAR(255) NOT NULL,
    is_healthy BOOLEAN,
    estimated_calories INTEGER,
    meal_type VARCHAR(50), -- breakfast, lunch, dinner, snack
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_food_user 
        FOREIGN KEY (user_key) 
        REFERENCES users(user_key) 
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_food_logs_user_key ON food_logs(user_key);
CREATE INDEX IF NOT EXISTS idx_food_logs_date ON food_logs(date);
CREATE INDEX IF NOT EXISTS idx_food_logs_created_at ON food_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_food_logs_user_date ON food_logs(user_key, date);

-- =====================================================
-- Table: food_ingredients
-- Description: Stores ingredients for each food log
-- =====================================================
CREATE TABLE IF NOT EXISTS food_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    food_log_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(50) NOT NULL CHECK (color IN ('red', 'green', 'teal')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ingredient_food_log 
        FOREIGN KEY (food_log_id) 
        REFERENCES food_logs(id) 
        ON DELETE CASCADE
);

-- Index for faster joins
CREATE INDEX IF NOT EXISTS idx_food_ingredients_food_log_id ON food_ingredients(food_log_id);

-- =====================================================
-- Table: user_rewards
-- Description: Stores user rewards and achievements
-- =====================================================
CREATE TABLE IF NOT EXISTS user_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_key VARCHAR(255) NOT NULL,
    reward_type VARCHAR(100) NOT NULL,
    reward_value INTEGER NOT NULL,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB, -- For storing additional reward information
    CONSTRAINT fk_reward_user 
        FOREIGN KEY (user_key) 
        REFERENCES users(user_key) 
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_rewards_user_key ON user_rewards(user_key);
CREATE INDEX IF NOT EXISTS idx_user_rewards_earned_at ON user_rewards(earned_at);
CREATE INDEX IF NOT EXISTS idx_user_rewards_reward_type ON user_rewards(reward_type);

-- =====================================================
-- Triggers for updated_at timestamp
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Optional: Sample Data for Testing (Comment out for production)
-- =====================================================

-- Uncomment below to insert sample data for testing
/*
-- Sample user
INSERT INTO users (user_key, gender, age_range) 
VALUES ('test_user_123', 'male', '20-30')
ON CONFLICT (user_key) DO NOTHING;

-- Sample exercise log
INSERT INTO exercise_logs (user_key, exercise_type, duration, calories, distance, date)
VALUES ('test_user_123', 'Running', 30, 300, 5.0, CURRENT_DATE)
ON CONFLICT DO NOTHING;

-- Sample food log
INSERT INTO food_logs (user_key, is_healthy, estimated_calories, meal_type, date)
VALUES ('test_user_123', true, 450, 'lunch', CURRENT_DATE)
RETURNING id INTO @food_log_id;

-- Sample ingredients (replace @food_log_id with actual UUID)
-- INSERT INTO food_ingredients (food_log_id, name, color)
-- VALUES (@food_log_id, 'Chicken Breast', 'green'),
--        (@food_log_id, 'Broccoli', 'green'),
--        (@food_log_id, 'Rice', 'teal');
*/

-- =====================================================
-- Grants (adjust based on your user setup)
-- =====================================================

-- Grant privileges to your application user
-- Replace 'your_app_user' with actual database user
-- GRANT USAGE ON SCHEMA swifty_app TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA swifty_app TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA swifty_app TO your_app_user;

-- =====================================================
-- End of Schema
-- =====================================================
