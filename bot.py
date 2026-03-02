import os
import requests
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Telegram Bot Token
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
APP_URL = "https://efootball-tournament.onrender.com"

# Admin usernames
OWNER_USERNAME = "awnowner"
ADMIN_USERNAME = "awnadmin"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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

# Home route
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'bot is running',
        'message': 'Telegram bot is active',
        'endpoints': ['/test', '/webhook', '/health', '/ping'],
        'bot_username': '@Awntournamentbot',
        'timestamp': datetime.now().isoformat()
    })

# Test route
@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'bot_token': BOT_TOKEN[:10] + '...',
        'app_url': APP_URL,
        'webhook_url': f"{APP_URL}/webhook"
    })

# Ping route
@app.route('/ping', methods=['GET'])
def ping():
    return "pong"

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# Webhook endpoint - receives updates from Telegram
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    # Handle GET requests (for testing)
    if request.method == 'GET':
        return jsonify({
            'message': 'Webhook endpoint is active. Send POST requests from Telegram.',
            'status': 'ready',
            'method': 'GET',
            'timestamp': datetime.now().isoformat()
        })
    
    # POST request from Telegram
    try:
        data = request.json
        logger.info(f"📩 Received webhook data: {data}")
        
        if data and 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')
            username = data['message']['from'].get('username', '')
            first_name = data['message']['from'].get('first_name', '')
            
            logger.info(f"👤 User: {first_name} (@{username}), Message: {text}")
            
            # Handle /start command
            if text == '/start':
                # Create inline keyboard with web app button
                keyboard = {
                    'inline_keyboard': [[
                        {
                            'text': '🚀 Open Tournament App',
                            'web_app': {'url': APP_URL}
                        }
                    ]]
                }
                
                # Send welcome message
                welcome_text = f"""
<b>⚽ Welcome to eFootball Tournament Bot!</b>

Hello {first_name} {f'(@{username})' if username else ''}!

This bot will notify you about:
• Registration approvals
• New matches
• Tournament updates
• Broadcast messages

Click the button below to open the app:
                """
                
                send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': welcome_text,
                    'parse_mode': 'HTML',
                    'reply_markup': keyboard
                }
                response = requests.post(send_url, json=payload)
                logger.info(f"✅ Sent welcome to {chat_id}: {response.status_code}")
            
            # Handle /help command
            elif text == '/help':
                help_text = """
<b>📚 Available Commands:</b>

/start - Open the tournament app
/help - Show this help message
/ping - Check if bot is alive
/status - Check your registration status

<b>📱 App Features:</b>
• Register with PIN security
• Upload payment screenshots
• View fixtures and standings
• Message admin directly
• Receive broadcast messages
                """
                send_message(chat_id, help_text)
            
            # Handle /ping command
            elif text == '/ping':
                send_message(chat_id, "pong 🏓")
            
            # Handle /status command
            elif text == '/status':
                status_text = f"Check your tournament status in the app:\n{APP_URL}"
                send_message(chat_id, status_text)
            
            # Handle unknown commands
            else:
                unknown_text = "Unknown command. Use /start to open the app or /help for commands."
                send_message(chat_id, unknown_text)
        
        # Always return OK to Telegram
        return jsonify({'ok': True})
    
    except Exception as e:
        logger.error(f"❌ Error in webhook: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

# Notification endpoints for the main app
@app.route('/api/notify', methods=['POST'])
def notify():
    """Endpoint for main app to send notifications"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        message = data.get('message')
        
        if chat_id and message:
            send_message(chat_id, message)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Missing chat_id or message'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Webhook management endpoints (for admin)
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Manually set the webhook"""
    webhook_url = f"{APP_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.get(url, params={'url': webhook_url})
    return jsonify(response.json())

@app.route('/get_webhook', methods=['GET'])
def get_webhook():
    """Get current webhook info"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    """Delete the webhook"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.get(url)
    return jsonify(response.json())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🤖 Telegram Bot starting on port {port}")
    logger.info(f"📱 Root URL: https://efootball-bot.onrender.com/")
    logger.info(f"📱 Webhook URL: https://efootball-bot.onrender.com/webhook")
    logger.info(f"📱 Test URL: https://efootball-bot.onrender.com/test")
    app.run(host='0.0.0.0', port=port, debug=False)
