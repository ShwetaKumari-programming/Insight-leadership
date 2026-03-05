let messagesContainer;
let ws = null;
let wsConnected = false;
let currentAssistantText = "";
let isStreaming = false;

const CHAT_STORAGE_KEY = "upi_chat_history_v1";
let chatHistory = [];

function updateConnectionStatus(connected) {
    const status = document.getElementById("connectionStatus");
    if (!status) return;
    status.textContent = connected ? "Online" : "Offline";
    status.style.background = connected ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)";
}

function connectWebSocket() {
    return new Promise((resolve, reject) => {
        if (ws && wsConnected) {
            resolve();
            return;
        }

        ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
        wsConnected = false;

        ws.onopen = () => {
            wsConnected = true;
            updateConnectionStatus(true);
            resolve();
        };

        ws.onclose = () => {
            wsConnected = false;
            updateConnectionStatus(false);
        };

        ws.onerror = (err) => {
            wsConnected = false;
            updateConnectionStatus(false);
            reject(err);
        };
    });
}

function createMessageNode(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message message-${sender}`;
    messageDiv.dataset.role = sender;

    const content = document.createElement("div");
    content.className = "message-content";

    const textNode = document.createElement("div");
    textNode.className = "message-text";
    textNode.innerHTML = formatMessageText(text);
    content.appendChild(textNode);

    if (sender === "bot") {
        const actions = document.createElement("div");
        actions.className = "message-actions";

        const copyBtn = document.createElement("button");
        copyBtn.className = "copy-btn";
        copyBtn.textContent = "Copy";
        copyBtn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(textNode.textContent || "");
                copyBtn.textContent = "Copied";
                setTimeout(() => {
                    copyBtn.textContent = "Copy";
                }, 1200);
            } catch (_) {
                copyBtn.textContent = "Failed";
                setTimeout(() => {
                    copyBtn.textContent = "Copy";
                }, 1200);
            }
        });

        actions.appendChild(copyBtn);
        content.appendChild(actions);
    }

    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return messageDiv;
}

function formatMessageText(text) {
    let formatted = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#039;");

    formatted = formatted.replace(/\n/g, "<br>");
    formatted = formatted.replace(/https?:\/\/[^\s]+/g, (match) => `<a href="${match}" target="_blank" rel="noopener noreferrer">${match}</a>`);
    return formatted;
}

function loadHistory() {
    try {
        const raw = localStorage.getItem(CHAT_STORAGE_KEY);
        if (!raw) return;
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return;

        chatHistory = parsed;
        chatHistory.forEach((msg) => {
            const sender = msg.role === "assistant" ? "bot" : "user";
            createMessageNode(msg.content || "", sender);
        });
    } catch (_) {
        chatHistory = [];
    }
}

function saveHistory() {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(chatHistory.slice(-50)));
}

function addUserMessageToHistory(text) {
    chatHistory.push({ role: "user", content: text });
    saveHistory();
}

function addAssistantMessageToHistory(text) {
    chatHistory.push({ role: "assistant", content: text });
    saveHistory();
}

function findLastUserMessage() {
    for (let i = chatHistory.length - 1; i >= 0; i -= 1) {
        if (chatHistory[i].role === "user") return chatHistory[i].content;
    }
    return null;
}

function removeLastAssistantMessage() {
    for (let i = chatHistory.length - 1; i >= 0; i -= 1) {
        if (chatHistory[i].role === "assistant") {
            chatHistory.splice(i, 1);
            break;
        }
    }
    saveHistory();

    const botNodes = [...messagesContainer.querySelectorAll('[data-role="bot"]')];
    if (botNodes.length > 0) {
        botNodes[botNodes.length - 1].remove();
    }
}

async function sendMessage(overrideQuestion = null, isRegenerate = false) {
    if (isStreaming) return;

    const inputField = document.getElementById("messageInput");
    const question = (overrideQuestion || inputField.value || "").trim();
    if (!question) return;

    try {
        await connectWebSocket();
    } catch (_) {
        createMessageNode("Connection error. Please try again.", "bot");
        return;
    }

    currentAssistantText = "";
    isStreaming = true;

    if (!isRegenerate) {
        createMessageNode(question, "user");
        addUserMessageToHistory(question);
        inputField.value = "";
    }

    const assistantNode = createMessageNode("", "bot");
    const messageTextNode = assistantNode.querySelector(".message-text");

    ws.onmessage = (event) => {
        if (event.data === "__END__") {
            isStreaming = false;
            addAssistantMessageToHistory(currentAssistantText.trim());
            return;
        }
        currentAssistantText += event.data;
        messageTextNode.innerHTML = formatMessageText(currentAssistantText);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    ws.send(JSON.stringify({
        message: question,
        history: chatHistory.slice(-12)
    }));
}

function stopStreaming() {
    if (!isStreaming) return;
    isStreaming = false;
    if (ws) {
        ws.close();
        ws = null;
    }
}

function startNewChat() {
    chatHistory = [];
    saveHistory();
    messagesContainer.innerHTML = "";
    loadWelcomeMessage();
}

function regenerateResponse() {
    const lastUser = findLastUserMessage();
    if (!lastUser || isStreaming) return;
    removeLastAssistantMessage();
    sendMessage(lastUser, true);
}

function exportChat() {
    if (!chatHistory.length) return;

    const lines = chatHistory.map((msg) => `${msg.role.toUpperCase()}: ${msg.content}`);
    const text = lines.join("\n\n");
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function askQuickQuestion(question) {
    const inputField = document.getElementById("messageInput");
    inputField.value = question;
    sendMessage();
}

function loadWelcomeMessage() {
    createMessageNode("Hi, I am your AI analytics assistant. Ask about failures, trends, weekend patterns, and performance.", "bot");
}

function setupHandlers() {
    document.getElementById("messageInput")?.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById("newChatBtn")?.addEventListener("click", startNewChat);
    document.getElementById("regenerateBtn")?.addEventListener("click", regenerateResponse);
    document.getElementById("stopBtn")?.addEventListener("click", stopStreaming);
    document.getElementById("exportBtn")?.addEventListener("click", exportChat);

    document.querySelectorAll(".prompt-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const question = chip.getAttribute("data-question") || "";
            askQuickQuestion(question);
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    messagesContainer = document.getElementById("messagesContainer");
    setupHandlers();
    loadHistory();

    if (!chatHistory.length) {
        loadWelcomeMessage();
    }

    connectWebSocket().catch(() => {
        updateConnectionStatus(false);
    });
});
