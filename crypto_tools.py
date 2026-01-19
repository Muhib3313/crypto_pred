"""
FreeCryptoAPI Tool Integration
Handles API calls with automatic KB caching
"""
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta


class FreeCryptoAPITool:
    """Tool for fetching crypto data from FreeCryptoAPI"""
    
    def __init__(self, api_key: str, kb_manager, freshness_ttl_minutes: int = 5):
        """
        Initialize API tool
        
        Args:
            api_key: FreeCryptoAPI key
            kb_manager: KnowledgeBaseManager instance
            freshness_ttl_minutes: TTL for cached data
        """
        self.api_key = api_key
        self.base_url = "https://api.freecryptoapi.com/v1"
        self.kb = kb_manager
        self.freshness_ttl = timedelta(minutes=freshness_ttl_minutes)
    
    def get_crypto_data(self, symbol: str, force_refresh: bool = False) -> Dict:
        """
        Fetch current price and market cap for a cryptocurrency
        
        Args:
            symbol: Coin symbol (e.g., "BTC", "ETH")
            force_refresh: If True, bypass cache and fetch from API
            
        Returns:
            {
                "success": bool,
                "data": {...},
                "source": str,
                "timestamp": str,
                "confidence": float
            }
        """
        # Step 1: Check KB cache (unless force refresh)
        if not force_refresh:
            cached_data = self.kb.get_cached_price_data(symbol)
            if cached_data and self._is_fresh(cached_data.get("price_timestamp")):
                return {
                    "success": True,
                    "data": {
                        "symbol": cached_data["symbol"],
                        "name": cached_data.get("name", "Unknown"),
                        "price": cached_data["last_price"],
                        "market_cap": cached_data["market_cap"],
                        "change_24h": cached_data.get("change_24h", 0),
                        "volume_24h": cached_data.get("volume_24h", 0),
                        "rank": cached_data.get("rank")
                    },
                    "source": "Knowledge Base",
                    "timestamp": cached_data["price_timestamp"],
                    "confidence": 1.0
                }
        
        # Step 2: Fetch from FreeCryptoAPI
        api_response = self._fetch_from_api(symbol)
        
        if api_response["success"]:
            # Step 3: Cache result in KB
            self._cache_to_kb(symbol, api_response["data"])
            
            return {
                "success": True,
                "data": api_response["data"],
                "source": "FreeCryptoAPI",
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.9
            }
        
        # Step 3: FreeCryptoAPI failed, try CoinGecko as fallback
        print(f"FreeCryptoAPI failed for {symbol}, trying CoinGecko...")
        coingecko_response = self._fetch_from_coingecko(symbol)
        
        if coingecko_response["success"]:
            # Cache CoinGecko result in KB
            self._cache_to_kb(symbol, coingecko_response["data"])
            
            return {
                "success": True,
                "data": coingecko_response["data"],
                "source": "CoinGecko API",
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.9
            }
        else:
            # Both APIs failed
            return {
                "success": False,
                "data": None,
                "source": None,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.0
            }
    
    def _fetch_from_api(self, symbol: str) -> Dict:
        """Fetch data from FreeCryptoAPI"""
        try:
            response = requests.get(
                f"{self.base_url}/getData",
                params={"symbol": symbol},
                headers={"X-API-KEY": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": {
                        "symbol": symbol,
                        "name": data.get("name", "Unknown"),
                        "price": float(data.get("price", 0)),
                        "market_cap": float(data.get("market_cap", 0)),
                        "change_24h": float(data.get("change_24h", 0)),
                        "volume_24h": float(data.get("volume_24h", 0)),
                        "rank": int(data.get("rank", 0))
                    }
                }
            else:
                return {"success": False, "data": None}
        except Exception as e:
            print(f"FreeCryptoAPI Error: {e}")
            return {"success": False, "data": None}
    
    def _fetch_from_coingecko(self, symbol: str) -> Dict:
        """Fetch data from CoinGecko API as fallback"""
        try:
            # CoinGecko uses coin IDs, need to map symbols to IDs
            symbol_to_id = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "ADA": "cardano",
                "XRP": "ripple",
                "DOT": "polkadot",
                "MATIC": "matic-network",
                "AVAX": "avalanche-2",
                "LINK": "chainlink",
                "UNI": "uniswap"
            }
            
            coin_id = symbol_to_id.get(symbol.upper())
            if not coin_id:
                print(f"CoinGecko: Unknown symbol {symbol}")
                return {"success": False, "data": None}
            
            # CoinGecko free API endpoint
            response = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", {})
                
                return {
                    "success": True,
                    "data": {
                        "symbol": symbol.upper(),
                        "name": data.get("name", "Unknown"),
                        "price": float(market_data.get("current_price", {}).get("usd", 0)),
                        "market_cap": float(market_data.get("market_cap", {}).get("usd", 0)),
                        "change_24h": float(market_data.get("price_change_percentage_24h", 0)),
                        "volume_24h": float(market_data.get("total_volume", {}).get("usd", 0)),
                        "rank": int(market_data.get("market_cap_rank", 0))
                    }
                }
            else:
                return {"success": False, "data": None}
        except Exception as e:
            print(f"CoinGecko API Error: {e}")
            return {"success": False, "data": None}
    
    def _cache_to_kb(self, symbol: str, data: Dict):
        """Cache API response to Knowledge Base"""
        self.kb.update_price_data(symbol, data)
    
    def _is_fresh(self, timestamp_str: str) -> bool:
        """Check if cached data is still fresh"""
        if not timestamp_str:
            return False
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
            age = now - timestamp
            return age < self.freshness_ttl
        except:
            return False


class CryptoNewsTool:
    """Tool for fetching crypto news"""
    
    def __init__(self, api_key: str, kb_manager, freshness_ttl_minutes: int = 60):
        self.api_key = api_key
        self.base_url = "https://cryptonewsapi.com/api/v1"
        self.kb = kb_manager
        self.freshness_ttl = timedelta(minutes=freshness_ttl_minutes)
    
    def get_news(self, symbol: str) -> Dict:
        """
        Fetch news for a cryptocurrency
        
        Args:
            symbol: Coin symbol
            
        Returns:
            News response dict
        """
        # Step 1: Check KB cache
        cached_news = self.kb.get_cached_news(symbol)
        if cached_news and self._is_fresh(cached_news.get("timestamp")):
            return {
                "success": True,
                "data": cached_news["items"],
                "source": "Knowledge Base",
                "timestamp": cached_news["timestamp"],
                "confidence": 1.0
            }
        
        # Step 2: Fetch from API
        try:
            # Placeholder for actual API call
            # using a public free news endpoint for demonstration if key fails
            # But using the configured key/url structure
            response = requests.get(
                self.base_url + "/category",
                params={
                    "section": "general",
                    "items": 3,
                    "token": self.api_key,
                    "tickers": symbol
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                news_items = []
                for item in data.get("data", [])[:3]:
                    news_items.append({
                        "title": item.get("title"),
                        "url": item.get("news_url"),
                        "source": item.get("source_name"),
                        "date": item.get("date")
                    })
                
                if news_items:
                    self.kb.update_news_data(symbol, news_items)
                    return {
                        "success": True,
                        "data": news_items,
                        "source": "CryptoNewsAPI",
                        "timestamp": datetime.now().isoformat(),
                        "confidence": 0.9
                    }
        except Exception as e:
            print(f"News API Error: {e}")
            
        return {
            "success": False,
            "data": None,
            "source": None,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.0
        }
    
    def _is_fresh(self, timestamp_str: str) -> bool:
        """Check if cached data is still fresh (default 60 mins for news)"""
        if not timestamp_str:
            return False
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
            age = now - timestamp
            return age < self.freshness_ttl
        except:
            return False
    
    def get_price(self, symbol: str) -> Dict:
        """Get only price for a cryptocurrency"""
        result = self.get_crypto_data(symbol)
        
        if result["success"]:
            return {
                "success": True,
                "price": result["data"]["price"],
                "symbol": result["data"]["symbol"],
                "source": result["source"],
                "timestamp": result["timestamp"],
                "confidence": result["confidence"]
            }
        else:
            return {
                "success": False,
                "price": None,
                "symbol": symbol,
                "source": None,
                "timestamp": result["timestamp"],
                "confidence": 0.0
            }
    
    
    # Static mapping for CoinGecko (demo purposes - normally would fetch list)
    COINGECKO_IDS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "ADA": "cardano",
        "XRP": "ripple",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "UNI": "uniswap"
    }
    
    def get_history(self, symbol: str, date: str) -> Dict:
        """
        Get historical price for a date
        
        Args:
            symbol: Coin symbol
            date: Date string (YYYY-MM-DD)
        """
        # Step 1: Check KB cache
        cached = self.kb.get_price_history(symbol, date)
        if cached:
            return {
                "success": True,
                "data": cached,
                "source": "Knowledge Base",
                "confidence": 1.0
            }
        
        # Step 2: Fetch from CoinGecko (best for history)
        return self._fetch_history_from_coingecko(symbol, date)
    
    def _fetch_history_from_coingecko(self, symbol: str, date: str) -> Dict:
        """Fetch history from CoinGecko"""
        try:
            coin_id = self.COINGECKO_IDS.get(symbol.upper())
            if not coin_id:
                return {"success": False, "data": None}
            
            # Convert YYYY-MM-DD to dd-mm-yyyy
            dt = datetime.strptime(date, "%Y-%m-%d")
            cg_date = dt.strftime("%d-%m-%Y")
            
            response = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}/history",
                params={
                    "date": cg_date,
                    "localization": "false"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", {})
                
                if not market_data:
                    return {"success": False, "data": None}
                
                price = market_data.get("current_price", {}).get("usd", 0)
                market_cap = market_data.get("market_cap", {}).get("usd", 0)
                
                # Cache to KB
                self.kb.add_price_history(symbol, date, price, market_cap)
                
                return {
                    "success": True,
                    "data": {
                        "date": date,
                        "price": price,
                        "market_cap": market_cap,
                        "symbol": symbol
                    },
                    "source": "CoinGecko API",
                    "confidence": 0.9
                }
            else:
                return {"success": False, "data": None}
        except Exception as e:
            print(f"History API Error: {e}")
            return {"success": False, "data": None}

    def get_market_cap(self, symbol: str) -> Dict:
        """Get only market cap for a cryptocurrency"""
        result = self.get_crypto_data(symbol)
        
        if result["success"]:
            return {
                "success": True,
                "market_cap": result["data"]["market_cap"],
                "symbol": result["data"]["symbol"],
                "source": result["source"],
                "timestamp": result["timestamp"],
                "confidence": result["confidence"]
            }
        else:
            return {
                "success": False,
                "market_cap": None,
                "symbol": symbol,
                "source": None,
                "timestamp": result["timestamp"],
                "confidence": 0.0
            }
