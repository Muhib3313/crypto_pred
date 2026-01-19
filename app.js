// Crypto Assistant - Frontend JavaScript

const API_URL = 'http://127.0.0.1:5000/api';
let sessionId = generateSessionId();

// DOM Elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const suggestionsContainer = document.getElementById('suggestions');

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
resetBtn.addEventListener('click', resetConversation);

// Suggestion chips
suggestionsContainer.addEventListener('click', (e) => {
    if (e.target.classList.contains('chip')) {
        const query = e.target.getAttribute('data-query');
        userInput.value = query;
        sendMessage();
    }
});

// Generate session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Send message
async function sendMessage() {
    const message = userInput.value.trim();

    if (!message) return;

    // Disable input
    userInput.disabled = true;
    sendBtn.disabled = true;

    // Add user message
    addMessage('user', message);

    // Clear input
    userInput.value = '';

    // Show loading indicator
    const loadingId = showLoading();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const data = await response.json();

        // Remove loading indicator
        removeLoading(loadingId);

        // Add assistant response
        addMessage('assistant', data.response, {
            source: data.source,
            confidence: data.confidence
        });

    } catch (error) {
        console.error('Error:', error);
        removeLoading(loadingId);
        addMessage('assistant', 'Sorry, I encountered an error. Please make sure the backend server is running.');
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Add message to chat
function addMessage(role, text, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user' ? '<span>👤</span>' : '<span>🤖</span>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';

    // Format text (preserve line breaks and structure)
    const formattedText = formatMessage(text);
    messageText.innerHTML = formattedText;

    // Add source tag if available
    if (metadata.source && metadata.confidence !== undefined) {
        const sourceTag = createSourceTag(metadata.source, metadata.confidence);
        messageText.appendChild(sourceTag);
    }

    content.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Format message text
function formatMessage(text) {
    // Convert line breaks to <br>
    let formatted = text.replace(/\n/g, '<br>');

    // Convert bullet points
    formatted = formatted.replace(/• /g, '<br>• ');

    // Convert source and confidence tags
    formatted = formatted.replace(/📊 Source: ([^<\n]+)/g, '');
    formatted = formatted.replace(/🎯 Confidence: ([^<\n]+)/g, '');

    return formatted;
}

// Create source tag
function createSourceTag(source, confidence) {
    const tag = document.createElement('div');
    tag.className = 'source-tag';

    // Determine source class
    if (source === 'Knowledge Base') {
        tag.classList.add('kb');
    } else if (source === 'FreeCryptoAPI') {
        tag.classList.add('api');
    } else if (source === 'CoinGecko API') {
        tag.classList.add('coingecko');
    } else if (source === 'CryptoNewsAPI') {
        tag.classList.add('news');
    }

    // Determine confidence class
    let confidenceClass = 'confidence-low';
    if (confidence >= 0.9) {
        confidenceClass = 'confidence-high';
    } else if (confidence >= 0.7) {
        confidenceClass = 'confidence-medium';
    }

    tag.innerHTML = `
        <span>📊 Source: <strong>${source}</strong></span>
        <span class="confidence-score ${confidenceClass}">🎯 ${confidence.toFixed(1)}</span>
    `;

    return tag;
}

// Show loading indicator
function showLoading() {
    const loadingId = 'loading_' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = loadingId;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<span>🤖</span>';

    const content = document.createElement('div');
    content.className = 'message-content';

    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.innerHTML = `
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
    `;

    content.appendChild(loading);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    return loadingId;
}

// Remove loading indicator
function removeLoading(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

// Reset conversation
async function resetConversation() {
    if (!confirm('Are you sure you want to start a new conversation?')) {
        return;
    }

    try {
        await fetch(`${API_URL}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });

        // Generate new session ID
        sessionId = generateSessionId();

        // Clear messages (keep welcome message)
        messagesContainer.innerHTML = '';

        // Add welcome message back
        addMessage('assistant', `Welcome! I'm your Agentic Crypto Assistant.

I can help you with:
• Cryptocurrency information and metadata
• Current prices and market caps
• Coin details (consensus, launch year, creator)

Note: I only provide factual data from my Knowledge Base and FreeCryptoAPI. I cannot make predictions or give investment advice.`);

    } catch (error) {
        console.error('Error resetting conversation:', error);
        alert('Failed to reset conversation');
    }
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Initialize
console.log('Crypto Assistant initialized');
console.log('Session ID:', sessionId);
