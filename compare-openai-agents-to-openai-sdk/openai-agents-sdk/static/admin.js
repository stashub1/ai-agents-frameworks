function formatDate(ts) {
  return new Date(ts * 1000).toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

async function load() {
  const res = await fetch("/api/admin/sessions");
  const sessions = await res.json();

  const tbody   = document.getElementById("adminBody");
  const empty   = document.getElementById("adminEmpty");
  const stats   = document.getElementById("adminStats");

  if (sessions.length === 0) {
    empty.style.display = "block";
    return;
  }

  // Stats
  const users = new Set(sessions.map(s => s.user_id)).size;
  stats.innerHTML = `
    <div class="stat"><span class="stat-value">${sessions.length}</span><span class="stat-label">Sessions</span></div>
    <div class="stat"><span class="stat-value">${users}</span><span class="stat-label">Users</span></div>
    <div class="stat"><span class="stat-value">${sessions.reduce((n, s) => n + s.message_count, 0)}</span><span class="stat-label">Messages</span></div>`;

  // Table rows
  tbody.innerHTML = sessions.map(s => `
    <tr>
      <td><a class="session-link" href="/?session=${s.id}">${escapeHtml(s.title)}</a></td>
      <td class="dim">${s.id.slice(0, 8)}</td>
      <td><span class="user-badge">${s.user_id.slice(0, 8)}</span></td>
      <td class="num">${s.message_count}</td>
      <td class="dim">${formatDate(s.updated_at)}</td>
      <td class="dim">${formatDate(s.created_at)}</td>
    </tr>`).join("");
}

load();
