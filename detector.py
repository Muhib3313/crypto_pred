"""
Entity and Intent Detection
Detects crypto entities and classifies user intents
"""
import re
from typing import Tuple, Optional, Dict


class EntityDetector:
    """Detects cryptocurrency entities in user queries"""
    
    def __init__(self, known_coins: dict, memory):
        """
        Initialize entity detector
        
        Args:
            known_coins: Dict mapping symbols to coin names
            memory: ConversationMemory instance
        """
        self.known_coins = known_coins
        self.memory = memory
    
    
    def detect_entity(self, query: str) -> Tuple[Optional[str], float]:
        """
        Detect entity with memory-based pronoun resolution (Backwards compatibility)
        Returns primary/first entity.
        """
        entities = self.detect_entities(query)
        if entities:
            return entities[0]
        return None, 0.0

    def detect_entities(self, query: str) -> list[Tuple[str, float]]:
        """
        Detect ALL unique entities in query
        
        Returns:
            List of (symbol, confidence)
        """
        entities = []
        found_symbols = set()
        
        # 1. Check for explicit symbols
        for symbol in self.known_coins.keys():
            if symbol in query.upper():
                if symbol not in found_symbols:
                    entities.append((symbol, 1.0))
                    found_symbols.add(symbol)
        
        # 2. Check for coin names
        query_lower = query.lower()
        for symbol, name in self.known_coins.items():
            if name.lower() in query_lower:
                if symbol not in found_symbols:
                    entities.append((symbol, 0.95))
                    found_symbols.add(symbol)
        
        # 3. Check for pronouns (only if no entities found or single entity context)
        # Note: Handling pronouns in multi-entity context is complex, so we limit it.
        if not entities:
            resolved_entity = self.memory.resolve_pronoun(query)
            if resolved_entity:
                entities.append((resolved_entity, 0.85))
                
        return entities
        
        # 4. No entity detected
        return None, 0.0


class IntentClassifier:
    """Classifies user intent for crypto queries"""
    
    # Disallowed intent patterns
    REJECTION_PATTERNS = [
        # Predictions
        r'\b(will|gonna|going to|predict|forecast|future|tomorrow|next week|next month|next year)\b',
        # Investment advice
        r'\b(should i|recommend|advice|advise|invest|buy|sell|hold|worth buying|good investment)\b',
        # Hypotheticals
        r'\b(if|what if|suppose|imagine|hypothetical)\b',
        # Price targets
        r'\b(reach|hit|get to|moon|crash|dump|pump)\b.*\$\d+',
    ]
    
    def classify_intent(self, query: str, has_entity: bool) -> Tuple[str, float]:
        """
        Classify user intent
        
        Args:
            query: User query
            has_entity: Whether an entity was detected
            
        Returns:
            (intent, confidence)
        """
        query_lower = query.lower()
        
        # 1. Check for rejected intents FIRST
        for pattern in self.REJECTION_PATTERNS:
            if re.search(pattern, query_lower):
                return "REJECTED", 1.0
        
        # 2. Classify allowed intents
        
        # Helper for keywords
             
        # Comparison intent
        if self._matches_keywords(query_lower, ['compare', 'vs', 'versus', 'difference', 'better', 'against', 'or']):
            return "comparison", 0.95

        # Price history intent
        if self._matches_keywords(query_lower, ['yesterday', 'last week', 'last month', 'ago', 'history', 'historical', 'was the price', 'price was', 'price on']):
            return "price_history", 0.95
            
        # Price intent
        if self._matches_keywords(query_lower, ['price', 'cost', 'how much', 'worth', 'value', 'trading at']):
            return "price", 0.95
        
        # Market cap intent
        if self._matches_keywords(query_lower, ['market cap', 'marketcap', 'market capitalization', 'mcap', 'market value']):
            return "market_cap", 0.95
        
        # News intent
        if self._matches_keywords(query_lower, ['news', 'headline', 'headlines', 'latest', 'recent', 'update', 'happening']):
            return "news", 0.95
        
        # Metadata intent
        if self._matches_keywords(query_lower, ['what is', 'what\'s', 'tell me about', 'explain', 'describe', 'info', 'information', 'consensus', 'launch', 'creator', 'created']):
            return "metadata", 0.90
        
        # Follow-up intent
        if self._is_follow_up(query_lower) and has_entity:
            return "follow_up", 0.80
        
        # Unknown intent
        return "unknown", 0.0
    
    def _matches_keywords(self, query: str, keywords: list) -> bool:
        """Check if query contains any of the keywords"""
        return any(keyword in query for keyword in keywords)
    
    def _is_follow_up(self, query: str) -> bool:
        """Check if query is a follow-up question"""
        follow_up_indicators = [
            'it', 'its', 'this', 'that', 'what about', 'how about', 'and'
        ]
        return any(indicator in query for indicator in follow_up_indicators)


class CryptoQueryDetector:
    """Combined entity and intent detection system"""
    
    def __init__(self, known_coins: dict, memory):
        self.entity_detector = EntityDetector(known_coins, memory)
        self.intent_classifier = IntentClassifier()
    
    def detect(self, query: str) -> Dict:
        """
        Detect entity and intent from query
        
        Returns:
            {
                "detected_entity": str or None,
                "detected_intent": str,
                "entity_confidence": float,
                "intent_confidence": float,
                "overall_confidence": float,
                "should_reject": bool
            }
        """
    def detect(self, query: str) -> Dict:
        """
        Detect entity and intent from query
        
        Returns:
            {
                "detected_entity": str or None,
                "detected_entities": List[str],
                "detected_intent": str,
                "entity_confidence": float,
                "intent_confidence": float,
                "overall_confidence": float,
                "should_reject": bool
            }
        """
        # Detect entities
        entities = self.entity_detector.detect_entities(query)
        primary_entity = entities[0][0] if entities else None
        entity_conf = entities[0][1] if entities else 0.0
        
        # Classify intent
        intent, intent_conf = self.intent_classifier.classify_intent(query, has_entity=(len(entities) > 0))
        
        # Calculate overall confidence
        overall_conf = min(entity_conf, intent_conf) if entities else intent_conf
        
        # Determine if should reject
        should_reject = (intent == "REJECTED")
        
        return {
            "detected_entity": primary_entity,
            "detected_entities": [e[0] for e in entities],
            "detected_intent": intent,
            "entity_confidence": entity_conf,
            "intent_confidence": intent_conf,
            "overall_confidence": overall_conf,
            "should_reject": should_reject
        }
