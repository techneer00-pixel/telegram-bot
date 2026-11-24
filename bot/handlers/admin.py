import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from bot.client import bot
import config

logger = logging.getLogger("HarmoniX.Admin")

async def is_admin(chat_id: int, user_id: int) -> bool:
    """Check if the user is an administrator or owner of the chat."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status.name in ("ADMINISTRATOR", "OWNER")
    except Exception:
        return False

async def get_target_user(message: Message):
    """Extracts target user ID from replied message or argument."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    args = message.text.split()
    if len(args) > 1:
        target = args[1]
        try:
            if target.isdigit():
                user = await bot.get_users(int(target))
            else:
                user = await bot.get_users(target)
            return user
        except Exception:
            return None
    return None

@bot.on_message(filters.command("ban", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def ban_user(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("⚠️ Please reply to a user's message or specify their username/ID to ban.")

    if await is_admin(message.chat.id, user.id):
        return await message.reply_text("❌ You cannot ban another administrator.")

    try:
        await message.chat.ban_member(user.id)
        await message.reply_text(f"🔨 **Banned:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to ban: `{e}`")

@bot.on_message(filters.command("unban", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def unban_user(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("⚠️ Please reply to a user's message or specify their username/ID to unban.")

    try:
        await message.chat.unban_member(user.id)
        await message.reply_text(f"✅ **Unbanned:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unban: `{e}`")

@bot.on_message(filters.command("kick", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def kick_user(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("⚠️ Please reply to a user's message or specify their username/ID to kick.")

    if await is_admin(message.chat.id, user.id):
        return await message.reply_text("❌ You cannot kick another administrator.")

    try:
        await message.chat.ban_member(user.id)
        await message.chat.unban_member(user.id)
        await message.reply_text(f"👢 **Kicked:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to kick: `{e}`")

@bot.on_message(filters.command("mute", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def mute_user(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("⚠️ Please reply to a user or provide username/ID to mute.")

    if await is_admin(message.chat.id, user.id):
        return await message.reply_text("❌ You cannot mute an administrator.")

    try:
        await message.chat.restrict_member(user.id, permissions=ChatPermissions())
        await message.reply_text(f"🔇 **Muted:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to mute: `{e}`")

@bot.on_message(filters.command("unmute", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def unmute_user(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("⚠️ Please reply to a user or provide username/ID to unmute.")

    try:
        # Restore standard permissions
        await message.chat.restrict_member(
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.reply_text(f"🔊 **Unmuted:** {user.mention}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unmute: `{e}`")

@bot.on_message(filters.command("pin", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def pin_message(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to pin messages.")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to the message you want to pin.")

    try:
        await message.reply_to_message.pin()
        await message.reply_text("📌 **Message pinned successfully.**")
    except Exception as e:
        await message.reply_text(f"❌ Failed to pin: `{e}`")

@bot.on_message(filters.command("unpin", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def unpin_message(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to unpin messages.")

    try:
        if message.reply_to_message:
            await message.reply_to_message.unpin()
        else:
            await message.chat.unpin_all_messages()
        await message.reply_text("📌 **Message(s) unpinned.**")
    except Exception as e:
        await message.reply_text(f"❌ Failed to unpin: `{e}`")

@bot.on_message(filters.command("purge", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def purge_messages(_, message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ You need to be an admin to purge messages.")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a message to purge from there down to this command.")

    start_id = message.reply_to_message.id
    end_id = message.id
    message_ids = list(range(start_id, end_id + 1))

    # Pyrogram can delete up to 100 messages at once
    chunks = [message_ids[i:i + 100] for i in range(0, len(message_ids), 100)]
    deleted_count = 0

    for chunk in chunks:
        try:
            await bot.delete_messages(chat_id=message.chat.id, message_ids=chunk)
            deleted_count += len(chunk)
        except Exception as e:
            logger.error(f"Error purging messages: {e}")

    notice = await bot.send_message(message.chat.id, f"🧹 **Purged {deleted_count} messages!**")
    # Auto delete confirmation after 5 seconds
    import asyncio
    await asyncio.sleep(5)
    try:
        await notice.delete()
    except Exception:
        pass

@bot.on_message(filters.command("id", prefixes=config.COMMAND_PREFIXES))
async def id_info(_, message: Message):
    chat = message.chat
    reply = message.reply_to_message

    text = f"💬 **Chat ID:** `{chat.id}`\n"
    text += f"👤 **Your User ID:** `{message.from_user.id}`\n"

    if reply and reply.from_user:
        text += f"🎯 **Replied User ID:** `{reply.from_user.id}`\n"
    if reply:
        text += f"✉️ **Replied Message ID:** `{reply.id}`\n"

    await message.reply_text(text, quote=True)

from bot.services.database import db

@bot.on_message(filters.command(["broadcast", "gcast", "bcast"], prefixes=config.COMMAND_PREFIXES))
async def broadcast_command(_, message: Message):
    """Broadcasts a promotional message or media to all served chats."""
    # Only bot owner can broadcast
    if config.OWNER_ID and message.from_user.id != config.OWNER_ID:
        return await message.reply_text("❌ Only the bot owner can broadcast promotional messages.")

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "⚠️ **Usage:**\n"
            "• Reply to any message/photo/video with `/broadcast`\n"
            "• Or type `/broadcast <Your promotion message>`",
            quote=True
        )

    chats = db.get_chats()
    if not chats:
        return await message.reply_text("ℹ️ No served chats found in database yet.")

    status = await message.reply_text(f"🚀 **Broadcasting promotion to {len(chats)} chats...**", quote=True)
    success = 0
    failed = 0

    for chat_id in chats:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(chat_id)
            else:
                promo_content = message.text.split(maxsplit=1)[1]
                await bot.send_message(chat_id, promo_content, disable_web_page_preview=False)
            success += 1
            await asyncio.sleep(0.2)  # Avoid Telegram FloodWait rate limits
        except Exception:
            failed += 1

    await status.edit_text(
        f"📢 **Promotion Broadcast Completed!**\n\n"
        f"✅ **Successfully Sent:** `{success}` chats\n"
        f"❌ **Failed:** `{failed}` chats"
    )
