import os

# Bot Configuration
BOT_TOKEN = "8406169991:AAHcP5z7eHiKiSFGlRH3fOSDQS5gkjK-0EM"
APP_URL = "https://efootball-tournament.onrender.com"

# Admin Configuration
OWNER_USERNAME = "@awn175"
RESULT_SUBMISSION = "@awn178"
ADMIN_PHONE = "+251961231633"

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Tournament Settings
DEFAULT_KNOCKOUT_BRACKETS = [
    {'amount': 30, 'max_players': 16},
    {'amount': 50, 'max_players': 32},
    {'amount': 100, 'max_players': 64}
]

DEFAULT_LEAGUE_BRACKETS = [
    {'amount': 30, 'max_players': 15},
    {'amount': 50, 'max_players': 15},
    {'amount': 100, 'max_players': 15}
]

# App Settings
APP_NAME = "eFootball Tournament"
APP_VERSION = "2.0.0"
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
MATCH_DEADLINE_HOURS = 48  # Default 48 hours to play match
WALKOVER_AFTER_HOURS = 72   # Walkover after 72 hours

# League Settings
LEAGUE_POINTS_WIN = 3
LEAGUE_POINTS_DRAW = 1
LEAGUE_POINTS_LOSS = 0

# Tiebreaker order: Points > Goal Difference > Goals For > Head-to-Head
LEAGUE_TIEBREAKERS = ['points', 'goal_difference', 'goals_for', 'head_to_head']

# Pagination
ITEMS_PER_PAGE = 20

# Cache Settings
CACHE_TIMEOUT = 300  # 5 minutes
