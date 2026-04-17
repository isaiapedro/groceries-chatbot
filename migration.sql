-- Run this in the Supabase SQL Editor
CREATE TABLE IF NOT EXISTS family_members (
    id          SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) NOT NULL UNIQUE,
    name         VARCHAR(100) NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
