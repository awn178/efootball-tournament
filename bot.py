import os
import requests
import time
import threading
from flask import Flask, request
import logging

# Telegram Bot Token
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
APP_URL = "https://efootball-tournament.onrender.com"

# Admin usernames
OWNER_USERNAME = "awnowner"
ADMIN_USERNAME = "awnadmin"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app for webhook
app = Flask(__name__)

# Store user chat IDs temporarily (in production, this is in database)
user_chat_ids = {}

# Send message function
def send_message(chat_id, text, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=payload)
        logger.info(f"Message sent to {chat_id}: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

# Send photo function
def send_photo(chat_id, photo_url, caption=''):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption
        }
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        return None

# Set webhook
def set_webhook():
    webhook_url = f"{APP_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.get(url, params={'url': webhook_url})
    logger.info(f"Webhook set: {response.json()}")
    return response.json()

# Remove webhook
def remove_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.get(url)
    logger.info(f"Webhook removed: {response.json()}")
    return response.json()

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Received update: {data}")
    
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        username = data['message']['from'].get('username', '')
        first_name = data['message']['from'].get('first_name', '')
        
        # Handle commands
        if text == '/start':
            welcome_message = f"""
<b>⚽ Welcome to eFootball Tournament Bot!</b>

Hello {first_name} (@{username})!

This bot will send you notifications about:
• Registration approvals
• New matches scheduled
• Match results
• Tournament updates
• Broadcast messages from admin

<b>📱 To use the tournament app:</b>
1. Open the app below
2. Login with your Telegram username
3. Use PIN to secure your account
4. Register for tournaments

<b>🔐 PIN Security:</b>
• Create a 4-6 digit PIN when registering
• Use same PIN to login
• Never share your PIN with others
            """
            
            keyboard = {
                'inline_keyboard': [[
                    {
                        'text': '🚀 Open Tournament App',
                        'web_app': {'url': APP_URL}
                    }
                ]]
            }
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': welcome_message,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            }
            requests.post(url, json=payload)
            
            # Save chat_id for this user
            if username:
                user_chat_ids[f"@{username}"] = chat_id
                logger.info(f"Saved chat_id for @{username}: {chat_id}")
            
        elif text == '/help':
            help_message = """
<b>📚 Available Commands:</b>

/start - Start bot and get app link
/help - Show this help message
/pin - How to use PIN security
/status - Check your registration status
/notify - Get latest notifications

<b>📱 App Features:</b>
• Register for tournaments with PIN
• Upload payment screenshots
• View fixtures and standings
• Message admin directly
• Receive broadcast messages
• Get match notifications

<b>🔐 PIN Tips:</b>
• Choose a PIN you'll remember
• 4-6 digits only
• Don't use easy numbers (1234)
• Never share your PIN
            """
            send_message(chat_id, help_message)
            
        elif text == '/pin':
            pin_message = """
<b>🔐 PIN Security Guide</b>

Your PIN protects your tournament account:

<b>When registering:</b>
• Create a 4-6 digit PIN
• You'll need it every time you login
• Write it down somewhere safe

<b>Why PIN?</b>
• Prevents others from accessing your account
• Even if someone knows your username, they need PIN
• Multiple users can't use same account

<b>Lost your PIN?</b>
Contact admin @awn178 for help
            """
            send_message(chat_id, pin_message)
            
        elif text == '/status':
            send_message(chat_id, f"Check your registration status in the app:\n{APP_URL}")
            
        elif text == '/notify':
            send_message(chat_id, "You'll receive notifications here for:\n• Registration updates\n• New matches\n• Results\n• Broadcasts")
            
        else:
            send_message(chat_id, "Use /start to open the app or /help for commands.")
    
    return {'ok': True}

# Background notification sender
class NotificationBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_notification(self, chat_id, message, parse_mode='HTML'):
        """Send notification to specific chat_id"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=payload)
            logger.info(f"Notification sent to {chat_id}: {response.status_code}")
            return response.json()
        except Exception as e:
            logger.error(f"Notification error: {e}")
            return None
    
    def notify_admin(self, message, admin_type='both'):
        """Send notification to admins"""
        # In production, get admin chat_ids from database
        admin_chat_ids = {
            OWNER_USERNAME: None,  # Would be fetched from DB
            ADMIN_USERNAME: None
        }
        
        if admin_type == 'owner' and admin_chat_ids[OWNER_USERNAME]:
            self.send_notification(admin_chat_ids[OWNER_USERNAME], f"👑 <b>Owner Notification</b>\n\n{message}")
        elif admin_type == 'admin' and admin_chat_ids[ADMIN_USERNAME]:
            self.send_notification(admin_chat_ids[ADMIN_USERNAME], f"📋 <b>Admin Notification</b>\n\n{message}")
        elif admin_type == 'both':
            if admin_chat_ids[OWNER_USERNAME]:
                self.send_notification(admin_chat_ids[OWNER_USERNAME], f"👑 <b>Notification</b>\n\n{message}")
            if admin_chat_ids[ADMIN_USERNAME]:
                self.send_notification(admin_chat_ids[ADMIN_USERNAME], f"📋 <b>Notification</b>\n\n{message}")
    
    def notify_user_by_username(self, username, message):
        """Send notification to user by username"""
        # In production, get chat_id from database
        chat_id = user_chat_ids.get(username)
        if chat_id:
            self.send_notification(chat_id, message)
            return True
        return False
    
    def broadcast_to_all(self, message, user_chat_ids_list):
        """Send broadcast to multiple users"""
        success_count = 0
        for chat_id in user_chat_ids_list:
            if chat_id:
                result = self.send_notification(chat_id, f"📢 <b>Broadcast Message</b>\n\n{message}")
                if result:
                    success_count += 1
        logger.info(f"Broadcast sent to {success_count} users")
        return success_count

# Notification templates
class NotificationTemplates:
    
    @staticmethod
    def registration_pending(username, tournament, amount):
        return f"""
<b>✅ Registration Submitted</b>

Thank you {username} for registering for <b>{tournament}</b>!

<b>Details:</b>
• Amount: {amount} Birr
• Status: Pending Approval

You will be notified once admin approves your registration.
        """
    
    @staticmethod
    def registration_approved(username, tournament):
        return f"""
<b>✅ Registration APPROVED!</b>

Congratulations {username}! Your registration for <b>{tournament}</b> has been approved.

You can now participate in the tournament. Check fixtures in the app.
        """
    
    @staticmethod
    def registration_rejected(username, tournament, reason):
        return f"""
<b>❌ Registration Rejected</b>

Sorry {username}, your registration for <b>{tournament}</b> was rejected.

<b>Reason:</b> {reason}

Please contact admin if you have questions.
        """
    
    @staticmethod
    def new_match(username, opponent, round_name, deadline=None):
        message = f"""
<b>⚔️ New Match Scheduled!</b>

Hello {username}, you have a new match!

<b>Opponent:</b> {opponent}
<b>Round:</b> {round_name}
        """
        if deadline:
            message += f"\n<b>Deadline:</b> {deadline}"
        message += "\n\nOpen the app to view details and contact your opponent."
        return message
    
    @staticmethod
    def match_result(username, opponent, score, result):
        result_emoji = "✅" if result == "win" else "🤝" if result == "draw" else "❌"
        return f"""
{result_emoji} <b>Match Result</b>

<b>Your match against {opponent}</b>
<b>Score:</b> {score}
<b>Result:</b> {result.upper()}

Check standings in the app.
        """
    
    @staticmethod
    def tournament_started(tournament_name, tournament_type):
        return f"""
<b>🚀 {tournament_name} has STARTED!</b>

Type: {tournament_type.upper()}

Registration is now open! Join in the app.
        """
    
    @staticmethod
    def tournament_completed(tournament_name, winner):
        return f"""
<b>🏆 {tournament_name} COMPLETED!</b>

Congratulations to the winner:
<b>{winner}</b>

Check tournament history in the app.
        """
    
    @staticmethod
    def admin_message(message):
        return f"""
<b>📩 Message from Admin</b>

{message}
        """
    
    @staticmethod
    def broadcast_all(message):
        return f"""
<b>📢 Announcement</b>

{message}
        """
    
    @staticmethod
    def pin_reminder():
        return f"""
<b>🔐 PIN Reminder</b>

Don't forget your PIN! You need it to login.

• Never share your PIN
• If you forget, contact @awn178
        """

# Initialize bot
notification_bot = NotificationBot()

# Function to run bot in background
def run_bot():
    # Set webhook when starting
    set_webhook()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001)

# API endpoints for the main app to send notifications
@app.route('/api/notify/registration', methods=['POST'])
def notify_registration():
    """Endpoint for main app to trigger registration notifications"""
    data = request.json
    username = data.get('username')
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    if chat_id:
        send_message(chat_id, message)
        return {'success': True}
    return {'success': False, 'error': 'No chat_id'}

@app.route('/api/notify/broadcast', methods=['POST'])
def notify_broadcast():
    """Endpoint for admin broadcast"""
    data = request.json
    target = data.get('target')
    message = data.get('message')
    user_list = data.get('users', [])
    
    # In production, fetch chat_ids from database
    success_count = 0
    for user in user_list:
        chat_id = user.get('chat_id')
        if chat_id:
            send_message(chat_id, f"📢 <b>Broadcast</b>\n\n{message}")
            success_count += 1
    
    return {'success': True, 'sent': success_count}

@app.route('/api/notify/test', methods=['GET'])
def test_notification():
    """Test endpoint"""
    return {'status': 'Bot is running', 'webhook': APP_URL + '/webhook'}

# If running standalone
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'set_webhook':
            set_webhook()
        elif sys.argv[1] == 'remove_webhook':
            remove_webhook()
        elif sys.argv[1] == 'test':
            print("Testing bot...")
            # Test code here
    else:
        # Run Flask app for webhook
        port = int(os.environ.get('PORT', 5001))
        logger.info(f"🤖 Telegram Bot starting on port {port}")
        app.run(host='0.0.0.0', port=port)
