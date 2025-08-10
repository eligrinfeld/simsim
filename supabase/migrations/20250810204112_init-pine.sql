-- Supabase Schema for Event Dashboard
-- Run this in your Supabase SQL Editor to create the required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users profile table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users_profile (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    display_name TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pine strategies table
CREATE TABLE IF NOT EXISTS pine_strategies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',
    description TEXT DEFAULT '',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pine backtest results table
CREATE TABLE IF NOT EXISTS pine_results (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    strategy_id UUID REFERENCES pine_strategies(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    timeframe TEXT DEFAULT '1m',
    data_hash TEXT, -- hash of candle data used
    sharpe_ratio NUMERIC,
    total_return NUMERIC,
    max_drawdown NUMERIC,
    trade_count INTEGER DEFAULT 0,
    trades JSONB DEFAULT '[]',
    equity_curve JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User sessions for replay/analysis
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT DEFAULT '1m',
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CEP rules table
CREATE TABLE IF NOT EXISTS cep_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    rule_type TEXT NOT NULL, -- 'sequence', 'sliding_count', 'anomaly'
    parameters JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Historical events for replay
CREATE TABLE IF NOT EXISTS historical_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- 'Breakout', 'NewsBurst', 'MacroShock'
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    data JSONB DEFAULT '{}',
    rule_id UUID REFERENCES cep_rules(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User annotations table
CREATE TABLE IF NOT EXISTS user_annotations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users_profile(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL, -- 'event', 'strategy', 'chart_point'
    target_id TEXT NOT NULL,
    symbol TEXT,
    note TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User alerts table
CREATE TABLE IF NOT EXISTS user_alerts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users_profile(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    rule_id UUID REFERENCES cep_rules(id),
    symbols TEXT[] DEFAULT '{}',
    delivery_method TEXT DEFAULT 'in_app', -- 'in_app', 'email', 'webhook'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pine_strategies_user_id ON pine_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_pine_results_strategy_id ON pine_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_historical_events_session_id ON historical_events(session_id);
CREATE INDEX IF NOT EXISTS idx_historical_events_symbol_timestamp ON historical_events(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_user_annotations_user_id ON user_annotations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_alerts_user_id ON user_alerts(user_id);

-- Row Level Security (RLS) Policies
ALTER TABLE users_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE pine_strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE pine_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cep_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own data
CREATE POLICY "Users can access their own profile" ON users_profile
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can access their own strategies" ON pine_strategies
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Public strategies are readable" ON pine_strategies
    FOR SELECT USING (is_public = true);

CREATE POLICY "Users can access results for their strategies" ON pine_results
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM pine_strategies 
            WHERE pine_strategies.id = pine_results.strategy_id 
            AND pine_strategies.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their own sessions" ON user_sessions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own rules" ON cep_rules
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access events from their sessions" ON historical_events
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_sessions 
            WHERE user_sessions.id = historical_events.session_id 
            AND user_sessions.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can access their own annotations" ON user_annotations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own alerts" ON user_alerts
    FOR ALL USING (auth.uid() = user_id);

-- Functions for automatic timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_profile_updated_at BEFORE UPDATE ON users_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pine_strategies_updated_at BEFORE UPDATE ON pine_strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
