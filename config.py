"""
Configuration management for Crypto Assistant
"""
import os
from dotenv import load_dotenv

# Load environment variables
# Load environment variables
basedir = os.path.abspath(os.path.dirname(__file__))
# Try loading from backend directory
load_dotenv(os.path.join(basedir, ".env"))
# Try loading from root directory (parent of backend)
load_dotenv(os.path.join(basedir, "..", ".env"))

class Config:
    """Application configuration"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    FREECRYPTO_API_KEY = os.getenv("FREECRYPTO_API_KEY")
    CRYPTONEWS_API_KEY = os.getenv("CRYPTONEWS_API_KEY")
    
    # Flask settings
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # Knowledge Base settings
    KB_FILE_PATH = os.path.join(os.path.dirname(__file__), "knowledge", "coins.json")
    FRESHNESS_TTL_MINUTES = int(os.getenv("FRESHNESS_TTL_MINUTES", "5"))
    
    # Memory settings
    MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
    
    # FreeCryptoAPI settings
    FREECRYPTO_BASE_URL = "https://api.freecryptoapi.com/v1"
    
    # Known coins (symbol -> name mapping)
    KNOWN_COINS = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "SOL": "Solana",
        "ADA": "Cardano",
        "XRP": "Ripple",
        "DOT": "Polkadot",
        "MATIC": "Polygon",
        "AVAX": "Avalanche",
        "LINK": "Chainlink",
        "UNI": "Uniswap"
    }
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not set")
        
        if not cls.FREECRYPTO_API_KEY:
            errors.append("FREECRYPTO_API_KEY not set")
            
        if not cls.CRYPTONEWS_API_KEY:
            errors.append("CRYPTONEWS_API_KEY not set")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
