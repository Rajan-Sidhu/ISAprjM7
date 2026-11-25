const who = document.querySelector("#who");
const errorBox = document.querySelector("#admin-error");
const dashboard = document.querySelector("#dashboard");

function when(value) {
  return new Date(value).toLocaleString();
}

function textCell(value) {
  const td = document.createElement("td");
  td.textContent = value ?? "—";
  return td;
}

function fill(table, rows, cells) {
  table.innerHTML = "";
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of cells(row)) {
      const td = document.createElement("td");
      td.textContent = value ?? "—";
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
}

document.querySelector("#logout").addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  window.location.href = "index.html";
});

async function boot() {
  let me;
  try {
    me = await api("/api/auth/me");
  } catch {
    window.location.href = "index.html";
    return;
  }
  who.textContent = me.user.email;
  try {
    const [users, stats] = await Promise.all([
      api("/api/admin/users"),
      api("/api/admin/stats"),
    ]);
    dashboard.hidden = false;
    document.querySelector("#total-users").textContent = stats.totals.users;
    document.querySelector("#total-plans").textContent = stats.totals.plans;
    document.querySelector("#total-requests").textContent = stats.totals.requests;
    const userRows = document.querySelector("#user-rows");
    userRows.innerHTML = "";
    for (const user of users.users) {
      const tr = document.createElement("tr");
      const email = document.createElement("td");
      email.textContent = user.email;
      const role = document.createElement("td");
      role.className = user.role === "admin" ? "role-admin" : "role-user";
      role.textContent = user.role;
      for (const cell of [
        email,
        role,
        textCell(user.plan_count),
        textCell(user.request_count),
        textCell(when(user.created_at)),
      ]) {
        tr.appendChild(cell);
      }
      userRows.appendChild(tr);
    }
    fill(document.querySelector("#endpoint-rows"), stats.by_endpoint, (row) => [
      row.method,
      row.endpoint,
      String(row.count),
    ]);
    fill(document.querySelector("#recent-rows"), stats.recent, (row) => [
      when(row.created_at),
      row.email || "anonymous",
      `${row.method} ${row.endpoint}`,
      String(row.status_code),
    ]);
  } catch (error) {
    dashboard.hidden = true;
    errorBox.textContent = `${error.status || ""} ${error.message}`.trim();
  }
}

boot();
