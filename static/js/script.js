
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const chatMessages = document.getElementById("chatMessages");
const sendButton = document.getElementById("sendButton");
const chatHistoryList = document.getElementById("chatHistoryList");
// Store conversation history
let chatHistory = [];


function addMessage(message, sender) {

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);

    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");

    if (sender === "bot" && typeof marked !== "undefined") {
       const formattedMessage = marked.parse(message);

       messageContent.innerHTML = DOMPurify.sanitize(formattedMessage);
    } else {
        messageContent.textContent = message;
    }

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const message = userInput.value.trim();

    if (!message) return;

    addMessage(message, "user");

    userInput.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                history: chatHistory
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to get response");
        }

        addMessage(data.reply, "bot");

        // Save successful conversation messages
        chatHistory.push(
            { role: "user", text: message },
            { role: "model", text: data.reply }
        );
        await loadChatSessions();

    } catch (error) {
        addMessage(
            "Sorry, something went wrong. Please try again.",
            "bot"
        );

        console.error("Chat error:", error);

    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        userInput.focus();
    }
});

const clearChatButton = document.getElementById("clearChatButton");

clearChatButton.addEventListener("click", async function () {

    const confirmClear = confirm("Are you sure you want to clear this conversation?");

    if (!confirmClear) {
        return;
    }

    try {

        const response = await fetch("/api/clear", {
            method: "POST"
        });

        const data = await response.json();

        if (response.ok && data.success) {

            chatHistory = [];

            chatMessages.innerHTML = "";

            addMessage("Hi! I'm Candy 🍬 How can I help you today?", "bot");

        } else {
            alert("Unable to clear chat. Please try again.");
        }

    } catch (error) {

        console.error("Clear chat error:", error);

        alert("Something went wrong while clearing chat.");

    }

});
const manageMemoriesButton = document.getElementById("manageMemoriesButton");
const memoriesPanel = document.getElementById("memoriesPanel");
const memoriesList = document.getElementById("memoriesList");
const clearAllMemoriesButton = document.getElementById("clearAllMemoriesButton");

// Open or close the memories panel
manageMemoriesButton.addEventListener("click", async function () {

    if (memoriesPanel.style.display === "none") {
        memoriesPanel.style.display = "block";
        await loadMemories();
    } else {
        memoriesPanel.style.display = "none";
    }

});

// Load saved memories
async function loadMemories() {

    memoriesList.textContent = "Loading memories...";

    try {
        const response = await fetch("/api/memories");
        const data = await response.json();

        memoriesList.innerHTML = "";

        if (data.memories.length === 0) {
            memoriesList.innerHTML =
                '<p class="memory-empty">Candy has no saved memories yet.</p>';
            return;
        }

        data.memories.forEach(memory => {

            const memoryItem = document.createElement("div");
            memoryItem.className = "memory-item";

            const preferenceText = document.createElement("span");
            preferenceText.textContent = memory.preference;

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Delete";

            deleteButton.addEventListener("click", async function () {
                await deleteMemory(memory.id);
            });

            memoryItem.appendChild(preferenceText);
            memoryItem.appendChild(deleteButton);

            memoriesList.appendChild(memoryItem);

        });

    } catch (error) {
        console.error("Load memories error:", error);
        memoriesList.textContent = "Unable to load memories.";
    }
}

// Delete one memory
async function deleteMemory(memoryId) {

    const confirmed = confirm("Delete this memory?");

    if (!confirmed) return;

    try {
        const response = await fetch(
            `/api/memories/delete/${memoryId}`,
            { method: "DELETE" }
        );

        const data = await response.json();

        if (response.ok && data.success) {
            await loadMemories();
        } else {
            alert("Unable to delete memory.");
        }

    } catch (error) {
        console.error("Delete memory error:", error);
        alert("Something went wrong.");
    }
}

// Clear all memories
clearAllMemoriesButton.addEventListener("click", async function () {

    const confirmed = confirm(
        "Are you sure you want to delete all saved memories?"
    );

    if (!confirmed) return;

    try {
        const response = await fetch("/api/memories/clear", {
            method: "DELETE"
        });

        const data = await response.json();

        if (response.ok && data.success) {
            await loadMemories();
            alert("All memories cleared successfully!");
        } else {
            alert("Unable to clear memories.");
        }

    } catch (error) {
        console.error("Clear all memories error:", error);
        alert("Something went wrong.");
    }
});
// New Chat button
const newChatButton = document.getElementById("newChatButton");

newChatButton.addEventListener("click", async function () {

    const confirmed = confirm("Start a new chat? Your current conversation will be cleared.");

    if (!confirmed) return;

    try {
        const response = await fetch("/api/clear", {
            method: "POST"
        });

        const data = await response.json();

        if (response.ok && data.success) {

            chatHistory = [];

            chatMessages.innerHTML = "";

            addMessage(
                "Hi there! I'm Candy 🍬 I'm your personal AI assistant. What would you like to do today?",
                "bot"
            );

            memoriesPanel.style.display = "none";

        } else {
            alert("Unable to start a new chat.");
        }

    } catch (error) {
        console.error("New chat error:", error);
        alert("Something went wrong.");
    }

});
// Load saved conversations in sidebar
// Open a saved conversation
async function openSavedChat(sessionId) {

    try {
        const response = await fetch(`/api/chats/${sessionId}`);
        const data = await response.json();

        if (!response.ok || !data.success) {
            alert("Unable to open this conversation.");
            return;
        }

        chatHistory = [];
        chatMessages.innerHTML = "";

        data.messages.forEach(message => {

            const sender = message.role === "user" ? "user" : "bot";

            addMessage(message.text, sender);

            chatHistory.push({
                role: message.role === "user" ? "user" : "model",
                text: message.text
            });

        });

        // Highlight the selected conversation
        document.querySelectorAll(".chat-history-item").forEach(item => {

            item.classList.toggle(
                "active",
                item.dataset.sessionId === sessionId
            );

        });

    } catch (error) {

        console.error("Open saved chat error:", error);
        alert("Something went wrong while opening this chat.");

    }
}
// Delete a saved conversation
async function deleteChat(sessionId) {

    const confirmed = confirm(
        "Are you sure you want to delete this conversation?"
    );

    if (!confirmed) return;

    try {

        const response = await fetch(`/api/chats/${sessionId}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (response.ok && data.success) {

            // If the deleted chat is currently open, clear the screen
            if (document.querySelector(
                `.chat-history-item[data-session-id="${sessionId}"].active`
            )) {

                chatHistory = [];
                chatMessages.innerHTML = "";

                addMessage(
                    "Hi there! I'm Candy 🍬 What would you like to do today?",
                    "bot"
                );
            }

            await loadChatSessions();

        } else {
            alert("Unable to delete conversation.");
        }

    } catch (error) {

        console.error("Delete chat error:", error);
        alert("Something went wrong while deleting this chat.");

    }
}
// Load saved conversations in sidebar

async function loadChatSessions() {

    chatHistoryList.textContent = "Loading chats...";

    try {
        const response = await fetch("/api/chats");
        const data = await response.json();

        chatHistoryList.innerHTML = "";

        if (!data.chats || data.chats.length === 0) {
            chatHistoryList.innerHTML =
                '<p class="chat-history-empty">No previous chats yet.</p>';
            return;
        }

        data.chats.forEach(chat => {

            const chatItem = document.createElement("div");
            chatItem.className = "chat-history-item";
            chatItem.dataset.sessionId = chat.session_id;

            const chatTitle = document.createElement("span");
            chatTitle.textContent = chat.title || "New Conversation";

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "🗑️";
            deleteButton.className = "delete-chat-button";
            deleteButton.title = "Delete conversation";

            deleteButton.addEventListener("click", function(event) {
                event.stopPropagation();
                deleteChat(chat.session_id);
            });

            chatItem.appendChild(chatTitle);
            chatItem.appendChild(deleteButton);

            chatItem.addEventListener("click", function() {
                openSavedChat(chat.session_id);
            });

            chatHistoryList.appendChild(chatItem);
        });

    } catch (error) {
        console.error("Chat history error:", error);
        chatHistoryList.textContent = "Unable to load chats.";
    }
}

// Load saved chats when the page opens
loadChatSessions();