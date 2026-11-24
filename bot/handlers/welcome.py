import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from bot import client
from bot.client import bot
import config

logger = logging.getLogger("HarmoniX.Welcome")

# In-memory per-chat welcome settings (chat_id -> dict)
chat_welcome_settings = {}

async def auto_add_assistant(chat_id: int) -> bool:
    """Automatically adds or joins the assistant account to the given group chat."""
    if client.assistant is None:
        return False

    try:
        asst = await client.assistant.get_me()
        asst_id = asst.id
    except Exception as e:
        logger.warning(f"Could not retrieve assistant info: {e}")
        return False

    # Check if assistant is already a member
    try:
        member = await bot.get_chat_member(chat_id, asst_id)
        if member and str(member.status) not in ("ChatMemberStatus.BANNED", "ChatMemberStatus.LEFT", "banned", "left"):
            logger.info(f"Assistant is already in chat {chat_id}.")
            return True
    except Exception:
        pass

    # Method 1: Try adding the assistant directly via bot
    try:
        await bot.add_chat_members(chat_id, asst_id)
        logger.info(f"✅ Automatically added assistant to chat {chat_id} directly.")
        return True
    except Exception as e:
        logger.info(f"Direct add_chat_members failed ({e}), attempting join via invite link...")

    # Method 2: Create invite link and have the assistant join
    try:
        chat = await bot.get_chat(chat_id)
        invite_link = chat.invite_link
        if not invite_link:
            invite = await bot.create_chat_invite_link(chat_id)
            invite_link = invite.invite_link

        if invite_link:
            await client.assistant.join_chat(invite_link)
            logger.info(f"✅ Assistant automatically joined chat {chat_id} via invite link.")
            return True
    except Exception as join_err:
        logger.warning(f"Auto-join assistant via invite link failed: {join_err}")

    return False

@bot.on_chat_member_updated()
async def bot_membership_updated(_, update: ChatMemberUpdated):
    """Triggers when bot is added to a group or promoted to Admin to auto-add assistant."""
    if update.new_chat_member and update.new_chat_member.user.is_self:
        status = str(update.new_chat_member.status).lower()
        if "administrator" in status or "member" in status:
            await auto_add_assistant(update.chat.id)

@bot.on_message(filters.new_chat_members)
async def welcome_new_members(_, message: Message):
    chat = message.chat
    bot_user = await bot.get_me()

    # 1. If Bot itself was added
    for member in message.new_chat_members:
        if member.id == bot_user.id:
            asst_joined = await auto_add_assistant(chat.id)
            status_text = "✅ **Voice Assistant:** Joined & ready for VC streaming!" if asst_joined else "💡 **Tip:** Promote me to **Admin** (Invite Users) so the Voice Assistant can auto-join."

            await message.reply_text(
                f"🎉 **Thanks for adding me to {chat.title}!**\n\n"
                f"{status_text}\n\n"
                "📌 **Quick Start:**\n"
                "• Make me an **Admin** with invite permissions.\n"
                "• Start a Voice Chat and type `/play <song name>`!\n"
                "• Type `/help` to see all moderation & music commands.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📖 Help Guide", callback_data="help_menu")]]
                )
            )
            return

    # 2. Check if welcome is globally or locally enabled
    settings = chat_welcome_settings.get(chat.id, {"enabled": config.WELCOME_ENABLED, "custom_msg": None})
    if not settings.get("enabled", True):
        return

    # 3. Greet new human users
    try:
        members_count = await chat.get_members_count()
    except Exception:
        members_count = "N/A"

    for member in message.new_chat_members:
        if member.is_bot:
            continue

        mention = member.mention
        custom_template = settings.get("custom_msg") or config.DEFAULT_WELCOME_MESSAGE

        welcome_text = custom_template.format(
            mention=mention,
            title=chat.title,
            count=members_count,
            first_name=member.first_name,
            id=member.id
        )

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📜 Rules", callback_data="chat_rules"),
                    InlineKeyboardButton("🎵 Music Help", callback_data="help_menu"),
                ]
            ]
        )

        try:
            await message.reply_text(
                welcome_text,
                reply_markup=buttons,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

@bot.on_callback_query(filters.regex("^chat_rules$"))
async def rules_callback(_, query):
    await query.answer(
        "📌 Group Rules:\n"
        "1. Be respectful to all members.\n"
        "2. No spam, advertising, or NSFW content.\n"
        "3. Keep discussions polite and friendly.",
        show_alert=True
    )

@bot.on_message(filters.command(["welcome"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def toggle_welcome(_, message: Message):
    # Only group admins can change welcome settings
    user = await message.chat.get_member(message.from_user.id)
    if user.status.name not in ("ADMINISTRATOR", "OWNER"):
        return await message.reply_text("❌ Only group administrators can configure welcome settings.")

    args = message.text.split()
    if len(args) < 2:
        current = chat_welcome_settings.get(message.chat.id, {}).get("enabled", config.WELCOME_ENABLED)
        status_str = "ENABLED ✅" if current else "DISABLED ❌"
        return await message.reply_text(
            f"ℹ️ Welcome messages are currently: **{status_str}**\n\n"
            f"Use `/welcome on` or `/welcome off` to change."
        )

    mode = args[1].lower()
    if mode in ("on", "enable", "true"):
        chat_welcome_settings.setdefault(message.chat.id, {})["enabled"] = True
        await message.reply_text("✅ Welcome messages enabled for this group.")
    elif mode in ("off", "disable", "false"):
        chat_welcome_settings.setdefault(message.chat.id, {})["enabled"] = False
        await message.reply_text("❌ Welcome messages disabled for this group.")
    else:
        await message.reply_text("⚠️ Invalid option. Use `/welcome on` or `/welcome off`.")
