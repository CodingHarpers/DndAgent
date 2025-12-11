from typing import Dict, Optional
import uuid
from app.storytelling.main import ArcanaSystem

class SessionManager:
    _instance = None
    _sessions: Dict[str, ArcanaSystem] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = ArcanaSystem(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[ArcanaSystem]:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_manager = SessionManager()
