import discord
from discord.ext import commands
import asyncio
from groq import Groq
import base64
import requests
from io import BytesIO
import json
import re
from datetime import datetime
import config

# Initialize Groq client
groq_client = Groq(api_key=config.GROQ_API_KEY)

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!guardian ', intents=intents)

# User warnings tracker
user_warnings = {}

def is_moderator(member):
    """Check if user has moderator role"""
    if member.guild_permissions.administrator:
        return True
    return any(role.name in config.MODERATOR_ROLES for role in member.roles)

async def get_log_channel(guild):
    """Get or create mod-logs channel"""
    log_channel = discord.utils.get(guild.text_channels, name=config.LOG_CHANNEL_NAME)
    if not log_channel:
        try:
            log_channel = await guild.create_text_channel(
                config.LOG_CHANNEL_NAME,
                topic="Guardian Bot moderation logs"
            )
        except:
            pass
    return log_channel

async def log_action(guild, action_type, user, reason, content_preview=""):
    """Log moderation actions"""
    log_channel = await get_log_channel(guild)
    if not log_channel:
        return
    
    embed = discord.Embed(
        title=f"[MODERATION] {action_type}",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    if content_preview:
        embed.add_field(name="Content", value=content_preview[:200], inline=False)
    
    await log_channel.send(embed=embed)

async def check_toxicity(text):
    """Check message for toxic content using Groq"""
    try:
        prompt = f"""Analyze this message for toxicity, hate speech, harassment, or harmful content.
Rate toxicity from 0.0 (completely safe) to 1.0 (extremely toxic).
Also explain why if toxic.

Message: "{text}"

Respond ONLY in JSON format:
{{"toxicity_score": 0.0, "is_toxic": false, "reason": ""}}"""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a content moderation AI. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        result_text = re.sub(r'```json\n?|\n?```', '', result_text)
        result = json.loads(result_text)
        
        return {
            'is_toxic': result.get('toxicity_score', 0) > config.TOXICITY_THRESHOLD,
            'score': result.get('toxicity_score', 0),
            'reason': result.get('reason', 'No reason provided')
        }
    except Exception as e:
        print(f"Error checking toxicity: {e}")
        return {'is_toxic': False, 'score': 0, 'reason': 'Error in analysis'}

async def check_image_nsfw(image_url):
    """Check image for NSFW content using Groq Vision"""
    try:
        prompt = """Analyze this image for NSFW content (nudity, sexual content, graphic violence, gore).
Rate NSFW level from 0.0 (completely safe) to 1.0 (explicit NSFW).

Respond ONLY in JSON format:
{"nsfw_score": 0.0, "is_nsfw": false, "reason": ""}"""

        response = groq_client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        result_text = re.sub(r'```json\n?|\n?```', '', result_text)
        result = json.loads(result_text)
        
        return {
            'is_nsfw': result.get('nsfw_score', 0) > config.NSFW_THRESHOLD,
            'score': result.get('nsfw_score', 0),
            'reason': result.get('reason', 'No reason provided')
        }
    except Exception as e:
        print(f"Error checking image: {e}")
        return {'is_nsfw': False, 'score': 0, 'reason': 'Error in analysis'}

def extract_urls(text):
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

async def check_suspicious_links(text):
    """Check for suspicious/phishing links"""
    urls = extract_urls(text)
    if not urls:
        return {'is_suspicious': False, 'urls': []}
    
    suspicious_patterns = [
        r'bit\.ly', r'tinyurl', r'discord\.gift', r'discordnitro',
        r'steam-community', r'steampowered-login', r'free-nitro'
    ]
    
    suspicious_urls = []
    for url in urls:
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in suspicious_patterns):
            suspicious_urls.append(url)
    
    return {
        'is_suspicious': len(suspicious_urls) > 0,
        'urls': suspicious_urls
    }

async def warn_user(user, guild, reason):
    """Warn a user and track warnings"""
    user_id = str(user.id)
    if user_id not in user_warnings:
        user_warnings[user_id] = []
    
    user_warnings[user_id].append({
        'timestamp': datetime.utcnow(),
        'reason': reason
    })
    
    warning_count = len(user_warnings[user_id])
    
    try:
        await user.send(
            f"**Warning from {guild.name}**\n"
            f"Reason: {reason}\n"
            f"Total warnings: {warning_count}\n\n"
            f"Please follow the server rules."
        )
    except:
        pass  # User has DMs disabled
    
    return warning_count

@bot.event
async def on_ready():
    print(f'Guardian Bot is online: {bot.user}')
    print(f'Serving {len(bot.guilds)} server(s)')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for rule violations"
        )
    )

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author.bot:
        return
    
    # Check if moderation is limited to specific channels
    if config.MODERATION_CHANNELS and message.channel.id not in config.MODERATION_CHANNELS:
        await bot.process_commands(message)
        return
    
    # Skip moderation for moderators but still process their commands (if exemption is enabled)
    if config.EXEMPT_MODERATORS and isinstance(message.author, discord.Member) and is_moderator(message.author):
        await bot.process_commands(message)
        return
    
    violations = []
    
    # Check text content for toxicity
    if message.content:
        toxicity_result = await check_toxicity(message.content)
        if toxicity_result['is_toxic']:
            violations.append(f"Toxic content (score: {toxicity_result['score']:.2f}): {toxicity_result['reason']}")
        
        # Check for suspicious links
        link_check = await check_suspicious_links(message.content)
        if link_check['is_suspicious']:
            violations.append(f"Suspicious link detected: {', '.join(link_check['urls'])}")
    
    # Check attachments for NSFW content
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                nsfw_result = await check_image_nsfw(attachment.url)
                if nsfw_result['is_nsfw']:
                    violations.append(f"NSFW image (score: {nsfw_result['score']:.2f}): {nsfw_result['reason']}")
    
    # Take action if violations found
    if violations:
        violation_text = "\n".join(violations)
        
        # Delete message
        try:
            await message.delete()
        except:
            pass
        
        # Warn user
        if config.WARN_USERS:
            warning_count = await warn_user(message.author, message.guild, violation_text)
            
            # Send warning in channel
            warning_msg = await message.channel.send(
                f"{message.author.mention} Your message was removed.\n"
                f"Reason: {violation_text}\n"
                f"Warnings: {warning_count}"
            )
            
            # Delete warning after 10 seconds
            await asyncio.sleep(10)
            try:
                await warning_msg.delete()
            except:
                pass
        
        # Log to mod channel
        await log_action(
            message.guild,
            "Message Deleted",
            message.author,
            violation_text,
            message.content[:200] if message.content else "[Image/Attachment]"
        )
    
    await bot.process_commands(message)

@bot.command(name='commands')
async def commands_list(ctx):
    """Display all available Guardian Bot commands"""
    embed = discord.Embed(
        title="🛡️ Guardian Bot Commands",
        description="AI-powered moderation bot using Groq",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📋 !guardian commands",
        value="Show this help message",
        inline=False
    )
    
    embed.add_field(
        name="📊 !guardian status",
        value="Check bot status and configuration",
        inline=False
    )
    
    embed.add_field(
        name="📈 !guardian stats [@user]",
        value="View warning statistics for yourself or another user (Moderator only)",
        inline=False
    )
    
    embed.add_field(
        name="🧹 !guardian clearwarnings @user",
        value="Clear all warnings for a user (Admin only)",
        inline=False
    )
    
    embed.add_field(
        name="🤖 Automatic Features",
        value="• Toxic message detection\n"
              "• NSFW image filtering\n"
              "• Phishing link detection\n"
              "• Auto-warnings & timeouts\n"
              "• Moderation logging",
        inline=False
    )
    
    embed.set_footer(text="Moderators are exempt from automatic moderation")
    await ctx.send(embed=embed)

@bot.command(name='check')
async def check_message(ctx, *, message: str):
    """Manually check a message for toxicity (useful for testing)"""
    async with ctx.typing():
        result = await check_toxicity(message)
        
        embed = discord.Embed(
            title="🔍 Toxicity Check",
            color=discord.Color.red() if result['is_toxic'] else discord.Color.green()
        )
        embed.add_field(name="Message", value=message[:500], inline=False)
        embed.add_field(name="Toxicity Score", value=f"{result['score']:.2f}/1.0", inline=True)
        embed.add_field(name="Threshold", value=f"{config.TOXICITY_THRESHOLD}", inline=True)
        embed.add_field(name="Is Toxic?", value="✅ Yes" if result['is_toxic'] else "❌ No", inline=True)
        
        if result['reason']:
            embed.add_field(name="Analysis", value=result['reason'], inline=False)
        
        await ctx.send(embed=embed)

@bot.command(name='checkimage')
async def check_image_command(ctx):
    """Manually check an attached image for NSFW content"""
    if not ctx.message.attachments:
        await ctx.send("Please attach an image to check.")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith('image/'):
        await ctx.send("Please attach a valid image file.")
        return
    
    async with ctx.typing():
        result = await check_image_nsfw(attachment.url)
        
        embed = discord.Embed(
            title="🖼️ NSFW Check",
            color=discord.Color.red() if result['is_nsfw'] else discord.Color.green()
        )
        embed.set_thumbnail(url=attachment.url)
        embed.add_field(name="NSFW Score", value=f"{result['score']:.2f}/1.0", inline=True)
        embed.add_field(name="Threshold", value=f"{config.NSFW_THRESHOLD}", inline=True)
        embed.add_field(name="Is NSFW?", value="✅ Yes" if result['is_nsfw'] else "❌ No", inline=True)
        
        if result['reason']:
            embed.add_field(name="Analysis", value=result['reason'], inline=False)
        
        await ctx.send(embed=embed)

@bot.command(name='stats')
@commands.has_permissions(manage_messages=True)
async def stats(ctx, user: discord.Member = None):
    """Check warning stats for a user"""
    if user is None:
        user = ctx.author
    
    user_id = str(user.id)
    warnings = user_warnings.get(user_id, [])
    
    embed = discord.Embed(
        title=f"Moderation Stats: {user.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Total Warnings", value=str(len(warnings)), inline=False)
    
    if warnings:
        recent = warnings[-3:]  # Last 3 warnings
        recent_text = "\n".join([
            f"{w['timestamp'].strftime('%Y-%m-%d %H:%M')}: {w['reason'][:100]}"
            for w in recent
        ])
        embed.add_field(name="Recent Warnings", value=recent_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='clearwarnings')
@commands.has_permissions(administrator=True)
async def clear_warnings(ctx, user: discord.Member):
    """Clear all warnings for a user (Admin only)"""
    user_id = str(user.id)
    if user_id in user_warnings:
        del user_warnings[user_id]
        await ctx.send(f"Cleared all warnings for {user.mention}")
    else:
        await ctx.send(f"{user.mention} has no warnings")

@bot.command(name='status')
async def status(ctx):
    """Check bot status and configuration"""
    embed = discord.Embed(
        title="Guardian Bot Status",
        color=discord.Color.green()
    )
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Toxicity Threshold", value=f"{config.TOXICITY_THRESHOLD}", inline=True)
    embed.add_field(name="NSFW Threshold", value=f"{config.NSFW_THRESHOLD}", inline=True)
    embed.add_field(
        name="Features",
        value="- Toxic message detection\n- NSFW image detection\n- Phishing link detection\n- Auto-moderation",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)