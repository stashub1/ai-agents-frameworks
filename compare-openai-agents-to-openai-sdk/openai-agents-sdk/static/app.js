// ── UUID ──────────────────────────────────────────────────
function generateId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

// ── State ─────────────────────────────────────────────────
let userId    = localStorage.getItem("userId")    || generateId();
let sessionId = localStorage.getItem("sessionId") || generateId();
let isStreaming = false;

localStorage.setItem("userId",    userId);
localStorage.setItem("sessionId", sessionId);

// ── DOM refs ──────────────────────────────────────────────
const messagesEl  = document.getElementById("messages");
const inputEl     = document.getElementById("input");
const sendBtn     = document.getElementById("send");
const newChatBtn  = document.getElementById("newChat");
const sessionList = document.getElementById("sessionList");
const headerTitle = document.getElementById("headerTitle");

// ── marked config ─────────────────────────────────────────
marked.setOptions({ breaks: true, gfm: true });

// ── Input behavior ────────────────────────────────────────
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + "px";
  sendBtn.disabled = inputEl.value.trim() === "" || isStreaming;
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!sendBtn.disabled) handleSend();
  }
});

sendBtn.addEventListener("click", handleSend);
newChatBtn.addEventListener("click", startNewChat);

// ── Helpers ───────────────────────────────────────────────
function getTime() {
  const now = new Date();
  return String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setStreaming(value) {
  isStreaming = value;
  inputEl.disabled = value;
  sendBtn.disabled = value || inputEl.value.trim() === "";
}

// ── Session sidebar ───────────────────────────────────────
async function loadSessions() {
  const res = await fetch(`/api/sessions?user_id=${userId}`);
  const sessions = await res.json();

  sessionList.innerHTML = "";

  if (sessions.length === 0) {
    sessionList.innerHTML = `<div class="no-sessions">No past sessions</div>`;
    return;
  }

  for (const s of sessions) {
    const el = document.createElement("div");
    el.className = "session-item" + (s.id === sessionId ? " active" : "");
    el.dataset.id = s.id;
    el.innerHTML = `
      <div class="session-title">${escapeHtml(s.title)}</div>
      <button class="session-delete" data-id="${s.id}" title="Delete">×</button>`;
    el.addEventListener("click", (e) => {
      if (!e.target.classList.contains("session-delete")) {
        switchSession(s.id, s.title);
      }
    });
    el.querySelector(".session-delete").addEventListener("click", async (e) => {
      e.stopPropagation();
      await deleteSession(s.id);
    });
    sessionList.appendChild(el);
  }
}

function markActiveSession() {
  document.querySelectorAll(".session-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === sessionId);
  });
}

async function switchSession(id, title) {
  sessionId = id;
  localStorage.setItem("sessionId", sessionId);
  markActiveSession();
  headerTitle.textContent = title || "Chat";

  // Load and render history
  const res = await fetch(`/api/sessions/${id}`);
  if (!res.ok) return;
  const { history } = await res.json();
  renderHistory(history);
}

async function deleteSession(id) {
  await fetch(`/api/sessions/${id}`, { method: "DELETE" });
  if (id === sessionId) {
    startNewChat();
  }
  await loadSessions();
}

function renderHistory(history) {
  messagesEl.innerHTML = "";
  for (const msg of history) {
    if (msg.role === "user") {
      appendUserMessage(msg.content, false);
    } else if (msg.role === "assistant") {
      const content = typeof msg.content === "string"
        ? msg.content
        : msg.content?.map(p => p.text || "").join("") || "";
      if (content) appendAssistantMessageStatic(content, msg.agent);
    }
  }
  scrollToBottom();
}

// ── DOM builders ──────────────────────────────────────────
function removeWelcome() {
  const el = document.getElementById("welcome");
  if (el) el.remove();
}

function appendUserMessage(text, animate = true) {
  removeWelcome();
  const el = document.createElement("div");
  el.className = "message user" + (animate ? "" : " no-anim");
  el.innerHTML = `
    <div class="msg-body">
      <div class="msg-content">${escapeHtml(text)}</div>
      <div class="msg-time">${getTime()}</div>
    </div>`;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function appendAssistantMessageStatic(text, agentName = null) {
  const el = document.createElement("div");
  el.className = "message assistant no-anim";
  const label = agentName
    ? `<div class="agent-label"><span class="agent-router">Router</span><span class="agent-arrow">→</span><span class="agent-name">${escapeHtml(agentName)}</span></div>`
    : "";
  el.innerHTML = `
    <div class="msg-avatar">◆</div>
    <div class="msg-body">
      ${label}
      <div class="msg-content">${marked.parse(text)}</div>
      <div class="msg-time">${getTime()}</div>
    </div>`;
  messagesEl.appendChild(el);
}

function appendTyping() {
  const el = document.createElement("div");
  el.className = "message assistant";
  el.innerHTML = `
    <div class="msg-avatar">◆</div>
    <div class="msg-body">
      <div class="typing-row">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
        <span class="typing-status"></span>
      </div>
    </div>`;
  messagesEl.appendChild(el);
  scrollToBottom();
  return el;
}

function setTypingStatus(typingEl, text) {
  const status = typingEl.querySelector(".typing-status");
  if (status) status.textContent = text;
}

function appendAssistantMessage(agentName = null) {
  const el = document.createElement("div");
  el.className = "message assistant";
  const label = agentName
    ? `<div class="agent-label"><span class="agent-router">Router</span><span class="agent-arrow">→</span><span class="agent-name">${escapeHtml(agentName)}</span></div>`
    : "";
  el.innerHTML = `
    <div class="msg-avatar">◆</div>
    <div class="msg-body">
      ${label}
      <div class="msg-content"></div>
      <div class="msg-time">${getTime()}</div>
    </div>`;
  messagesEl.appendChild(el);
  scrollToBottom();
  return el.querySelector(".msg-content");
}

// ── Send message ──────────────────────────────────────────
async function handleSend() {
  const text = inputEl.value.trim();
  if (!text || isStreaming) return;

  inputEl.value = "";
  inputEl.style.height = "auto";

  appendUserMessage(text);
  setStreaming(true);

  const typingEl = appendTyping();

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, user_id: userId, message: text }),
    });

    if (!response.ok) throw new Error(`Server error ${response.status}`);

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = "";
    let buffer = "";
    let contentEl = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") break;

        try {
          const parsed = JSON.parse(payload);
          if (parsed.routing) {
            setTypingStatus(typingEl, "routing…");
          } else if (parsed.agent) {
            typingEl.remove();
            contentEl = appendAssistantMessage(parsed.agent);
          } else if (parsed.content && contentEl) {
            fullContent += parsed.content;
            contentEl.innerHTML = marked.parse(fullContent);
            scrollToBottom();
          }
        } catch {
          // Ignore malformed SSE lines
        }
      }
    }

    // Refresh sidebar after response (title may now be set)
    await loadSessions();
    markActiveSession();

  } catch (err) {
    typingEl.remove();
    const contentEl = appendAssistantMessage();
    contentEl.textContent = "Error: " + err.message;
    console.error(err);
  } finally {
    setStreaming(false);
    inputEl.focus();
  }
}

// ── New chat ──────────────────────────────────────────────
function startNewChat() {
  sessionId = generateId();
  localStorage.setItem("sessionId", sessionId);
  headerTitle.textContent = "Chat";
  messagesEl.innerHTML = `
    <div class="welcome" id="welcome">
      <div class="welcome-diamond">◆</div>
      <h2>What can I help with?</h2>
      <p>Type a message below to begin.</p>
    </div>`;
  markActiveSession();
  inputEl.focus();
}

// ── Init ──────────────────────────────────────────────────
async function init() {
  await loadSessions();

  // If saved session exists on server, restore it
  const res = await fetch(`/api/sessions/${sessionId}`);
  if (res.ok) {
    const { history } = await res.json();
    // Get title from sidebar
    const item = document.querySelector(`.session-item[data-id="${sessionId}"]`);
    headerTitle.textContent = item?.querySelector(".session-title")?.textContent || "Chat";
    renderHistory(history);
  }

  inputEl.focus();
}

init();
