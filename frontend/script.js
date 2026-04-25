const API_URL = "http://localhost:8000";

const els = {
    btnConnect: document.getElementById("btn-connect"),
    btnSync: document.getElementById("btn-sync"),
    syncStatus: document.getElementById("sync-status"),
    authBadge: document.getElementById("auth-status"),
    authDot: document.querySelector(".status-badge .dot"),
    chatInput: document.getElementById("chat-input"),
    btnSend: document.getElementById("btn-send"),
    chatHistory: document.getElementById("chat-history"),
    mStatus: document.getElementById("metric-status"),
    mDocs: document.getElementById("metric-docs"),
    mChunks: document.getElementById("metric-chunks"),
};

// ── Check Status on Load ──
async function checkStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();
        
        // Update Auth
        if (data.drive_connected) {
            els.authDot.className = "dot green";
            els.authBadge.innerHTML = `<span class="dot green"></span> Connected`;
            els.btnConnect.innerHTML = "Reconnect Drive";
            els.btnConnect.classList.replace("primary", "secondary");
            els.btnSync.disabled = false;
        }

        // Update Index Stats
        if (data.faiss_index_exists) {
            els.mStatus.textContent = "Ready";
            els.mStatus.style.color = "var(--success)";
            els.mDocs.textContent = data.unique_documents;
            els.mChunks.textContent = data.total_chunks_indexed;
            
            // Enable chat
            els.chatInput.disabled = false;
            els.btnSend.disabled = false;
        }
    } catch (e) {
        console.error("Status check failed", e);
    }
}

// ── Event Listeners ──

els.btnConnect.addEventListener("click", () => {
    window.location.href = `${API_URL}/auth/login`;
});

els.btnSync.addEventListener("click", async () => {
    els.btnSync.disabled = true;
    els.syncStatus.innerHTML = `<svg class="spinner" viewBox="25 25 50 50"><circle cx="50" cy="50" r="20" fill="none"></circle></svg> Syncing Drive...`;
    
    try {
        const res = await fetch(`${API_URL}/sync-drive`, { method: "POST" });
        const data = await res.json();
        
        if (res.ok) {
            els.syncStatus.textContent = `✅ Synced ${data.files_processed} files (${data.total_new_chunks} chunks). Skipped ${data.files_skipped_unchanged}.`;
            checkStatus(); // Refresh stats
        } else {
            els.syncStatus.textContent = `❌ Error: ${data.detail || "Failed to sync"}`;
        }
    } catch (e) {
        els.syncStatus.textContent = `❌ Network Error`;
    } finally {
        els.btnSync.disabled = false;
    }
});

els.btnSend.addEventListener("click", sendQuestion);
els.chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendQuestion();
});

async function sendQuestion() {
    const query = els.chatInput.value.trim();
    if (!query) return;

    // Append User Message
    appendMessage("user", query);
    els.chatInput.value = "";
    els.btnSend.disabled = true;

    // Append Loading Assistant Message
    const loadingId = "loading-" + Date.now();
    appendMessage("assistant", "Thinking...", [], loadingId);

    try {
        const res = await fetch(`${API_URL}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });
        const data = await res.json();
        
        const loadingEl = document.getElementById(loadingId);
        if (res.ok) {
            loadingEl.querySelector('.message-content').innerHTML = `
                ${data.answer}
                <div class="sources">
                    <strong>Sources:</strong> ${data.sources.map(s => `<a href="${s.link}" target="_blank" class="source-tag">${s.name}</a>`).join('')}
                </div>
            `;
        } else {
            loadingEl.querySelector('.message-content').textContent = `Error: ${data.detail}`;
        }
    } catch (e) {
        document.getElementById(loadingId).querySelector('.message-content').textContent = "Network Error communicating with API.";
    } finally {
        els.btnSend.disabled = false;
        els.chatInput.focus();
    }
}

function appendMessage(role, text, sources = [], id = null) {
    const msg = document.createElement("div");
    msg.className = `message ${role}`;
    if (id) msg.id = id;
    
    let content = `<div class="message-content">${text}</div>`;
    msg.innerHTML = content;
    
    els.chatHistory.appendChild(msg);
    els.chatHistory.scrollTop = els.chatHistory.scrollHeight;
}

// Init
checkStatus();
