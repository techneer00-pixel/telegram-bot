import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger("HarmoniX.Database")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "served_chats.json"

class Storage:
    def __init__(self):
        self.served_chats: Set[int] = set()
        self.served_users: Set[int] = set()
        self._load()

    def _load(self):
        if DB_FILE.exists():
            try:
                data = json.loads(DB_FILE.read_text(encoding="utf-8"))
                self.served_chats = set(data.get("chats", []))
                self.served_users = set(data.get("users", []))
                logger.info(f"Loaded {len(self.served_chats)} served chats and {len(self.served_users)} served users.")
            except Exception as e:
                logger.warning(f"Failed to load database: {e}")

    def _save(self):
        try:
            payload = {
                "chats": list(self.served_chats),
                "users": list(self.served_users),
            }
            DB_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save database: {e}")

    def add_chat(self, chat_id: int):
        if chat_id not in self.served_chats:
            self.served_chats.add(chat_id)
            self._save()

    def remove_chat(self, chat_id: int):
        if chat_id in self.served_chats:
            self.served_chats.discard(chat_id)
            self._save()

    def add_user(self, user_id: int):
        if user_id not in self.served_users:
            self.served_users.add(user_id)
            self._save()

    def get_chats(self) -> list[int]:
        return list(self.served_chats)

    def get_users(self) -> list[int]:
        return list(self.served_users)

db = Storage()
