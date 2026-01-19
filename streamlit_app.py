import streamlit as st
import sys
import os
import uuid

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from config import Config
    from knowledge_base import KnowledgeBaseManager
    from crypto_tools import FreeCryptoAPITool, CryptoNewsTool
    from memory import SessionManager
    from detector import CryptoQueryDetector
    from llm_orchestrator import LLMOrchestrator
    from pipeline import KnowledgeFirstPipeline
except ImportError as e:
    st.error(f"Error importing backend components: {e}")
    st.info("Make sure you are running this from the project root directory.")
    st.stop()

# Page Config
st.set_page_config(
    page_title="Agentic Crypto Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .source-tag {
        font-size: 0.8em;
        padding: 2px 8px;
        border-radius: 12px;
        margin-left: 8px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .source-kb { border-color: #10b981; color: #10b981; }
    .source-api { border-color: #3b82f6; color: #3b82f6; }
    .source-gecko { border-color: #8b5cf6; color: #8b5cf6; }
    .source-news { border-color: #f43f5e; color: #f43f5e; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'messages' not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def get_components():
    """Initialize backend components once"""
    try:
        Config.validate()
        
        kb_manager = KnowledgeBaseManager(Config.KB_FILE_PATH)
        session_manager = SessionManager(Config.KNOWN_COINS)
        llm_orchestrator = LLMOrchestrator(Config.OPENAI_API_KEY)
        
        api_tool = FreeCryptoAPITool(
            api_key=Config.FREECRYPTO_API_KEY,
            kb_manager=kb_manager,
            freshness_ttl_minutes=Config.FRESHNESS_TTL_MINUTES
        )
        
        news_tool = CryptoNewsTool(
            api_key=Config.CRYPTONEWS_API_KEY,
            kb_manager=kb_manager
        )
        
        return kb_manager, session_manager, llm_orchestrator, api_tool, news_tool
    except Exception as e:
        st.error(f"Component Initialization Error: {e}")
        return None, None, None, None, None

# Load components
kb_manager, session_manager, llm_orchestrator, api_tool, news_tool = get_components()

if not all([kb_manager, session_manager, llm_orchestrator, api_tool]):
    st.stop()

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")
    if st.button("Reset Conversation", type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        session_manager.clear_session(st.session_state.session_id)
        st.rerun()
    
    st.markdown("### System Status")
    st.success(f"Knowledge Base: {len(kb_manager.get_all_coins())} coins")
    st.info("API Connections: Active")

# Main Interface
st.title("🤖 Agentic Crypto Assistant")
st.markdown("Ask about prices, history, news, or compare coins!")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                # Get memory for session
                memory = session_manager.get_memory(st.session_state.session_id)
                
                # Init per-request components
                detector = CryptoQueryDetector(Config.KNOWN_COINS, memory)
                
                pipeline = KnowledgeFirstPipeline(
                    kb_manager=kb_manager,
                    api_tool=api_tool,
                    news_tool=news_tool,
                    detector=detector,
                    memory=memory,
                    llm_orchestrator=llm_orchestrator
                )
                
                # Detect and add to memory
                detection = detector.detect(prompt)
                memory.add_turn("user", prompt, detection["detected_entity"])
                
                # Run pipeline
                result = pipeline.process_query(prompt)
                formatted_response = pipeline.format_final_response(result)
                
                # Add source styling if needed (basic markdown for now)
                final_output = formatted_response
                
                st.markdown(final_output)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": final_output})
                memory.add_turn("assistant", formatted_response, result["entity"])
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
