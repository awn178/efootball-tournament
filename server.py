import os
import json
import psycopg2
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import base64

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Database connection
def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    return psycopg2.connect(DATABASE_URL)

# Initialize database tables
def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Read and execute schema
    with open('database.sql', 'r') as f:
        cur.execute(f.read())
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized!")

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
    return jsonify({'status': 'Server is running!'})

# 1. Register user (Telegram login)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    telegram_id = data.get('telegram_id')
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute("SELECT id, is_admin FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()
    
    if not user:
        # New user
        cur.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (%s, %s, %s) RETURNING id",
            (telegram_id, username, first_name)
        )
        user_id = cur.fetchone()[0]
        is_admin = False
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

# 2. Get tournament status
@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, type, status 
        FROM tournaments 
        WHERE status != 'completed'
        ORDER BY id
    """)
    tournaments = cur.fetchall()
    
    result = []
    for t in tournaments:
        # Get settings for this tournament
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

# 3. Submit registration with screenshot
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    user_id = data.get('user_id')
    tournament_id = data.get('tournament_id')
    amount = data.get('amount')
    screenshot_data = data.get('screenshot')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get setting_id
    cur.execute("""
        SELECT id FROM tournament_settings 
        WHERE tournament_id = %s AND amount = %s AND is_active = TRUE
    """, (tournament_id, amount))
    setting = cur.fetchone()
    
    if not setting:
        return jsonify({'success': False, 'message': 'Invalid tournament or amount'})
    
    setting_id = setting[0]
    
    # Save screenshot
    screenshot_filename = f"payment_{user_id}_{uuid.uuid4()}.jpg"
    screenshot_path = f"/tmp/{screenshot_filename}"
    
    # Decode base64 image
    try:
        if ',' in screenshot_data:
            screenshot_data = screenshot_data.split(',')[1]
        
        img_data = base64.b64decode(screenshot_data)
        with open(screenshot_path, 'wb') as f:
            f.write(img_data)
    except Exception as e:
        return jsonify({'success': False, 'message': 'Invalid image data'})
    
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

# 4. Get pending registrations (admin only)
@app.route('/api/admin/pending', methods=['GET'])
def get_pending():
    admin_user = request.args.get('admin')
    if admin_user != '@awn175':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.id, u.username, u.first_name, t.name, r.amount, r.screenshot_url, r.submitted_date
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
            'name': p[2],
            'tournament': p[3],
            'amount': p[4],
            'screenshot': p[5],
            'date': p[6].isoformat() if p[6] else ''
        })
    
    cur.close()
    conn.close()
    
    return jsonify(result)

# 5. Approve/reject registration (admin only)
@app.route('/api/admin/process_registration', methods=['POST'])
def process_registration():
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

# 6. Send message to admin
@app.route('/api/send_message', methods=['POST'])
def send_message():
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

# 7. Get messages for admin
@app.route('/api/admin/messages', methods=['GET'])
def get_messages():
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

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
