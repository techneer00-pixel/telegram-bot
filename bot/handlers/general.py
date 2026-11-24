import time
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import bot
from bot.services.database import db
import config

logger = logging.getLogger("HarmoniX.General")

START_TEXT = f"""
✨ **Hello! I am {config.BOT_NAME}**

I am an all-in-one Telegram bot designed to:
🎶 **Stream audio & 720p HD video** in Group Voice Chats.
🛡 **Manage and moderate** your Telegram groups with ease.
👋 **Welcome new members** with custom greetings and rules.
📢 **Promotions & Broadcasts** across connected communities.

Add me to your group and promote me as an admin to get started!
"""

HELP_TEXT = """
📖 **Available Commands Guide**

🎵 **Music & Video Commands:**
• `/play <name or link>` - Stream music in voice chat
• `/vplay <name or link>` - Stream 720p HD video in voice chat
• `/pause` - Pause ongoing playback
• `/resume` - Resume paused playback
• `/skip` - Skip to next track
• `/stop` - Stop streaming and leave voice chat
• `/queue` - Display current playlist/queue
• `/song <name>` - Download and send the audio file directly

📢 **Promotions & Info:**
• `/promo` - View official channels, sponsors, and advertising
• `/stats` - View live bot statistics & connected groups
• `/broadcast <msg>` - (Owner) Broadcast promotion to all groups

🛡 **Group Management Commands:**
• `/ban <user>` - Ban user from group
• `/unban <user>` - Unban user from group
• `/mute <user>` - Mute user in group
• `/unmute <user>` - Unmute user in group
• `/kick <user>` - Kick user from group
• `/pin` - Pin replied message
• `/unpin` - Unpin replied message
• `/purge` - Delete messages up to replied message
• `/id` - View User ID and Chat ID
"""

@bot.on_message(group=-1)
async def incoming_debug_logger(_, message: Message):
    """Logs every incoming message and registers chats for broadcasting."""
    if message.chat:
        db.add_chat(message.chat.id)
    if message.from_user:
        db.add_user(message.from_user.id)

    chat_info = message.chat.title or message.chat.first_name or "Private Chat"
    sender = message.from_user.first_name if message.from_user else "Unknown"
    logger.info(f"📩 [INCOMING] in '{chat_info}' from {sender} (ID: {message.from_user.id if message.from_user else 'N/A'}): {message.text or '[Media/Service]'}")

@bot.on_message(filters.command("start", prefixes=config.COMMAND_PREFIXES))
async def start_handler(_, message: Message):
    try:
        user_name = message.from_user.first_name if message.from_user else "User"
        logger.info(f"Received /start from {user_name} (ID: {message.from_user.id if message.from_user else 'Unknown'})")
        bot_username = bot.me.username if bot.me else (await bot.get_me()).username
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Add to Group",
                        url=f"https://t.me/{bot_username}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu"),
                ],
            ]
        )
        await message.reply_text(START_TEXT, reply_markup=buttons, quote=True)
    except Exception as e:
        logger.error(f"Error handling /start: {e}", exc_info=True)

@bot.on_message(filters.command("help", prefixes=config.COMMAND_PREFIXES))
async def help_handler(_, message: Message):
    try:
        logger.info(f"Received /help from {message.from_user.id if message.from_user else 'Unknown'}")
        await message.reply_text(HELP_TEXT, quote=True)
    except Exception as e:
        logger.error(f"Error handling /help: {e}", exc_info=True)

@bot.on_callback_query(filters.regex("^help_menu$"))
async def help_callback(_, query):
    try:
        await query.message.edit_text(
            HELP_TEXT,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="start_menu")]]
            ),
        )
    except Exception as e:
        logger.error(f"Error in help_callback: {e}", exc_info=True)

@bot.on_callback_query(filters.regex("^start_menu$"))
async def start_callback(_, query):
    try:
        bot_username = bot.me.username if bot.me else (await bot.get_me()).username
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Add to Group",
                        url=f"https://t.me/{bot_username}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu"),
                ],
            ]
        )
        await query.message.edit_text(START_TEXT, reply_markup=buttons)
    except Exception as e:
        logger.error(f"Error in start_callback: {e}", exc_info=True)

@bot.on_message(filters.command("ping", prefixes=config.COMMAND_PREFIXES))
async def ping_handler(_, message: Message):
    try:
        start = time.time()
        reply = await message.reply_text("🏓 Pinging...")
        end = time.time()
        latency = round((end - start) * 1000, 2)
        await reply.edit_text(f"🏓 **Pong!**\n⚡ Latency: `{latency} ms`")
    except Exception as e:
        logger.error(f"Error in ping_handler: {e}", exc_info=True)

@bot.on_message(filters.command(["promo", "promote", "ads"], prefixes=config.COMMAND_PREFIXES))
async def promo_handler(_, message: Message):
    """Displays promotional information and official sponsor links."""
    text = f"📢 **Promotions & Official Links for {config.BOT_NAME}**\n\n"
    if config.PROMO_TEXT:
        text += f"✨ {config.PROMO_TEXT}\n\n"
    text += "🚀 Want to sponsor or promote your channel/group with our bot?\n"
    text += "Reach thousands of active members across connected groups.\n\n"
    text += "Connect with our official channels below:"

    buttons = []
    row = []
    if config.UPDATES_CHANNEL:
        url = config.UPDATES_CHANNEL if config.UPDATES_CHANNEL.startswith("http") else f"https://t.me/{config.UPDATES_CHANNEL.lstrip('@')}"
        row.append(InlineKeyboardButton("📢 Channel", url=url))
    if config.SUPPORT_GROUP:
        url = config.SUPPORT_GROUP if config.SUPPORT_GROUP.startswith("http") else f"https://t.me/{config.SUPPORT_GROUP.lstrip('@')}"
        row.append(InlineKeyboardButton("💬 Support", url=url))
    if config.PROMO_URL and not row:
        row.append(InlineKeyboardButton("🌟 Sponsor", url=config.PROMO_URL))
    if row:
        buttons.append(row)

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None, quote=True)

@bot.on_message(filters.command(["stats", "status"], prefixes=config.COMMAND_PREFIXES))
async def stats_handler(_, message: Message):
    """Displays live bot reach statistics."""
    chats_count = len(db.get_chats())
    users_count = len(db.get_users())
    await message.reply_text(
        f"📊 **{config.BOT_NAME} Network Statistics:**\n\n"
        f"👥 **Connected Communities:** `{chats_count}`\n"
        f"👤 **Total Users Discovered:** `{users_count}`\n"
        f"⚡ **Media Engine:** PyTgCalls v3.0 (Audio + 720p Video)\n"
        f"🛡 **Framework:** Pyrogram v2",
        quote=True
    )
