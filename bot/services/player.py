import os
import logging
from typing import Optional, Dict, Any
from bot import client
from bot.client import bot
from bot.services.queue_manager import music_queue

logger = logging.getLogger("HarmoniX.Player")

def get_media_stream(file_path: str, is_video: bool = False):
    """Returns appropriate PyTgCalls MediaStream object depending on installed version."""
    try:
        from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
        if is_video:
            return MediaStream(
                file_path,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.HD_720p,
            )
        return MediaStream(
            file_path,
            audio_parameters=AudioQuality.STUDIO,
            video_flags=MediaStream.Flags.IGNORE,
        )
    except Exception:
        try:
            from pytgcalls.types import MediaStream
            return MediaStream(file_path)
        except Exception:
            from pytgcalls.types.input_stream import AudioPiped
            return AudioPiped(file_path)

async def play_next(chat_id: int) -> Optional[Dict[str, Any]]:
    """Plays the next song in the queue for the given chat_id."""
    next_track = music_queue.pop(chat_id)
    if not next_track:
        await stop_stream(chat_id)
        try:
            await bot.send_message(
                chat_id,
                "🎵 **Queue finished!** Left the voice chat.",
            )
        except Exception as e:
            logger.error(f"Error sending queue finished message: {e}")
        return None

    try:
        is_vid = next_track.get("is_video", False)
        stream = get_media_stream(next_track["file_path"], is_video=is_vid)
        if hasattr(client.call_py, "play"):
            await client.call_py.play(chat_id, stream)
        elif hasattr(client.call_py, "change_stream"):
            await client.call_py.change_stream(chat_id, stream)

        media_icon = "🎥" if is_vid else "▶️"
        await bot.send_message(
            chat_id,
            f"{media_icon} **Now Playing:** [{next_track['title']}]({next_track['url']})\n"
            f"⏱ **Duration:** `{next_track['duration_str']}`\n"
            f"👤 **Requested by:** {next_track.get('requester', 'Unknown')}",
            disable_web_page_preview=True
        )
        return next_track
    except Exception as e:
        logger.error(f"Failed to play next song in chat {chat_id}: {e}")
        # Try playing next after failure
        return await play_next(chat_id)

async def ensure_assistant_in_chat(chat_id: int):
    """Ensures assistant account has joined the chat and resolved the peer."""
    if client.assistant is None:
        return
    try:
        await client.assistant.get_chat(chat_id)
    except Exception as e:
        logger.info(f"Assistant not yet in chat {chat_id} or cannot resolve peer ({e}). Attempting auto-join...")
        # 1. Try adding directly via bot
        try:
            asst = await client.assistant.get_me()
            await bot.add_chat_members(chat_id, asst.id)
            logger.info(f"Assistant auto-added directly to chat {chat_id}.")
            return
        except Exception:
            pass

        # 2. Try creating invite link and having assistant join
        try:
            chat = await bot.get_chat(chat_id)
            invite_link = chat.invite_link
            if not invite_link:
                new_invite = await bot.create_chat_invite_link(chat_id)
                invite_link = new_invite.invite_link

            if invite_link:
                await client.assistant.join_chat(invite_link)
                logger.info(f"Assistant successfully auto-joined chat {chat_id}.")
        except Exception as join_err:
            logger.warning(f"Auto-join assistant failed: {join_err}")

async def start_or_queue_stream(chat_id: int, track: Dict[str, Any]) -> str:
    """
    Adds track to queue. If nothing was playing, starts streaming.
    Returns status: 'playing' or 'queued'.
    """
    if client.call_py is None:
        raise RuntimeError(
            "Voice chat streaming is not available. Please configure SESSION_STRING in .env to enable Voice Chat music."
        )

    is_first = music_queue.is_empty(chat_id)
    position = music_queue.add(chat_id, track)

    if is_first:
        await ensure_assistant_in_chat(chat_id)
        is_vid = track.get("is_video", False)
        stream = get_media_stream(track["file_path"], is_video=is_vid)
        try:
            if hasattr(client.call_py, "play"):
                await client.call_py.play(chat_id, stream)
            elif hasattr(client.call_py, "join_group_call"):
                await client.call_py.join_group_call(chat_id, stream)
        except Exception as e:
            music_queue.clear(chat_id)
            raise e
        return "playing"
    else:
        return f"queued:{position}"

async def pause_stream(chat_id: int) -> bool:
    if client.call_py is None:
        return False
    try:
        if hasattr(client.call_py, "pause_stream"):
            await client.call_py.pause_stream(chat_id)
        elif hasattr(client.call_py, "pause"):
            await client.call_py.pause(chat_id)
        return True
    except Exception as e:
        logger.error(f"Error pausing stream: {e}")
        return False

async def resume_stream(chat_id: int) -> bool:
    if client.call_py is None:
        return False
    try:
        if hasattr(client.call_py, "resume_stream"):
            await client.call_py.resume_stream(chat_id)
        elif hasattr(client.call_py, "resume"):
            await client.call_py.resume(chat_id)
        return True
    except Exception as e:
        logger.error(f"Error resuming stream: {e}")
        return False

async def stop_stream(chat_id: int) -> bool:
    if client.call_py is None:
        music_queue.clear(chat_id)
        return False
    try:
        music_queue.clear(chat_id)
        if hasattr(client.call_py, "leave_call"):
            await client.call_py.leave_call(chat_id)
        elif hasattr(client.call_py, "leave_group_call"):
            await client.call_py.leave_group_call(chat_id)
        return True
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        return False

# Register Stream End Event if PyTgCalls is loaded
def register_call_handlers():
    if client.call_py is not None:
        try:
            @client.call_py.on_update()
            async def stream_update_handler(_, update):
                try:
                    name = update.__class__.__name__
                    if "StreamAudioEnded" in name or "StreamEnded" in name:
                        chat_id = getattr(update, "chat_id", None)
                        if chat_id:
                            await play_next(chat_id)
                except Exception as ex:
                    logger.error(f"Error in stream update handler: {ex}")
        except Exception as err:
            logger.warning(f"Could not register auto-next callback on call_py: {err}")

register_call_handlers()
