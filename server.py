import os
import json
import psycopg2
import uuid
import base64
import logging
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
print("⚽ SERVER STARTING - DEBUG MODE ON")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Database connection
def get_db():
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        print(f"🔌 Connecting to database...")
        if not DATABASE_URL:
            print("❌ DATABASE_URL is empty!")
            return None
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Database connected!")
        return conn
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        raise e

# Initialize database tables
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        print("📦 Creating database tables...")
        
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                username VARCHAR(255),
                first_name VARCHAR(255),
                is_admin BOOLEAN DEFAULT FALSE,
                is_banned BOOLEAN DEFAULT FALSE,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ users table created")
        
        # Tournaments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tournaments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'not_started',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ tournaments table created")
        
        # Tournament settings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tournament_settings (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
                amount INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                current_registered INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("✅ tournament_settings table created")
        
        # Registrations
        cur.execute("""
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
            )
        """)
        print("✅ registrations table created")
        
        # Messages
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                from_user_id INTEGER REFERENCES users(id),
                to_user_id INTEGER,
                message_type VARCHAR(50),
                content TEXT,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE
            )
        """)
        print("✅ messages table created")
        
        # Insert owner
        cur.execute("""
            INSERT INTO users (telegram_id, username, first_name, is_admin) 
            VALUES (0, '@awn175', 'Owner', TRUE) 
            ON CONFLICT (telegram_id) DO NOTHING
        """)
        print("✅ owner user created")
        
        # Check if tournaments exist
        cur.execute("SELECT COUNT(*) FROM tournaments")
        count = cur.fetchone()[0]
        
        if count == 0:
            print("🏆 Creating default tournaments...")
            
            # Create Knockout tournament
            cur.execute("""
                INSERT INTO tournaments (name, type, status) 
                VALUES ('Knockout Championship', 'knockout', 'not_started') 
                RETURNING id
            """)
            knockout_id = cur.fetchone()[0]
            
            # Create League tournament
            cur.execute("""
                INSERT INTO tournaments (name, type, status) 
                VALUES ('League Championship', 'league', 'not_started') 
                RETURNING id
            """)
            league_id = cur.fetchone()[0]
            
            # Add settings for Knockout
            settings = [(30, 16), (50, 32), (100, 64)]
            for amount, max_players in settings:
                cur.execute("""
                    INSERT INTO tournament_settings (tournament_id, amount, max_players)
                    VALUES (%s, %s, %s)
                """, (knockout_id, amount, max_players))
            
            # Add settings for League
            settings = [(30, 15), (50, 15), (100, 15)]
            for amount, max_players in settings:
                cur.execute("""
                    INSERT INTO tournament_settings (tournament_id, amount, max_players)
                    VALUES (%s, %s, %s)
                """, (league_id, amount, max_players))
            
            print("✅ Default tournaments created!")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ All database tables ready!")
        
    except Exception as e:
        print(f"❌ Database init error: {str(e)}")
        raise e

# Serve HTML files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

# Test route
@app.route('/api/test')
def test():
    return jsonify({'status': 'Server is running!', 'database': 'connected'})

# 1. Register/Login user
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        username = data.get('username', '')
        first_name = data.get('first_name', '')
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, is_admin FROM users WHERE telegram_id = %s", (telegram_id,))
        user = cur.fetchone()
        
        if not user:
            cur.execute(
                "INSERT INTO users (telegram_id, username, first_name) VALUES (%s, %s, %s) RETURNING id",
                (telegram_id, username, first_name)
            )
            user_id = cur.fetchone()[0]
            is_admin = (username == '@awn175')
            if is_admin:
                cur.execute("UPDATE users SET is_admin = TRUE WHERE id = %s", (user_id,))
        else:
            user_id = user[0]
            is_admin = user[1]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_admin': is_admin,
            'username': username
        })
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 2. Get tournaments
@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, type, status FROM tournaments ORDER BY id")
        tournaments = cur.fetchall()
        
        result = []
        for t in tournaments:
            cur.execute("""
                SELECT amount, max_players, current_registered 
                FROM tournament_settings 
                WHERE tournament_id = %s AND is_active = TRUE
            """, (t[0],))
            settings = cur.fetchall()
            
            settings_list = []
            for s in settings:
                settings_list.append({
                    'amount': s[0],
                    'max_players': s[1],
                    'current': s[2]
                })
            
            result.append({
                'id': t[0],
                'name': t[1],
                'type': t[2],
                'status': t[3],
                'settings': settings_list
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Tournaments error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 3. Submit registration
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        user_id = data.get('user_id')
        tournament_type = data.get('tournament_id')
        amount = data.get('amount')
        screenshot_data = data.get('screenshot')
        
        conn = get_db()
        cur = conn.cursor()
        
        # Get tournament_id from type
        cur.execute("SELECT id FROM tournaments WHERE type = %s", (tournament_type,))
        tournament = cur.fetchone()
        if not tournament:
            return jsonify({'success': False, 'message': 'Tournament not found'})
        tournament_id = tournament[0]
        
        # Get setting_id
        cur.execute("""
            SELECT id FROM tournament_settings 
            WHERE tournament_id = %s AND amount = %s AND is_active = TRUE
        """, (tournament_id, amount))
        setting = cur.fetchone()
        
        if not setting:
            return jsonify({'success': False, 'message': 'Invalid amount'})
        
        setting_id = setting[0]
        
        # Save screenshot
        screenshot_filename = f"payment_{user_id}_{uuid.uuid4()}.jpg"
        screenshot_path = f"/tmp/{screenshot_filename}"
        
        try:
            if ',' in screenshot_data:
                screenshot_data = screenshot_data.split(',')[1]
            img_data = base64.b64decode(screenshot_data)
            with open(screenshot_path, 'wb') as f:
                f.write(img_data)
        except Exception as e:
            return jsonify({'success': False, 'message': 'Invalid image'})
        
        # Create registration
        cur.execute("""
            INSERT INTO registrations 
            (user_id, tournament_id, setting_id, amount, screenshot_url, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            RETURNING id
        """, (user_id, tournament_id, setting_id, amount, screenshot_path))
        
        reg_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'registration_id': reg_id})
    except Exception as e:
        print(f"❌ Register error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 4. Get pending registrations
@app.route('/api/admin/pending', methods=['GET'])
def get_pending():
    try:
        admin_user = request.args.get('admin')
        if admin_user != '@awn175':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT r.id, u.username, t.type, r.amount, r.screenshot_url, r.submitted_date
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.status = 'pending'
            ORDER BY r.submitted_date DESC
        """)
        
        pending = cur.fetchall()
        result = []
        for p in pending:
            result.append({
                'id': p[0],
                'username': p[1],
                'tournament': p[2],
                'amount': p[3],
                'screenshot': p[4],
                'date': p[5].isoformat() if p[5] else ''
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Pending error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 5. Approve/reject registration
@app.route('/api/admin/process_registration', methods=['POST'])
def process_registration():
    try:
        data = request.json
        admin_user = data.get('admin')
        reg_id = data.get('registration_id')
        action = data.get('action')
        reason = data.get('reason', '')
        
        if admin_user != '@awn175':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        if action == 'approve':
            cur.execute("""
                UPDATE registrations 
                SET status = 'approved', approved_date = CURRENT_TIMESTAMP, approved_by = %s
                WHERE id = %s
                RETURNING user_id, setting_id
            """, (admin_user, reg_id))
            
            reg = cur.fetchone()
            if reg:
                user_id = reg[0]
                setting_id = reg[1]
                
                cur.execute("""
                    UPDATE tournament_settings 
                    SET current_registered = current_registered + 1
                    WHERE id = %s
                """, (setting_id,))
        else:
            cur.execute("""
                UPDATE registrations 
                SET status = 'rejected', rejection_reason = %s, approved_by = %s
                WHERE id = %s
            """, (reason, admin_user, reg_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Process error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 6. Get approved players
@app.route('/api/players', methods=['GET'])
def get_players():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.username, t.type, r.amount
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.status = 'approved'
            ORDER BY t.type, r.amount
        """)
        
        players = cur.fetchall()
        result = []
        for p in players:
            result.append({
                'username': p[0],
                'tournament': p[1],
                'amount': p[2]
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Players error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 7. Send message to admin
@app.route('/api/send_message', methods=['POST'])
def send_message():
    try:
        data = request.json
        user_id = data.get('user_id')
        message = data.get('message')
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO messages (from_user_id, message_type, content)
            VALUES (%s, 'user_to_admin', %s)
        """, (user_id, message))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Message error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 8. Get messages for admin
@app.route('/api/admin/messages', methods=['GET'])
def get_messages():
    try:
        admin_user = request.args.get('admin')
        if admin_user != '@awn175':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT m.id, u.username, m.content, m.sent_date
            FROM messages m
            JOIN users u ON m.from_user_id = u.id
            WHERE m.message_type = 'user_to_admin'
            ORDER BY m.sent_date DESC
        """)
        
        messages = cur.fetchall()
        result = []
        for m in messages:
            result.append({
                'id': m[0],
                'username': m[1],
                'message': m[2],
                'date': m[3].isoformat() if m[3] else ''
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        print(f"❌ Messages error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 9. Update tournament settings
@app.route('/api/admin/update_settings', methods=['POST'])
def update_settings():
    try:
        data = request.json
        admin_user = data.get('admin')
        tournament_type = data.get('type')
        settings = data.get('settings')
        
        if admin_user != '@awn175':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM tournaments WHERE type = %s", (tournament_type,))
        tournament = cur.fetchone()
        if not tournament:
            return jsonify({'success': False, 'message': 'Tournament not found'})
        tournament_id = tournament[0]
        
        cur.execute("UPDATE tournament_settings SET is_active = FALSE WHERE tournament_id = %s", (tournament_id,))
        
        for s in settings:
            cur.execute("""
                INSERT INTO tournament_settings (tournament_id, amount, max_players, current_registered, is_active)
                VALUES (%s, %s, %s, 0, TRUE)
            """, (tournament_id, s['amount'], s['max_players']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Settings error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 10. Start tournament
@app.route('/api/admin/start_tournament', methods=['POST'])
def start_tournament():
    try:
        data = request.json
        admin_user = data.get('admin')
        tournament_type = data.get('type')
        
        if admin_user != '@awn175':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE tournaments 
            SET status = 'registration' 
            WHERE type = %s
        """, (tournament_type,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Start error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 11. Send broadcast
@app.route('/api/admin/broadcast', methods=['POST'])
def send_broadcast():
    try:
        data = request.json
        admin_user = data.get('admin')
        target = data.get('target')
        specific_user = data.get('specific_user')
        message = data.get('message')
        
        if admin_user != '@awn175':
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        if target == 'all':
            cur.execute("SELECT id FROM users WHERE is_banned = FALSE")
            users = cur.fetchall()
            for user in users:
                cur.execute("""
                    INSERT INTO messages (from_user_id, to_user_id, message_type, content)
                    VALUES (1, %s, 'admin_broadcast', %s)
                """, (user[0], message))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Broadcast error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Initialize database on startup
print("🚀 Initializing database...")
init_db()

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f"🚀 Server starting on port {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
