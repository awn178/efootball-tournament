import os
import requests
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Telegram Bot Token
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
APP_URL = "https://efootball-tournament.onrender.com"

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

# Home endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'bot is running',
        'endpoints': ['/test', '/webhook', '/health']
    })

# Test endpoint
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'bot is running', 'webhook': '/webhook'})

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# IMPORTANT: WEBHOOK ENDPOINT - THIS MUST EXIST!
@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint that receives updates from Telegram"""
    data = request.json
    logger.info(f"Received update: {data}")
    
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        username = data['message']['from'].get('username', '')
        first_name = data['message']['from'].get('first_name', '')
        
        # Handle /start command
        if text == '/start':
            welcome_message = f"""
<b>⚽ Welcome to eFootball Tournament Bot!</b>

Hello {first_name} {f'(@{username})' if username else ''}!

Use the button below to open the tournament app:
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
            logger.info(f"Sent welcome message to {chat_id}")
        
        elif text == '/help':
            help_message = "Available commands: /start, /help"
            send_message(chat_id, help_message)
        
        else:
            send_message(chat_id, "Use /start to open the app")
    
    # Always return OK to Telegram
    return jsonify({'ok': True})

# Optional: Handle GET requests to webhook (for testing)
@app.route('/webhook', methods=['GET'])
def webhook_get():
    return jsonify({
        'message': 'This is the webhook endpoint. POST requests only.',
        'status': 'active'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🤖 Telegram Bot starting on port {port}")
    logger.info(f"📱 Webhook URL: https://efootball-bot.onrender.com/webhook")
    app.run(host='0.0.0.0', port=port)
