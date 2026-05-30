class MemoryService:
    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def get_history(self, session_id: str) -> list[dict]:
        return self._store.get(session_id, [])

    def append_turn(self, session_id: str, user_msg: str, agent_msg: str) -> None:
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append({"role": "user", "content": user_msg})
        self._store[session_id].append({"role": "assistant", "content": agent_msg})