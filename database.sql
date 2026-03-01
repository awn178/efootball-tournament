-- Users table with PIN
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

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    winner_id INTEGER REFERENCES users(id),
    completed_date TIMESTAMP
);

-- Tournament brackets
CREATE TABLE IF NOT EXISTS brackets (
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
    bracket_id INTEGER REFERENCES brackets(id) ON DELETE CASCADE,
    screenshot_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    rejection_reason TEXT,
    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    approved_by VARCHAR(255)
);

-- League standings
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

-- Matches
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    round INTEGER,
    player1_id INTEGER REFERENCES users(id),
    player2_id INTEGER REFERENCES users(id),
    player1_score INTEGER DEFAULT 0,
    player2_score INTEGER DEFAULT 0,
    winner_id INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'scheduled',
    match_date TIMESTAMP
);

-- Messages (including broadcasts)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER REFERENCES users(id),
    to_user_id INTEGER,
    content TEXT NOT NULL,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    message_type VARCHAR(50) DEFAULT 'user_to_admin'
);

-- Broadcast messages (store for users)
CREATE TABLE IF NOT EXISTS broadcasts (
    id SERIAL PRIMARY KEY,
    from_admin VARCHAR(255),
    target VARCHAR(50),
    content TEXT NOT NULL,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User broadcast read status
CREATE TABLE IF NOT EXISTS user_broadcasts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    broadcast_id INTEGER REFERENCES broadcasts(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    read_date TIMESTAMP,
    UNIQUE(user_id, broadcast_id)
);

-- Admin logs
CREATE TABLE IF NOT EXISTS admin_logs (
    id SERIAL PRIMARY KEY,
    admin_username VARCHAR(255),
    action VARCHAR(255),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert admin users (run this separately)
-- INSERT INTO users (telegram_username, pin, is_admin, admin_role) 
-- VALUES ('awnowner', '12604', TRUE, 'owner'),
--        ('awnadmin', '11512', TRUE, 'admin')
-- ON CONFLICT (telegram_username) DO UPDATE SET 
-- is_admin = TRUE, admin_role = EXCLUDED.admin_role;
