-- ==================== COMPLETE DATABASE SCHEMA ====================
-- This file contains all tables needed for the eFootball Tournament system
-- Run this on your PostgreSQL database to create/update all tables

-- ==================== USERS TABLE ====================
-- Stores all user information including PIN and admin status
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_username VARCHAR(255) UNIQUE NOT NULL,
    pin VARCHAR(10) NOT NULL,
    phone VARCHAR(50),
    is_admin BOOLEAN DEFAULT FALSE,
    admin_role VARCHAR(50),
    is_banned BOOLEAN DEFAULT FALSE,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chat_id BIGINT,
    last_login TIMESTAMP
);

-- ==================== TOURNAMENTS TABLE ====================
-- Stores tournament information including prizes and round tracking
CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'league' or 'knockout'
    status VARCHAR(50) DEFAULT 'not_started', -- 'not_started', 'registration', 'in_progress', 'completed'
    prize_1st INTEGER DEFAULT 0,
    prize_2nd INTEGER DEFAULT 0,
    current_round INTEGER DEFAULT 1,
    total_rounds INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    winner_id INTEGER REFERENCES users(id),
    completed_date TIMESTAMP
);

-- ==================== BRACKETS TABLE ====================
-- Stores entry fee brackets for each tournament
CREATE TABLE IF NOT EXISTS brackets (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    max_players INTEGER NOT NULL,
    current_registered INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- ==================== REGISTRATIONS TABLE ====================
-- Stores user registrations with payment status
CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bracket_id INTEGER REFERENCES brackets(id) ON DELETE CASCADE,
    screenshot_url TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    rejection_reason TEXT,
    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    approved_by VARCHAR(255)
);

-- ==================== LEAGUE STANDINGS TABLE ====================
-- Stores league standings for each tournament
CREATE TABLE IF NOT EXISTS league_standings (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    played INTEGER DEFAULT 0,
    won INTEGER DEFAULT 0,
    drawn INTEGER DEFAULT 0,
    lost INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    UNIQUE(tournament_id, user_id)
);

-- ==================== MATCHES TABLE ====================
-- Stores all matches for both league and knockout tournaments
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    round INTEGER NOT NULL,
    match_number INTEGER,
    player1_id INTEGER REFERENCES users(id),
    player2_id INTEGER REFERENCES users(id),
    player1_score INTEGER DEFAULT 0,
    player2_score INTEGER DEFAULT 0,
    winner_id INTEGER REFERENCES users(id),
    is_bye BOOLEAN DEFAULT FALSE,
    round_completed BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'walkover'
    match_date TIMESTAMP
);

-- ==================== KNOCKOUT MATCHES TABLE ====================
-- Stores knockout bracket structure (links matches to next round)
CREATE TABLE IF NOT EXISTS knockout_matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    round INTEGER NOT NULL,
    match_id INTEGER REFERENCES matches(id),
    next_match_id INTEGER,
    position INTEGER
);

-- ==================== MESSAGES TABLE ====================
-- Stores user messages to admin
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    to_user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    message_type VARCHAR(50) DEFAULT 'user_to_admin' -- 'user_to_admin', 'admin_reply'
);

-- ==================== BROADCASTS TABLE ====================
-- Stores broadcast messages sent by admin
CREATE TABLE IF NOT EXISTS broadcasts (
    id SERIAL PRIMARY KEY,
    from_admin VARCHAR(255),
    target VARCHAR(50), -- 'all', 'knockout', 'league', 'specific'
    content TEXT NOT NULL,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== USER BROADCASTS TABLE ====================
-- Tracks which users have read which broadcasts
CREATE TABLE IF NOT EXISTS user_broadcasts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    broadcast_id INTEGER REFERENCES broadcasts(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    read_date TIMESTAMP,
    UNIQUE(user_id, broadcast_id)
);

-- ==================== MATCH RULES TABLE ====================
-- Stores editable rules for league and knockout tournaments
CREATE TABLE IF NOT EXISTS match_rules (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    league_rules TEXT,
    knockout_rules TEXT,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id)
);

-- ==================== ADMIN LOGS TABLE ====================
-- Logs all admin actions for auditing
CREATE TABLE IF NOT EXISTS admin_logs (
    id SERIAL PRIMARY KEY,
    admin_username VARCHAR(255),
    action VARCHAR(255),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== SETTINGS TABLE ====================
-- Stores global settings like result submission username
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== DEFAULT DATA ====================

-- Insert default settings
INSERT INTO settings (key, value) 
VALUES ('result_username', '@awn178')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Insert admin users (run this separately or when creating users)
-- INSERT INTO users (telegram_username, pin, is_admin, admin_role) 
-- VALUES ('awnowner', '12604', TRUE, 'owner'),
--        ('awnadmin', '11512', TRUE, 'admin')
-- ON CONFLICT (telegram_username) DO UPDATE SET 
-- is_admin = TRUE, admin_role = EXCLUDED.admin_role;

-- ==================== INDEXES FOR PERFORMANCE ====================

-- Speed up common queries
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_player ON matches(player1_id);
CREATE INDEX IF NOT EXISTS idx_matches_player2 ON matches(player2_id);
CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON registrations(status);
CREATE INDEX IF NOT EXISTS idx_league_standings_tournament ON league_standings(tournament_id);
CREATE INDEX IF NOT EXISTS idx_knockout_matches_tournament ON knockout_matches(tournament_id);
CREATE INDEX IF NOT EXISTS idx_messages_from_user ON messages(from_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp ON admin_logs(timestamp);

-- ==================== END OF SCHEMA ====================
