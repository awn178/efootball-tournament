-- Users table (Telegram users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started',
    created_by VARCHAR(255),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tournament settings
CREATE TABLE IF NOT EXISTS tournament_settings (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    max_players INTEGER NOT NULL,
    current_registered INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Registrations
CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    setting_id INTEGER REFERENCES tournament_settings(id),
    amount INTEGER NOT NULL,
    screenshot_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    rejection_reason TEXT,
    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    approved_by VARCHAR(255)
);

-- Insert owner
INSERT INTO users (telegram_id, username, first_name, is_admin) 
VALUES (0, '@awn175', 'Owner', TRUE) 
ON CONFLICT (username) DO NOTHING;
