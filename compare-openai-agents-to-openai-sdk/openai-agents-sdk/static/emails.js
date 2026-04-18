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
  const res = await fetch("/api/email-logs");
  const logs = await res.json();

  const tbody = document.getElementById("tbody");
  const empty = document.getElementById("empty");
  const stats = document.getElementById("stats");

  if (logs.length === 0) {
    empty.style.display = "block";
    return;
  }

  stats.innerHTML = `
    <div class="stat"><span class="stat-value">${logs.length}</span><span class="stat-label">Emails sent</span></div>`;

  tbody.innerHTML = logs.map(l => `
    <tr>
      <td class="dim">${l.id}</td>
      <td><span class="user-badge">${escapeHtml(l.user_id.slice(0, 8))}</span></td>
      <td>${escapeHtml(l.email)}</td>
      <td class="dim">${formatDate(l.created_at)}</td>
    </tr>`).join("");
}

load();
