import os

# Bot Configuration
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
APP_URL = "https://efootball-tournament.onrender.com"

# Admin Configuration
OWNER_USERNAME = "awnowner"
ADMIN_USERNAME = "awnadmin"
RESULT_SUBMISSION = "@awn178"
ADMIN_PHONE = "+251961231633"

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Tournament Settings
DEFAULT_PRIZES = {
    '1st': 0,
    '2nd': 0
}

# App Settings
APP_NAME = "eFootball Tournament"
APP_VERSION = "3.0.0"
DEBUG_MODE = True

# File Upload Settings
MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Notification Settings
ENABLE_TELEGRAM_NOTIFICATIONS = True
NOTIFY_ADMIN_ON_REGISTRATION = True
NOTIFY_USER_ON_APPROVAL = True
NOTIFY_USER_ON_MATCH = True

# Match Settings
MATCH_DEADLINE_HOURS = 48
WALKOVER_AFTER_HOURS = 72

# League Settings
LEAGUE_POINTS_WIN = 3
LEAGUE_POINTS_DRAW = 1
LEAGUE_POINTS_LOSS = 0

# Tiebreaker order: Points > Goal Difference > Goals For
LEAGUE_TIEBREAKERS = ['points', 'goal_difference', 'goals_for']

# Pagination
ITEMS_PER_PAGE = 20

# Cache Settings
CACHE_TIMEOUT = 300  # 5 minutes
