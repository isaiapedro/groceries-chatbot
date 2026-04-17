-- Run this in the Supabase SQL Editor

-- Family members table
CREATE TABLE IF NOT EXISTS family_members (
    id           SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    name         VARCHAR(100) NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Block public REST API access to phone numbers (service role / Lambda bypasses this)
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;

-- Shopping sessions (bulk-delete and interactive shopping state)
CREATE TABLE IF NOT EXISTS shopping_sessions (
    id           SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    session_type VARCHAR(50) NOT NULL,  -- 'bulk_delete' | 'interactive_shopping'
    payload      JSONB NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    expires_at   TIMESTAMPTZ DEFAULT NOW() + INTERVAL '6 hours'
);
