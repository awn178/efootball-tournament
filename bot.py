import os
import requests
import time
import threading
from flask import Flask, request

# Telegram Bot Token
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
APP_URL = "https://efootball-tournament.onrender.com"

# Initialize Flask app for webhook
app = Flask(__name__)

# Store user chat IDs (in production, this would be in database)
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
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
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
        print(f"Error sending photo: {e}")
        return None

# Set webhook
def set_webhook():
    webhook_url = f"{APP_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.get(url, params={'url': webhook_url})
    print(f"Webhook set: {response.json()}")

# Remove webhook
def remove_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.get(url)
    print(f"Webhook removed: {response.json()}")

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f"Received update: {data}")
    
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        # Handle commands
        if text == '/start':
            welcome_message = """
<b>⚽ Welcome to eFootball Tournament Bot!</b>

This bot will send you notifications about:
• Registration approvals
• New matches scheduled
• Match results
• Tournament updates

To use the tournament app, click the button below:
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
            
        elif text == '/help':
            help_message = """
<b>📚 Available Commands:</b>

/start - Start the bot and get app link
/help - Show this help message
/status - Check your registration status
/notify - Get latest notifications

<b>📱 App Features:</b>
• Register for tournaments
• Upload payment screenshots
• View fixtures and standings
• Message admin
• Get match notifications
            """
            send_message(chat_id, help_message)
            
        elif text == '/status':
            send_message(chat_id, "Check your registration status in the app: " + APP_URL)
            
        elif text == '/notify':
            send_message(chat_id, "You'll receive notifications here when there are updates.")
            
        else:
            send_message(chat_id, "Use /start to open the tournament app or /help for commands.")
    
    return {'ok': True}

# Background notification sender (for non-webhook messages)
class NotificationBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_notification(self, chat_id, message, parse_mode='HTML'):
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except Exception as e:
            print(f"Notification error: {e}")
            return None
    
    def notify_admin(self, message):
        """Send notification to admin (@awn175)"""
        # In production, get admin chat_id from database
        admin_chat_id = None  # This would be stored when admin starts bot
        if admin_chat_id:
            self.send_notification(admin_chat_id, f"👑 <b>Admin Notification</b>\n\n{message}")
    
    def notify_user(self, username, message):
        """Send notification to specific user"""
        # In production, get chat_id from database using username
        chat_id = None  # This would be stored when user starts bot
        if chat_id:
            self.send_notification(chat_id, message)
    
    def notify_tournament_players(self, tournament_name, message, player_chat_ids):
        """Send notification to all players in a tournament"""
        for chat_id in player_chat_ids:
            self.send_notification(chat_id, f"🏆 <b>{tournament_name}</b>\n\n{message}")
    
    def broadcast(self, message, chat_ids):
        """Send broadcast to multiple users"""
        for chat_id in chat_ids:
            self.send_notification(chat_id, f"📢 <b>Broadcast Message</b>\n\n{message}")

# Notification templates
class NotificationTemplates:
    
    @staticmethod
    def registration_pending(username, tournament, amount):
        return f"""
<b>✅ Registration Submitted</b>

Thank you {username} for registering for {tournament}!

<b>Details:</b>
• Amount: {amount} Birr
• Status: Pending Approval

You will be notified once admin approves your registration.
        """
    
    @staticmethod
    def registration_approved(username, tournament):
        return f"""
<b>✅ Registration APPROVED!</b>

Congratulations {username}! Your registration for {tournament} has been approved.

You can now participate in the tournament. Check fixtures in the app.
        """
    
    @staticmethod
    def registration_rejected(username, tournament, reason):
        return f"""
<b>❌ Registration Rejected</b>

Sorry {username}, your registration for {tournament} was rejected.

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

# Initialize bot
notification_bot = NotificationBot()

# Function to run bot in background
def run_bot():
    # Set webhook when starting
    set_webhook()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001)

# If running standalone
if __name__ == '__main__':
    # Check if we should set webhook or run polling
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'set_webhook':
        set_webhook()
    elif len(sys.argv) > 1 and sys.argv[1] == 'remove_webhook':
        remove_webhook()
    else:
        # Run Flask app for webhook
        print("🤖 Telegram Bot starting on port 5001...")
        app.run(host='0.0.0.0', port=5001)
