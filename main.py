import asyncio
import logging
import os
import sys

# Ensure Gyan FFmpeg directory and venv Scripts are on system PATH for PyTgCalls & yt-dlp
for path in [
    os.path.join(sys.prefix, "Scripts"),
    os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"),
]:
    if os.path.isdir(path) and path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")

# Setup logging immediately before any module imports
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("HarmoniX.Main")

from pyrogram import idle
import config
from bot import client
from bot.client import bot, assistant, call_py

# Import handlers to register them with the bot client
from bot.handlers import general, welcome, admin, music

async def main():
    logger.info("Initializing HarmoniX Telegram Bot...")

    # Bind active event loop to Pyrogram clients and dispatchers
    loop = asyncio.get_running_loop()
    bot.loop = loop
    bot.dispatcher.loop = loop
    if assistant is not None:
        assistant.loop = loop
        assistant.dispatcher.loop = loop

    if not config.BOT_TOKEN or not config.API_ID or not config.API_HASH:
        logger.error(
            "CRITICAL: API_ID, API_HASH, and BOT_TOKEN must be set in .env file!"
        )
        print("\n❌ Error: Missing credentials in .env file.")
        print("Please edit .env with your API_ID, API_HASH, and BOT_TOKEN.\n")
        return

    # Clear any conflicting webhooks from Telegram
    try:
        import urllib.request
        webhook_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        with urllib.request.urlopen(webhook_url, timeout=5) as resp:
            pass
        logger.info("Cleared any conflicting Telegram webhooks.")
    except Exception:
        pass

    # Start main Telegram Bot with retry for temporary Telegram server hiccups (RPC 500)
    for attempt in range(1, 6):
        try:
            await bot.start()
            break
        except Exception as e:
            if attempt == 5:
                logger.error(f"Failed to start bot after 5 attempts: {e}")
                raise
            logger.warning(f"Telegram connection attempt {attempt} failed ({e}). Retrying in 4 seconds...")
            await asyncio.sleep(4)

    bot_info = await bot.get_me()
    total_handlers = sum(len(h) for h in bot.dispatcher.groups.values())
    logger.info(f"✅ Bot started successfully as @{bot_info.username} (ID: {bot_info.id}) [{total_handlers} handlers active]")

    # Start Assistant & PyTgCalls if configured
    if client.assistant is not None:
        try:
            for attempt in range(1, 6):
                try:
                    await client.assistant.start()
                    break
                except Exception as e:
                    if attempt == 5:
                        raise
                    logger.warning(f"Assistant connection attempt {attempt} failed ({e}). Retrying in 4 seconds...")
                    await asyncio.sleep(4)
            assistant_info = await client.assistant.get_me()
            logger.info(
                f"✅ Assistant Userbot started as @{assistant_info.username or assistant_info.first_name} (ID: {assistant_info.id})"
            )
            # Ensure PyTgCalls is initialized on the active loop
            if client.call_py is None and config.SESSION_STRING:
                try:
                    from pytgcalls import PyTgCalls
                    client.call_py = PyTgCalls(client.assistant)
                    logger.info("✅ Voice Call assistant (PyTgCalls) initialized on running loop.")
                except Exception as ex:
                    logger.error(f"❌ Failed to initialize PyTgCalls on running loop: {ex}", exc_info=True)

            if client.call_py is not None:
                client.call_py.loop = loop
                await client.call_py.start()
                from bot.services.player import register_call_handlers
                register_call_handlers()
                logger.info("✅ PyTgCalls voice engine started.")
            else:
                logger.warning("⚠️ call_py is None. Voice chat streaming is not available.")
        except Exception as e:
            logger.error(f"❌ Failed to start assistant userbot / PyTgCalls: {e}", exc_info=True)
            logger.warning("Bot will continue running without voice call streaming.")
    else:
        logger.info("ℹ️ Running in basic mode (Admin + Welcome + Direct Audio). Add SESSION_STRING in .env for VC music.")

    logger.info(f"✨ {config.BOT_NAME} is fully operational and listening for events...")

    # Start web health check server for Cloud Hosting (Koyeb / Render)
    port = int(os.environ.get("PORT", "8080"))
    try:
        from aiohttp import web
        async def health_handler(request):
            return web.Response(text=f"✨ {config.BOT_NAME} is alive and streaming!")

        app = web.Application()
        app.router.add_get("/", health_handler)
        app.router.add_get("/health", health_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"🌐 Cloud health server listening on port {port}")
    except Exception as e:
        logger.warning(f"Could not start cloud health server: {e}")

    await idle()

    # Graceful shutdown
    logger.info("Shutting down bot services...")
    if call_py is not None:
        try:
            # Leave or stop call client
            pass
        except Exception:
            pass
    if assistant is not None:
        await assistant.stop()
    await bot.stop()
    logger.info("Bot stopped successfully. Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process terminated by user.")
