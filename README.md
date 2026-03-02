# eFootball Tournament Telegram Mini App

A complete tournament management system for eFootball competitions on Telegram.

## 🚀 Features

### For Users
- ✅ Manual Telegram username login with PIN security
- ✅ View multiple tournaments with prize information
- ✅ Multiple entry brackets per tournament
- ✅ Registration with payment screenshot
- ✅ View registered players
- ✅ League standings (P, W, D, L, GF, GA, GD, PTS)
- ✅ Visual knockout brackets with friendly messages when empty
- ✅ Message inbox for admin replies and broadcasts
- ✅ Message admin directly
- ✅ Click usernames to open Telegram DM
- ✅ Telegram bot notifications
- ✅ Result submission instructions

### For Admin (@awnowner - Owner)
- ✅ Create unlimited tournaments with custom prizes
- ✅ Set multiple entry brackets per tournament
- ✅ Edit tournament name, prizes, and status
- ✅ Delete tournaments (only if no players)
- ✅ Start/stop tournaments
- ✅ Approve/reject registrations with screenshot view
- ✅ Enter match results
- ✅ Auto-calculate league standings
- ✅ Manage knockout brackets
- ✅ View user messages
- ✅ Broadcast to all/specific users
- ✅ Ban/unban users
- ✅ Edit result submission username
- ✅ View admin action logs
- ✅ Telegram notifications for new registrations

### For Admin (@awnadmin - Limited)
- ✅ Approve/reject payments
- ✅ Enter match results
- ✅ Broadcast messages
- ✅ View messages
- ❌ Cannot create tournaments
- ❌ Cannot edit/delete tournaments
- ❌ Cannot ban users
- ❌ Cannot view logs

## 📱 Telegram Bot

Bot username: **@Awntournamentbot**

### Bot Commands
- `/start` - Get welcome message and app link
- `/help` - Show available commands
- `/pin` - PIN security guide
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

- **Owner**: `awnowner` / `12604` (full control)
- **Admin**: `awnadmin` / `11512` (limited access)
- **Result submission**: Configurable in Settings tab (default: @awn178)
- **Admin phone**: +251961231633

## 📸 Payment

- TeleBirr number: +251961231633
- Users upload screenshot during registration
- Admin approves/rejects with one click
- Screenshots viewable in admin panel

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

Tiebreakers: Points > GD > GF

## 🏆 Knockout Brackets

- Visual bracket display
- Automatic progression
- Result entry per match
- Winner tracking
- Friendly message when no fixtures: "Fixtures will be available when players are fully registered"

## 📝 Tournament Prizes

- Configurable 1st and 2nd place prizes
- Displayed prominently in tournament cards
- Editable after creation

## 📬 Message System

- Users can message admin directly
- Admin replies appear in user inbox
- Broadcast messages appear in user inbox with special styling
- Unread message counter

## 📋 Admin Logs

- All admin actions are logged
- Viewable in Logs tab (owner only)
- Includes: tournament creation, approvals, broadcasts, edits, deletions

## 📱 Mobile Optimized

- All tables horizontally scrollable
- Buttons wrap properly on small screens
- Cards layout for matches
- Touch-friendly interface

## 📞 Support

- Telegram: @awn178 (configurable)
- Phone: +251961231633

## 📝 License

© 2026 eFootball Tournament. All rights reserved.
