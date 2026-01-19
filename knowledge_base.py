"""
Knowledge Base Manager for Crypto Assistant
Handles KB operations including metadata queries and price caching
"""
import json
import os
from typing import Dict, Optional, List
from datetime import datetime


class KnowledgeBaseManager:
    """Manages Knowledge Base operations"""
    
    def __init__(self, kb_file_path: str):
        """
        Initialize KB manager
        
        Args:
            kb_file_path: Path to JSON KB file
        """
        self.kb_path = kb_file_path
        self.kb_data = self._load_kb()
    
    def _load_kb(self) -> Dict:
        """Load KB from file"""
        try:
            if os.path.exists(self.kb_path):
                with open(self.kb_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create empty KB if doesn't exist
                return {"metadata_version": "1.0", "coins": []}
        except Exception as e:
            print(f"Error loading KB: {e}")
            return {"metadata_version": "1.0", "coins": []}
    
    def _save_kb(self):
        """Save KB to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
            
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(self.kb_data, f, indent=2, ensure_ascii=False)
            
            # Update last_updated timestamp
            self.kb_data["last_updated"] = datetime.now().isoformat()
        except Exception as e:
            print(f"Error saving KB: {e}")
    
    def get_coin_metadata(self, symbol: str) -> Optional[Dict]:
        """
        Get static metadata for a coin
        
        Args:
            symbol: Coin symbol (e.g., "BTC")
            
        Returns:
            Metadata dict or None
        """
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                return {
                    "coin": coin.get("coin"),
                    "symbol": coin.get("symbol"),
                    "description": coin.get("description"),
                    "launch_year": coin.get("launch_year"),
                    "consensus": coin.get("consensus"),
                    "chain_type": coin.get("chain_type"),
                    "creator": coin.get("creator"),
                    "max_supply": coin.get("max_supply")
                }
        return None
    
    def get_cached_price_data(self, symbol: str) -> Optional[Dict]:
        """
        Get cached price data for a coin
        
        Args:
            symbol: Coin symbol
            
        Returns:
            Price data dict or None
        """
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                # Only return if price data exists
                if coin.get("last_price") is not None:
                    return {
                        "symbol": coin.get("symbol"),
                        "name": coin.get("coin"),
                        "last_price": coin.get("last_price"),
                        "market_cap": coin.get("market_cap"),
                        "price_timestamp": coin.get("price_timestamp"),
                        "change_24h": coin.get("change_24h", 0),
                        "volume_24h": coin.get("volume_24h", 0),
                        "rank": coin.get("rank")
                    }
        return None
    
    def update_price_data(self, symbol: str, price_data: Dict):
        """
        Update cached price data from API response
        
        Args:
            symbol: Coin symbol
            price_data: Price data from API
        """
        # Find existing coin
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                # Update price fields
                coin["last_price"] = price_data.get("price")
                coin["market_cap"] = price_data.get("market_cap")
                coin["price_timestamp"] = datetime.now().isoformat()
                coin["change_24h"] = price_data.get("change_24h", 0)
                coin["volume_24h"] = price_data.get("volume_24h", 0)
                coin["rank"] = price_data.get("rank")
                self._save_kb()
                return
        
        # Coin not in KB, add it (with minimal metadata)
        new_coin = {
            "coin": price_data.get("name", "Unknown"),
            "symbol": symbol,
            "description": None,
            "launch_year": None,
            "consensus": None,
            "chain_type": None,
            "creator": None,
            "max_supply": None,
            "last_price": price_data.get("price"),
            "market_cap": price_data.get("market_cap"),
            "price_timestamp": datetime.now().isoformat(),
            "change_24h": price_data.get("change_24h", 0),
            "volume_24h": price_data.get("volume_24h", 0),
            "rank": price_data.get("rank")
        }
        self.kb_data["coins"].append(new_coin)
        self._save_kb()
    
    def get_cached_news(self, symbol: str) -> Optional[Dict]:
        """
        Get cached news for a coin
        
        Args:
            symbol: Coin symbol
            
        Returns:
            News dict or None
        """
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                if coin.get("news"):
                    return coin["news"]
        return None
    
    def update_news_data(self, symbol: str, news_items: List[Dict]):
        """
        Update cached news for a coin
        
        Args:
            symbol: Coin symbol
            news_items: List of news items
        """
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                coin["news"] = {
                    "items": news_items,
                    "timestamp": datetime.now().isoformat()
                }
                self._save_kb()
                return
    
    
    def get_price_history(self, symbol: str, date: str) -> Optional[Dict]:
        """
        Get price history for a date
        
        Args:
            symbol: Coin symbol
            date: Date string (YYYY-MM-DD)
        """
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                for entry in coin.get("history", []):
                    if entry.get("date") == date:
                        return entry
        return None

    def add_price_history(self, symbol: str, date: str, price: float, market_cap: float):
        """Add price history entry"""
        for coin in self.kb_data.get("coins", []):
            if coin.get("symbol") == symbol:
                if "history" not in coin:
                    coin["history"] = []
                
                # Check if exists to update or append
                for entry in coin["history"]:
                    if entry.get("date") == date:
                        entry["price"] = price
                        entry["market_cap"] = market_cap
                        self._save_kb()
                        return
                
                # Append new
                coin["history"].append({
                    "date": date,
                    "price": price,
                    "market_cap": market_cap
                })
                self._save_kb()
                return

    def get_all_coins(self) -> List[str]:
        """Get list of all coin symbols in KB"""
        return [coin.get("symbol") for coin in self.kb_data.get("coins", [])]
