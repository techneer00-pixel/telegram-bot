from typing import Dict, List, Any, Optional

class QueueManager:
    def __init__(self):
        # chat_id -> list of track dictionaries
        self._queues: Dict[int, List[Dict[str, Any]]] = {}

    def add(self, chat_id: int, track: Dict[str, Any]) -> int:
        """Adds a track to the chat queue. Returns the position in queue."""
        if chat_id not in self._queues:
            self._queues[chat_id] = []
        self._queues[chat_id].append(track)
        return len(self._queues[chat_id])

    def get_current(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Returns the currently playing track (first item) without removing it."""
        if chat_id in self._queues and self._queues[chat_id]:
            return self._queues[chat_id][0]
        return None

    def pop(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Removes the finished/skipped track and returns the next track if any."""
        if chat_id in self._queues and self._queues[chat_id]:
            self._queues[chat_id].pop(0)
            if self._queues[chat_id]:
                return self._queues[chat_id][0]
        return None

    def clear(self, chat_id: int) -> None:
        """Clears the entire queue for a chat."""
        if chat_id in self._queues:
            self._queues[chat_id] = []

    def is_empty(self, chat_id: int) -> bool:
        """Checks if there are no songs playing or queued."""
        return chat_id not in self._queues or len(self._queues[chat_id]) == 0

    def get_queue(self, chat_id: int) -> List[Dict[str, Any]]:
        """Returns the list of tracks currently queued."""
        return self._queues.get(chat_id, [])

# Global singleton queue manager
music_queue = QueueManager()
