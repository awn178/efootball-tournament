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

-- Tournaments table with prizes
CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started',
    prize_1st INTEGER DEFAULT 0,
    prize_2nd INTEGER DEFAULT 0,
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

-- Knockout bracket structure
CREATE TABLE IF NOT EXISTS knockout_matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    round INTEGER NOT NULL,
    match_id INTEGER REFERENCES matches(id),
    next_match_id INTEGER,
    position INTEGER
);

-- Messages (user to admin)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    to_user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    message_type VARCHAR(50) DEFAULT 'user_to_admin'
);

-- Broadcasts table
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

-- Admin logs table
CREATE TABLE IF NOT EXISTS admin_logs (
    id SERIAL PRIMARY KEY,
    admin_username VARCHAR(255),
    action VARCHAR(255),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT INTO settings (key, value) VALUES ('result_username', '@awn178')
ON CONFLICT (key) DO NOTHING;

-- Insert admin users (run this separately or in init_db)
-- INSERT INTO users (telegram_username, pin, is_admin, admin_role) 
-- VALUES ('awnowner', '12604', TRUE, 'owner'),
--        ('awnadmin', '11512', TRUE, 'admin')
-- ON CONFLICT (telegram_username) DO UPDATE SET 
-- is_admin = TRUE, admin_role = EXCLUDED.admin_role;
