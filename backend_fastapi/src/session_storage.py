import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.models import SessionData

# PUBLIC_INTERFACE
class SessionStorage:
    """In-memory session storage for managing authentication tokens."""
    
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}
    
    # PUBLIC_INTERFACE
    def create_session(self, session_data: SessionData) -> str:
        """
        Create a new session and return session token.
        
        Args:
            session_data: Session data to store
            
        Returns:
            str: Generated session token
        """
        session_token = str(uuid.uuid4())
        self._sessions[session_token] = session_data
        return session_token
    
    # PUBLIC_INTERFACE
    def get_session(self, session_token: str) -> Optional[SessionData]:
        """
        Retrieve session data by token.
        
        Args:
            session_token: Session token to lookup
            
        Returns:
            SessionData or None if not found or expired
        """
        if session_token not in self._sessions:
            return None
        
        session_data = self._sessions[session_token]
        
        # Check if session has expired
        if datetime.utcnow() > session_data.expires_at:
            self.delete_session(session_token)
            return None
        
        return session_data
    
    # PUBLIC_INTERFACE
    def delete_session(self, session_token: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_token: Session token to delete
            
        Returns:
            bool: True if session was deleted, False if not found
        """
        if session_token in self._sessions:
            del self._sessions[session_token]
            return True
        return False
    
    # PUBLIC_INTERFACE
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, session_data in self._sessions.items():
            if current_time > session_data.expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self._sessions[token]
        
        return len(expired_tokens)
    
    # PUBLIC_INTERFACE
    def get_session_count(self) -> int:
        """Get the current number of active sessions."""
        return len(self._sessions)

# Global session storage instance
session_storage = SessionStorage()
