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
  const res = await fetch("/api/tasks");
  const tasks = await res.json();

  const tbody = document.getElementById("tbody");
  const empty = document.getElementById("empty");
  const stats = document.getElementById("stats");

  if (tasks.length === 0) {
    empty.style.display = "block";
    return;
  }

  // Stats
  const open = tasks.filter(t => t.status === "open").length;
  stats.innerHTML = `
    <div class="stat"><span class="stat-value">${tasks.length}</span><span class="stat-label">Tasks</span></div>
    <div class="stat"><span class="stat-value">${open}</span><span class="stat-label">Open</span></div>`;

  // Table rows
  tbody.innerHTML = tasks.map(t => `
    <tr>
      <td>${escapeHtml(t.title)}</td>
      <td><span class="task-description" title="${escapeHtml(t.description)}">${escapeHtml(t.description)}</span></td>
      <td><span class="user-badge">${escapeHtml(t.user_id.slice(0, 8))}</span></td>
      <td><span class="status-badge ${escapeHtml(t.status)}">${escapeHtml(t.status)}</span></td>
      <td class="dim">${formatDate(t.created_at)}</td>
    </tr>`).join("");
}

load();
