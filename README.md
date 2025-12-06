# Guardian Discord Bot

An advanced AI-powered Discord moderation bot that automatically detects and removes toxic content, NSFW images, and suspicious links using Groq's language models.

## Features

### Automatic Content Moderation
- **Toxicity Detection**: Analyzes messages for hate speech, harassment, and harmful content using Llama 3.3 70B
- **NSFW Image Filtering**: Scans images for explicit content, nudity, and graphic violence using Llama 3.2 90B Vision
- **Phishing Link Detection**: Identifies suspicious URLs and common phishing patterns
- **Contextual Analysis**: AI-powered detection understands context and intent, not just keywords

### Moderation Actions
- Automatic message deletion for policy violations
- Progressive warning system with escalating consequences
- Automatic timeouts after repeated violations
- Comprehensive moderation logging
- Moderator role exemption (configurable)

### Manual Commands
- `!guardian commands` - Display all available commands
- `!guardian status` - View bot configuration and statistics
- `!guardian stats [@user]` - Check warning history for users (Moderator only)
- `!guardian clearwarnings @user` - Clear user warnings (Admin only)
- `!guardian check <message>` - Manually test toxicity detection
- `!guardian checkimage` - Manually test image content filtering (attach image)

## Installation

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- Groq API Key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd guardian-discord-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

5. Configure the bot by editing `config.py`:
```python
TOXICITY_THRESHOLD = 0.7  # Range: 0.0-1.0 (higher = stricter)
NSFW_THRESHOLD = 0.6      # Range: 0.0-1.0 (higher = stricter)
MODERATOR_ROLES = ['Moderator', 'Admin', 'Mod']
EXEMPT_MODERATORS = True  # Set to False for testing
```

## Discord Bot Setup

### Creating a Discord Bot

1. Visit the [Discord Developer Portal](https://discord.com/developers/applications/)
2. Click "New Application" and give it a name
3. Navigate to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token and add it to your `.env` file

### Enable Privileged Intents

In the Bot section of the Developer Portal, enable:
- Server Members Intent
- Message Content Intent

### Bot Permissions

When generating the invite URL, the bot requires the following permissions:
- Read Messages/View Channels
- Send Messages
- Manage Messages (to delete violations)
- Kick Members
- Ban Members
- Moderate Members (for timeouts)
- Read Message History
- Manage Channels (to create mod-logs channel)

### Invite the Bot

1. Go to OAuth2 > URL Generator
2. Select scopes: `bot` and `applications.commands`
3. Select the permissions listed above
4. Use the generated URL to invite the bot to your server

## Usage

### Running the Bot

```bash
python bot.py
```

The bot will:
- Connect to Discord
- Create a `mod-logs` channel if it doesn't exist
- Begin monitoring all messages and images
- Log all moderation actions

### Configuration Options

Edit `config.py` to customize behavior:

| Setting | Description | Default |
|---------|-------------|---------|
| `TOXICITY_THRESHOLD` | Toxicity score threshold (0.0-1.0) | 0.7 |
| `NSFW_THRESHOLD` | NSFW content threshold (0.0-1.0) | 0.6 |
| `MODERATOR_ROLES` | Roles exempt from moderation | ['Moderator', 'Admin', 'Mod'] |
| `EXEMPT_MODERATORS` | Enable moderator exemption | True |
| `DELETE_TOXIC_MESSAGES` | Auto-delete toxic messages | True |
| `DELETE_NSFW_IMAGES` | Auto-delete NSFW images | True |
| `WARN_USERS` | Enable warning system | True |
| `MODERATION_CHANNELS` | Limit moderation to specific channels | [] (all channels) |
| `LOG_CHANNEL_NAME` | Channel name for mod logs | 'mod-logs' |

### Warning System

The bot implements a progressive discipline system:
1. **First Warning**: User is notified, message is deleted
2. **Second Warning**: User is notified, message is deleted
3. **Third Warning**: User receives a 10-minute timeout
4. **Subsequent Warnings**: Longer timeouts or potential ban

All actions are logged in the mod-logs channel with:
- Timestamp
- User information
- Violation reason
- Content preview
- Toxicity/NSFW scores

## Technical Details

### AI Models

- **Text Moderation**: Llama 3.3 70B Versatile (via Groq)
- **Image Moderation**: Llama 3.2 90B Vision Preview (via Groq)

### Detection Categories

**Toxicity Analysis**:
- Hate speech and discriminatory language
- Harassment and personal attacks
- Threats and incitement to violence
- Harmful content promotion

**Image Analysis**:
- Nudity and sexual content
- Graphic violence and gore
- Disturbing imagery

**Link Analysis**:
- Phishing attempts (fake Discord Nitro, Steam login)
- URL shorteners used maliciously
- Known suspicious domains

### Architecture

The bot uses:
- Discord.py for Discord API interactions
- Groq API for AI-powered content analysis
- Asynchronous processing for optimal performance
- JSON-based analysis results for reliability

## Development

### Project Structure

```
guardian-discord-bot/
├── bot.py              # Main bot application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in repo)
└── README.md          # This file
```

### Testing

For testing purposes, you can:

1. Set `EXEMPT_MODERATORS = False` in `config.py`
2. Lower thresholds temporarily (e.g., `TOXICITY_THRESHOLD = 0.3`)
3. Use manual check commands to test detection without triggering actions

### Contributing

Contributions are welcome. Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with Discord.py
- Powered by Groq's AI models
- Uses Llama models from Meta

## Support

For issues, questions, or feature requests, please open an issue on the repository.
