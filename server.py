import os
import json
import psycopg2
import psycopg2.extras
import uuid
import base64
import logging
import sys
import requests
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
print("⚽ EFOOTBALL TOURNAMENT SERVER STARTING")
print("✅ Debug mode ON")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configuration
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
OWNER_USERNAME = "awnowner"  # Changed from @awn175
ADMIN_USERNAME = "awnadmin"
RESULT_SUBMISSION = "@awn178"
ADMIN_PHONE = "+251961231633"

# Admin credentials (in production, these would be hashed in database)
ADMIN_CREDENTIALS = {
    "awnowner": {
        "password": "12604",
        "role": "owner",
        "full_name": "Owner"
    },
    "awnadmin": {
        "password": "11512",
        "role": "admin",
        "full_name": "Tournament Admin"
    }
}

# Database connection
def get_db():
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if not DATABASE_URL:
            print("❌ DATABASE_URL is empty!")
            return None
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        raise e

# Validate Telegram username
def validate_telegram_username(username):
    """Check if username exists on Telegram (simulated - in production would use Telegram API)"""
    # Remove @ if present
    clean_username = username.replace('@', '')
    
    # Basic validation: at least 5 chars, alphanumeric + underscore
    if len(clean_username) < 5:
        return False, "Username too short (min 5 characters)"
    
    if not re.match("^[a-zA-Z0-9_]+$", clean_username):
        return False, "Username can only contain letters, numbers, and underscore"
    
    # In production, you would call Telegram API to verify
    # For now, we'll accept all valid format usernames
    return True, clean_username

# Send Telegram notification
def send_telegram(chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram error: {str(e)}")

# Initialize database
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        print("📦 Creating database tables...")
        
        # Users table with PIN
        cur.execute("""
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
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                winner_id INTEGER REFERENCES users(id),
                completed_date TIMESTAMP
            )
        """)
        print("✅ tournaments table created")
        
        # Tournament brackets
        cur.execute("""
            CREATE TABLE IF NOT EXISTS brackets (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
                amount INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                current_registered INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("✅ brackets table created")
        
        # Registrations
        cur.execute("""
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
            )
        """)
        print("✅ registrations table created")
        
        # League standings
        cur.execute("""
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
            )
        """)
        print("✅ league_standings table created")
        
        # Matches
        cur.execute("""
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
            )
        """)
        print("✅ matches table created")
        
        # Messages (including broadcasts)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                from_user_id INTEGER REFERENCES users(id),
                to_user_id INTEGER,
                content TEXT NOT NULL,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                message_type VARCHAR(50) DEFAULT 'user_to_admin'
            )
        """)
        print("✅ messages table created")
        
        # Broadcast messages (store for users)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id SERIAL PRIMARY KEY,
                from_admin VARCHAR(255),
                target VARCHAR(50),
                content TEXT NOT NULL,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ broadcasts table created")
        
        # User broadcast read status
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_broadcasts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                broadcast_id INTEGER REFERENCES broadcasts(id) ON DELETE CASCADE,
                is_read BOOLEAN DEFAULT FALSE,
                read_date TIMESTAMP,
                UNIQUE(user_id, broadcast_id)
            )
        """)
        print("✅ user_broadcasts table created")
        
        # Admin logs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id SERIAL PRIMARY KEY,
                admin_username VARCHAR(255),
                action VARCHAR(255),
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ admin_logs table created")
        
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

@app.route('/admin/login')
def admin_login_page():
    return send_from_directory('.', 'admin_login.html')

# Test route
@app.route('/api/test')
def test():
    return jsonify({'status': 'Server is running!', 'database': 'connected'})

# 1. Admin login
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Check credentials
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username]['password'] == password:
            role = ADMIN_CREDENTIALS[username]['role']
            return jsonify({
                'success': True,
                'username': username,
                'role': role,
                'full_name': ADMIN_CREDENTIALS[username]['full_name']
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
            
    except Exception as e:
        print(f"❌ Admin login error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 2. Register/Login user (with PIN)
@app.route('/api/register_user', methods=['POST'])
def register_user():
    try:
        data = request.json
        telegram_username = data.get('telegram_username', '')
        pin = data.get('pin', '')
        phone = data.get('phone', '')
        chat_id = data.get('chat_id')
        
        if not telegram_username or not pin:
            return jsonify({'success': False, 'message': 'Username and PIN required'})
        
        if len(pin) < 4 or len(pin) > 6:
            return jsonify({'success': False, 'message': 'PIN must be 4-6 digits'})
        
        # Validate username
        is_valid, result = validate_telegram_username(telegram_username)
        if not is_valid:
            return jsonify({'success': False, 'message': result})
        
        clean_username = '@' + result
        
        conn = get_db()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute("SELECT id, pin, is_admin, is_banned FROM users WHERE telegram_username = %s", (clean_username,))
        user = cur.fetchone()
        
        if not user:
            # New user - register with PIN
            cur.execute("""
                INSERT INTO users (telegram_username, pin, phone, chat_id) 
                VALUES (%s, %s, %s, %s) RETURNING id, is_admin, is_banned
            """, (clean_username, pin, phone, chat_id))
            user = cur.fetchone()
            user_id = user[0]
            is_admin = user[1]
            is_banned = user[2]
            
            # Welcome message
            if chat_id:
                send_telegram(chat_id, f"👋 Welcome to eFootball Tournament {clean_username}!\nYour account is created with PIN protection.")
        else:
            # Existing user - verify PIN
            user_id = user[0]
            stored_pin = user[1]
            is_admin = user[2]
            is_banned = user[3]
            
            if stored_pin != pin:
                cur.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Invalid PIN'})
            
            # Update chat_id if provided
            if chat_id:
                cur.execute("UPDATE users SET chat_id = %s, last_login = CURRENT_TIMESTAMP WHERE id = %s", (chat_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        if is_banned:
            return jsonify({'success': False, 'message': 'You are banned from the tournament'})
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_admin': is_admin,
            'username': clean_username
        })
        
    except Exception as e:
        print(f"❌ Register user error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 3. User login (existing user)
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        telegram_username = data.get('telegram_username', '')
        pin = data.get('pin', '')
        chat_id = data.get('chat_id')
        
        if not telegram_username or not pin:
            return jsonify({'success': False, 'message': 'Username and PIN required'})
        
        clean_username = telegram_username if telegram_username.startswith('@') else '@' + telegram_username
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("SELECT id, pin, is_admin, is_banned FROM users WHERE telegram_username = %s", (clean_username,))
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'User not found. Please register first.'})
        
        user_id = user[0]
        stored_pin = user[1]
        is_admin = user[2]
        is_banned = user[3]
        
        if stored_pin != pin:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid PIN'})
        
        # Update chat_id if provided
        if chat_id:
            cur.execute("UPDATE users SET chat_id = %s, last_login = CURRENT_TIMESTAMP WHERE id = %s", (chat_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        if is_banned:
            return jsonify({'success': False, 'message': 'You are banned from the tournament'})
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_admin': is_admin,
            'username': clean_username
        })
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 4. Get all tournaments
@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT * FROM tournaments 
            WHERE status != 'completed' 
            ORDER BY created_date DESC
        """)
        tournaments = cur.fetchall()
        
        result = []
        for t in tournaments:
            # Get brackets
            cur.execute("""
                SELECT * FROM brackets 
                WHERE tournament_id = %s AND is_active = TRUE
                ORDER BY amount
            """, (t['id'],))
            brackets = cur.fetchall()
            
            bracket_list = []
            for b in brackets:
                bracket_list.append({
                    'id': b['id'],
                    'amount': b['amount'],
                    'max_players': b['max_players'],
                    'current': b['current_registered']
                })
            
            # Get registered players
            cur.execute("""
                SELECT u.telegram_username, b.amount
                FROM registrations r
                JOIN users u ON r.user_id = u.id
                JOIN brackets b ON r.bracket_id = b.id
                WHERE r.status = 'approved' AND b.tournament_id = %s
                ORDER BY b.amount, u.telegram_username
            """, (t['id'],))
            players = cur.fetchall()
            
            player_list = []
            for p in players:
                player_list.append({
                    'username': p['telegram_username'],
                    'amount': p['amount']
                })
            
            result.append({
                'id': t['id'],
                'name': t['name'],
                'type': t['type'],
                'status': t['status'],
                'brackets': bracket_list,
                'players': player_list,
                'created': t['created_date'].isoformat() if t['created_date'] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Tournaments error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 5. Create tournament (admin only - owner only)
@app.route('/api/admin/create_tournament', methods=['POST'])
def create_tournament():
    try:
        data = request.json
        admin_user = data.get('admin')
        admin_role = data.get('role')
        name = data.get('name')
        tournament_type = data.get('type')
        brackets = data.get('brackets')
        
        # Only owner can create tournaments
        if admin_role != 'owner':
            return jsonify({'success': False, 'message': 'Only owner can create tournaments'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO tournaments (name, type, status) 
            VALUES (%s, %s, 'not_started') 
            RETURNING id
        """, (name, tournament_type))
        tournament_id = cur.fetchone()[0]
        
        # Create brackets
        for b in brackets:
            cur.execute("""
                INSERT INTO brackets (tournament_id, amount, max_players)
                VALUES (%s, %s, %s)
            """, (tournament_id, b['amount'], b['max_players']))
        
        # Log action
        cur.execute("""
            INSERT INTO admin_logs (admin_username, action, details)
            VALUES (%s, 'create_tournament', %s)
        """, (admin_user, f"Created {tournament_type} tournament: {name}"))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'tournament_id': tournament_id})
        
    except Exception as e:
        print(f"❌ Create tournament error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 6. Start tournament (admin only - owner only)
@app.route('/api/admin/start_tournament', methods=['POST'])
def start_tournament():
    try:
        data = request.json
        admin_user = data.get('admin')
        admin_role = data.get('role')
        tournament_id = data.get('tournament_id')
        
        # Only owner can start tournaments
        if admin_role != 'owner':
            return jsonify({'success': False, 'message': 'Only owner can start tournaments'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE tournaments 
            SET status = 'registration' 
            WHERE id = %s
            RETURNING name, type
        """, (tournament_id,))
        tournament = cur.fetchone()
        
        # Get all users to notify
        cur.execute("SELECT chat_id FROM users WHERE chat_id IS NOT NULL")
        users = cur.fetchall()
        
        # Send notifications
        for user in users:
            if user[0]:
                send_telegram(user[0], 
                    f"📢 <b>{tournament[0]}</b> is now OPEN for registration!\n"
                    f"Type: {tournament[1]}\n"
                    f"Register now in the app!")
        
        # Log action
        cur.execute("""
            INSERT INTO admin_logs (admin_username, action, details)
            VALUES (%s, 'start_tournament', %s)
        """, (admin_user, f"Started tournament ID: {tournament_id}"))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Start tournament error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 7. Submit registration with screenshot
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        user_id = data.get('user_id')
        bracket_id = data.get('bracket_id')
        screenshot_data = data.get('screenshot')
        transaction_id = data.get('transaction_id', '')
        
        if not user_id or not bracket_id or not screenshot_data:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Check if already registered in this tournament
        cur.execute("""
            SELECT r.id FROM registrations r
            JOIN brackets b ON r.bracket_id = b.id
            WHERE r.user_id = %s AND b.tournament_id = (
                SELECT tournament_id FROM brackets WHERE id = %s
            ) AND r.status = 'approved'
        """, (user_id, bracket_id))
        existing = cur.fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'Already registered in this tournament'})
        
        # Save screenshot
        screenshot_filename = f"payment_{user_id}_{bracket_id}_{uuid.uuid4()}.jpg"
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
            INSERT INTO registrations (user_id, bracket_id, screenshot_url, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id
        """, (user_id, bracket_id, screenshot_path))
        reg_id = cur.fetchone()[0]
        
        # Get tournament info for notification
        cur.execute("""
            SELECT t.name, b.amount, u.telegram_username, u.chat_id
            FROM brackets b
            JOIN tournaments t ON b.tournament_id = t.id
            JOIN users u ON u.id = %s
            WHERE b.id = %s
        """, (user_id, bracket_id))
        info = cur.fetchone()
        
        if info and info[3]:  # user has chat_id
            send_telegram(info[3], 
                f"✅ Registration submitted!\n"
                f"Tournament: {info[0]}\n"
                f"Amount: {info[1]} Birr\n"
                f"Status: Pending approval")
        
        # Notify admins (both owner and admin)
        cur.execute("SELECT chat_id FROM users WHERE telegram_username IN ('awnowner', 'awnadmin') AND chat_id IS NOT NULL")
        admins = cur.fetchall()
        for admin in admins:
            if admin[0]:
                send_telegram(admin[0],
                    f"👑 NEW REGISTRATION PENDING\n"
                    f"User: {info[2]}\n"
                    f"Tournament: {info[0]}\n"
                    f"Amount: {info[1]} Birr\n"
                    f"Check admin panel to approve")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'registration_id': reg_id})
        
    except Exception as e:
        print(f"❌ Register error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 8. Get pending registrations (admin - both owner and admin)
@app.route('/api/admin/pending', methods=['GET'])
def get_pending():
    try:
        admin_user = request.args.get('admin')
        admin_role = request.args.get('role')
        
        # Both owner and admin can view pending
        if admin_role not in ['owner', 'admin']:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT r.id, u.telegram_username, t.name as tournament_name, 
                   b.amount, r.screenshot_url, r.submitted_date
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            JOIN brackets b ON r.bracket_id = b.id
            JOIN tournaments t ON b.tournament_id = t.id
            WHERE r.status = 'pending'
            ORDER BY r.submitted_date DESC
        """)
        
        pending = cur.fetchall()
        result = []
        for p in pending:
            # Read screenshot file and convert to base64 for display
            screenshot_base64 = None
            try:
                with open(p['screenshot_url'], 'rb') as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode('utf-8')
            except:
                pass
            
            result.append({
                'id': p['id'],
                'username': p['telegram_username'],
                'tournament': p['tournament_name'],
                'amount': p['amount'],
                'screenshot': f"data:image/jpeg;base64,{screenshot_base64}" if screenshot_base64 else None,
                'date': p['submitted_date'].isoformat() if p['submitted_date'] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Pending error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 9. Approve/reject registration (admin - both owner and admin)
@app.route('/api/admin/process_registration', methods=['POST'])
def process_registration():
    try:
        data = request.json
        admin_user = data.get('admin')
        admin_role = data.get('role')
        reg_id = data.get('registration_id')
        action = data.get('action')
        reason = data.get('reason', '')
        
        # Both owner and admin can approve/reject
        if admin_role not in ['owner', 'admin']:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Get registration details
        cur.execute("""
            SELECT r.user_id, r.bracket_id, u.telegram_username, u.chat_id, b.tournament_id
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            JOIN brackets b ON r.bracket_id = b.id
            WHERE r.id = %s
        """, (reg_id,))
        reg = cur.fetchone()
        
        if not reg:
            return jsonify({'success': False, 'message': 'Registration not found'})
        
        user_id = reg[0]
        bracket_id = reg[1]
        username = reg[2]
        chat_id = reg[3]
        tournament_id = reg[4]
        
        if action == 'approve':
            # Update registration
            cur.execute("""
                UPDATE registrations 
                SET status = 'approved', approved_date = CURRENT_TIMESTAMP, approved_by = %s
                WHERE id = %s
            """, (admin_user, reg_id))
            
            # Update bracket count
            cur.execute("""
                UPDATE brackets 
                SET current_registered = current_registered + 1
                WHERE id = %s
            """, (bracket_id,))
            
            # Add to league standings if league tournament
            cur.execute("SELECT type FROM tournaments WHERE id = %s", (tournament_id,))
            t_type = cur.fetchone()[0]
            
            if t_type == 'league':
                cur.execute("""
                    INSERT INTO league_standings (tournament_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT (tournament_id, user_id) DO NOTHING
                """, (tournament_id, user_id))
            
            # Notify user
            if chat_id:
                send_telegram(chat_id, 
                    f"✅ <b>Registration APPROVED!</b>\n"
                    f"You can now participate in the tournament.\n"
                    f"Check fixtures in the app.")
            
            message = f"Registration approved for {username}"
            
        else:
            # Reject
            cur.execute("""
                UPDATE registrations 
                SET status = 'rejected', rejection_reason = %s, approved_by = %s
                WHERE id = %s
            """, (reason, admin_user, reg_id))
            
            # Notify user
            if chat_id:
                send_telegram(chat_id, 
                    f"❌ <b>Registration REJECTED</b>\n"
                    f"Reason: {reason}\n"
                    f"Contact admin for more information.")
            
            message = f"Registration rejected for {username}: {reason}"
        
        # Log action
        cur.execute("""
            INSERT INTO admin_logs (admin_username, action, details)
            VALUES (%s, %s, %s)
        """, (admin_user, f'{action}_registration', message))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Process error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 10. Get league standings
@app.route('/api/standings/<int:tournament_id>', methods=['GET'])
def get_standings(tournament_id):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT ls.*, u.telegram_username
            FROM league_standings ls
            JOIN users u ON ls.user_id = u.id
            WHERE ls.tournament_id = %s
            ORDER BY ls.points DESC, ls.goal_difference DESC, ls.goals_for DESC
        """, (tournament_id,))
        
        standings = cur.fetchall()
        result = []
        for s in standings:
            result.append({
                'username': s['telegram_username'],
                'played': s['played'],
                'won': s['won'],
                'drawn': s['drawn'],
                'lost': s['lost'],
                'gf': s['goals_for'],
                'ga': s['goals_against'],
                'gd': s['goal_difference'],
                'points': s['points']
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Standings error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 11. Get messages for user (including broadcasts)
@app.route('/api/user/messages', methods=['GET'])
def get_user_messages():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'})
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get personal messages (user to admin replies)
        cur.execute("""
            SELECT m.id, 'admin_reply' as type, m.content, m.sent_date
            FROM messages m
            WHERE m.to_user_id = %s
            ORDER BY m.sent_date DESC
        """, (int(user_id),))
        personal_msgs = cur.fetchall()
        
        # Get broadcasts for this user
        cur.execute("""
            SELECT b.id, 'broadcast' as type, b.content, b.sent_date, ub.is_read
            FROM broadcasts b
            JOIN user_broadcasts ub ON b.id = ub.broadcast_id
            WHERE ub.user_id = %s
            ORDER BY b.sent_date DESC
        """, (int(user_id),))
        broadcasts = cur.fetchall()
        
        # Combine and sort
        all_messages = []
        for m in personal_msgs:
            all_messages.append({
                'id': m['id'],
                'type': m['type'],
                'content': m['content'],
                'date': m['sent_date'].isoformat() if m['sent_date'] else None,
                'is_read': True
            })
        
        for b in broadcasts:
            all_messages.append({
                'id': b['id'],
                'type': b['type'],
                'content': b['content'],
                'date': b['sent_date'].isoformat() if b['sent_date'] else None,
                'is_read': b['is_read']
            })
        
        # Sort by date (newest first)
        all_messages.sort(key=lambda x: x['date'], reverse=True)
        
        # Mark broadcasts as read
        cur.execute("""
            UPDATE user_broadcasts SET is_read = TRUE, read_date = CURRENT_TIMESTAMP
            WHERE user_id = %s AND is_read = FALSE
        """, (int(user_id),))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify(all_messages)
        
    except Exception as e:
        print(f"❌ User messages error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 12. Send broadcast (admin only)
@app.route('/api/admin/broadcast', methods=['POST'])
def send_broadcast():
    try:
        data = request.json
        admin_user = data.get('admin')
        admin_role = data.get('role')
        target = data.get('target')
        specific_user = data.get('specific_user')
        message = data.get('message')
        
        # Both owner and admin can broadcast
        if admin_role not in ['owner', 'admin']:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Save broadcast
        cur.execute("""
            INSERT INTO broadcasts (from_admin, target, content)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (admin_user, target, message))
        broadcast_id = cur.fetchone()[0]
        
        # Get target users and send
        if target == 'all':
            cur.execute("SELECT id, chat_id FROM users WHERE chat_id IS NOT NULL AND is_banned = FALSE")
            users = cur.fetchall()
            for user in users:
                if user[1]:
                    send_telegram(user[1], f"📢 <b>Broadcast Message</b>\n\n{message}")
                # Link broadcast to user
                cur.execute("""
                    INSERT INTO user_broadcasts (user_id, broadcast_id)
                    VALUES (%s, %s)
                """, (user[0], broadcast_id))
                
        elif target == 'knockout':
            cur.execute("""
                SELECT DISTINCT u.id, u.chat_id
                FROM users u
                JOIN registrations r ON u.id = r.user_id
                JOIN brackets b ON r.bracket_id = b.id
                JOIN tournaments t ON b.tournament_id = t.id
                WHERE t.type = 'knockout' AND r.status = 'approved' AND u.chat_id IS NOT NULL
            """)
            users = cur.fetchall()
            for user in users:
                if user[1]:
                    send_telegram(user[1], f"🏆 <b>Knockout Tournament Update</b>\n\n{message}")
                cur.execute("""
                    INSERT INTO user_broadcasts (user_id, broadcast_id)
                    VALUES (%s, %s)
                """, (user[0], broadcast_id))
                
        elif target == 'league':
            cur.execute("""
                SELECT DISTINCT u.id, u.chat_id
                FROM users u
                JOIN registrations r ON u.id = r.user_id
                JOIN brackets b ON r.bracket_id = b.id
                JOIN tournaments t ON b.tournament_id = t.id
                WHERE t.type = 'league' AND r.status = 'approved' AND u.chat_id IS NOT NULL
            """)
            users = cur.fetchall()
            for user in users:
                if user[1]:
                    send_telegram(user[1], f"⚽ <b>League Tournament Update</b>\n\n{message}")
                cur.execute("""
                    INSERT INTO user_broadcasts (user_id, broadcast_id)
                    VALUES (%s, %s)
                """, (user[0], broadcast_id))
                
        elif target == 'specific' and specific_user:
            cur.execute("SELECT id, chat_id FROM users WHERE telegram_username = %s", (specific_user,))
            user = cur.fetchone()
            if user:
                if user[1]:
                    send_telegram(user[1], f"📩 <b>Message from Admin</b>\n\n{message}")
                cur.execute("""
                    INSERT INTO user_broadcasts (user_id, broadcast_id)
                    VALUES (%s, %s)
                """, (user[0], broadcast_id))
        
        # Log action
        cur.execute("""
            INSERT INTO admin_logs (admin_username, action, details)
            VALUES (%s, 'broadcast', %s)
        """, (admin_user, f"Broadcast to {target}: {message[:50]}..."))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Broadcast error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 13. Send message to admin
@app.route('/api/send_message', methods=['POST'])
def send_message():
    try:
        data = request.json
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return jsonify({'success': False, 'message': 'Missing fields'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Save message
        cur.execute("""
            INSERT INTO messages (from_user_id, message_type, content)
            VALUES (%s, 'user_to_admin', %s)
            RETURNING id
        """, (user_id, message))
        msg_id = cur.fetchone()[0]
        
        # Get user info
        cur.execute("SELECT telegram_username, chat_id FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if user and user[1]:
            send_telegram(user[1], "📨 Your message has been sent to admin. You'll receive a reply soon.")
        
        # Notify all admins
        cur.execute("SELECT chat_id FROM users WHERE telegram_username IN ('awnowner', 'awnadmin') AND chat_id IS NOT NULL")
        admins = cur.fetchall()
        for admin in admins:
            if admin[0]:
                send_telegram(admin[0],
                    f"💬 <b>New message from {user[0]}</b>\n\n{message}\n\nReply in admin panel.")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message_id': msg_id})
        
    except Exception as e:
        print(f"❌ Message error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 14. Get messages for admin
@app.route('/api/admin/messages', methods=['GET'])
def get_admin_messages():
    try:
        admin_user = request.args.get('admin')
        admin_role = request.args.get('role')
        
        if admin_role not in ['owner', 'admin']:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT m.id, u.telegram_username, m.content, m.sent_date, m.is_read
            FROM messages m
            JOIN users u ON m.from_user_id = u.id
            WHERE m.message_type = 'user_to_admin'
            ORDER BY m.sent_date DESC
        """)
        
        messages = cur.fetchall()
        result = []
        for m in messages:
            result.append({
                'id': m['id'],
                'username': m['telegram_username'],
                'message': m['content'],
                'date': m['sent_date'].isoformat() if m['sent_date'] else None,
                'is_read': m['is_read']
            })
        
        # Mark as read
        cur.execute("UPDATE messages SET is_read = TRUE WHERE message_type = 'user_to_admin'")
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Messages error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 15. Check if user is registered in tournament
@app.route('/api/check_registration', methods=['GET'])
def check_registration():
    try:
        user_id = request.args.get('user_id')
        tournament_id = request.args.get('tournament_id')
        
        if not user_id or not tournament_id:
            return jsonify({'success': False, 'message': 'Missing parameters'})
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT r.id FROM registrations r
            JOIN brackets b ON r.bracket_id = b.id
            WHERE r.user_id = %s AND b.tournament_id = %s AND r.status = 'approved'
        """, (int(user_id), int(tournament_id)))
        
        registered = cur.fetchone() is not None
        
        cur.close()
        conn.close()
        
        return jsonify({'registered': registered})
        
    except Exception as e:
        print(f"❌ Check registration error: {str(e)}")
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
