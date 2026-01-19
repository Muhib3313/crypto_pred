"""
Short-term conversation memory system
Tracks last 8-10 turns and resolves pronouns
"""
from typing import List, Dict, Optional
from collections import deque
from datetime import datetime


class ConversationMemory:
    """Manages short-term conversation memory"""
    
    def __init__(self, max_turns: int = 10, known_coins: dict = None):
        """
        Initialize conversation memory
        
        Args:
            max_turns: Maximum number of turns to remember
            known_coins: Dict mapping symbols to coin names
        """
        self.max_turns = max_turns
        self.known_coins = known_coins or {}
        self.history = deque(maxlen=max_turns)
        self.last_entity = None
        self.last_entity_timestamp = None
    
    def add_turn(self, role: str, content: str, entity: Optional[str] = None):
        """
        Add a turn to conversation history
        
        Args:
            role: "user" or "assistant"
            content: Message content
            entity: Detected entity (if any)
        """
        turn = {
            "role": role,
            "content": content,
            "entity": entity,
            "timestamp": datetime.now().isoformat()
        }
        
        self.history.append(turn)
        
        # Update last entity if present
        if entity:
            self.last_entity = entity
            self.last_entity_timestamp = turn["timestamp"]
    
    def get_history(self, num_turns: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history
        
        Args:
            num_turns: Number of recent turns to get
            
        Returns:
            List of turns in chronological order
        """
        if num_turns is None:
            return list(self.history)
        else:
            return list(self.history)[-num_turns:]
    
    def get_last_entity(self) -> Optional[str]:
        """Get the last mentioned crypto entity"""
        return self.last_entity
    
    def resolve_pronoun(self, query: str) -> Optional[str]:
        """
        Resolve pronoun to entity by checking conversation history
        
        Args:
            query: User query containing pronoun
            
        Returns:
            Resolved entity symbol or None
        """
        query_lower = query.lower()
        
        # Check if query contains pronoun
        pronouns = ['it', 'its', 'this', 'that', 'the coin', 'the token', 'same']
        has_pronoun = any(pronoun in query_lower for pronoun in pronouns)
        
        if not has_pronoun:
            return None
        
        # Return last entity
        return self.last_entity
    
    def extract_entity_from_turn(self, content: str) -> Optional[str]:
        """Extract crypto entity from turn content"""
        content_upper = content.upper()
        
        # Check for symbols
        for symbol in self.known_coins.keys():
            if symbol in content_upper:
                return symbol
        
        # Check for coin names
        content_lower = content.lower()
        for symbol, name in self.known_coins.items():
            if name.lower() in content_lower:
                return symbol
        
        return None
    
    def clear_history(self):
        """Clear conversation history"""
        self.history.clear()
        self.last_entity = None
        self.last_entity_timestamp = None


class SessionManager:
    """Manages multiple conversation sessions"""
    
    def __init__(self, known_coins: dict):
        self.known_coins = known_coins
        self.sessions = {}  # session_id -> ConversationMemory
    
    def get_memory(self, session_id: str) -> ConversationMemory:
        """Get or create memory for session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(
                max_turns=10,
                known_coins=self.known_coins
            )
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            self.sessions[session_id].clear_history()
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
