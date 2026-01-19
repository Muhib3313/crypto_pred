"""
Knowledge-First Reasoning Pipeline
Main processing pipeline with hallucination prevention
"""
from typing import Dict, Optional
from datetime import datetime


class KnowledgeFirstPipeline:
    """Knowledge-first reasoning pipeline with guards"""
    
    INSUFFICIENT_DATA_MESSAGE = "INSUFFICIENT DATA – Not found in Knowledge Base or API"
    
    def __init__(self, kb_manager, api_tool, news_tool, detector, memory, llm_orchestrator):
        """
        Initialize pipeline
        
        Args:
            kb_manager: KnowledgeBaseManager instance
            api_tool: FreeCryptoAPITool instance
            news_tool: CryptoNewsTool instance
            detector: CryptoQueryDetector instance
            memory: ConversationMemory instance
            llm_orchestrator: LLMOrchestrator instance
        """
        self.kb = kb_manager
        self.api = api_tool
        self.news = news_tool
        self.detector = detector
        self.memory = memory
        self.llm = llm_orchestrator
    
    def process_query(self, query: str) -> Dict:
        """
        Process user query through knowledge-first pipeline
        
        Returns:
            {
                "response": str,
                "source": str or None,
                "confidence": float,
                "entity": str or None,
                "intent": str
            }
        """
        # Step 1: Detect entity and intent
        detection = self.detector.detect(query)
        
        # Step 2: Check if intent should be rejected
        if detection["should_reject"]:
            return self._reject_response(detection)
        
        # Step 3: Check if detection confidence is too low
        if detection["overall_confidence"] < 0.5:
            return self._clarification_response(detection)
        
        entity = detection["detected_entity"]
        entities = detection.get("detected_entities", [])
        intent = detection["detected_intent"]
        
        # Step 4: Route based on intent
        if intent == "metadata":
            return self._handle_metadata(entity, detection)
        elif intent in ["price", "market_cap"]:
            return self._handle_price_data(entity, intent, detection)
        elif intent == "news":
            return self._handle_news(entity, detection)
        elif intent == "price_history":
            return self._handle_history(entity, detection, query)
        elif intent == "comparison":
            return self._handle_comparison(entities, detection)
        else:
            return self._clarification_response(detection)
    
    def _handle_metadata(self, entity: str, detection: Dict) -> Dict:
        """Handle metadata queries (static data from KB)"""
        # Search KB for metadata
        kb_data = self.kb.get_coin_metadata(entity)
        
        if kb_data:
            # Format response using LLM
            response_text = self.llm.format_metadata_response(kb_data)
            
            return {
                "response": response_text,
                "source": "Knowledge Base",
                "confidence": 1.0,
                "entity": entity,
                "intent": "metadata"
            }
        else:
            # No metadata in KB
            return {
                "response": self.INSUFFICIENT_DATA_MESSAGE,
                "source": None,
                "confidence": 0.0,
                "entity": entity,
                "intent": "metadata"
            }
    
    def _handle_price_data(self, entity: str, intent: str, detection: Dict) -> Dict:
        """Handle price/market cap queries with API tool"""
        # Use API tool (which checks KB cache first)
        result = self.api.get_crypto_data(entity)
        
        if result["success"]:
            # Format response using LLM
            response_text = self.llm.format_price_response(result["data"], intent)
            
            return {
                "response": response_text,
                "source": result["source"],
                "confidence": result["confidence"],
                "entity": entity,
                "intent": intent
            }
        else:
            # API failed
            return {
                "response": self.INSUFFICIENT_DATA_MESSAGE,
                "source": None,
                "confidence": 0.0,
                "entity": entity,
                "intent": intent
            }
    def _handle_news(self, entity: str, detection: Dict) -> Dict:
        """Handle news queries"""
        # Use News tool
        result = self.news.get_news(entity)
        
        if result["success"]:
            # Format response using LLM
            response_text = self.llm.format_news_response(result["data"], entity)
            
            return {
                "response": response_text,
                "source": result["source"],
                "confidence": result["confidence"],
                "entity": entity,
                "intent": "news"
            }
        else:
            # API failed
            return {
                "response": self.INSUFFICIENT_DATA_MESSAGE,
                "source": None,
                "confidence": 0.0,
                "entity": entity,
                "intent": "news"
            }

    def _handle_history(self, entity: str, detection: Dict, query: str) -> Dict:
        """Handle historical price queries"""
        # ... (keep existing code)
        if result["success"]:
            # Format response
            response_text = self.llm.format_history_response(result["data"])
            
            return {
                "response": response_text,
                "source": result["source"],
                "confidence": result["confidence"],
                "entity": entity,
                "intent": "price_history"
            }
        else:
            return {
                "response": f"INSUFFICIENT DATA – I don't have price data for {entity} on {date}.",
                "source": None,
                "confidence": 0.0,
                "entity": entity,
                "intent": "price_history"
            }

    def _handle_comparison(self, entities: list, detection: Dict) -> Dict:
        """Handle comparison queries"""
        if not entities or len(entities) < 2:
            return {
                "response": "Please specify at least two cryptocurrencies to compare (e.g., 'Compare Bitcoin and Ethereum').",
                "source": None,
                "confidence": 0.0,
                "entity": None,
                "intent": "comparison"
            }
            
        results = []
        sources = set()
        total_confidence = 0
        
        for entity in entities:
            # Get current data (price/mcap)
            res = self.api.get_crypto_data(entity)
            if res["success"]:
                results.append(res["data"])
                if res["source"]:
                    sources.add(res["source"])
                total_confidence += res["confidence"]
        
        if not results:
             return {
                "response": self.INSUFFICIENT_DATA_MESSAGE,
                "source": None,
                "confidence": 0.0,
                "entity": ", ".join(entities),
                "intent": "comparison"
             }

        # Format comparison
        response_text = self.llm.format_comparison_response(results)
        
        avg_confidence = total_confidence / len(results) if results else 0.0
        source_str = ", ".join(sources) if sources else "Knowledge Base"
        
        return {
            "response": response_text,
            "source": source_str,
            "confidence": avg_confidence,
            "entity": ", ".join(entities),
            "intent": "comparison"
        }

    def _reject_response(self, detection: Dict) -> Dict:
        """Return rejection response for disallowed intents"""
        return {
            "response": self.INSUFFICIENT_DATA_MESSAGE,
            "source": None,
            "confidence": 0.0,
            "entity": detection["detected_entity"],
            "intent": detection["detected_intent"]
        }
    
    def _clarification_response(self, detection: Dict) -> Dict:
        """Return clarification request"""
        return {
            "response": "I can help with cryptocurrency information, prices, and market data. Could you please clarify what you'd like to know?",
            "source": None,
            "confidence": detection["overall_confidence"],
            "entity": detection["detected_entity"],
            "intent": detection["detected_intent"]
        }
    
    def format_final_response(self, result: Dict) -> str:
        """Format final response with source tag and confidence"""
        response = result["response"]
        source = result["source"]
        confidence = result["confidence"]
        
        if source:
            source_tag = f"\n\n📊 Source: {source}\n🎯 Confidence: {confidence:.1f}"
        else:
            source_tag = ""
        
        return f"{response}{source_tag}"
