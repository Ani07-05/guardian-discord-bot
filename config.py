import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Moderation Settings
TOXICITY_THRESHOLD = 0.7  # 0-1, higher = stricter
NSFW_THRESHOLD = 0.6  # 0-1, higher = stricter

# Allowed channels (empty list = all channels)
MODERATION_CHANNELS = []  # Add channel IDs to limit moderation

# Moderator role names (users with these roles bypass checks)
MODERATOR_ROLES = ['Moderator', 'Admin', 'Mod']

# Testing - Set to False to disable moderator exemption (useful for testing)
EXEMPT_MODERATORS = False  # Set to True in production!

# Actions
DELETE_TOXIC_MESSAGES = True
DELETE_NSFW_IMAGES = True
WARN_USERS = True
LOG_CHANNEL_NAME = 'mod-logs'  # Create this channel in your server