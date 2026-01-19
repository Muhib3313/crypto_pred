"""
Flask REST API for Crypto Assistant
Main application entry point
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

from config import Config
from knowledge_base import KnowledgeBaseManager
from crypto_tools import FreeCryptoAPITool, CryptoNewsTool
from memory import SessionManager
from detector import CryptoQueryDetector
from llm_orchestrator import LLMOrchestrator
from pipeline import KnowledgeFirstPipeline

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Validate configuration
try:
    Config.validate()
    print("✓ Configuration validated")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
    print("Please set API keys in .env file")
    exit(1)

# Initialize components
print("Initializing components...")
kb_manager = KnowledgeBaseManager(Config.KB_FILE_PATH)
session_manager = SessionManager(Config.KNOWN_COINS)
llm_orchestrator = LLMOrchestrator(Config.OPENAI_API_KEY)

print(f"✓ Knowledge Base loaded ({len(kb_manager.get_all_coins())} coins)")
print("✓ All components initialized")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "coins_in_kb": len(kb_manager.get_all_coins())
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({
                "error": "Message is required"
            }), 400
        
        # Get or create session memory
        memory = session_manager.get_memory(session_id)
        
        # Initialize session-specific components
        api_tool = FreeCryptoAPITool(
            api_key=Config.FREECRYPTO_API_KEY,
            kb_manager=kb_manager,
            freshness_ttl_minutes=Config.FRESHNESS_TTL_MINUTES
        )
        
        news_tool = CryptoNewsTool(
            api_key=Config.CRYPTONEWS_API_KEY,
            kb_manager=kb_manager
        )
        
        detector = CryptoQueryDetector(Config.KNOWN_COINS, memory)
        
        pipeline = KnowledgeFirstPipeline(
            kb_manager=kb_manager,
            api_tool=api_tool,
            news_tool=news_tool,
            detector=detector,
            memory=memory,
            llm_orchestrator=llm_orchestrator
        )
        
        # Add user message to memory
        detection = detector.detect(message)
        memory.add_turn("user", message, detection["detected_entity"])
        
        # Process query
        result = pipeline.process_query(message)
        
        # Format final response
        formatted_response = pipeline.format_final_response(result)
        
        # Add assistant response to memory
        memory.add_turn("assistant", formatted_response, result["entity"])
        
        return jsonify({
            "response": formatted_response,
            "source": result["source"],
            "confidence": result["confidence"],
            "entity": result["entity"],
            "intent": result["intent"],
            "session_id": session_id
        })
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation history"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        session_manager.clear_session(session_id)
        
        return jsonify({
            "message": "Conversation reset successfully",
            "session_id": session_id
        })
    
    except Exception as e:
        return jsonify({
            "error": "Failed to reset conversation",
            "message": str(e)
        }), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get active sessions (debugging)"""
    return jsonify({
        "active_sessions": list(session_manager.sessions.keys()),
        "count": len(session_manager.sessions)
    })


if __name__ == '__main__':
    print(f"\n{'='*50}")
    print("🚀 Crypto Assistant API Server")
    print(f"{'='*50}")
    print(f"Server: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print(f"Health: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}/api/health")
    print(f"{'='*50}\n")
    
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
