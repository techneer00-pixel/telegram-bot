import logging
from pyrogram import Client
import pyrogram.utils
import pyrogram.errors
import config

# Fix Pyrogram bug for modern Telegram Channel/Supergroup IDs (e.g. -1003...)
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999999

# Fix Pyrogram hardcoded DC 2 issue for modern bots registered on DC 5 (Asia)
from pyrogram.session import Auth, Session
_orig_load_session = Client.load_session

async def _patched_load_session(self):
    await self.storage.open()
    session_empty = any([
        await self.storage.test_mode() is None,
        await self.storage.auth_key() is None,
        await self.storage.user_id() is None,
        await self.storage.is_bot() is None
    ])
    if session_empty:
        await self.storage.api_id(self.api_id)
        # Modern bot accounts default to DC 5
        await self.storage.dc_id(5)
        await self.storage.date(0)
        await self.storage.test_mode(self.test_mode)
        await self.storage.auth_key(
            await Auth(self, await self.storage.dc_id(), await self.storage.test_mode()).create()
        )
    self.session = Session(
        self, await self.storage.dc_id(),
        await self.storage.auth_key(), await self.storage.test_mode()
    )
    await self.session.start()

Client.load_session = _patched_load_session

# Fix PyTgCalls compatibility with Pyrogram v2
if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    class GroupcallForbidden(pyrogram.errors.RPCError):
        pass
    pyrogram.errors.GroupcallForbidden = GroupcallForbidden

if not hasattr(pyrogram.errors, "GroupcallInvalid"):
    pyrogram.errors.GroupcallInvalid = getattr(pyrogram.errors, "GroupCallInvalid", pyrogram.errors.RPCError)

# Inject missing Telegram Layer conference call stubs for PyTgCalls 3.0 compatibility
import pyrogram.raw.functions.phone as raw_phone
import pyrogram.raw.types as raw_types

for _stub in (
    "CreateConferenceCall",
    "GetGroupCallChainBlocks",
    "InviteConferenceCallParticipant",
    "SendConferenceCallBroadcast",
):
    if not hasattr(raw_phone, _stub):
        setattr(raw_phone, _stub, type(_stub, (), {}))

# Patch JoinGroupCall to tolerate PyTgCalls 3.0 passing block / public_key on Layer 158
if hasattr(raw_phone, "JoinGroupCall"):
    _orig_join_init = raw_phone.JoinGroupCall.__init__
    def _safe_join_init(self, *args, **kwargs):
        kwargs.pop("block", None)
        kwargs.pop("public_key", None)
        return _orig_join_init(self, *args, **kwargs)
    raw_phone.JoinGroupCall.__init__ = _safe_join_init

for _stub in (
    "MessageActionConferenceCall",
    "PhoneCallDiscardReasonMigrateConferenceCall",
    "UpdateGroupCallChainBlocks",
    "InputGroupCallInviteMessage",
    "InputGroupCallSlug",
):
    if not hasattr(raw_types, _stub):
        setattr(raw_types, _stub, type(_stub, (), {}))

logger = logging.getLogger("HarmoniX")

# 1. Main Telegram Bot Client
bot = Client(
    name="HarmoniXBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    in_memory=True,
)

# 2. Assistant Userbot Client (Required for streaming directly into Group Voice Chats)
assistant: Client | None = None
call_py = None

if config.SESSION_STRING:
    assistant = Client(
        name="HarmoniXAssistant",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=config.SESSION_STRING,
        in_memory=True,
    )
    try:
        from pytgcalls import PyTgCalls
        call_py = PyTgCalls(assistant)
        logger.info("Voice Call assistant (PyTgCalls) initialized.")
        print("✅ Voice Call assistant (PyTgCalls) initialized.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PyTgCalls: {e}", exc_info=True)
        print(f"❌ Failed to initialize PyTgCalls at import: {e}")
        call_py = None
else:
    logger.warning("No SESSION_STRING provided. Voice chat streaming will be disabled until configured.")
