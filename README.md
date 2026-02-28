# eFootball Tournament Telegram Mini App

A complete tournament management system for eFootball competitions on Telegram.

## 🚀 Features

### For Users
- ✅ Manual Telegram username login
- ✅ View multiple tournaments
- ✅ Multiple entry brackets per tournament
- ✅ Registration with payment screenshot
- ✅ View registered players
- ✅ League standings (P, W, D, L, GF, GA, GD, PTS)
- ✅ Visual knockout brackets
- ✅ Tournament history
- ✅ Message admin directly
- ✅ Click usernames to open Telegram DM
- ✅ Telegram bot notifications

### For Admin (@awn175)
- ✅ Create unlimited tournaments
- ✅ Set multiple entry brackets per tournament
- ✅ Start/stop tournaments
- ✅ Approve/reject registrations with screenshot view
- ✅ Enter match results
- ✅ Auto-calculate league standings
- ✅ Manage knockout brackets
- ✅ View user messages
- ✅ Broadcast to all/specific users
- ✅ Ban/unban users
- ✅ View admin action logs
- ✅ Telegram notifications for new registrations

## 📱 Telegram Bot

Bot username: **@Awntournamentbot**

### Bot Commands
- `/start` - Get welcome message and app link
- `/help` - Show available commands
- `/status` - Check registration status
- `/notify` - Get latest notifications

### Bot Notifications
- ✅ New registration pending (admin only)
- ✅ Registration approved/rejected
- ✅ New match scheduled
- ✅ Match result entered
- ✅ Tournament started
- ✅ Broadcast messages

## 🛠️ Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python Flask
- **Database**: PostgreSQL
- **Bot**: python-telegram-bot
- **Hosting**: Render.com

## 📦 Installation

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up PostgreSQL database
4. Configure environment variables in `.env`
5. Run: `python server.py`

## 🌐 Deployment on Render

1. Connect GitHub repository
2. Create PostgreSQL database
3. Set environment variables
4. Deploy web service
5. Set bot webhook: `python bot.py set_webhook`

## 👑 Admin Access

- **Owner**: @awn175 (full control)
- **Result submission**: @awn178
- **Admin phone**: +251961231633

## 📸 Payment

- TeleBirr number: +251961231633
- Users upload screenshot during registration
- Admin approves/rejects with one click

## 📊 League Standings

Full statistics including:
- Played (P)
- Won (W)
- Drawn (D)
- Lost (L)
- Goals For (GF)
- Goals Against (GA)
- Goal Difference (GD)
- Points (PTS)

Tiebreakers: Points > GD > GF > Head-to-Head

## 🏆 Knockout Brackets

- Visual bracket display
- Automatic progression
- Result entry per match
- Winner tracking

## 📝 License

© 2026 eFootball Tournament. All rights reserved.

## 📞 Support

- Telegram: @awn178
- Phone: +251961231633
