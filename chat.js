/**
 * Chat.js - Conversational AI chat interface
 * Handles message sending and receiving from the auto-routing backend
 */

let messagesContainer;


// WebSocket connection for real-time chat
let ws = null;
let wsConnected = false;

function connectWebSocket() {
    if (ws && wsConnected) return;
    ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
    wsConnected = false;

    ws.onopen = () => {
        wsConnected = true;
        console.log('WebSocket connected');
    };
    ws.onclose = () => {
        wsConnected = false;
        console.log('WebSocket disconnected');
    };
    ws.onerror = (e) => {
        wsConnected = false;
        console.error('WebSocket error:', e);
    };
}

async function sendMessage() {
    connectWebSocket();
    const inputField = document.querySelector('#messageInput') || document.querySelector('.message-input');
    const question = inputField.value.trim();
    if (!question) return;

    // Display user message
    displayMessage(question, 'user');
    inputField.value = '';

    // Prepare bot message for streaming
    let botMsgDiv = document.createElement('div');
    botMsgDiv.className = 'message message-bot';
    let msgContent = document.createElement('div');
    msgContent.className = 'message-content';
    let msgText = document.createElement('div');
    msgText.className = 'message-text';
    msgContent.appendChild(msgText);
    botMsgDiv.appendChild(msgContent);
    messagesContainer.appendChild(botMsgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Show loading indicator
    showLoadingIndicator();

    // Send question and stream response
    if (ws && wsConnected) {
        ws.send(question);
        let fullResponse = '';
        ws.onmessage = (event) => {
            if (event.data === '__END__') {
                hideLoadingIndicator();
                // Optionally, trigger follow-up UI here
                return;
            }
            fullResponse += event.data;
            msgText.textContent = fullResponse;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        };
    } else {
        hideLoadingIndicator();
        msgText.textContent = 'Connection error. Please check your internet connection and try again.';
    }
}

// Alias for backward compatibility
async function sendChatMessage() {
    return sendMessage();
}

function displayMessage(text, sender, type = '') {
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${sender}`;
    
    if (type) {
        const typeTag = `<span class="message-type">${type.replace(/_/g, ' ').toUpperCase()}</span>`;
        messageDiv.innerHTML = `<div class="message-content">${typeTag}<div class="message-text">${formatMessageText(text)}</div></div>`;
    } else {
        messageDiv.innerHTML = `<div class="message-content"><div class="message-text">${text}</div></div>`;
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displayExplanation(explanationText) {
    if (!messagesContainer) return;
    
    const explanationDiv = document.createElement('div');
    explanationDiv.className = 'message-explanation';
    explanationDiv.innerHTML = `
        <div class="explanation-header">
            <span class="explanation-icon">💡</span>
            <span class="explanation-title">Why this happened:</span>
        </div>
        <div class="explanation-content">
            ${formatMessageText(explanationText)}
        </div>
    `;
    
    messagesContainer.appendChild(explanationDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displayMetadata(metadata) {
    if (!messagesContainer) return;
    
    const metadataDiv = document.createElement('div');
    metadataDiv.className = 'message-metadata';
    metadataDiv.innerHTML = `
        <span class="metadata-item">Analysis Type: <strong>${metadata.type.replace(/_/g, ' ')}</strong></span>
        <span class="metadata-item">Processing Time: <strong>${metadata.processingTime.toFixed(3)}s</strong></span>
    `;
    
    messagesContainer.appendChild(metadataDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add contextual dashboard drill-down links based on analysis type
function addDashboardDrillDowns(questionType) {
    if (!messagesContainer) return;
    
    // Define drill-down options for each analysis type
    const guidedExploration = {
        'failure_analysis': {
            primary: { 
                link: '/failures', 
                text: '🔴 View Error Breakdown',
                description: 'See detailed breakdown by error code and patterns'
            },
            secondary: [
                { link: '/weekend', text: '📅 Weekend Analysis', description: 'Compare weekend vs weekday failures' },
                { link: '/dashboard', text: '📊 Overview', description: 'Back to main metrics' }
            ]
        },
        'weekend_analysis': {
            primary: { 
                link: '/weekend', 
                text: '📅 View Weekend Comparison',
                description: 'See detailed weekend vs weekday breakdown with charts'
            },
            secondary: [
                { link: '/failures', text: '🔴 Failure Details', description: 'Drill into failure codes' },
                { link: '/dashboard', text: '📊 Overview', description: 'See full metrics dashboard' }
            ]
        },
        'performance_analysis': {
            primary: { 
                link: '/performance', 
                text: '⚡ View Performance Dashboard',
                description: 'See latency trends, percentiles, and APDEX scores'
            },
            secondary: [
                { link: '/trends', text: '📈 Trends', description: 'View performance history and forecasts' },
                { link: '/dashboard', text: '📊 Overview', description: 'Back to main dashboard' }
            ]
        },
        'trend_analysis': {
            primary: { 
                link: '/trends', 
                text: '📈 View Trends & Forecast',
                description: 'See historical trends, predictions, and anomaly detection'
            },
            secondary: [
                { link: '/performance', text: '⚡ Performance Metrics', description: 'View latency and throughput' },
                { link: '/dashboard', text: '📊 Overview', description: 'See full dashboard' }
            ]
        },
        'comparison': {
            primary: { 
                link: '/weekend', 
                text: '📅 View Detailed Comparison',
                description: 'See side-by-side metrics with visual charts'
            },
            secondary: [
                { link: '/failures', text: '🔴 Error Analysis', description: 'Break down by error type' },
                { link: '/dashboard', text: '📊 Overview', description: 'Main dashboard' }
            ]
        }
    };
    
    const exploration = guidedExploration[questionType] || {
        primary: { 
            link: '/dashboard', 
            text: '📊 View Dashboard',
            description: 'Explore the data with visual charts'
        },
        secondary: [
            { link: '/failures', text: '🔴 Failures', description: 'Error analysis' },
            { link: '/weekend', text: '📅 Weekend', description: 'Weekend comparison' }
        ]
    };
    
    // Create the drill-down suggestion
    const drillDownDiv = document.createElement('div');
    drillDownDiv.className = 'message drill-down-suggestion';
    
    const primaryDescription = exploration.primary.description;
    
    let secondaryHTML = '';
    if (exploration.secondary && exploration.secondary.length > 0) {
        secondaryHTML = '<p style="margin: 12px 0 0 0; font-size: 0.85em; color: #777;"><strong>Or explore:</strong></p>';
        secondaryHTML += '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">';
        exploration.secondary.forEach(item => {
            secondaryHTML += `
                <a href="${item.link}" style="
                    padding: 6px 12px;
                    background: white;
                    border: 1.5px solid #667eea;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 0.8em;
                    font-weight: 500;
                    transition: all 0.2s;
                    cursor: pointer;
                " 
                onmouseover="this.style.background='#667eea'; this.style.color='white';" 
                onmouseout="this.style.background='white'; this.style.color='#667eea';"
                title="${item.description}"
                >${item.text}</a>
            `;
        });
        secondaryHTML += '</div>';
    }
    
    drillDownDiv.innerHTML = `
        <div style="
            margin-top: 15px; 
            padding: 14px 16px; 
            background: linear-gradient(135deg, #f0f4ff 0%, #f5f1ff 100%);
            border-left: 4px solid #667eea;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        ">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 1.2em;">💡</span>
                <div>
                    <p style="margin: 0; font-size: 0.95em; color: #333;"><strong>Want to see this visually?</strong></p>
                    <p style="margin: 4px 0 0 0; font-size: 0.85em; color: #666;">${primaryDescription}</p>
                </div>
            </div>
            <a href="${exploration.primary.link}" style="
                display: inline-block;
                padding: 9px 18px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 0.9em;
                font-weight: 600;
                transition: all 0.2s;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                cursor: pointer;
            " 
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';" 
            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.3)';"
            >${exploration.primary.text}</a>
            ${secondaryHTML}
        </div>
    `;
    
    messagesContainer.appendChild(drillDownDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add guided follow-up suggestions based on question type
function addFollowUpSuggestions(questionType) {
    if (!messagesContainer) return;
    
    const followUpQuestions = {
        'failure_analysis': [
            '🔴 Which error code causes the most impact?',
            '📅 Are failures different on weekends?',
            '⏰ When do errors spike the most?'
        ],
        'weekend_analysis': [
            '🔴 What are the specific errors on weekends?',
            '📈 Is this pattern consistent week-to-week?',
            '⚡ How does performance compare?'
        ],
        'performance_analysis': [
            '📊 Why is latency increasing?',
            '📈 What are the recent trends?',
            '🔴 Links to any failures?'
        ],
        'trend_analysis': [
            '🔮 What does the forecast show?',
            '📊 Has anything changed recently?',
            '🔴 Are there related failures?'
        ]
    };
    
    const suggestions = followUpQuestions[questionType] || [];
    
    if (suggestions.length > 0) {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'message follow-up-suggestions';
        
        let suggestionsHTML = '<div style="margin-top: 15px; padding: 12px 14px; background: #f9f9f9; border-radius: 6px; border: 1px solid #e0e0e0;">';
        suggestionsHTML += '<p style="margin: 0 0 10px 0; font-size: 0.85em; color: #777;"><strong>Follow-up questions you could ask:</strong></p>';
        suggestionsHTML += '<div style="display: flex; flex-direction: column; gap: 6px;">';
        
        suggestions.forEach((suggestion, index) => {
            suggestionsHTML += `
                <button onclick="askQuickQuestion('${suggestion}')" style="
                    text-align: left;
                    padding: 8px 11px;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    font-size: 0.85em;
                    color: #333;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-family: inherit;
                "
                onmouseover="this.style.borderColor='#667eea'; this.style.backgroundColor='#f5f8ff';"
                onmouseout="this.style.borderColor='#ddd'; this.style.backgroundColor='white';"
                >${suggestion}</button>
            `;
        });
        
        suggestionsHTML += '</div></div>';
        suggestionDiv.innerHTML = suggestionsHTML;
        
        messagesContainer.appendChild(suggestionDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Quick question handler
function askQuickQuestion(question) {
    const inputField = document.querySelector('#messageInput') || document.querySelector('.message-input');
    if (inputField) {
        inputField.value = question;
        inputField.focus();
        // Optionally auto-send
        setTimeout(() => sendMessage(), 100);
    }
}

function formatMessageText(text) {
    // Escape HTML
    let formatted = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    // Add line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Make URLs clickable
    formatted = formatted.replace(
        /https?:\/\/[^\s]+/g,
        match => `<a href="${match}" target="_blank">${match}</a>`
    );
    
    return formatted;
}

function showLoadingIndicator() {
    if (!messagesContainer) return;
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message message-bot loading';
    loadingDiv.id = 'loading-indicator';
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideLoadingIndicator() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function setupChatInputListener() {
    // Try multiple selectors for compatibility
    const inputField = document.querySelector('#messageInput') || 
                      document.querySelector('.message-input') || 
                      document.querySelector('.chat-input');
    
    if (inputField) {
        // Enable Enter key to send message
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function setupQuickQuestions() {
    const quickQuestions = document.querySelectorAll('[data-question]');
    quickQuestions.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.getAttribute('data-question');
            const inputField = document.querySelector('#messageInput') || 
                              document.querySelector('.message-input') ||
                              document.querySelector('.chat-input');
            if (inputField) {
                inputField.value = question;
                sendMessage();
            }
        });
    });
}

function loadSampleMessage() {
    const message = "👋 Hi! I'm your analytics assistant. I can help you analyze failures, compare weekends vs weekdays, check performance metrics, and identify trends in your system. Try asking me questions like:\n\n• 'What is the current failure rate?'\n• 'Why did failures increase last weekend?'\n• 'Is our system getting slower?'\n• 'Compare weekends vs weekdays'\n• 'What errors are we seeing?'";
    
    displayMessage(message, 'bot');
}

function setupNavigationListeners() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat page loaded');
    
    // Try multiple selectors for the messages container
    messagesContainer = document.querySelector('#messagesContainer') || 
                       document.querySelector('.messages-container') ||
                       document.querySelector('.chat-messages');
    
    setupChatInputListener();
    setupQuickQuestions();
    setupNavigationListeners();
    
    // Show welcome message
    loadSampleMessage();
    
    // Focus on input field
    const inputField = document.querySelector('#messageInput') || 
                      document.querySelector('.message-input') || 
                      document.querySelector('.chat-input');
    if (inputField) {
        inputField.focus();
    }
});
