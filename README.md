# Agentic Crypto Assistant

An intelligent cryptocurrency chatbot with **strict data source validation**, **confidence scoring**, and **hallucination prevention**.

## 🎯 Key Features

### Hard Rules Implemented
- ✅ **NEVER** answers from LLM's own knowledge
- ✅ **ONLY** uses data from Knowledge Base or FreeCryptoAPI
- ✅ Returns "INSUFFICIENT DATA" when data is missing
- ✅ **Rejects** predictions, investment advice, and hypotheticals
- ✅ Every response includes **source attribution** and **confidence score**

### Core Capabilities
- 📊 **Knowledge-First Strategy**: Checks KB before calling API
- 🔄 **Smart Caching**: 5-minute TTL for price data
- 💬 **Conversation Memory**: Tracks last 8-10 turns, resolves pronouns
- 🎯 **Confidence Scoring**: 1.0 (KB), 0.9 (API), 0.0 (rejected)
- 🛡️ **Hallucination Prevention**: Multi-level validation guards

---

## 📁 Project Structure

```
crypto-chatbot/
├── backend/
│   ├── app.py                    # Flask REST API
│   ├── config.py                 # Configuration
│   ├── knowledge_base.py         # KB manager
│   ├── crypto_tools.py           # FreeCryptoAPI integration
│   ├── memory.py                 # Conversation memory
│   ├── detector.py               # Entity/intent detection
│   ├── llm_orchestrator.py       # LLM formatting
│   ├── pipeline.py               # Main processing pipeline
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example             # Environment template
│   └── knowledge/
│       └── coins.json            # Knowledge Base
├── frontend/
│   ├── index.html               # Chat interface
│   ├── styles.css               # Premium styling
│   └── app.js                   # Frontend logic
└── README.md
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- OpenAI API key
- FreeCryptoAPI key (free at https://freecryptoapi.com/panel)

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure API Keys

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
FREECRYPTO_API_KEY=your_freecrypto_api_key_here
```

### Step 3: Start Backend Server

```bash
python app.py
```

Server will start on `http://127.0.0.1:5000`

### Step 4: Open Frontend

Open `frontend/index.html` in your web browser.

Or serve with Python:
```bash
cd frontend
python -m http.server 8000
```

Then visit `http://localhost:8000`

---

## 💡 Example Queries

### ✅ Allowed Queries

**Metadata:**
- "What is Bitcoin?"
- "Tell me about Ethereum"
- "What consensus does Solana use?"

**Price Data:**
- "What is the price of BTC?"
- "ETH market cap"
- "How much is Cardano worth?"

**Follow-ups:**
- User: "What is Ethereum?"
- Bot: [Provides info]
- User: "What's its price?" ← Resolves "its" to Ethereum

### ❌ Rejected Queries

- "Will Bitcoin reach $100k?" (prediction)
- "Should I invest in Ethereum?" (investment advice)
- "What if Bitcoin crashes?" (hypothetical)

**Response:** "INSUFFICIENT DATA – Not found in Knowledge Base or API"

---

## 🏗️ Architecture

### Knowledge-First Pipeline

```
User Query
    ↓
Detect Entity & Intent
    ↓
Search Knowledge Base
    ↓
Check Freshness (< 5 min?)
    ↓
If Fresh → Answer from KB
If Stale/Missing → Call API → Update KB → Answer from API
If Still Missing → "INSUFFICIENT DATA"
    ↓
Attach Source + Confidence
```

### Confidence Scoring

| Source | Freshness | Confidence |
|--------|-----------|------------|
| KB (metadata) | Always fresh | **1.0** |
| KB (price) | < 5 minutes | **1.0** |
| FreeCryptoAPI | Direct fetch | **0.9** |
| Rejected query | N/A | **0.0** |

---

## 🧠 Knowledge Base

The Knowledge Base (`backend/knowledge/coins.json`) contains:

**Static Metadata:**
- Coin name, symbol
- Launch year, creator
- Consensus mechanism
- Chain type

**Cached Price Data:**
- Last price, market cap
- 24h change, volume
- Timestamp (for freshness validation)

**Included Coins:**
- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)
- Cardano (ADA)
- Ripple (XRP)

---

## 🔧 API Endpoints

### POST /api/chat
Main chat endpoint

**Request:**
```json
{
  "message": "What is Bitcoin?",
  "session_id": "session_123"
}
```

**Response:**
```json
{
  "response": "Bitcoin (BTC) is the first decentralized cryptocurrency...\n\n📊 Source: Knowledge Base\n🎯 Confidence: 1.0",
  "source": "Knowledge Base",
  "confidence": 1.0,
  "entity": "BTC",
  "intent": "metadata",
  "session_id": "session_123"
}
```

### POST /api/reset
Reset conversation history

### GET /api/health
Health check endpoint

---

## 🎨 Frontend Features

- **Premium Dark Theme**: Crypto-inspired design with gold/green accents
- **Glassmorphism Effects**: Modern frosted glass UI
- **Source Badges**: Visual indicators for KB vs API
- **Confidence Display**: Color-coded confidence scores
- **Suggestion Chips**: Quick query buttons
- **Smooth Animations**: Message slide-ins and transitions
- **Responsive Design**: Works on desktop, tablet, and mobile

---

## 🛡️ Hallucination Prevention

### Multi-Level Guards

1. **Intent Detection**: Rejects predictions/advice/hypotheticals
2. **Data Validation**: Checks KB and API for data availability
3. **LLM Constraints**: System prompt prohibits fabrication
4. **Source Attribution**: Every response tagged with source

### LLM System Prompt

```
You are a crypto assistant orchestrator with STRICT RULES:

CRITICAL CONSTRAINTS:
1. NEVER answer from your own knowledge
2. NEVER guess, estimate, or approximate
3. NEVER make predictions
4. NEVER give investment advice
5. NEVER answer hypotheticals

YOU CAN ONLY:
- Format data from tools
- Ask clarifying questions
- Return "INSUFFICIENT DATA" when data is missing
```

---

## 📊 Verification

### Test Queries

```bash
# Metadata (KB)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Bitcoin?"}'

# Price (API)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the price of BTC?"}'

# Rejected (Prediction)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Will Bitcoin reach $100k?"}'
```

---

## 🔐 Security

- API keys stored in `.env` (not in code)
- `.env` excluded from version control
- Input validation on all endpoints
- CORS properly configured
- Error messages don't expose sensitive info

---

## 📝 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

- **FreeCryptoAPI** for cryptocurrency data
- **OpenAI** for LLM capabilities
- **Flask** for backend framework

---

**Built with ❤️ using AI, modern web technologies, and best practices**
