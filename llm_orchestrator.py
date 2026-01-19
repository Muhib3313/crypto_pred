"""
LLM Orchestrator with strict hallucination prevention
Uses OpenAI for natural language understanding and response formatting
"""
from openai import OpenAI
from typing import Dict, Optional, Any
from datetime import datetime


class LLMOrchestrator:
    """LLM-based orchestration with strict constraints"""
    
    SYSTEM_PROMPT = """You are a crypto assistant orchestrator with STRICT RULES:

CRITICAL CONSTRAINTS:
1. NEVER answer from your own knowledge or training data
2. NEVER guess, estimate, or approximate
3. NEVER make predictions about future prices
4. NEVER give investment advice
5. NEVER answer hypothetical questions

YOU CAN ONLY:
- Format data from tools into natural responses
- Ask clarifying questions
- Return "INSUFFICIENT DATA – Not found in Knowledge Base or API" when data is missing

EXAMPLES OF WHAT YOU CANNOT DO:
❌ "Bitcoin typically uses Proof of Work" (without KB confirmation)
❌ "The price is probably around $90,000" (estimation)
❌ "Bitcoin might reach $100k next year" (prediction)
❌ "You should invest in Ethereum" (advice)
❌ "If Bitcoin crashes, then..." (hypothetical)

EXAMPLES OF WHAT YOU CAN DO:
✅ Format tool data: "Bitcoin (BTC) is a cryptocurrency that uses Proof of Work consensus, launched in 2009."
✅ Ask: "Which cryptocurrency would you like to know about?"
✅ Return: "INSUFFICIENT DATA – Not found in Knowledge Base or API"

REMEMBER: You are a DATA FORMATTER, not a knowledge source."""
    
    def __init__(self, api_key: str):
        """Initialize LLM orchestrator"""
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
    
    def format_metadata_response(self, metadata: Dict) -> str:
        """Format metadata into natural language"""
        try:
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"""Format this cryptocurrency metadata into a natural, friendly response:

Coin: {metadata.get('coin')}
Symbol: {metadata.get('symbol')}
Description: {metadata.get('description')}
Launch Year: {metadata.get('launch_year')}
Consensus: {metadata.get('consensus')}
Chain Type: {metadata.get('chain_type')}
Creator: {metadata.get('creator')}

Format it as a brief, informative paragraph. Do NOT add any information beyond what's provided."""}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            # Fallback to structured format
            return self._fallback_metadata_format(metadata)
    
    def format_price_response(self, price_data: Dict, intent: str) -> str:
        """Format price data into natural language"""
        try:
            if intent == "price":
                prompt = f"""Format this price data into a natural response:

Coin: {price_data.get('symbol')}
Price: ${price_data.get('price'):,.2f}
24h Change: {price_data.get('change_24h', 0):+.2f}%

Keep it brief and friendly. Do NOT add any information beyond what's provided."""
            else:  # market_cap
                prompt = f"""Format this market cap data into a natural response:

Coin: {price_data.get('symbol')}
Market Cap: ${price_data.get('market_cap', 0):,.0f}
Current Price: ${price_data.get('price'):,.2f}

Keep it brief and friendly. Do NOT add any information beyond what's provided."""
            
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            # Fallback to structured format
            return self._fallback_price_format(price_data, intent)
    
    def format_news_response(self, news_items: list, entity: str) -> str:
        """Format news items into natural language"""
        try:
            news_text = "\n".join([f"- {item['title']} ({item['source']})" for item in news_items])
            
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"""Format these news headlines for {entity} into a concise list.
Do NOT summarize opinions. Just list the facts/headlines.

News:
{news_text}

Format as a bulleted list."""}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._fallback_news_format(news_items)

    def _fallback_news_format(self, news_items: list) -> str:
        """Fallback formatting for news"""
        lines = ["Latest News:"]
        for item in news_items:
            lines.append(f"• {item['title']} - {item['source']}")
        return "\n".join(lines)
    
    def _fallback_metadata_format(self, metadata: Dict) -> str:
        """Fallback formatting for metadata"""
        parts = [f"{metadata.get('coin')} ({metadata.get('symbol')})"]
        
        if metadata.get('description'):
            parts.append(f"\n{metadata.get('description')}")
        
        details = []
        if metadata.get('launch_year'):
            details.append(f"Launch Year: {metadata.get('launch_year')}")
        if metadata.get('consensus'):
            details.append(f"Consensus: {metadata.get('consensus')}")
        if metadata.get('chain_type'):
            details.append(f"Chain Type: {metadata.get('chain_type')}")
        if metadata.get('creator'):
            details.append(f"Creator: {metadata.get('creator')}")
        
        if details:
            parts.append("\n\n• " + "\n• ".join(details))
        
        return "".join(parts)
    
    def _fallback_price_format(self, price_data: Dict, intent: str) -> str:
        """Fallback formatting for price data"""
        if intent == "price":
            return f"Current price of {price_data.get('symbol')}: ${price_data.get('price'):,.2f}"
        else:
            return f"Market cap of {price_data.get('symbol')}: ${price_data.get('market_cap', 0):,.0f}\n\n• Current Price: ${price_data.get('price'):,.2f}"
            
    def extract_date_from_query(self, query: str) -> str:
        """Extract target date from query in YYYY-MM-DD format"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            messages = [
                {"role": "system", "content": f"You are a date extractor. Today is {today}. Extract the target date from the user query in YYYY-MM-DD format. If date is relative (yesterday, last week, 3 days ago), calculate it. Return ONLY the date string (YYYY-MM-DD) with no other text. If no specific date found, return 'None'."},
                {"role": "user", "content": query}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=20
            )
            
            result = response.choices[0].message.content.strip()
            return None if result == 'None' else result
        except Exception as e:
            print(f"Date Extraction Error: {e}")
            return None

    def format_history_response(self, history_data: Dict) -> str:
        """Format history data into natural language"""
        try:
            prompt = f"""Format this historical price data into a natural response for {history_data.get('symbol')}:

Date: {history_data.get('date')}
Price: ${history_data.get('price'):,.2f}
Market Cap: ${history_data.get('market_cap'):,.0f}

Keep it brief and factual. Mention the date clearly."""
            
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"On {history_data.get('date')}, the price of {history_data.get('symbol')} was ${history_data.get('price'):,.2f}."
    
    def format_comparison_response(self, comparison_data: list) -> str:
        """Format comparison data into natural language with table"""
        try:
            # Prepare data summary for prompt
            data_str = ""
            for item in comparison_data:
                data_str += f"- {item.get('symbol')}: Price=${item.get('price')}, Rank={item.get('rank')}, MCap=${item.get('market_cap')}, Change24h={item.get('change_24h')}%\n"
            
            prompt = f"""Compare these cryptocurrencies based on the following data:
{data_str}

Format the response as:
1. A brief comparison sentence highlighting key differences (e.g., which is larger/more expensive).
2. A Markdown table with columns: Coin, Price, Market Cap, 24h Change, Rank.
3. Keep it factual and concise."""
            
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return "Unable to generate comparison table."
