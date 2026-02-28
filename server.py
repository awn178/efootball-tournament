import os
import json
import psycopg2
import psycopg2.extras
import uuid
import base64
import logging
import sys
import requests
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
OWNER_USERNAME = "@awn175"
RESULT_SUBMISSION = "@awn178"
ADMIN_PHONE = "+251961231633"

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
        
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_username VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(50),
                is_admin BOOLEAN DEFAULT FALSE,
                is_banned BOOLEAN DEFAULT FALSE,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chat_id BIGINT
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
        
        # Tournament brackets (multiple entry fees per tournament)
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
                match_date TIMESTAMP,
                UNIQUE(tournament_id, round, player1_id, player2_id)
            )
        """)
        print("✅ matches table created")
        
        # Knockout bracket structure
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knockout_matches (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
                round INTEGER NOT NULL,
                match_id INTEGER REFERENCES matches(id),
                next_match_id INTEGER,
                position INTEGER
            )
        """)
        print("✅ knockout_matches table created")
        
        # Messages
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                from_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                to_user_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                message_type VARCHAR(50) DEFAULT 'user_to_admin'
            )
        """)
        print("✅ messages table created")
        
        # Tournament history archive
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tournament_history (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id),
                user_id INTEGER REFERENCES users(id),
                result VARCHAR(50),
                prize VARCHAR(100),
                archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ tournament_history table created")
        
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
        
        # Insert owner as admin
        cur.execute("""
            INSERT INTO users (telegram_username, is_admin) 
            VALUES (%s, TRUE) 
            ON CONFLICT (telegram_username) DO UPDATE SET is_admin = TRUE
        """, (OWNER_USERNAME,))
        print("✅ owner admin created")
        
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
        telegram_username = data.get('telegram_username', '')
        phone = data.get('phone', '')
        chat_id = data.get('chat_id')
        
        if not telegram_username:
            return jsonify({'success': False, 'message': 'Username required'})
        
        if not telegram_username.startswith('@'):
            telegram_username = '@' + telegram_username
        
        conn = get_db()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute("SELECT id, is_admin, is_banned FROM users WHERE telegram_username = %s", (telegram_username,))
        user = cur.fetchone()
        
        if not user:
            # New user
            cur.execute("""
                INSERT INTO users (telegram_username, phone, chat_id) 
                VALUES (%s, %s, %s) RETURNING id, is_admin, is_banned
            """, (telegram_username, phone, chat_id))
            user = cur.fetchone()
            user_id = user[0]
            is_admin = user[1]
            is_banned = user[2]
            
            # Welcome message
            if chat_id:
                send_telegram(chat_id, f"👋 Welcome to eFootball Tournament {telegram_username}!\nYou can now register for tournaments.")
        else:
            user_id = user[0]
            is_admin = user[1]
            is_banned = user[2]
            
            # Update chat_id if provided
            if chat_id:
                cur.execute("UPDATE users SET chat_id = %s WHERE id = %s", (chat_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        if is_banned:
            return jsonify({'success': False, 'message': 'You are banned from the tournament'})
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_admin': is_admin,
            'username': telegram_username
        })
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 2. Get all tournaments
@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all active tournaments
        cur.execute("""
            SELECT * FROM tournaments 
            WHERE status != 'completed' 
            ORDER BY created_date DESC
        """)
        tournaments = cur.fetchall()
        
        result = []
        for t in tournaments:
            # Get brackets for this tournament
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
            
            # Get registered players for this tournament
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

# 3. Create tournament (admin only)
@app.route('/api/admin/create_tournament', methods=['POST'])
def create_tournament():
    try:
        data = request.json
        admin_user = data.get('admin')
        name = data.get('name')
        tournament_type = data.get('type')
        brackets = data.get('brackets')  # List of {amount, max_players}
        
        if admin_user != OWNER_USERNAME:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Create tournament
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

# 4. Start tournament (admin only)
@app.route('/api/admin/start_tournament', methods=['POST'])
def start_tournament():
    try:
        data = request.json
        admin_user = data.get('admin')
        tournament_id = data.get('tournament_id')
        
        if admin_user != OWNER_USERNAME:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Update tournament status
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

# 5. Submit registration with screenshot
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
        
        # Check if already registered
        cur.execute("""
            SELECT id FROM registrations 
            WHERE user_id = %s AND bracket_id = %s AND status = 'approved'
        """, (user_id, bracket_id))
        existing = cur.fetchone()
        if existing:
            return jsonify({'success': False, 'message': 'Already registered'})
        
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
        
        # Notify admin
        admin_chat_id = None
        cur.execute("SELECT chat_id FROM users WHERE telegram_username = %s", (OWNER_USERNAME,))
        admin = cur.fetchone()
        if admin and admin[0]:
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

# 6. Get pending registrations (admin)
@app.route('/api/admin/pending', methods=['GET'])
def get_pending():
    try:
        admin_user = request.args.get('admin')
        if admin_user != OWNER_USERNAME:
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
            result.append({
                'id': p['id'],
                'username': p['telegram_username'],
                'tournament': p['tournament_name'],
                'amount': p['amount'],
                'screenshot': p['screenshot_url'],
                'date': p['submitted_date'].isoformat() if p['submitted_date'] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Pending error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 7. Approve/reject registration
@app.route('/api/admin/process_registration', methods=['POST'])
def process_registration():
    try:
        data = request.json
        admin_user = data.get('admin')
        reg_id = data.get('registration_id')
        action = data.get('action')  # 'approve' or 'reject'
        reason = data.get('reason', '')
        
        if admin_user != OWNER_USERNAME:
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

# 8. Get league standings
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

# 9. Get knockout bracket
@app.route('/api/bracket/<int:tournament_id>', methods=['GET'])
def get_bracket(tournament_id):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get all matches for this tournament
        cur.execute("""
            SELECT m.*, u1.telegram_username as player1, u2.telegram_username as player2,
                   w.telegram_username as winner_name
            FROM matches m
            LEFT JOIN users u1 ON m.player1_id = u1.id
            LEFT JOIN users u2 ON m.player2_id = u2.id
            LEFT JOIN users w ON m.winner_id = w.id
            WHERE m.tournament_id = %s
            ORDER BY m.round, m.id
        """, (tournament_id,))
        
        matches = cur.fetchall()
        
        # Group by round
        rounds = {}
        for m in matches:
            if m['round'] not in rounds:
                rounds[m['round']] = []
            rounds[m['round']].append({
                'id': m['id'],
                'player1': m['player1'],
                'player2': m['player2'],
                'score1': m['player1_score'],
                'score2': m['player2_score'],
                'winner': m['winner_name'],
                'status': m['status']
            })
        
        cur.close()
        conn.close()
        return jsonify(rounds)
        
    except Exception as e:
        print(f"❌ Bracket error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 10. Enter match result (admin only)
@app.route('/api/admin/enter_result', methods=['POST'])
def enter_result():
    try:
        data = request.json
        admin_user = data.get('admin')
        match_id = data.get('match_id')
        score1 = data.get('score1', 0)
        score2 = data.get('score2', 0)
        
        if admin_user != OWNER_USERNAME:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Get match details
        cur.execute("""
            SELECT m.*, t.type, t.id as tournament_id,
                   u1.chat_id as player1_chat, u2.chat_id as player2_chat,
                   u1.telegram_username as p1_name, u2.telegram_username as p2_name
            FROM matches m
            JOIN tournaments t ON m.tournament_id = t.id
            LEFT JOIN users u1 ON m.player1_id = u1.id
            LEFT JOIN users u2 ON m.player2_id = u2.id
            WHERE m.id = %s
        """, (match_id,))
        match = cur.fetchone()
        
        if not match:
            return jsonify({'success': False, 'message': 'Match not found'})
        
        winner_id = None
        if score1 > score2:
            winner_id = match[2]  # player1_id
        elif score2 > score1:
            winner_id = match[3]  # player2_id
        
        # Update match
        cur.execute("""
            UPDATE matches 
            SET player1_score = %s, player2_score = %s, winner_id = %s, status = 'completed'
            WHERE id = %s
        """, (score1, score2, winner_id, match_id))
        
        # If league, update standings
        if match[13] == 'league':  # type
            tournament_id = match[14]
            
            # Update player1 stats
            if match[2]:  # player1_id
                cur.execute("""
                    UPDATE league_standings 
                    SET played = played + 1,
                        goals_for = goals_for + %s,
                        goals_against = goals_against + %s,
                        goal_difference = (goals_for + %s) - (goals_against + %s)
                    WHERE tournament_id = %s AND user_id = %s
                """, (score1, score2, score1, score2, tournament_id, match[2]))
                
                if winner_id == match[2]:
                    cur.execute("""
                        UPDATE league_standings 
                        SET won = won + 1,
                            points = points + 3
                        WHERE tournament_id = %s AND user_id = %s
                    """, (tournament_id, match[2]))
                elif winner_id is None:
                    cur.execute("""
                        UPDATE league_standings 
                        SET drawn = drawn + 1,
                            points = points + 1
                        WHERE tournament_id = %s AND user_id = %s
                    """, (tournament_id, match[2]))
                else:
                    cur.execute("""
                        UPDATE league_standings 
                        SET lost = lost + 1
                        WHERE tournament_id = %s AND user_id = %s
                    """, (tournament_id, match[2]))
            
            # Update player2 stats
            if match[3]:  # player2_id
                cur.execute("""
                    UPDATE league_standings 
                    SET played = played + 1,
                        goals_for = goals_for + %s,
                        goals_against = goals_against + %s,
                        goal_difference = (goals_for + %s) - (goals_against + %s)
                    WHERE tournament_id = %s AND user_id = %s
                """, (score2, score1, score2, score1, tournament_id, match[3]))
                
                if winner_id == match[3]:
                    cur.execute("""
                        UPDATE league_standings 
                        SET won = won + 1,
                            points = points + 3
                        WHERE tournament_id = %s AND user_id = %s
                    """, (tournament_id, match[3]))
                elif winner_id is None:
                    cur.execute("""
                        UPDATE league_standings 
                        SET drawn = drawn + 1,
                            points = points + 1
                        WHERE tournament_id = %s AND user_id = %s
                    """, (tournament_id, match[3]))
                else:
                    cur.execute("""
                        UPDATE league_standings 
                        SET lost = lost + 1
                        WHERE tournament_id = %s AND user_id = %s
                    """, (tournament_id, match[3]))
        
        # Notify players
        result_text = f"{score1} - {score2}"
        winner_name = match[15] if winner_id == match[2] else match[16] if winner_id == match[3] else "Draw"
        
        if match[4]:  # player1_chat
            send_telegram(match[4], 
                f"⚔️ <b>Match Result</b>\n"
                f"{match[15]} vs {match[16]}\n"
                f"Score: {result_text}\n"
                f"Winner: {winner_name}")
        
        if match[5] and match[5] != match[4]:  # player2_chat if different
            send_telegram(match[5], 
                f"⚔️ <b>Match Result</b>\n"
                f"{match[15]} vs {match[16]}\n"
                f"Score: {result_text}\n"
                f"Winner: {winner_name}")
        
        # Log action
        cur.execute("""
            INSERT INTO admin_logs (admin_username, action, details)
            VALUES (%s, 'enter_result', %s)
        """, (admin_user, f"Match {match_id}: {result_text}"))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Result error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 11. Send message to admin
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
        
        # Get user info and notify admin
        cur.execute("SELECT telegram_username, chat_id FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if user and user[1]:
            send_telegram(user[1], "📨 Your message has been sent to admin. You'll receive a reply soon.")
        
        # Notify admin
        cur.execute("SELECT chat_id FROM users WHERE telegram_username = %s", (OWNER_USERNAME,))
        admin = cur.fetchone()
        if admin and admin[0]:
            send_telegram(admin[0],
                f"💬 <b>New message from {user[0]}</b>\n\n{message}\n\nReply in admin panel.")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message_id': msg_id})
        
    except Exception as e:
        print(f"❌ Message error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 12. Get messages for admin
@app.route('/api/admin/messages', methods=['GET'])
def get_messages():
    try:
        admin_user = request.args.get('admin')
        if admin_user != OWNER_USERNAME:
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

# 13. Broadcast message (admin only)
@app.route('/api/admin/broadcast', methods=['POST'])
def broadcast():
    try:
        data = request.json
        admin_user = data.get('admin')
        target = data.get('target')  # 'all', 'knockout', 'league', 'specific'
        specific_user = data.get('specific_user')
        message = data.get('message')
        
        if admin_user != OWNER_USERNAME:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        conn = get_db()
        cur = conn.cursor()
        
        if target == 'all':
            cur.execute("SELECT chat_id, telegram_username FROM users WHERE chat_id IS NOT NULL AND is_banned = FALSE")
            users = cur.fetchall()
            for user in users:
                if user[0]:
                    send_telegram(user[0], f"📢 <b>Broadcast Message</b>\n\n{message}")
                    
        elif target == 'knockout':
            cur.execute("""
                SELECT DISTINCT u.chat_id, u.telegram_username
                FROM users u
                JOIN registrations r ON u.id = r.user_id
                JOIN brackets b ON r.bracket_id = b.id
                JOIN tournaments t ON b.tournament_id = t.id
                WHERE t.type = 'knockout' AND r.status = 'approved' AND u.chat_id IS NOT NULL
            """)
            users = cur.fetchall()
            for user in users:
                if user[0]:
                    send_telegram(user[0], f"🏆 <b>Knockout Tournament Update</b>\n\n{message}")
                    
        elif target == 'league':
            cur.execute("""
                SELECT DISTINCT u.chat_id, u.telegram_username
                FROM users u
                JOIN registrations r ON u.id = r.user_id
                JOIN brackets b ON r.bracket_id = b.id
                JOIN tournaments t ON b.tournament_id = t.id
                WHERE t.type = 'league' AND r.status = 'approved' AND u.chat_id IS NOT NULL
            """)
            users = cur.fetchall()
            for user in users:
                if user[0]:
                    send_telegram(user[0], f"⚽ <b>League Tournament Update</b>\n\n{message}")
                    
        elif target == 'specific' and specific_user:
            cur.execute("SELECT chat_id FROM users WHERE telegram_username = %s", (specific_user,))
            user = cur.fetchone()
            if user and user[0]:
                send_telegram(user[0], f"📩 <b>Message from Admin</b>\n\n{message}")
        
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

# 14. Get tournament history
@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT t.name, t.type, u.telegram_username as winner, t.completed_date
            FROM tournaments t
            LEFT JOIN users u ON t.winner_id = u.id
            WHERE t.status = 'completed'
            ORDER BY t.completed_date DESC
            LIMIT 20
        """)
        
        history = cur.fetchall()
        result = []
        for h in history:
            result.append({
                'name': h['name'],
                'type': h['type'],
                'winner': h['winner'] or 'Not finished',
                'date': h['completed_date'].isoformat() if h['completed_date'] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ History error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 15. Get user registrations
@app.route('/api/my_registrations', methods=['GET'])
def my_registrations():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'})
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT t.name, t.type, b.amount, r.status, r.submitted_date, r.approved_date
            FROM registrations r
            JOIN brackets b ON r.bracket_id = b.id
            JOIN tournaments t ON b.tournament_id = t.id
            WHERE r.user_id = %s
            ORDER BY r.submitted_date DESC
        """, (user_id,))
        
        regs = cur.fetchall()
        result = []
        for r in regs:
            result.append({
                'tournament': r['name'],
                'type': r['type'],
                'amount': r['amount'],
                'status': r['status'],
                'submitted': r['submitted_date'].isoformat() if r['submitted_date'] else None,
                'approved': r['approved_date'].isoformat() if r['approved_date'] else None
            })
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ My registrations error: {str(e)}")
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
