import os
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import client
from bot.client import bot
from bot.services.downloader import search_and_download
from bot.services.queue_manager import music_queue
from bot.services.player import (
    start_or_queue_stream,
    pause_stream,
    resume_stream,
    stop_stream,
    play_next,
)
import config

logger = logging.getLogger("HarmoniX.Music")

def get_control_buttons() -> InlineKeyboardMarkup:
    """Generates music & video playback control buttons with promotional links."""
    buttons = [
        [
            InlineKeyboardButton("⏸ Pause", callback_data="music_pause"),
            InlineKeyboardButton("▶️ Resume", callback_data="music_resume"),
            InlineKeyboardButton("⏭ Skip", callback_data="music_skip"),
        ],
        [
            InlineKeyboardButton("⏹ Stop", callback_data="music_stop"),
            InlineKeyboardButton("📜 Queue", callback_data="music_queue"),
        ],
    ]
    promo_row = []
    if config.UPDATES_CHANNEL:
        url = config.UPDATES_CHANNEL if config.UPDATES_CHANNEL.startswith("http") else f"https://t.me/{config.UPDATES_CHANNEL.lstrip('@')}"
        promo_row.append(InlineKeyboardButton("📢 Channel", url=url))
    if config.SUPPORT_GROUP:
        url = config.SUPPORT_GROUP if config.SUPPORT_GROUP.startswith("http") else f"https://t.me/{config.SUPPORT_GROUP.lstrip('@')}"
        promo_row.append(InlineKeyboardButton("💬 Support", url=url))
    if config.PROMO_URL and not promo_row:
        promo_row.append(InlineKeyboardButton("🌟 Sponsor", url=config.PROMO_URL))
    if promo_row:
        buttons.append(promo_row)
    return InlineKeyboardMarkup(buttons)

def get_promo_tag() -> str:
    return f"\n\n📢 {config.PROMO_TEXT}" if config.PROMO_TEXT else ""

@bot.on_message(filters.command(["play", "p"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def play_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ Please provide a song name or YouTube link!\n"
            "Example: `/play Believer Imagine Dragons`",
            quote=True,
        )

    query = message.text.split(maxsplit=1)[1]
    status_msg = await message.reply_text(f"🔍 Searching for **{query}**...", quote=True)

    try:
        track = await search_and_download(query)
        track["requester"] = message.from_user.mention
    except Exception as e:
        logger.error(f"Download/Search error: {e}")
        return await status_msg.edit_text(f"❌ Failed to find or download song: `{e}`")

    # If PyTgCalls is not initialized, fallback to sending audio directly to the chat
    if client.call_py is None:
        await status_msg.edit_text("📤 Uploading audio directly to chat...")
        try:
            await message.reply_audio(
                audio=track["file_path"],
                title=track["title"],
                duration=track["duration"],
                caption=(
                    f"🎵 **{track['title']}**\n"
                    f"⏱ **Duration:** `{track['duration_str']}`\n"
                    f"👤 **Requested by:** {track['requester']}\n\n"
                    f"💡 *Sent directly as audio file. (Voice Chat streaming requires an assistant SESSION_STRING).* "
                ),
                quote=True,
            )
            return await status_msg.delete()
        except Exception as e:
            logger.error(f"Failed to send audio file: {e}")
            return await status_msg.edit_text(f"❌ Failed to upload song: `{e}`")

    try:
        res = await start_or_queue_stream(message.chat.id, track)
        buttons = get_control_buttons()
        promo_tag = get_promo_tag()

        if res == "playing":
            await status_msg.edit_text(
                f"▶️ **Started Playing in Voice Chat:**\n\n"
                f"🏷 **Title:** [{track['title']}]({track['url']})\n"
                f"⏱ **Duration:** `{track['duration_str']}`\n"
                f"👤 **Requested by:** {track['requester']}"
                f"{promo_tag}",
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
        else:
            pos = res.split(":")[1]
            await status_msg.edit_text(
                f"⏳ **Added to Queue at Position #{pos}:**\n\n"
                f"🏷 **Title:** [{track['title']}]({track['url']})\n"
                f"⏱ **Duration:** `{track['duration_str']}`\n"
                f"👤 **Requested by:** {track['requester']}"
                f"{promo_tag}",
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
    except Exception as e:
        logger.error(f"Stream error: {e}")
        err_msg = str(e)
        if "CHANNEL_INVALID" in err_msg or "USER_NOT_PARTICIPANT" in err_msg or "ChannelInvalid" in err_msg:
            asst_username = None
            if client.assistant is not None:
                try:
                    me = await client.assistant.get_me()
                    asst_username = me.username
                except Exception:
                    pass

            button = None
            if asst_username:
                button = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Assistant to Group", url=f"https://t.me/{asst_username}?startgroup=true")]
                ])

            return await status_msg.edit_text(
                "⚠️ **Assistant is not in this group!**\n\n"
                f"To play music in Voice Chat, the assistant account "
                f"({f'@{asst_username}' if asst_username else 'Userbot'}) "
                "must be a member of this group with permission to speak.\n\n"
                "👉 Please add the assistant to the group, start the Voice Chat, and try `/play` again!",
                reply_markup=button,
            )

        await status_msg.edit_text(
            f"❌ **Failed to start stream:** `{e}`\n\n"
            "Ensure that:\n"
            "1. A Voice Chat is actively started in this group.\n"
            "2. The assistant account is in this group with permission to speak."
        )

@bot.on_message(filters.command(["vplay", "v", "video", "vstream"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def vplay_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ Please provide a video name or YouTube link!\n"
            "Example: `/vplay Believer Imagine Dragons`",
            quote=True,
        )

    query = message.text.split(maxsplit=1)[1]
    status_msg = await message.reply_text(f"🔍 Searching & downloading video for **{query}**...", quote=True)

    try:
        track = await search_and_download(query, is_video=True)
        track["requester"] = message.from_user.mention
    except Exception as e:
        logger.error(f"Video Download/Search error: {e}")
        return await status_msg.edit_text(f"❌ Failed to find or download video: `{e}`")

    # If PyTgCalls is not initialized, fallback to sending video directly to the chat
    if client.call_py is None:
        await status_msg.edit_text("📤 Uploading video directly to chat...")
        try:
            await message.reply_video(
                video=track["file_path"],
                caption=(
                    f"🎥 **{track['title']}**\n"
                    f"⏱ **Duration:** `{track['duration_str']}`\n"
                    f"👤 **Requested by:** {track['requester']}\n\n"
                    f"💡 *Sent directly as video file. (Video Chat streaming requires an assistant SESSION_STRING).*"
                    f"{get_promo_tag()}"
                ),
                quote=True,
            )
            return await status_msg.delete()
        except Exception as e:
            logger.error(f"Failed to send video file: {e}")
            return await status_msg.edit_text(f"❌ Failed to upload video: `{e}`")

    try:
        res = await start_or_queue_stream(message.chat.id, track)
        buttons = get_control_buttons()
        promo_tag = get_promo_tag()

        if res == "playing":
            await status_msg.edit_text(
                f"🎥 **Started Video Streaming in Voice Chat:**\n\n"
                f"🏷 **Title:** [{track['title']}]({track['url']})\n"
                f"⏱ **Duration:** `{track['duration_str']}`\n"
                f"👤 **Requested by:** {track['requester']}"
                f"{promo_tag}",
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
        else:
            pos = res.split(":")[1]
            await status_msg.edit_text(
                f"⏳ **Added Video to Queue at Position #{pos}:**\n\n"
                f"🏷 **Title:** [{track['title']}]({track['url']})\n"
                f"⏱ **Duration:** `{track['duration_str']}`\n"
                f"👤 **Requested by:** {track['requester']}"
                f"{promo_tag}",
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
    except Exception as e:
        logger.error(f"Video Stream error: {e}")
        err_msg = str(e)
        if "CHANNEL_INVALID" in err_msg or "USER_NOT_PARTICIPANT" in err_msg or "ChannelInvalid" in err_msg:
            asst_username = None
            if client.assistant is not None:
                try:
                    me = await client.assistant.get_me()
                    asst_username = me.username
                except Exception:
                    pass

            button = None
            if asst_username:
                button = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Assistant to Group", url=f"https://t.me/{asst_username}?startgroup=true")]
                ])

            return await status_msg.edit_text(
                "⚠️ **Assistant is not in this group!**\n\n"
                f"To stream video in Voice Chat, the assistant account "
                f"({f'@{asst_username}' if asst_username else 'Userbot'}) "
                "must be a member of this group with permission to speak.\n\n"
                "👉 Please add the assistant to the group, start the Video Chat, and try `/vplay` again!",
                reply_markup=button,
            )

        await status_msg.edit_text(
            f"❌ **Failed to start video stream:** `{e}`\n\n"
            "Ensure that:\n"
            "1. A Video/Voice Chat is actively started in this group.\n"
            "2. The assistant account is in this group with permission to speak."
        )

@bot.on_message(filters.command(["song"], prefixes=config.COMMAND_PREFIXES))
async def send_song_file(_, message: Message):
    """Downloads and sends audio file directly to the chat."""
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/song <song name or link>`", quote=True)

    query = message.text.split(maxsplit=1)[1]
    status = await message.reply_text(f"📥 Downloading audio for: **{query}**...", quote=True)

    try:
        track = await search_and_download(query)
        await status.edit_text("📤 Uploading audio to Telegram...")

        await message.reply_audio(
            audio=track["file_path"],
            title=track["title"],
            duration=track["duration"],
            caption=f"🎵 **{track['title']}**\n👤 Requested by {message.from_user.mention}",
            quote=True,
        )
        await status.delete()
    except Exception as e:
        logger.error(f"Failed to send song: {e}")
        await status.edit_text(f"❌ Failed to download or upload song: `{e}`")

@bot.on_message(filters.command("pause", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def pause_cmd(_, message: Message):
    if await pause_stream(message.chat.id):
        await message.reply_text("⏸ **Playback paused.**")
    else:
        await message.reply_text("⚠️ Nothing is currently playing or failed to pause.")

@bot.on_message(filters.command("resume", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def resume_cmd(_, message: Message):
    if await resume_stream(message.chat.id):
        await message.reply_text("▶️ **Playback resumed.**")
    else:
        await message.reply_text("⚠️ Stream is not paused or nothing is playing.")

@bot.on_message(filters.command("skip", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def skip_cmd(_, message: Message):
    status = await message.reply_text("⏭ **Skipping current track...**")
    next_track = await play_next(message.chat.id)
    if not next_track:
        await status.edit_text("⏹ **Queue finished! Left voice chat.**")
    else:
        await status.delete()

@bot.on_message(filters.command("stop", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def stop_cmd(_, message: Message):
    await stop_stream(message.chat.id)
    await message.reply_text("⏹ **Playback stopped and queue cleared.**")

@bot.on_message(filters.command("queue", prefixes=config.COMMAND_PREFIXES) & filters.group)
async def queue_cmd(_, message: Message):
    q = music_queue.get_queue(message.chat.id)
    if not q:
        return await message.reply_text("📭 The queue is currently empty.")

    text = "📜 **Current Music Queue:**\n\n"
    text += f"▶️ **Now Playing:** {q[0]['title']} (`{q[0]['duration_str']}`)\n\n"

    if len(q) > 1:
        text += "📋 **Up Next:**\n"
        for i, track in enumerate(q[1:], start=1):
            text += f"`{i}.` {track['title']} (`{track['duration_str']}`) | Req: {track.get('requester', 'Unknown')}\n"

    await message.reply_text(text, disable_web_page_preview=True)

# Callback queries for inline music buttons
@bot.on_callback_query(filters.regex("^music_pause$"))
async def cb_pause(_, query):
    if await pause_stream(query.message.chat.id):
        await query.answer("Playback paused!")
    else:
        await query.answer("Could not pause.", show_alert=True)

@bot.on_callback_query(filters.regex("^music_resume$"))
async def cb_resume(_, query):
    if await resume_stream(query.message.chat.id):
        await query.answer("Playback resumed!")
    else:
        await query.answer("Could not resume.", show_alert=True)

@bot.on_callback_query(filters.regex("^music_skip$"))
async def cb_skip(_, query):
    await query.answer("Skipping track...")
    await play_next(query.message.chat.id)

@bot.on_callback_query(filters.regex("^music_stop$"))
async def cb_stop(_, query):
    await stop_stream(query.message.chat.id)
    await query.answer("Stopped playback and left.")
    await query.message.reply_text("⏹ **Playback stopped by user.**")

@bot.on_callback_query(filters.regex("^music_queue$"))
async def cb_queue(_, query):
    q = music_queue.get_queue(query.message.chat.id)
    if not q:
        return await query.answer("Queue is empty!", show_alert=True)

    text = f"▶️ Now: {q[0]['title']}\n"
    if len(q) > 1:
        text += f"Next: {len(q)-1} tracks in queue."
    await query.answer(text, show_alert=True)
