# 🎵 HarmoniX — All-in-One Telegram Music & Group Management Bot

HarmoniX is a modern, modular, asynchronous Telegram bot built with **Pyrogram v2**, **PyTgCalls**, and **yt-dlp**. It streams high-quality music into Telegram Group Voice Chats, welcomes new members with interactive messages, and provides a full suite of group moderation tools.

---

## ✨ Features

### 🎶 1. Voice Chat Music Streaming
- **Voice Chat Playback:** Streams songs live into Telegram group voice chats.
- **Queue Management:** Smart queue system with auto-play for next songs.
- **Playback Controls:** `/play`, `/pause`, `/resume`, `/skip`, `/stop`, `/queue`.
- **Interactive Inline Buttons:** Control playback directly from chat messages.
- **Direct Song Downloader (`/song`):** Download and send MP3 files directly into the chat without needing voice chat.
- **Fast Search:** Search YouTube or stream directly from URLs via `yt-dlp`.

### 👋 2. Member Welcoming & Greetings
- **Customizable Welcome Messages:** Automatically greet new members with their name, mention, and total member count.
- **Interactive Buttons:** Welcome card with quick links to rules and help.
- **Admin Toggle:** Enable or disable greetings per group with `/welcome on` or `/welcome off`.

### 🛡 3. Full Group Moderation
- `/ban` & `/unban` — Ban or unban troublesome users.
- `/mute` & `/unmute` — Mute or unmute members from chatting.
- `/kick` — Kick members out of the group.
- `/pin` & `/unpin` — Pin or unpin group messages.
- `/purge` — Bulk delete messages up to the replied message.
- `/id` — Inspect Chat ID, User ID, and message IDs.

---

## 🏗 Why Is an Assistant Account Required for Music?

Telegram's official **Bot API does not support joining Voice Chats** (group calls). To stream live audio into a group call, a standard Telegram user account (an "Assistant") is used alongside the bot using Telegram's MTProto API via **PyTgCalls**.

- The **Bot** (`BOT_TOKEN`) receives user commands, manages the group, and sends messages.
- The **Assistant** (`SESSION_STRING`) connects to the voice chat and streams the audio.

*(Note: The bot can also run in standalone mode without an assistant for group management, welcome messages, and the `/song` file downloader!)*

---

## 📋 Prerequisites

1. **Python 3.10 or higher** installed.
2. **FFmpeg** installed and added to your system `PATH`:
   - **Windows:** Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) or install via `winget install Gyan.FFmpeg` / `choco install ffmpeg`.
   - **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install ffmpeg -y`
   - **macOS:** `brew install ffmpeg`
3. **Telegram Credentials:**
   - **API_ID & API_HASH:** From [my.telegram.org](https://my.telegram.org) under API Development Tools.
   - **BOT_TOKEN:** From [@BotFather](https://t.me/BotFather) on Telegram.

---

## 🚀 Quick Setup Guide

### Step 1: Clone / Navigate to Project Directory
```bash
cd tg_music_manager_bot
```

### Step 2: Install Dependencies
Create a virtual environment (recommended) and install requirements:
```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Generate Assistant String Session (For Voice Chat Music)
Run the included session generator:
```bash
python generate_session.py
```
1. Enter your `API_ID` and `API_HASH`.
2. Enter the phone number of the assistant account (or your secondary Telegram account).
3. Enter the login confirmation code sent by Telegram.
4. Copy the generated **Session String**.

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows:
copy .env.example .env

# Linux/macOS:
cp .env.example .env
```
Open `.env` and fill in your values:
```env
API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=1234567890:ABCdef...
SESSION_STRING=your_generated_assistant_string_here
OWNER_ID=your_telegram_user_id
BOT_NAME=HarmoniX
```

### Step 5: Start the Bot
```bash
python main.py
```

---

## 👥 Setting Up in Your Telegram Group

1. Create a Telegram Group (or open an existing one).
2. **Add your Bot** to the group and promote it as an **Administrator** with permissions to:
   - Delete messages
   - Ban users
   - Pin messages
3. **Add your Assistant account** to the group.
4. **Start a Voice Chat** in your group (Three dots menu at top right -> *Start Video Chat / Voice Chat*).
5. Send `/play Shape of You` or `/play <YouTube URL>`!

---

## 📖 Command Reference

| Command | Description |
| :--- | :--- |
| `/start` | Start the bot and see welcome buttons |
| `/help` | Detailed help menu |
| `/ping` | Check bot latency |
| `/play <query/url>` | Search & play audio in the group voice chat |
| `/song <query/url>` | Download & upload MP3 directly into chat |
| `/pause` | Pause voice chat audio |
| `/resume` | Resume voice chat audio |
| `/skip` | Skip currently playing track |
| `/stop` | Stop streaming and clear the queue |
| `/queue` | View the upcoming playlist |
| `/welcome <on/off>`| Toggle welcome greetings for new members |
| `/ban` | Ban replied user or username/ID |
| `/unban` | Unban replied user or username/ID |
| `/kick` | Kick replied user |
| `/mute` | Mute replied user |
| `/unmute` | Unmute replied user |
| `/pin` | Pin replied message |
| `/unpin` | Unpin replied message |
| `/purge` | Bulk delete messages down to current message |
| `/id` | Show IDs of user, chat, and replied message |

---

## 📁 Project Structure

```
tg_music_manager_bot/
├── .env.example              # Template configuration
├── config.py                 # Configuration loader & defaults
├── requirements.txt          # Python dependencies
├── generate_session.py       # Assistant string session generator
├── main.py                   # Bot startup & lifecycle script
├── bot/
│   ├── __init__.py
│   ├── client.py             # Pyrogram & PyTgCalls initialization
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── general.py        # /start, /help, /ping
│   │   ├── welcome.py        # New members welcome & toggle
│   │   ├── admin.py          # /ban, /kick, /mute, /purge, /pin
│   │   └── music.py          # /play, /pause, /skip, /stop, /queue
│   └── services/
│       ├── __init__.py
│       ├── downloader.py     # yt-dlp audio extractor
│       ├── queue_manager.py  # In-memory playlist manager
│       └── player.py         # PyTgCalls streaming controller
└── downloads/                # Cached audio files
```
