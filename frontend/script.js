const API_URL = "";

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
    btnMic: document.getElementById("btn-mic"),
    btnSpeaker: document.getElementById("btn-speaker"),
    iconSpeakerOn: document.querySelector(".icon-speaker-on"),
    iconSpeakerOff: document.querySelector(".icon-speaker-off"),
    quickPrompts: document.getElementById("quick-prompts"),
    promptBtns: document.querySelectorAll(".prompt-btn"),
    themeToggle: document.getElementById("theme-toggle"),
    sunIcon: document.querySelector(".sun-icon"),
    moonIcon: document.querySelector(".moon-icon"),
    folderLinkInput: document.getElementById("folder-link"),
    chatOverlay: document.getElementById("chat-overlay"),
    btnDisconnect: document.getElementById("btn-disconnect"),
    btnClear: document.getElementById("btn-clear"),
    indexMetrics: document.getElementById("index-metrics"),
};

// ── Voice & Theme State ──
let voiceEnabled = true;
let isRecording = false;
let isDarkMode = localStorage.getItem("theme") !== "light"; // Default to dark
let recognition = null;
let availableVoices = [];

// Load voices
window.speechSynthesis.onvoiceschanged = () => {
    availableVoices = window.speechSynthesis.getVoices();
};

// Initialize Speech Recognition if available
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        els.chatInput.value = transcript;
        // Don't auto send, let them review
        // sendQuestion(); 
    };

    recognition.onend = () => {
        isRecording = false;
        els.btnMic.classList.remove("recording");
        els.chatInput.placeholder = "e.g. What is our refund policy?";
        els.chatInput.closest('.chat-input-wrapper').classList.remove("recording-active");
    };
    
    recognition.onerror = (e) => {
        console.error("Speech recognition error:", e);
        isRecording = false;
        els.btnMic.classList.remove("recording");
        els.chatInput.placeholder = "e.g. What is our refund policy?";
        els.chatInput.closest('.chat-input-wrapper').classList.remove("recording-active");
    };
} else {
    els.btnMic.style.display = "none"; // Hide if unsupported
}

// ── Check Status on Load ──
async function checkStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();
        
        // Update Auth
        if (data.drive_connected) {
            els.authDot.className = "dot green";
            els.authBadge.innerHTML = `<span class="dot green"></span> Connected as ${data.user_email || 'Drive'}`;
            els.btnConnect.innerHTML = "Reconnect Drive";
            els.btnConnect.classList.replace("primary", "secondary");
            els.btnSync.disabled = false;
            els.btnDisconnect.disabled = false;
        } else {
            els.btnDisconnect.disabled = true;
        }

        // Update Index Stats
        if (data.faiss_index_exists) {
            els.mStatus.textContent = "Ready";
            els.mStatus.style.color = "var(--success)";
            els.mDocs.textContent = data.unique_documents;
            els.mChunks.textContent = data.total_chunks_indexed;
            
            // Enable chat and Layman features
            // Enable chat and Layman features
            els.chatInput.disabled = false;
            els.btnSend.disabled = false;
            els.btnMic.disabled = false;
            els.btnSpeaker.disabled = false;
            els.quickPrompts.style.display = "flex";
            els.btnClear.disabled = false;
            els.indexMetrics.style.display = "block";
            if (els.chatOverlay) els.chatOverlay.style.display = "none";
            
            // Render Fetched Documents List
            const libraryDocs = document.getElementById("library-docs");
            const libraryEmpty = document.getElementById("library-empty");
            const fetchedDocsList = document.getElementById("fetched-docs-list");
            
            if (data.documents && data.documents.length > 0) {
                if (libraryDocs) libraryDocs.style.display = "block";
                if (libraryEmpty) libraryEmpty.style.display = "none";
                if (fetchedDocsList) {
                    fetchedDocsList.innerHTML = "";
                    data.documents.forEach(doc => {
                        const li = document.createElement("li");
                        li.className = "doc-list-item";
                        // If it's a URL/ID from gdown, we can just show the name. 
                        // If we want a link, we need to decide what it links to. We'll just show the name.
                        li.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg viewBox="0 0 24 24" width="16" height="16" stroke="var(--primary)" stroke-width="2" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                                <span style="font-weight: 500;">${doc.file_name}</span>
                            </div>
                        `;
                        fetchedDocsList.appendChild(li);
                    });
                }
            } else {
                if (libraryDocs) libraryDocs.style.display = "none";
                if (libraryEmpty) libraryEmpty.style.display = "block";
            }
        } else {
            els.btnClear.disabled = true;
            els.indexMetrics.style.display = "none";
            const libraryDocs = document.getElementById("library-docs");
            const libraryEmpty = document.getElementById("library-empty");
            if (libraryDocs) libraryDocs.style.display = "none";
            if (libraryEmpty) libraryEmpty.style.display = "block";
        }
    } catch (e) {
        console.error("Status check failed", e);
    }
}

// ── Theme Logic ──
function initTheme() {
    if (isDarkMode) {
        document.body.classList.add("dark");
        els.sunIcon.style.display = "none";
        els.moonIcon.style.display = "block";
    }
}

els.themeToggle.addEventListener("click", () => {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle("dark", isDarkMode);
    localStorage.setItem("theme", isDarkMode ? "dark" : "light");
    
    if (isDarkMode) {
        els.sunIcon.style.display = "none";
        els.moonIcon.style.display = "block";
    } else {
        els.sunIcon.style.display = "block";
        els.moonIcon.style.display = "none";
    }
});

// ── Tab Switching Logic ──
const tabBtns = document.querySelectorAll('.nav-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all
        tabBtns.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));
        
        // Add active class to clicked
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        document.getElementById(targetId).classList.add('active');
    });
});

// ── Event Listeners ──

els.btnConnect.addEventListener("click", () => {
    window.location.href = `${API_URL}/auth/login`;
});

els.btnDisconnect.addEventListener("click", async () => {
    if(!confirm("Are you sure you want to disconnect Google Drive?")) return;
    try {
        const res = await fetch(`${API_URL}/disconnect`, { method: "POST" });
        if(res.ok) {
            alert("Drive disconnected.");
            window.location.reload();
        } else {
            alert("Failed to disconnect.");
        }
    } catch(e) {
        alert("Network Error.");
    }
});

els.btnClear.addEventListener("click", async () => {
    if(!confirm("Are you sure you want to clear all synced FAISS data and downloads? This cannot be undone.")) return;
    try {
        const res = await fetch(`${API_URL}/clear-data`, { method: "POST" });
        if(res.ok) {
            alert("Synced data cleared!");
            window.location.reload();
        } else {
            alert("Failed to clear data.");
        }
    } catch(e) {
        alert("Network Error.");
    }
});

    // Input listener for dynamic button enablement
    els.folderLinkInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        // If they enter a valid folder link, enable Sync (even if not connected)
        if (val.match(/folders\/([a-zA-Z0-9_-]+)/)) {
            els.btnSync.disabled = false;
        } else {
            // Revert to connection status
            checkStatus();
        }
    });

    els.btnSync.addEventListener("click", async () => {
        const folderLink = els.folderLinkInput.value.trim();
        let folderId = null;
        
        if (folderLink) {
            // Extract ID from Google Drive folder link
            const match = folderLink.match(/folders\/([a-zA-Z0-9_-]+)/);
            if (match) {
                folderId = match[1];
            } else {
                els.syncStatus.textContent = "❌ Invalid Drive folder link.";
                return;
            }
        }

    els.btnSync.disabled = true;
    els.syncStatus.innerHTML = `<svg class="spinner" viewBox="25 25 50 50"><circle cx="50" cy="50" r="20" fill="none"></circle></svg> Syncing Drive...`;
    
    try {
        const res = await fetch(`${API_URL}/sync-drive`, { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ folder_id: folderId })
        });
        const data = await res.json();
        
        if (res.ok) {
            els.syncStatus.textContent = `✅ Synced ${data.files_processed} files (${data.total_new_chunks} chunks). Skipped ${data.files_skipped_unchanged}.`;
            // Enable Chat UI after successful sync even if anonymous
            els.chatInput.disabled = false;
            els.btnSend.disabled = false;
            els.btnMic.disabled = false;
            els.btnSpeaker.disabled = false;
            els.quickPrompts.style.display = "flex";
            els.btnClear.disabled = false;
            if (els.chatOverlay) els.chatOverlay.style.display = "none";
            
            checkStatus(); // Refresh stats
            fetchRecommendations(); // Fetch new context-aware questions
        } else {
            els.syncStatus.textContent = `❌ Error: ${data.detail || "Failed to sync"}`;
        }
    } catch (e) {
        els.syncStatus.textContent = `❌ Network Error`;
    } finally {
        els.btnSync.disabled = false;
    }
});

const btnSyncDemo = document.getElementById("btn-sync-demo");
const demoSyncStatus = document.getElementById("demo-sync-status");

if (btnSyncDemo) {
    btnSyncDemo.addEventListener("click", async () => {
        const demoFolderId = "1ZP8lXDro7XL3Kfyg2avmDwlSOcAgabc-";
        
        btnSyncDemo.disabled = true;
        demoSyncStatus.innerHTML = `<svg class="spinner" viewBox="25 25 50 50"><circle cx="50" cy="50" r="20" fill="none"></circle></svg> Fetching Demo Documents...`;
        
        try {
            const res = await fetch(`${API_URL}/sync-drive`, { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folder_id: demoFolderId })
            });
            const data = await res.json();
            
            if (res.ok) {
                demoSyncStatus.textContent = `✅ Successfully loaded and indexed ${data.files_processed} demo documents.`;
                // Switch to Library tab to show results
                const libTabBtn = document.querySelector('[data-tab="tab-library"]');
                if (libTabBtn) libTabBtn.click();
                
                checkStatus(); // Refresh stats
                fetchRecommendations(); // Fetch new context-aware questions
            } else {
                demoSyncStatus.textContent = `❌ Error: ${data.detail || "Failed to sync demo docs"}`;
            }
        } catch (e) {
            demoSyncStatus.textContent = `❌ Network Error`;
        } finally {
            btnSyncDemo.disabled = false;
        }
    });
}

async function fetchRecommendations() {
    try {
        const res = await fetch(`${API_URL}/recommend-questions`);
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.questions && data.questions.length > 0) {
            els.quickPrompts.innerHTML = "";
            data.questions.forEach(q => {
                const btn = document.createElement("button");
                btn.className = "prompt-btn";
                btn.textContent = q;
                btn.addEventListener("click", () => {
                    els.chatInput.value = q;
                    sendQuestion();
                });
                els.quickPrompts.appendChild(btn);
            });
            els.quickPrompts.style.display = "flex";
        }
    } catch (e) {
        console.error("Failed to fetch recommendations", e);
    }
}

// Quick Prompts
els.promptBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        els.chatInput.value = btn.textContent;
        sendQuestion();
    });
});

window.fillQuestion = function(q) {
    els.chatInput.value = q;
    els.chatInput.focus();
};

// Mic Toggle
els.btnMic.addEventListener("click", () => {
    if (!recognition) return;
    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
        isRecording = true;
        els.btnMic.classList.add("recording");
        els.chatInput.placeholder = "Listening... Speak now";
        els.chatInput.closest('.chat-input-wrapper').classList.add("recording-active");
    }
});

// Speaker Toggle (Global mute/unmute)
els.btnSpeaker.addEventListener("click", () => {
    voiceEnabled = !voiceEnabled;
    if (voiceEnabled) {
        els.iconSpeakerOn.style.display = "block";
        els.iconSpeakerOff.style.display = "none";
    } else {
        els.iconSpeakerOn.style.display = "none";
        els.iconSpeakerOff.style.display = "block";
        window.speechSynthesis.cancel(); // Stop current speech if any
    }
});

els.btnSend.addEventListener("click", sendQuestion);
els.chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendQuestion();
});

// Text to Speech (Female Voice)
window.speakText = function(text) {
    if (!voiceEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    
    // Clean markdown before speaking
    const cleanText = text.replace(/[*#_`]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "en-US";
    utterance.rate = 1.0;

    // Load voices if empty
    if (availableVoices.length === 0) {
        availableVoices = window.speechSynthesis.getVoices();
    }

    // Find female voice
    const femaleVoice = availableVoices.find(v => 
        v.name.includes('Female') || 
        v.name.includes('Samantha') || 
        v.name.includes('Victoria') ||
        v.name.includes('Karen') ||
        v.name.includes('Moira') ||
        v.name.includes('Google US English')
    );
    
    if (femaleVoice) {
        utterance.voice = femaleVoice;
    }
    
    window.speechSynthesis.speak(utterance);
}

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
                <div class="message-actions">
                    <button class="btn-play-dictation" title="Play Dictation">
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                        Listen
                    </button>
                </div>
                <div class="sources">
                    <strong>Sources:</strong> ${data.sources.map(s => `<a href="${s.link}" target="_blank" class="source-tag">${s.name}</a>`).join('')}
                </div>
            `;
            // Attach event listener instead of using inline onclick to prevent escaping bugs
            const playBtn = loadingEl.querySelector('.btn-play-dictation');
            playBtn.addEventListener('click', () => {
                speakText(data.answer);
            });
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
initTheme();
checkStatus();
fetchRecommendations();
