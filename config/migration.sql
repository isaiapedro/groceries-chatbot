-- Run this in the Supabase SQL Editor

-- Grocery items
CREATE TABLE IF NOT EXISTS grocery_list (
    id             SERIAL PRIMARY KEY,
    item_name      VARCHAR(255) NOT NULL UNIQUE,
    quantity       INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    aisle_category VARCHAR(100) NOT NULL DEFAULT 'Uncategorized'
);

-- Family members table
CREATE TABLE IF NOT EXISTS family_members (
    id           SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    name         VARCHAR(100) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Block public REST API access to phone numbers (service role / Lambda bypasses this)
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;

-- Shopping sessions (bulk-delete and interactive shopping state)
CREATE TABLE IF NOT EXISTS shopping_sessions (
    id           SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    session_type VARCHAR(50) NOT NULL,  -- bulk_delete, interactive_shopping, confirm_add, confirm_delete
    payload      JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '6 hours'
);

CREATE INDEX IF NOT EXISTS shopping_sessions_phone_number_idx
    ON shopping_sessions (phone_number);
CREATE INDEX IF NOT EXISTS shopping_sessions_expires_at_idx
    ON shopping_sessions (expires_at);

-- The Lambda database role must be granted access explicitly. Do not create
-- permissive public policies for these tables.
ALTER TABLE grocery_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_sessions ENABLE ROW LEVEL SECURITY;
